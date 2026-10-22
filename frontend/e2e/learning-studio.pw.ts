import {
  test,
  expect,
  type Page,
  type APIRequestContext,
} from "@playwright/test";

const credentials = {
  name: "BrowserOwner",
  password: "synthetic-browser-password-123",
};
async function fixture(page: Page, request: APIRequestContext, visual = false) {
  const login = await request.post("/api/v1/auth/login", { data: credentials });
  expect(login.ok()).toBeTruthy();
  const token = (await login.json()).token;
  await page.addInitScript(
    (value) => sessionStorage.setItem("xinxin-session", value),
    token,
  );
  const headers = { Authorization: `Bearer ${token}` };
  const marker = crypto.randomUUID();
  const text = visual
    ? `第一章 理解变化\n\n从平均变化率，到瞬时变化率\n\n一辆车在一小时内行驶了 60 公里，我们说它的平均速度是每小时 60 公里。但在某一个瞬间，它可能正在加速，也可能正在减速。描述这一瞬间的变化，需要一个更精确的工具：导数。\n\n设函数 $f(x)$ 在点 $x_0$ 附近有定义。当自变量增加 $h$ 时，平均变化率为：\n\n$$\\frac{f(x_0+h)-f(x_0)}{h}$$\n\n让 $h$ 趋近于零，如果这个比值趋向一个确定的数，这个数就是函数在该点的导数。它描述变化发生的快慢，而非函数值本身的大小。\n\n在几何上，导数就是曲线在这一点的切线斜率。斜率为正，函数局部上升；斜率为负，函数局部下降。\n\n试着想一想：函数值很大时，导数一定很大吗？一辆车停在山顶，位置很高，速度却可以为零。区分“状态”和“变化”，是理解导数的第一步。\n\n第二章 从概念到应用\n\n以 $f(x)=x^2$ 为例，导数是 $f'(x)=2x$。在 $x=1$ 处，切线的斜率为 2；在 $x=0$ 处，切线是水平的。导数为零只是极值的必要条件之一，还需要结合邻域内的变化判断。\n\n学习时应先理解变化率的含义，再掌握计算规则，最后通过图像核对直觉。不要把公式的熟练程度当作概念理解的全部。`
    : "第一章 理解变化\n\n" +
      Array.from(
        { length: 130 },
        (_, index) =>
          `第${index}段 ${marker}：导数刻画瞬时变化率，几何意义是函数图像在该点的切线斜率。\n`,
      ).join("") +
      "\n第二章 从概念到应用\n\n" +
      "理解导数后可以把变化率应用到速度和增长分析。\n".repeat(30);
  const uploaded = await request.post("/api/v1/files", {
    headers,
    multipart: {
      file: {
        name: "微积分 · 从概念到理解.txt",
        mimeType: "text/plain",
        buffer: Buffer.from(text),
      },
    },
  });
  const added = await request.post("/api/v1/learning/books", {
    headers,
    data: { file_id: (await uploaded.json()).id, subject: "数学" },
  });
  expect(added.ok()).toBeTruthy();
  const book = (await added.json()).book;
  await page.goto(`/learning/books/${book.id}`);
  await expect(
    page.getByRole("heading", { name: book.title, exact: true }),
  ).toBeVisible();
  await expect(page.locator(".study-unit input").first()).toBeVisible();
  return { book, headers };
}
async function panel(page: Page, name: string) {
  const tabs = page.getByRole("navigation", { name: "工作室面板" });
  if (await tabs.isVisible())
    await tabs.getByRole("button", { name, exact: true }).click();
}
async function configure(page: Page, focus = "") {
  await panel(page, "出题");
  await page.getByLabel("每个片段", { exact: true }).selectOption("1");
  await page.getByLabel("填空", { exact: true }).uncheck();
  await page.getByLabel("简答", { exact: true }).uncheck();
  await page.getByLabel("难度", { exact: true }).selectOption("2");
  await page.getByLabel("考查重点").fill(focus);
}

test("真实出题：范围、定制、刷新恢复、原文依据和练习", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(err.message));
  const { book, headers } = await fixture(page, request);
  await page.locator(".study-unit input").nth(0).check();
  await page.locator(".study-unit input").nth(1).check();
  await configure(page, "合成延迟：理解几何意义");
  const started = page.waitForResponse(
    (response) =>
      response.url().endsWith("/generations") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "生成这一组题", exact: true }).click();
  expect((await started).ok()).toBeTruthy();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "本次出题完成", exact: true }),
  ).toBeVisible({ timeout: 15_000 });
  const progress = page.getByRole("progressbar", { name: "题目入库进度" });
  await expect(progress).toHaveAttribute("aria-valuenow", "2");
  await expect(page.locator(".study-question-bank li")).toHaveCount(2);
  await page.getByRole("button", { name: "核对原文依据" }).first().click();
  const dialog = page.getByRole("dialog", { name: "回到原文" });
  await expect(dialog.locator(".study-quote")).toContainText("出题依据");
  await expect(dialog.locator(".study-source-text")).toContainText(
    "导数刻画瞬时变化率",
  );
  await dialog.getByRole("button", { name: "关闭对话框" }).click();
  await page.getByRole("button", { name: "全书练习", exact: true }).click();
  await expect(page.locator(".quiz-shell")).toBeVisible();
  await page.getByRole("button", { name: "回到原文，寻找线索" }).click();
  await expect(page.getByRole("dialog", { name: "回到原文" })).toBeVisible();
  expect(errors).toEqual([]);
  const response = await request.get(
    `/api/v1/learning/books/${book.id}/sources`,
    { headers },
  );
  expect(
    (await response.json()).sources.filter(
      (unit: { question_count: number }) => unit.question_count > 0,
    ),
  ).toHaveLength(2);
});

test("真实任务取消，随后仅补出缺少的题", async ({ page, request }) => {
  await fixture(page, request);
  await page.locator(".study-unit input").first().check();
  await configure(page, "合成延迟：取消与补出");
  await page.getByRole("button", { name: "生成这一组题", exact: true }).click();
  await page.getByRole("button", { name: "停止出题", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "已取消", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("progressbar")).toHaveAttribute(
    "aria-valuenow",
    "0",
  );
  await page.getByRole("button", { name: "补出缺少的题", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "本次出题完成", exact: true }),
  ).toBeVisible({ timeout: 15_000 });
  await expect(page.locator(".study-question-bank li")).toHaveCount(1);
});

test("无依据的模型题不会入库，显示失败和重试入口", async ({
  page,
  request,
}) => {
  await fixture(page, request);
  await page.locator(".study-unit input").first().check();
  await configure(page, "合成无效：测试引文校验");
  await page.getByRole("button", { name: "生成这一组题", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "未能完成", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".study-job-items")).toContainText(
    "原文依据无法核对",
  );
  await expect(page.getByRole("progressbar")).toHaveAttribute(
    "aria-valuenow",
    "0",
  );
  await expect(
    page.getByRole("button", { name: "补出缺少的题" }),
  ).toBeEnabled();
  await expect(page.locator(".study-question-bank li")).toHaveCount(0);
});

test("目录键盘操作与原文预览，不误选出题范围", async ({ page, request }) => {
  await fixture(page, request);
  const checkbox = page.locator(".study-unit input").first();
  await checkbox.focus();
  await page.keyboard.press("Space");
  await expect(checkbox).toBeChecked();
  await page.locator(".study-unit button").nth(1).click();
  await expect(page.locator(".study-paper-text")).toBeVisible();
  await panel(page, "目录");
  await expect(page.locator(".study-unit input:checked")).toHaveCount(1);
  await page.getByRole("button", { name: "清空选择", exact: true }).click();
  await expect(page.locator(".study-unit input:checked")).toHaveCount(0);
  await panel(page, "出题");
  await expect(
    page.getByRole("button", { name: "生成这一组题", exact: true }),
  ).toBeDisabled();
});

test("响应式、减少动效及视觉记录", async ({ page, request }, info) => {
  test.skip(info.project.name !== "desktop", "由桌面项目覆盖四档视口");
  test.setTimeout(60_000);
  const { book } = await fixture(page, request, true);
  await page.emulateMedia({ reducedMotion: "reduce" });
  for (const width of [1440, 1024, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/learning");
    await expect(page.locator(".study-hero h1")).toBeVisible();
    await expect(page.locator(".study-shelf-card").first()).toBeVisible();
    await expect(
      page.locator(".study-ledger > div").first().locator("strong"),
    ).not.toContainText("—");
    await page.screenshot({
      path: `.qa-data/learning-studio/home-${width}.png`,
      fullPage: true,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await page.goto(`/learning/books/${book.id}`);
    await expect(page.locator(".study-unit input").first()).toBeVisible();
    await page.screenshot({
      path: `.qa-data/learning-studio/studio-${width}.png`,
      fullPage: true,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await panel(page, "原文");
    await expect(page.locator(".study-paper-text")).toBeVisible();
    await page.screenshot({
      path: `.qa-data/learning-studio/reader-${width}.png`,
      fullPage: true,
    });
    await panel(page, "出题");
    await expect(page.getByLabel("考查重点")).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    const duration = await page
      .locator(".study-generate")
      .evaluate((element) => getComputedStyle(element).transitionDuration);
    expect(duration).toBe("0s");
    await page.screenshot({
      path: `.qa-data/learning-studio/settings-${width}.png`,
      fullPage: true,
    });
  }
});
