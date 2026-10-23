import {
  test,
  expect,
  type Page,
  type APIRequestContext,
  type TestInfo,
} from "@playwright/test";
import { randomUUID } from "node:crypto";
import { mkdir } from "node:fs/promises";
import { syntheticPdf } from "./support/pdf";

async function fixture(page: Page, request: APIRequestContext, pdf = false) {
  const login = await request.post("/api/v1/auth/login", {
    data: { name: "BrowserOwner", password: "synthetic-browser-password-123" },
  });
  const { token } = await login.json();
  await page.addInitScript(
    (value) => sessionStorage.setItem("xinxin-session", value),
    token,
  );
  const headers = { Authorization: `Bearer ${token}` };
  const content =
    "导数表示瞬时变化率，几何意义为函数图像在指定点的切线斜率。".repeat(12) +
    randomUUID();
  const upload = await request.post("/api/v1/files", {
    headers,
    multipart: {
      file: {
        name: pdf ? "synthetic-scope.pdf" : "synthetic-experience.txt",
        mimeType: pdf ? "application/pdf" : "text/plain",
        buffer: pdf ? syntheticPdf(5) : Buffer.from(content),
      },
    },
  });
  expect(upload.ok()).toBeTruthy();
  const file = await upload.json();
  const response = await request.post("/api/v1/learning/books", {
    headers,
    data: { file_id: file.id, title: "合成学习体验验收" },
  });
  const { book } = await response.json();
  const listing = await request.get(
    `/api/v1/learning/books/${book.id}/sources`,
    { headers },
  );
  const { sources } = await listing.json();
  return { headers, book, file, sources };
}

async function generatedQuiz(
  page: Page,
  request: APIRequestContext,
  focus: string,
  kind: string,
  count = 1,
) {
  const data = await fixture(page, request);
  const response = await request.post(
    `/api/v1/learning/books/${data.book.id}/generations`,
    {
      headers: data.headers,
      data: {
        source_ids: [data.sources[0].id],
        kinds: [kind],
        count,
        focus,
        request_key: randomUUID(),
      },
    },
  );
  const { job } = await response.json();
  await expect
    .poll(
      async () =>
        (
          await (
            await request.get(`/api/v1/learning/generations/${job.id}`, {
              headers: data.headers,
            })
          ).json()
        ).job.status,
    )
    .toBe("completed");
  const quiz = await request.post("/api/v1/learning/quiz", {
    headers: data.headers,
    data: { book_id: data.book.id, count },
  });
  const { session } = await quiz.json();
  await page.goto(`/learning/quiz/${session.id}`);
  await expect(page.locator(".quiz-stem")).toBeVisible();
  return { ...data, session };
}

async function panel(page: Page, name: string) {
  const nav = page.getByRole("navigation", { name: "工作室面板" });
  if (await nav.isVisible())
    await nav.getByRole("button", { name, exact: true }).click();
}

async function screenshot(page: Page, info: TestInfo, name: string) {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBeTruthy();
  await mkdir(".qa-data/learning-experience", { recursive: true });
  await page.screenshot({
    path: `.qa-data/learning-experience/${info.project.name}-${name}.png`,
  });
}

test("多空逐项输入、切题和刷新保留草稿，区间与代码标点原样提交", async ({
  page,
  request,
}, info) => {
  await generatedQuiz(page, request, "合成逐空", "fill", 2);
  const first = page.getByRole("textbox", { name: "第 1 空答案", exact: true });
  const second = page.getByRole("textbox", {
    name: "第 2 空答案",
    exact: true,
  });
  await first.fill("(0,1)");
  await page.getByRole("button", { name: "第 2 题", exact: true }).click();
  await expect(first).toHaveValue("");
  await page.getByRole("button", { name: "第 1 题", exact: true }).click();
  await expect(first).toHaveValue("(0,1)");
  await second.fill("A;B");
  await page.reload();
  await expect(first).toHaveValue("(0,1)");
  await expect(second).toHaveValue("A;B");
  const submitted = page.waitForRequest(
    (call) => call.url().includes("/answer") && call.method() === "POST",
  );
  await page.getByRole("button", { name: "提交", exact: true }).click();
  expect((await submitted).postDataJSON().answers).toEqual(["(0,1)", "A;B"]);
  await expect(page.locator(".quiz-verdict")).toContainText("答对了");
  await screenshot(page, info, "multiple-blanks");
});

test("老师与 Xinxin 追问草稿隔离，刷新恢复且成功追问后清除对应草稿", async ({
  page,
  request,
}) => {
  await generatedQuiz(page, request, "", "single");
  const teacher = page.getByRole("textbox", { name: "向老师提问" });
  await expect(teacher).toBeEnabled();
  await teacher.fill("为什么切线能表示变化率？");
  await page.getByRole("button", { name: "Xinxin 辅导", exact: true }).click();
  const xinxin = page.getByRole("textbox", { name: "向Xinxin提问" });
  await expect(xinxin).toBeEnabled();
  await expect(xinxin).toHaveValue("");
  await xinxin.fill("能用比喻再解释一下吗？");
  await page.getByRole("button", { name: "普通老师", exact: true }).click();
  await expect(teacher).toHaveValue("为什么切线能表示变化率？");
  await page.reload();
  await expect(teacher).toBeEnabled();
  await expect(teacher).toHaveValue("为什么切线能表示变化率？");
  await page.getByRole("button", { name: "让老师讲这道", exact: true }).click();
  await expect(page.locator(".tutor-log li.assistant")).toHaveCount(1);
  await expect(teacher).toHaveValue("为什么切线能表示变化率？");
  await page.getByRole("button", { name: "发送追问" }).click();
  await expect(teacher).toHaveValue("");
  await expect(page.locator(".tutor-log li.user").last()).toContainText(
    "为什么切线能表示变化率？",
  );
  await page.getByRole("button", { name: "Xinxin 辅导", exact: true }).click();
  await expect(xinxin).toHaveValue("能用比喻再解释一下吗？");
});

test("主观判分故障保留作答，总结显示待核对并可对原作答重判", async ({
  page,
  request,
}, info) => {
  const { session, headers } = await generatedQuiz(
    page,
    request,
    "合成待核对",
    "short",
  );
  await page
    .getByRole("textbox", { name: "简答", exact: true })
    .fill("导数的几何意义是切线斜率。");
  await page.getByRole("button", { name: "提交", exact: true }).click();
  await expect(page.locator(".quiz-summary")).toContainText("等待核对");
  await expect(page.locator(".quiz-summary")).toContainText("1 道待核对");
  await page.getByRole("button", { name: "查看讲解", exact: true }).click();
  await expect(
    page.getByRole("textbox", { name: "简答", exact: true }),
  ).toHaveValue("导数的几何意义是切线斜率。");
  await page
    .getByRole("button", { name: "重试判分 · 保留原作答", exact: true })
    .click();
  await expect(page.locator(".quiz-verdict")).toContainText("答对了");
  const value = await (
    await request.get(`/api/v1/learning/quiz/${session.id}`, { headers })
  ).json();
  expect(value.session.answered).toBe(1);
  expect(value.session.correct).toBe(1);
  expect(value.session.questions[0].answered).toBe(
    "导数的几何意义是切线斜率。",
  );
  await page
    .locator(".quiz-top")
    .getByRole("button", { name: "查看总结", exact: true })
    .click();
  await expect(page.locator(".quiz-summary")).toContainText("100%");
  await screenshot(page, info, "grading-recovery");
});

test("精读起止页、无效范围提示、部分覆盖与原题数量上限", async ({
  page,
  request,
}, info) => {
  const { book, sources } = await fixture(page, request, true);
  await page.goto(`/learning/books/${book.id}`);
  await expect(
    page.getByRole("button", {
      name: "先精读当前片段的 3 个原页",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "先精读当前片段的 3 个原页", exact: true })
    .click();
  await panel(page, "出题");
  await expect(page.getByLabel("材料读取方式", { exact: true })).toHaveValue(
    "pdf",
  );
  await page.getByLabel("精读起始页", { exact: true }).fill("2");
  await page.getByLabel("精读结束页", { exact: true }).fill("1");
  await expect(
    page.getByRole("button", { name: "生成这一组题", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("region", { name: "当前片段精读范围" }),
  ).toContainText("起始页不能大于结束页");
  await page.getByLabel("精读结束页", { exact: true }).fill("3");
  await page.getByLabel("出题策略", { exact: true }).selectOption("original");
  const submitted = page.waitForRequest(
    (call) =>
      call.url().endsWith(`/books/${book.id}/generations`) &&
      call.method() === "POST",
  );
  await page.getByRole("button", { name: "生成这一组题", exact: true }).click();
  expect((await submitted).postDataJSON().page_ranges).toEqual({
    [sources[0].id]: [2, 3],
  });
  await expect(
    page.getByRole("heading", { name: "本次出题完成", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "资料理解与覆盖" }),
  ).toContainText("仅分析了部分原页");
  await expect(page.locator(".study-generation-total strong")).toHaveText(
    /1\s*\/\s*1/,
  );
  await panel(page, "原文");
  await expect(
    page.getByRole("region", { name: "当前片段总结" }),
  ).toContainText("第 2–3 页");
  await page
    .getByRole("button", { name: "对照 PDF 原页", exact: true })
    .click();
  await expect(page.getByAltText("教材 PDF 物理第 2 页原图")).toBeVisible();
  await page.getByRole("button", { name: "下一原页", exact: true }).click();
  await expect(page.getByAltText("教材 PDF 物理第 3 页原图")).toBeVisible();
  await screenshot(page, info, "focused-pdf");
});

test("刷新后恢复识别任务，完成快照会刷新书架", async ({ page, request }) => {
  const { file, headers } = await fixture(page, request);
  const started = await request.post("/api/v1/learning/imports", {
    headers,
    data: {
      file_id: file.id,
      title: "合成异步书架恢复",
      request_key: randomUUID(),
    },
  });
  const { job } = await started.json();
  let done: any;
  await expect
    .poll(async () => {
      done = (
        await (
          await request.get(`/api/v1/learning/imports/${job.id}`, { headers })
        ).json()
      ).job;
      return done.status;
    })
    .toBe("completed");
  let initialBooks = true;
  let release = () => {};
  const loaded = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/learning/books", async (route) => {
    const response = await route.fetch();
    if (initialBooks) {
      initialBooks = false;
      const value = await response.json();
      await route.fulfill({
        response,
        json: {
          books: value.books.filter(
            (book: { id: string }) => book.id !== done.book_id,
          ),
        },
      });
      release();
    } else await route.fulfill({ response });
  });
  await page.route("**/api/v1/learning/imports", (route) =>
    route.fulfill({
      json: { job: { ...done, status: "running", book_id: null } },
    }),
  );
  await page.route(`**/api/v1/learning/imports/${job.id}`, async (route) => {
    await loaded;
    await route.fulfill({ json: { job: done } });
  });
  await page.goto("/learning");
  await expect(
    page.locator(`a.study-cover[href="/learning/books/${done.book_id}"]`),
  ).toBeVisible();
});
