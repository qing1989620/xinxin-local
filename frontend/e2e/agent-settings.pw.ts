import { test, expect } from "@playwright/test";

for (const failFirst of [false, true]) {
  for (const resume of [false, true]) {
    test(`Agent：${resume ? "续接" : "发送"}在配置${failFirst ? "失败重试" : "延迟加载"}时保留草稿并等待就绪`, async ({
      page,
      request,
    }) => {
      const login = await request.post("/api/v1/auth/login", {
        data: {
          name: "BrowserOwner",
          password: "synthetic-browser-password-123",
        },
      });
      expect(login.ok()).toBe(true);
      const token = (await login.json()).token;
      await page.addInitScript(
        (token) => sessionStorage.setItem("xinxin-session", token),
        token,
      );
      let original: { id: string; conversation_id: string } | null = null;
      if (resume) {
        const headers = { Authorization: `Bearer ${token}` };
        const created = await request.post("/api/v1/runs", {
          headers,
          data: {
            task: "合成 SkillNet 路线：只读核验后取消。",
            permission: "read",
            request_key: crypto.randomUUID(),
          },
        });
        expect(created.ok()).toBe(true);
        original = await created.json();
        expect(
          (
            await request.post(`/api/v1/runs/${original!.id}/cancel`, {
              headers,
              data: {},
            })
          ).ok(),
        ).toBe(true);
        await expect
          .poll(
            async () =>
              (
                await (
                  await request.get(`/api/v1/runs/${original!.id}`, { headers })
                ).json()
              ).status,
          )
          .toBe("cancelled");
      }
      let release!: () => void;
      const ready = new Promise<void>((resolve) => {
        release = resolve;
      });
      let count = 0;
      await page.route("**/api/v1/settings", async (route) => {
        count++;
        if (failFirst && count === 1) {
          await route.fulfill({
            status: 503,
            json: { detail: "Synthetic configuration failure" },
          });
          return;
        }
        await ready;
        await route.continue();
      });
      try {
        await page.goto(
          original
            ? `/agent?conversation=${original.conversation_id}`
            : "/agent?new=1",
        );
        const draft = page.getByLabel("给 Agent 的任务");
        const send = page.getByRole("button", {
          name: original ? "继续原任务" : "发送任务",
          exact: true,
        });
        await draft.fill("一句简短的合成问候");
        await expect(send).toBeDisabled();
        if (failFirst) {
          await expect(
            page.getByRole("alert").filter({ hasText: "你的草稿已保留" }),
          ).toBeVisible();
          await page.screenshot({
            path: `.qa-data/agent-readiness/error-${resume ? "resume" : "submit"}-${test.info().project.name}.png`,
            fullPage: true,
          });
          await page.getByRole("button", { name: "重新读取任务配置" }).click();
        }
        await expect(
          page.getByRole("status").filter({ hasText: "正在读取任务配置" }),
        ).toBeVisible();
        await expect(draft).toHaveValue("一句简短的合成问候");
        await page.screenshot({
          path: `.qa-data/agent-readiness/loading-${resume ? "resume" : "submit"}-${test.info().project.name}.png`,
          fullPage: true,
        });
        release();
        await expect(send).toBeEnabled();
        const submitPath = original
          ? `/api/v1/runs/${original.id}/continue`
          : "/api/v1/runs";
        const submittedRequests: string[] = [];
        page.on("request", (outgoing) => {
          if (
            outgoing.method() === "POST" &&
            outgoing.url().endsWith(submitPath)
          )
            submittedRequests.push(outgoing.url());
        });
        const submitted = page.waitForResponse(
          (response) =>
            response.url().endsWith(submitPath) &&
            response.request().method() === "POST",
        );
        await send.click();
        const response = await submitted;
        expect(response.ok()).toBe(true);
        if (original) {
          expect((await response.json()).conversation_id).toBe(
            original.conversation_id,
          );
          expect(response.request().postDataJSON().instruction).toBe(
            "一句简短的合成问候",
          );
        }
        await expect(draft).toHaveValue("");
        expect(submittedRequests).toHaveLength(1);
      } finally {
        release();
        if (!page.isClosed())
          await page.unrouteAll({ behavior: "ignoreErrors" });
      }
    });
  }
}
