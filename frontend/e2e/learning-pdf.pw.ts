import { test, expect, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { syntheticPdf } from "./support/pdf";

async function panel(page: Page, name: string) {
  const navigation = page.getByRole("navigation", { name: "工作室面板" });
  if (await navigation.isVisible())
    await navigation.getByRole("button", { name, exact: true }).click();
}

test("PDF 原页预览、明确选择图片读取、部分证据恢复与题目定位", async ({
  page,
  request,
}, info) => {
  const login = await request.post("/api/v1/auth/login", {
    data: { name: "BrowserOwner", password: "synthetic-browser-password-123" },
  });
  const { token } = await login.json();
  await page.addInitScript(
    (value) => sessionStorage.setItem("xinxin-session", value),
    token,
  );
  const headers = { Authorization: `Bearer ${token}` };
  const fileResponse = await request.post("/api/v1/files", {
    headers,
    multipart: {
      file: {
        name: "synthetic-equations.pdf",
        mimeType: "application/pdf",
        buffer: syntheticPdf(),
      },
    },
  });
  expect(fileResponse.ok()).toBeTruthy();
  const file = await fileResponse.json();
  const added = await request.post("/api/v1/learning/books", {
    headers,
    data: { file_id: file.id, title: "合成数学原页验收" },
  });
  expect(added.ok()).toBeTruthy();
  const { book } = await added.json();
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(`/learning/books/${book.id}`);
  await expect(page.locator(".study-unit input").first()).toBeVisible();
  await page.locator(".study-unit input").first().check();
  await panel(page, "出题");
  await expect(page.getByLabel("材料读取方式", { exact: true })).toHaveValue(
    "text",
  );
  await page.getByLabel("材料读取方式", { exact: true }).selectOption("pdf");
  await expect(page.locator(".study-config")).toContainText(
    "2 个 PDF 原页图片发送给当前模型",
  );
  await panel(page, "目录");
  await page.locator(".study-unit button").first().click();
  await page
    .getByRole("button", { name: "对照 PDF 原页", exact: true })
    .click();
  await expect(page.getByAltText("教材 PDF 物理第 1 页原图")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "上一原页", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "下一原页", exact: true }).click();
  await expect(page.getByAltText("教材 PDF 物理第 2 页原图")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "下一原页", exact: true }),
  ).toBeDisabled();
  await panel(page, "出题");
  await page
    .getByRole("button", { name: "先总结选中材料", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "材料分析完成", exact: true }),
  ).toBeVisible();
  await panel(page, "原文");
  await expect(
    page.getByRole("region", { name: "当前片段总结" }),
  ).toContainText("合成原页");
  await page
    .getByText("已保留有效内容 · 跳过 1 条分析项 · 查看跳过与待核对项", {
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("region", { name: "当前片段总结" }),
  ).toContainText("来源编号超出");
  await panel(page, "出题");
  await page.getByLabel("每个片段", { exact: true }).selectOption("2");
  await page.getByRole("button", { name: "生成这一组题", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "本次出题完成", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".study-question-bank > li")).toHaveCount(2);
  const questions = await request.get(
    `/api/v1/learning/questions?book_id=${book.id}`,
    { headers },
  );
  const rows = (await questions.json()).questions;
  expect(
    rows.every(
      (row: { source_method: string; source_pages: number[] }) =>
        row.source_method === "pdf_images" && row.source_pages[0] === 1,
    ),
  ).toBeTruthy();
  expect(errors).toEqual([]);
  await page
    .locator(".study-question-bank > li")
    .first()
    .getByRole("button", { name: "核对原文依据", exact: true })
    .click();
  const sourceDialog = page.getByRole("dialog", { name: "回到原文" });
  await expect(
    sourceDialog.getByAltText("教材 PDF 物理第 1 页原图"),
  ).toBeVisible();
  await expect(sourceDialog.locator(".katex-error")).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(sourceDialog).toHaveCount(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBeTruthy();
  await mkdir(".qa-data/learning-pdf", { recursive: true });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.evaluate(async () => {
    await document.fonts.ready;
    window.scrollTo(0, 0);
  });
  await page.screenshot({
    path: `.qa-data/learning-pdf/${info.project.name}.png`,
    fullPage: true,
  });
});
