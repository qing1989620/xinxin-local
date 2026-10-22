import { test, expect } from "@playwright/test";

const credentials = {
  name: "BrowserOwner",
  password: "synthetic-browser-password-123",
};

test("真实后端：登录及全部一级页面冒烟", async ({ page }) => {
  test.setTimeout(90_000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.goto("/music");
  await page.getByLabel("主人账号").fill(credentials.name);
  await page.getByLabel("密码", { exact: true }).fill(credentials.password);
  await page
    .locator(
      ".auth-panel button[type=submit], .auth-panel .form-stack button.primary",
    )
    .click();
  await expect(page.getByRole("heading", { name: "背景音乐" })).toBeVisible();
  const paths = [
    "/",
    "/agent",
    "/tasks",
    "/files",
    "/servers",
    "/skills",
    "/learning",
    "/content",
    "/tools",
    "/music",
    "/memories",
    "/schedules",
    "/settings",
  ];
  for (const path of paths) {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main.main")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "界面出了一点问题" }),
    ).toHaveCount(0);
    await expect(page.locator("main.main .error-state")).toHaveCount(0);
  }
  expect(errors).toEqual([]);
});

test("真实后端：档位保存与辅导历史跨页面恢复", async ({ page, request }) => {
  // Several full navigations, reloads and a real tutor round share this budget.
  // Keep assertion timeouts strict; allow the whole journey under CI/CPU load.
  test.setTimeout(60_000);
  const login = await request.post("/api/v1/auth/login", { data: credentials });
  expect(login.ok()).toBe(true);
  const token = (await login.json()).token;
  await page.addInitScript(
    (value) => sessionStorage.setItem("xinxin-session", value),
    token,
  );
  const headers = { Authorization: `Bearer ${token}` };
  const books = await request.get("/api/v1/learning/books", { headers });
  const book = (await books.json()).books.find(
    (item: { title: string }) => item.title === "合成浏览器讲义",
  );
  const quiz = await request.post("/api/v1/learning/quiz", {
    headers,
    data: { book_id: book.id, count: 1 },
  });
  const session = (await quiz.json()).session;
  const qid = session.questions[0].id;
  await page.goto("/music");
  await page.getByRole("radio", { name: "敏感", exact: true }).check();
  await expect(
    page.getByRole("radio", { name: "敏感", exact: true }),
  ).toBeEnabled();
  await page.reload();
  await expect(
    page.getByRole("radio", { name: "敏感", exact: true }),
  ).toBeChecked();
  await page.goto(`/learning/quiz/${session.id}`);
  await page.getByRole("button", { name: "Xinxin 辅导", exact: true }).click();
  await page.getByRole("button", { name: "让Xinxin讲这道" }).click();
  await expect(page.locator(".tutor-log li.assistant")).not.toHaveCount(0);
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Xinxin 辅导", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".tutor-log li.assistant")).not.toHaveCount(0);
  const history = await request.get(
    `/api/v1/learning/questions/${qid}/tutor?mode=xinxin`,
    { headers },
  );
  expect((await history.json()).history.length).toBeGreaterThanOrEqual(2);
  await page.getByRole("button", { name: "普通老师", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "让老师讲这道" }),
  ).toBeEnabled();
  const normalHistory = await request.get(
    `/api/v1/learning/questions/${qid}/tutor`,
    { headers },
  );
  expect((await normalHistory.json()).history).toEqual([]);
});
