import { test, expect } from "@playwright/test";

for (const failFirst of [false, true]) {
  test(`Agent：配置${failFirst ? "失败重试" : "延迟加载"}时保留草稿并在就绪后发送`, async ({
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
    await page.addInitScript(
      (token) => sessionStorage.setItem("xinxin-session", token),
      (await login.json()).token,
    );
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
      await page.goto("/agent?new=1");
      const draft = page.getByLabel("给 Agent 的任务");
      const send = page.getByRole("button", { name: "发送任务", exact: true });
      await draft.fill("一句简短的合成问候");
      await expect(send).toBeDisabled();
      if (failFirst) {
        await expect(page.getByRole("alert")).toContainText("你的草稿已保留");
        await page.screenshot({
          path: `.qa-data/agent-readiness/error-${test.info().project.name}.png`,
          fullPage: true,
        });
        await page.getByRole("button", { name: "重新读取任务配置" }).click();
      }
      await expect(
        page.getByRole("status").filter({ hasText: "正在读取任务配置" }),
      ).toBeVisible();
      await expect(draft).toHaveValue("一句简短的合成问候");
      await page.screenshot({
        path: `.qa-data/agent-readiness/loading-${test.info().project.name}.png`,
        fullPage: true,
      });
      release();
      await expect(send).toBeEnabled();
      const submitted = page.waitForResponse(
        (response) =>
          response.url().endsWith("/api/v1/runs") &&
          response.request().method() === "POST",
      );
      await send.click();
      expect((await submitted).ok()).toBe(true);
      await expect(draft).toHaveValue("");
    } finally {
      release();
      await page.unrouteAll({ behavior: "ignoreErrors" });
    }
  });
}
