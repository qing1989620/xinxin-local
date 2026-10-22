import {
  test,
  expect,
  type Page,
  type APIRequestContext,
} from "@playwright/test";

async function login(page: Page, request: APIRequestContext) {
  const response = await request.post("/api/v1/auth/login", {
    data: {
      name: "BrowserOwner",
      password: "synthetic-browser-password-123",
    },
  });
  expect(response.ok()).toBe(true);
  const token = (await response.json()).token;
  await page.addInitScript(
    (value) => sessionStorage.setItem("xinxin-session", value),
    token,
  );
  return { Authorization: `Bearer ${token}` };
}

async function createRun(
  request: APIRequestContext,
  headers: Record<string, string>,
  permission: string,
  onCreated?: (run: any) => Promise<void>,
) {
  const response = await request.post("/api/v1/runs", {
    headers,
    data: {
      task: "合成 SkillNet 路线：使用 coding-workspace 方法写入一份说明文件。",
      permission,
      request_key: crypto.randomUUID(),
      max_calls: 8,
    },
  });
  expect(response.ok()).toBe(true);
  const created = await response.json();
  const id = created.id;
  await onCreated?.(created);
  await expect
    .poll(
      async () => {
        const detail = await request.get(`/api/v1/runs/${id}`, { headers });
        return (await detail.json()).status;
      },
      { timeout: 20_000 },
    )
    .not.toMatch(/^(queued|running|cancelling)$/);
  return (await request.get(`/api/v1/runs/${id}`, { headers })).json();
}

test("SkillNet：真实读取与工具证据在对话和历史中可见，连接本轮交付", async ({
  page,
  request,
}, testInfo) => {
  test.setTimeout(60_000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const headers = await login(page, request);
  // Observe a live run after the Agent has mounted. Cold-route performance is
  // measured separately, not conflated with a 3.6-second synthetic SSE run.
  await page.goto("/agent");
  await expect(
    page.getByRole("textbox", { name: "给 Agent 的任务" }),
  ).toBeVisible();
  const run = await createRun(
    request,
    headers,
    "workspace",
    async (created) => {
      await page.goto(`/agent?conversation=${created.conversation_id}`);
      const live = page.getByRole("region", { name: "SkillNet 本轮能力路线" });
      await expect(live).toBeVisible();
      await expect(live).toContainText("代码工作区");
      await expect(
        page.getByRole("button", { name: "停止当前任务" }),
      ).toBeVisible();
    },
  );
  expect(run.status).toBe("completed");
  expect(
    run.files.some(
      (file: { name: string }) => file.name === "skillnet-demo.txt",
    ),
  ).toBe(true);
  await page.goto(`/agent?conversation=${run.conversation_id}`);
  const route = page.getByRole("region", { name: "SkillNet 本轮能力路线" });
  await expect(route).toBeVisible();
  await route.locator("summary").click();
  const used = route
    .locator(".skillnet-cards li")
    .filter({ hasText: "参考读取 1 次" });
  await expect(used).toHaveCount(1);
  await expect(used).toContainText("关联工具成功返回 1 次");
  await used.getByRole("button").click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.locator(".skill-markdown")).not.toBeEmpty();
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await page.screenshot({
    path: `.qa-data/playwright/skillnet-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await route.getByRole("link", { name: "查看本轮结果与交付" }).click();
  await expect(page).toHaveURL(new RegExp(`/tasks\\?run=${run.id}`));
  await expect(
    page.getByText("skillnet-demo.txt", { exact: true }).first(),
  ).toBeVisible();
  // A newer round moves the earlier route into lazily loaded history.
  const next = await request.post("/api/v1/runs", {
    headers,
    data: {
      task: "一句简短的合成问候",
      conversation_id: run.conversation_id,
      request_key: crypto.randomUUID(),
      max_calls: 1,
    },
  });
  expect(next.ok()).toBe(true);
  await expect
    .poll(
      async () =>
        (
          await (
            await request.get(`/api/v1/runs/${(await next.json()).id}`, {
              headers,
            })
          ).json()
        ).status,
    )
    .toBe("completed");
  await page.goto(`/agent?conversation=${run.conversation_id}`);
  await expect(
    page.getByRole("region", { name: "SkillNet 本轮能力路线" }).last(),
  ).toContainText("本轮未选额外技能");
  const historical = page
    .getByRole("region", { name: "SkillNet 本轮能力路线" })
    .first();
  await historical.locator("summary").click();
  await expect(historical).toContainText("参考读取 1 次");
  await expect(historical).toContainText("关联工具成功返回 1 次");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
});

test("SkillNet：只读权限失败不会显示为工具成功", async ({ page, request }) => {
  test.setTimeout(60_000);
  const headers = await login(page, request);
  const run = await createRun(request, headers, "read");
  expect(run.status).toBe("failed");
  expect(run.files).toEqual([]);
  await page.goto(`/agent?conversation=${run.conversation_id}`);
  const route = page.getByRole("region", { name: "SkillNet 本轮能力路线" });
  await route.locator("summary").click();
  await expect(route).toContainText("参考读取 1 次");
  await expect(route).toContainText("有 1 次未成功返回");
  await expect(route).not.toContainText("关联工具成功返回");
});
