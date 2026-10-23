import { test, expect } from "@playwright/test";

// Route the isolated app through a non-trustworthy HTTP origin. This keeps the
// browser's real secure-context restrictions; it never opens a LAN listener.
const origin = "http://xinxin.invalid";
test.afterEach(async ({ page }) => {
  // Import navigation starts background reads; drain the proxy before teardown.
  await page.unrouteAll({ behavior: "wait" });
});
test("局域网 HTTP：上传、Agent 连续提交及学习导入可用", async ({
  page,
  request,
}) => {
  test.setTimeout(90_000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route(origin + "/**", async (route) => {
    const target = route
      .request()
      .url()
      .replace(origin, "http://127.0.0.1:5187");
    const headers = { ...route.request().headers(), host: "127.0.0.1:5187" };
    await route.fulfill({
      response: await route.fetch({ url: target, headers }),
    });
  });
  const login = await request.post("/api/v1/auth/login", {
    data: { name: "BrowserOwner", password: "synthetic-browser-password-123" },
  });
  expect(login.ok()).toBe(true);
  const { token } = await login.json();
  await page.addInitScript(
    (value) => sessionStorage.setItem("xinxin-session", value),
    token,
  );
  await page.goto(origin + "/files");
  expect(
    await page.evaluate(() => ({
      secure: isSecureContext,
      uuid: typeof crypto.randomUUID,
      digest: typeof crypto.subtle,
    })),
  ).toEqual({ secure: false, uuid: "undefined", digest: "undefined" });
  const filename = `synthetic-lan-${test.info().project.name}.txt`;
  const uploaded = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/files") &&
      response.request().method() === "POST",
  );
  await page.locator('input[type="file"]').setInputFiles({
    name: filename,
    mimeType: "text/plain",
    buffer: Buffer.from(
      "第一章 导数\n" +
        "导数刻画瞬时变化率，几何意义是函数图像在该点的切线斜率。\n".repeat(12),
    ),
  });
  const fileResponse = await uploaded;
  expect(fileResponse.ok()).toBe(true);
  const file = await fileResponse.json();
  await expect(
    page.locator(".library-file-row").filter({ hasText: filename }),
  ).toBeVisible();
  await page.goto(origin + "/agent");
  for (const task of ["一句简短的合成问候", "再给我一句简短的合成问候"]) {
    await page.getByLabel("给 Agent 的任务").fill(task);
    const submitted = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/v1/runs") &&
        response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "发送任务", exact: true }).click();
    const response = await submitted;
    expect(response.ok()).toBe(true);
    const run = await response.json();
    await expect
      .poll(async () =>
        (
          await request.get(`/api/v1/runs/${run.id}`, {
            headers: { Authorization: `Bearer ${token}` },
          })
        )
          .json()
          .then((value) => value.status),
      )
      .toBe("completed");
    await expect(
      page.getByRole("button", { name: "发送任务", exact: true }),
    ).toBeVisible();
  }
  await page.goto(origin + "/learning");
  await page.getByRole("button", { name: "加入书架", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("combobox").selectOption(file.id);
  const imported = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/learning/imports") &&
      response.request().method() === "POST",
  );
  await dialog
    .getByRole("button", { name: "加入并开始学习", exact: true })
    .click();
  expect((await imported).ok()).toBe(true);
  await expect(page).toHaveURL(/\/learning\/books\//);
  expect(errors).toEqual([]);
});
