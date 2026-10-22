import {
  test,
  expect,
  type Page,
  type APIRequestContext,
} from "@playwright/test";
import { mkdir } from "node:fs/promises";

async function fixture(page: Page, request: APIRequestContext) {
  const response = await request.post("/api/v1/auth/login", {
    data: { name: "BrowserOwner", password: "synthetic-browser-password-123" },
  });
  const token = (await response.json()).token;
  await page.addInitScript(
    (value) => sessionStorage.setItem("xinxin-session", value),
    token,
  );
  const headers = { Authorization: `Bearer ${token}` };
  const text =
    "目录\n" +
    Array.from(
      { length: 12 },
      (_, n) => `第${n + 1}章 导数的基础…………${n + 3}`,
    ).join("\n") +
    "\n第一章 导数\n" +
    "导数刻画瞬时变化率，在几何上表示函数曲线在该点的切线斜率。\n".repeat(35);
  const file = await request.post("/api/v1/files", {
    headers,
    multipart: {
      file: {
        name: "合成讲练材料.txt",
        mimeType: "text/plain",
        buffer: Buffer.from(text),
      },
    },
  });
  const added = await request.post("/api/v1/learning/books", {
    headers,
    data: {
      file_id: (await file.json()).id,
      title: `合成讲练材料 ${crypto.randomUUID().slice(0, 6)}`,
    },
  });
  expect(added.ok()).toBeTruthy();
  const book = (await added.json()).book;
  await page.goto(`/learning/books/${book.id}`);
  await expect(page.locator(".study-unit input").last()).toBeVisible();
  return { book, headers };
}
async function panel(page: Page, name: string) {
  const tabs = page.getByRole("navigation", { name: "工作室面板" });
  if (await tabs.isVisible())
    await tabs.getByRole("button", { name, exact: true }).click();
}
async function selectBody(page: Page) {
  await expect(page.locator(".study-unit input").first()).toBeDisabled();
  await page.locator(".study-unit input").last().check();
  await panel(page, "出题");
}

test("目录排除、片段总结、校对失效、24题分批与来源标识", async ({
  page,
  request,
}) => {
  test.setTimeout(45_000);
  await fixture(page, request);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await selectBody(page);
  await expect(page.getByLabel("每个片段", { exact: true })).toHaveValue("12");
  await page
    .getByRole("button", { name: "先总结选中材料", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "材料分析完成", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("progressbar", { name: "材料分析进度" }),
  ).toHaveAttribute("aria-valuenow", "1");
  await panel(page, "目录");
  await page.locator(".study-unit button").last().click();
  await expect(
    page.getByRole("region", { name: "当前片段总结" }),
  ).toContainText("切线斜率");
  await page.getByRole("button", { name: "校对识别文字", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "校对识别文字" });
  await dialog
    .getByLabel("片段正文", { exact: true })
    .fill(
      "导数刻画瞬时变化率，在几何上表示切线斜率。函数 y=x^2 的导函数为 2x。\n".repeat(
        6,
      ),
    );
  await dialog.getByRole("button", { name: "保存校对", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.locator(".study-paper-footer")).toContainText("已人工校对");
  await expect(page.getByRole("region", { name: "当前片段总结" })).toHaveCount(
    0,
  );
  await panel(page, "出题");
  await page.getByLabel("每个片段", { exact: true }).selectOption("24");
  await page.getByRole("button", { name: "生成这一组题", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "本次出题完成", exact: true }),
  ).toBeVisible({ timeout: 15_000 });
  await expect(
    page.getByRole("progressbar", { name: "题目入库进度" }),
  ).toHaveAttribute("aria-valuenow", "24");
  await expect(page.locator(".study-question-bank>li")).toHaveCount(12);
  await page.getByRole("button", { name: /再看 12 道题/ }).click();
  await expect(page.locator(".study-question-bank>li")).toHaveCount(24);
  await page.reload();
  await expect(
    page.getByRole("progressbar", { name: "题目入库进度" }),
  ).toHaveAttribute("aria-valuenow", "24");
  await panel(page, "目录");
  await page.locator(".study-unit button").last().click();
  await expect(
    page.getByRole("button", { name: "校对识别文字", exact: true }),
  ).toBeDisabled();
  expect(errors).toEqual([]);
});

for (const [focus, reason] of [
  ["合成目录题", "章节、页码或出版信息"],
  ["合成审题拒绝", "审题未通过"],
  ["合成审题缺失", "复核结果缺失"],
]) {
  test(`无效题拦截：${focus}`, async ({ page, request }) => {
    await fixture(page, request);
    await selectBody(page);
    await page.getByLabel("每个片段", { exact: true }).selectOption("1");
    await page.getByLabel("填空", { exact: true }).uncheck();
    await page.getByLabel("简答", { exact: true }).uncheck();
    await page.getByLabel("考查重点").fill(focus);
    await page
      .getByRole("button", { name: "生成这一组题", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "未能完成", exact: true }),
    ).toBeVisible();
    await expect(page.locator(".study-job-items")).toContainText(reason);
    await expect(page.locator(".study-question-bank>li")).toHaveCount(0);
  });
}

test("能力星球：领域、键盘、选择、缩放、减少动态与窄屏", async ({
  page,
  request,
}, info) => {
  await fixture(page, request);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/skills");
  await expect(page.locator(".atlas-viewport")).toHaveAttribute(
    "data-renderer",
    "sphere-canvas",
  );
  await expect(
    page.getByRole("button", { name: "缓慢旋转", exact: true }),
  ).toBeDisabled();
  const domain = page.getByLabel("筛选技能领域", { exact: true });
  const first = await domain.locator("option").nth(1).getAttribute("value");
  await domain.selectOption(first!);
  await expect(
    page.locator(".atlas-directory-list>button").first(),
  ).toBeVisible();
  await page.locator(".atlas-directory-list>button").first().click();
  await expect(page.getByRole("region", { name: "当前技能" })).toBeVisible();
  await domain.selectOption("全部");
  await page.getByLabel("搜索星图技能", { exact: true }).fill("代码工作区");
  await page.getByLabel("搜索星图技能", { exact: true }).press("Enter");
  await expect(page.getByRole("region", { name: "当前技能" })).toContainText(
    "代码工作区",
  );
  const viewport = page.getByRole("group", { name: /技能星球，拖动旋转/ });
  await viewport.focus();
  await page.keyboard.press("+");
  await expect(page.locator(".atlas-scale")).toContainText("112%");
  await page.keyboard.press("Home");
  await expect(page.locator(".atlas-scale")).toContainText("100%");
  await page.getByRole("button", { name: "显示关系连线", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "显示关系连线", exact: true }),
  ).toHaveAttribute("aria-pressed", "false");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  if (info.project.name === "desktop") {
    await mkdir(".qa-data/learning-quality", { recursive: true });
    for (const width of [1440, 1024, 768, 390, 320]) {
      await page.setViewportSize({ width, height: 1000 });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({
        path: `.qa-data/learning-quality/skills-${width}.png`,
        fullPage: true,
      });
    }
  }
});
