import {
  test,
  expect,
  type Page,
  type APIRequestContext,
} from "@playwright/test";
import { mkdir, readFile } from "node:fs/promises";

const credentials = {
  name: "BrowserOwner",
  password: "synthetic-browser-password-123",
};
test.beforeEach(async () => {
  await mkdir(".qa-data/unified-workspace/final", { recursive: true });
});
async function login(page: Page, request: APIRequestContext) {
  const response = await request.post("/api/v1/auth/login", {
    data: credentials,
  });
  expect(response.ok()).toBe(true);
  const token = (await response.json()).token;
  await page.addInitScript(
    (value) => sessionStorage.setItem("xinxin-session", value),
    token,
  );
  return { Authorization: `Bearer ${token}` };
}

async function seedWorkspace(
  request: APIRequestContext,
  headers: Record<string, string>,
) {
  const record = async (kind: string, payload: Record<string, unknown>) => {
    const response = await request.post("/api/v1/records", {
      headers,
      data: { kind, payload },
    });
    expect(response.ok()).toBe(true);
    return response.json();
  };
  const collection = await record("collection", {
    title: "日常观察",
    description: "把平常的片刻，收进自己的叙事。",
  });
  const doc = JSON.stringify({
    type: "doc",
    content: [
      {
        type: "heading",
        attrs: { level: 2 },
        content: [{ type: "text", text: "给想法一个发生的地方" }],
      },
      {
        type: "paragraph",
        content: [
          {
            type: "text",
            text: "从一份资料、一段对话开始。把目标拆成行动，把过程留下证据，再把答案变成自己的理解。",
          },
        ],
      },
    ],
  });
  await record("article", {
    title: "把今天，写成一页。",
    summary: "记录那些值得停留的想法，也为下一次出发留一点线索。",
    content: doc,
    collection_id: collection.id,
    published: false,
  });
  await record("article", {
    title: "让行动慢慢成形",
    summary: "在阅读与实践之间，找到属于自己的节奏。",
    content: doc,
    collection_id: collection.id,
  });
  await record("photo", {
    title: "慢一点的日常",
    description: "午后、纸张、光线。平常的一天，也有值得收藏的部分。",
    category: "日常",
  });
  await record("poem", {
    title: "山中",
    content: "山中何事？\n松花酿酒，春水煎茶。",
    author: "张可久",
    source: "人月圆·山中书事",
  });
  await record("resume", {
    name: "林同学",
    title: "全栈开发 / AI 应用工程",
    location: "中国",
    bio: "将想法变成可验证的产品，关注体验、可靠性与技术的边界。此简历为测试合成内容。",
    skills: [
      { name: "React / TypeScript" },
      { name: "Python / FastAPI" },
      { name: "Agent / SkillNet" },
    ],
    education: [
      {
        title: "计算机科学与技术",
        subtitle: "合成示例大学",
        startDate: "2022",
        endDate: "2026",
      },
    ],
    experiences: [
      {
        title: "Xinxin · 私人智能工作空间",
        description:
          "从文档检索、任务执行到来源可验证的学习工作室，设计完整的产品闭环。",
        startDate: "2026",
      },
    ],
    certificates: [],
  });
  for (const content of [
    "回复优先使用简洁中文，重要结论附上依据。",
    "正在学习全栈开发，喜欢从真实项目理解技术。",
    "先给一点提示，让我自己想明白，再看完整解析。",
  ]) {
    expect(
      (
        await request.post("/api/v1/memories", {
          headers,
          data: { content, category: "preference" },
        })
      ).ok(),
    ).toBe(true);
  }
  expect(
    (
      await request.post("/api/v1/servers", {
        headers,
        data: {
          name: "个人开发环境",
          host: "example.invalid",
          port: 22,
          username: "developer",
          workdir: "/srv/xinxin",
        },
      })
    ).ok(),
  ).toBe(true);
  expect(
    (
      await request.post("/api/v1/schedules", {
        headers,
        data: {
          title: "每周回顾，留一点成长的线索",
          task: "整理本周的学习与项目进展，用三句话概括下一步。",
          interval_minutes: 10080,
          permission: "read",
          enabled: false,
        },
      })
    ).ok(),
  ).toBe(true);
  expect(
    (
      await request.post("/api/v1/files", {
        headers,
        multipart: {
          file: {
            name: "每周学习记录.csv",
            mimeType: "text/csv",
            buffer: Buffer.from("week,hours\n1,4\n2,7\n3,6\n4,10\n"),
          },
        },
      })
    ).ok(),
  ).toBe(true);
}

test("全站视觉与响应式清单", async ({ page, request }, testInfo) => {
  test.skip(
    testInfo.project.name !== "desktop",
    "此场景显式遍历多个视口，其他交互场景同时运行手机项目。",
  );
  test.setTimeout(360_000);
  const phase = process.env.UI_AUDIT_PHASE || "final";
  const output = `.qa-data/unified-workspace/${phase}`;
  await mkdir(output, { recursive: true });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "回到你的空间" }),
  ).toBeVisible();
  await page.screenshot({
    path: `${output}/auth-1440.png`,
    fullPage: true,
    animations: "disabled",
  });
  const headers = await login(page, request);
  await seedWorkspace(request, headers);
  const books = await request.get("/api/v1/learning/books", { headers });
  const book = (await books.json()).books.find(
    (item: { title: string }) => item.title === "合成浏览器讲义",
  );
  const quiz = await request.post("/api/v1/learning/quiz", {
    headers,
    data: { book_id: book.id, count: 1 },
  });
  const session = (await quiz.json()).session;
  const routes = [
    ["dashboard", "/"],
    ["agent", "/agent"],
    ["tasks", "/tasks"],
    ["files", "/files"],
    ["servers", "/servers"],
    ["skills", "/skills"],
    ["learning", "/learning"],
    ["articles", "/content"],
    ["collections", "/content?kind=collection"],
    ["photos", "/content?kind=photo"],
    ["poems", "/content?kind=poem"],
    ["resume", "/content?kind=resume"],
    ["tools", "/tools"],
    ["music", "/music"],
    ["memories", "/memories"],
    ["schedules", "/schedules"],
    ["settings", "/settings"],
    ["book", `/learning/books/${book.id}`],
    ["quiz", `/learning/quiz/${session.id}`],
    ["missing", "/does-not-exist"],
  ];
  const failures: string[] = [];
  page.on("pageerror", (error) => failures.push(error.message));
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const [name, route] of routes) {
      if (
        [1024, 768].includes(width) &&
        ![
          "dashboard",
          "agent",
          "skills",
          "settings",
          "tools",
          "music",
          "book",
          "quiz",
        ].includes(name)
      )
        continue;
      await page.goto(route);
      await expect(page.locator("main.main")).toBeVisible();
      await expect(page.locator("main.main .loading")).toHaveCount(0, {
        timeout: 15_000,
      });
      await page.evaluate(() => document.fonts.ready);
      await expect(page.locator("main.main .error-state")).toHaveCount(0);
      await page.screenshot({
        path: `${output}/${name}-${width}.png`,
        fullPage: true,
        animations: "disabled",
      });
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - innerWidth,
      );
      expect.soft(overflow, `${name} at ${width}px`).toBeLessThanOrEqual(1);
    }
  }
  expect(failures).toEqual([]);
});

test("全局入口：搜索设置、无结果、Enter、焦点恢复与移动导航", async ({
  page,
  request,
}, testInfo) => {
  await login(page, request);
  await page.goto("/files");
  const trigger = page.getByRole("button", { name: "搜索页面", exact: true });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "在空间里寻找" });
  const input = dialog.getByLabel("查找页面");
  await expect(input).toBeFocused();
  await input.fill("不存在的入口");
  await expect(dialog.getByRole("status")).toContainText("没有匹配");
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
  await trigger.click();
  await dialog.getByLabel("查找页面").fill("设置");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/settings$/);
  await expect(page).toHaveTitle("Xinxin · 设置");
  await expect(
    page.getByRole("navigation", { name: "设置分区" }),
  ).toBeVisible();
  if (testInfo.project.name === "mobile") {
    await page.getByRole("button", { name: "更多", exact: true }).click();
    const drawer = page.getByRole("dialog", { name: "功能导航" });
    await expect(drawer).toBeVisible();
    await page.keyboard.press("Shift+Tab");
    expect(
      await drawer.evaluate((element) =>
        element.contains(document.activeElement),
      ),
    ).toBe(true);
    await drawer.getByRole("link", { name: "记忆", exact: true }).click();
    await expect(page.getByRole("heading", { name: "长期记忆" })).toBeVisible();
    await expect(drawer).toHaveCount(0);
  }
});

test("记忆保存：重复提交保护、忙碌弹窗、失败保留与真实重试", async ({
  page,
  request,
}) => {
  await login(page, request);
  let count = 0;
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/memories", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    count += 1;
    if (count === 1) {
      await gate;
      return route.fulfill({
        status: 503,
        json: { detail: "合成保存失败，请重试" },
      });
    }
    return route.continue();
  });
  await page.goto("/memories");
  await page.getByRole("button", { name: "添加记忆" }).click();
  const dialog = page.getByRole("dialog", { name: "留下一条记忆" });
  const content = `合成保存回归 ${crypto.randomUUID()}`;
  await dialog.getByLabel("记住什么").fill(content);
  await dialog.locator("form").evaluate((form) => {
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
  });
  await expect.poll(() => count).toBe(1);
  await expect(dialog.getByLabel("记住什么")).toBeDisabled();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeVisible();
  release();
  await expect(dialog.getByRole("button", { name: "保存记忆" })).toBeEnabled();
  await expect(dialog.getByRole("alert")).toContainText("合成保存失败");
  await expect(dialog.getByLabel("记住什么")).toHaveValue(content);
  await dialog.getByRole("button", { name: "保存记忆" }).click();
  await expect(dialog).toHaveCount(0);
  await expect(
    page.locator(".memory-card").filter({ hasText: content }),
  ).toHaveCount(1);
  expect(count).toBe(2);
});

test("资料检索：新查询与关闭预览不被旧响应覆盖，正文失败可重试", async ({
  page,
  request,
}) => {
  await login(page, request);
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/files/search?**", async (route) => {
    const old =
      new URL(route.request().url()).searchParams.get("q") === "旧关键词";
    if (old) await gate;
    return route.fulfill({
      json: [
        {
          filename: old ? "旧结果不应出现" : "当前资料",
          text: old ? "旧响应" : "当前查询的合成正文",
          file_id: "synthetic-search",
        },
      ],
    });
  });
  await page.goto("/files");
  const input = page.getByLabel("搜索私人资料");
  await input.fill("旧关键词");
  await page.getByRole("button", { name: "检索正文" }).click();
  await expect(page.getByRole("button", { name: "正在检索…" })).toBeVisible();
  await input.fill("新关键词");
  await page.getByRole("button", { name: "检索正文" }).click();
  await expect(page.getByText("当前查询的合成正文")).toBeVisible();
  release();
  await expect(page.getByText("旧结果不应出现")).toHaveCount(0);
  await input.fill("");
  let textAttempts = 0;
  await page.route("**/api/v1/files/*/text", (route) => {
    textAttempts += 1;
    return textAttempts === 1
      ? route.fulfill({ status: 503, json: { detail: "合成正文暂不可用" } })
      : route.continue();
  });
  await page
    .locator(".file-open")
    .filter({ hasText: "合成浏览器讲义.txt" })
    .click();
  const dialog = page.getByRole("dialog", { name: "合成浏览器讲义.txt" });
  await expect(dialog.getByRole("alert")).toContainText("合成正文暂不可用");
  await dialog.getByRole("button", { name: "重新读取" }).click();
  await expect(dialog.locator(".document-text")).toContainText(
    "导数刻画变化率",
  );
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
});

test("任务详情：失效入口可恢复，缺少 finished 事件时核对权威快照", async ({
  page,
  request,
}) => {
  await login(page, request);
  await page.goto("/tasks?run=ui-audit-missing");
  const detail = page.locator(".task-detail, .task-detail-content");
  await expect(detail.getByRole("alert")).toBeVisible();
  let reads = 0;
  const run = {
    id: "ui-audit-missing",
    task: "合成快照恢复",
    permission: "read",
    created: Date.now(),
    usage: "{}",
    files: [],
    conversation_id: "synthetic",
    error: "",
  };
  await page.route("**/api/v1/runs/ui-audit-missing", (route) =>
    route.fulfill({
      json: { ...run, status: ++reads === 1 ? "running" : "completed" },
    }),
  );
  await page.route("**/api/v1/runs/ui-audit-missing/events?**", (route) =>
    route.fulfill({
      headers: { "content-type": "text/event-stream" },
      body: "event: end\ndata: {}\n\n",
    }),
  );
  await detail.getByRole("button", { name: "重新读取" }).click();
  await expect(detail.locator(".status")).toHaveText("已完成");
  await expect(
    detail.getByRole("heading", { name: "合成快照恢复" }),
  ).toBeVisible();
});

for (const [kind, name] of [
  ["article", "文章"],
  ["collection", "合集"],
  ["photo", "相册"],
  ["poem", "诗词"],
  ["resume", "简历"],
]) {
  test(`个人内容 ${name}：真实保存、预览和编辑窗口`, async ({
    page,
    request,
  }) => {
    await login(page, request);
    await page.goto(`/content?kind=${kind}`);
    await page
      .getByRole("button", { name: `新建${name}`, exact: true })
      .click();
    const dialog = page.getByRole("dialog", { name: `新建${name}` });
    const title = `合成${name} ${crypto.randomUUID().slice(0, 8)}`;
    if (kind === "resume")
      await dialog.getByLabel("姓名", { exact: true }).fill(title);
    else if (kind === "poem") {
      await dialog
        .getByLabel("内容", { exact: true })
        .fill(title + "\n一页纸，记住安静的时刻。");
      await dialog.getByLabel("作者", { exact: true }).fill(title);
    } else await dialog.getByLabel("标题", { exact: true }).fill(title);
    if (kind === "article")
      await dialog
        .getByRole("textbox", { name: "文章正文编辑器" })
        .fill("把思考写成自己的表达。合成内容用于浏览器验证。");
    await dialog.getByRole("button", { name: "保存记录" }).click();
    await expect(dialog).toHaveCount(0);
    if (kind === "resume")
      await expect(
        page.locator(".resume-document").filter({ hasText: title }),
      ).toBeVisible();
    else {
      const card = page.locator(".content-card").filter({ hasText: title });
      await expect(card).toHaveCount(1);
      await card.locator(".content-card-open").click();
      await expect(page.getByRole("dialog")).toContainText(title);
      await page.getByRole("button", { name: "编辑记录" }).click();
      await expect(
        page.getByRole("dialog", { name: `编辑${name}` }),
      ).toBeVisible();
      await page.keyboard.press("Escape");
    }
  });
}

test("生图输入法：组合输入 Enter 不触发生成，非模态窗口焦点可回落", async ({
  page,
  request,
}) => {
  await login(page, request);
  let calls = 0;
  await page.route("**/api/v1/images", (route) => {
    if (route.request().method() === "POST") calls += 1;
    return route.fulfill({ json: [] });
  });
  await page.goto("/agent");
  const trigger = page.getByRole("button", { name: "生图工作台", exact: true });
  await trigger.click();
  const input = page.getByRole("textbox", { name: "生图描述" });
  await expect(input).toBeFocused();
  await input.fill("一片安静的森林");
  await input.dispatchEvent("keydown", {
    key: "Enter",
    code: "Enter",
    isComposing: true,
  });
  expect(calls).toBe(0);
  await expect(input).toHaveValue("一片安静的森林");
  await page.getByRole("button", { name: "收起生图面板" }).click();
  await expect(trigger).toBeFocused();
});

test("各功能入口弹窗：统一框架、长表单关闭可达与焦点恢复", async ({
  page,
  request,
}, info) => {
  test.setTimeout(120_000);
  await login(page, request);
  await mkdir(".qa-data/unified-workspace/final", { recursive: true });
  const cases = [
    ["/servers", ".page-heading-action button", "登记服务器", "server-form"],
    ["/memories", ".page-heading-action button", "留下一条记忆", "memory-form"],
    [
      "/schedules",
      ".page-heading-action button",
      "创建定期行动",
      "schedule-form",
    ],
    ["/tools", ".plot-tool", "创建一张数据图", "plot-form"],
    ["/tools", ".zine-tool", "拾景 · 图片风格转换", "image-form"],
    [
      "/agent",
      'button[aria-label="上传或选择资源"]',
      "给 Xinxin 添加资源",
      "resource-picker",
    ],
    [
      "/agent",
      'button[aria-label="本轮参数与记忆授权"]',
      "本轮执行参数",
      "agent-options",
    ],
  ];
  for (const [url, selector, title, name] of cases) {
    await page.goto(url);
    const trigger = page.locator(selector);
    await trigger.click();
    const dialog = page.getByRole("dialog", { name: title });
    await expect(dialog).toBeVisible();
    await expect(dialog.locator(".loading")).toHaveCount(0, {
      timeout: 15_000,
    });
    expect(
      await dialog.evaluate(
        (element) => element.scrollWidth <= element.clientWidth + 1,
      ),
    ).toBe(true);
    await dialog.evaluate((element) => {
      element.scrollTop = element.scrollHeight;
    });
    const close = dialog.getByRole("button", { name: "关闭对话框" });
    await expect(close).toBeInViewport();
    await page.screenshot({
      path: `.qa-data/unified-workspace/final/${name}-${info.project.name}.png`,
      animations: "disabled",
    });
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await expect(trigger).toBeFocused();
  }
});

test("技能子视图：检索、列表、实验室与详情迟到响应", async ({
  page,
  request,
}, info) => {
  test.setTimeout(60_000);
  const headers = await login(page, request);
  const response = await request.get("/api/v1/skills", { headers });
  const skills = await response.json();
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route(`**/api/v1/skills/${skills[0].id}`, async (route) => {
    await gate;
    return route.fulfill({
      json: {
        name: skills[0].id,
        markdown: "旧详情不得覆盖当前能力",
        resources: [],
      },
    });
  });
  await page.route(`**/api/v1/skills/${skills[1].id}`, (route) =>
    route.fulfill({
      json: {
        name: skills[1].id,
        markdown: "这是当前选中的合成能力详情。",
        resources: [{ path: "slow.txt", bytes: 40 }],
      },
    }),
  );
  await page.goto("/skills");
  await page.getByRole("button", { name: /^能力库/ }).click();
  const cards = page.locator(".capability-card");
  await cards.nth(0).click();
  await cards.nth(1).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("这是当前选中的合成能力详情");
  release();
  await expect(dialog).not.toContainText("旧详情不得覆盖");
  await page.keyboard.press("Escape");
  await page.getByLabel("搜索技能库").fill("不可能命中的合成查询");
  await expect(
    page.getByRole("heading", { name: "还没找到合适的能力" }),
  ).toBeVisible();
  await page.getByLabel("搜索技能库").fill("");
  await page.getByRole("button", { name: "列表视图", exact: true }).click();
  await expect(cards.first()).toBeVisible();
  await page.screenshot({
    path: `.qa-data/unified-workspace/final/skill-library-${info.project.name}.png`,
    animations: "disabled",
  });
  await page.getByRole("button", { name: "试一试技能选择" }).click();
  await page.getByLabel("你想完成的目标").fill("阅读私人 PDF 并总结");
  await page.getByRole("button", { name: "预览技能选择", exact: true }).click();
  await expect(page.locator(".routing-goal")).toHaveText("阅读私人 PDF 并总结");
  await expect(
    page.getByRole("button", { name: "带着目标开始对话" }),
  ).toBeVisible();
  await page.screenshot({
    path: `.qa-data/unified-workspace/final/skill-lab-${info.project.name}.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("音乐资料库：键盘标签、歌单保存和关闭后的迟到请求", async ({
  page,
  request,
}, info) => {
  await login(page, request);
  await page.goto("/music");
  await page.getByRole("tab", { name: "搜索", exact: true }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: /收藏/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await page.screenshot({
    path: `.qa-data/unified-workspace/final/music-favorites-${info.project.name}.png`,
    animations: "disabled",
  });
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: /歌单/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await page
    .locator(".listening-index")
    .getByRole("button", { name: "新建", exact: true })
    .click();
  const dialog = page.getByRole("dialog", { name: "新建歌单" });
  const name = `安静时刻 ${crypto.randomUUID().slice(0, 6)}`;
  await dialog.getByLabel("名字").fill(name);
  await dialog.getByRole("button", { name: "建好", exact: true }).click();
  const row = page.locator(".playlist-row").filter({ hasText: name });
  await expect(row).toHaveCount(1);
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/music/playlists/*", async (route) => {
    await gate;
    return route.continue();
  });
  await row.click();
  await expect(
    page.getByRole("status").filter({ hasText: "正在读取歌单" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "全部歌单", exact: true }).click();
  release();
  await expect(
    page.getByRole("button", { name: "全部歌单", exact: true }),
  ).toHaveCount(0);
  await expect(row).toBeVisible();
  await page.screenshot({
    path: `.qa-data/unified-workspace/final/music-playlists-${info.project.name}.png`,
    animations: "disabled",
  });
});

test("书架弹窗：隐藏上传控件不抢占可见字段的初始焦点", async ({
  page,
  request,
}) => {
  await login(page, request);
  await page.goto("/learning");
  await page.getByRole("button", { name: "加入书架", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "加入书架" });
  await expect(
    dialog.getByRole("combobox", { name: "或从私人资料中选择" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
});

test("歌单刷新不等待收藏请求，保存后的列表立即可见", async ({
  page,
  request,
}) => {
  await login(page, request);
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/music/favorites", async (route) => {
    await gate;
    await route.continue();
  });
  try {
    await page.goto("/music");
    await page.getByRole("tab", { name: /歌单/ }).click();
    await page
      .locator(".listening-index")
      .getByRole("button", { name: "新建", exact: true })
      .click();
    const dialog = page.getByRole("dialog", { name: "新建歌单" });
    const name = `不受收藏影响 ${crypto.randomUUID().slice(0, 6)}`;
    await dialog.getByLabel("名字").fill(name);
    await dialog.getByRole("button", { name: "建好", exact: true }).click();
    await expect(
      page.locator(".playlist-row").filter({ hasText: name }),
    ).toHaveCount(1);
  } finally {
    release();
  }
});

test("桌面入口模板：启动和错误窗口窄屏、减少动态及长日志", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "desktop",
    "模板使用独立的桌面 HTML，本场景显式覆盖窄视口。",
  );
  await mkdir(".qa-data/unified-workspace/final", { recursive: true });
  await page.emulateMedia({ reducedMotion: "reduce" });
  for (const width of [1024, 320]) {
    await page.setViewportSize({ width, height: 800 });
    for (const name of ["starting", "error-template"]) {
      const html = (await readFile(`../desktop/assets/${name}.html`, "utf8"))
        .replace("{{MESSAGE}}", "合成连接失败：请检查本机端口与服务状态。")
        .replace("{{LOG}}", "合成日志，仅用于布局审查。\n".repeat(40))
        .replace(
          "{{LOGPATH}}",
          "D:\\synthetic-workspace\\runtime\\desktop.log",
        );
      await page.setContent(html);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth - innerWidth,
        ),
      ).toBeLessThanOrEqual(1);
      await page.screenshot({
        path: `.qa-data/unified-workspace/final/desktop-${name}-${width}.png`,
        fullPage: true,
        animations: "disabled",
      });
    }
  }
});

test("身份入口：验证码、找回、初始化和离线连接的状态反馈", async ({
  page,
}, info) => {
  await page.goto("/");
  await page.getByRole("button", { name: "邮箱验证码", exact: true }).click();
  await page.getByLabel("主人邮箱").fill("owner@example.invalid");
  await page.route("**/api/v1/auth/email/code", (route) =>
    route.fulfill({ status: 503, json: { detail: "合成邮件服务暂不可用" } }),
  );
  await page.getByRole("button", { name: "发送验证码", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("合成邮件服务暂不可用");
  await page.getByRole("button", { name: "找回密码", exact: true }).click();
  await expect(page.getByLabel("新密码", { exact: true })).toHaveAttribute(
    "minlength",
    "10",
  );
  await page.getByRole("button", { name: "连接自己的后端" }).click();
  await page.getByLabel("后端地址").fill("http://example.invalid");
  await page.getByRole("button", { name: "保存并重新连接" }).click();
  await expect(page.getByRole("alert")).toContainText("HTTPS");
  await page.route("**/api/v1/auth/status", (route) =>
    route.fulfill({ json: { configured: false } }),
  );
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "建立你的私人空间" }),
  ).toBeVisible();
  await expect(page.getByLabel("初始化码")).toBeVisible();
  await page.screenshot({
    path: `.qa-data/unified-workspace/final/auth-setup-${info.project.name}.png`,
    fullPage: true,
    animations: "disabled",
  });
  await page.unroute("**/api/v1/auth/status");
  await page.route("**/api/v1/auth/status", (route) => route.abort());
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "还没连接到你的空间" }),
  ).toBeVisible();
  await page.screenshot({
    path: `.qa-data/unified-workspace/final/offline-${info.project.name}.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("设置：320px 布局、四种主题、背景、邮件分支及连接错误恢复", async ({
  page,
  request,
}) => {
  await login(page, request);
  await page.setViewportSize({ width: 320, height: 900 });
  let networkFails = true;
  await page.route("**/api/v1/network", (route) =>
    networkFails
      ? route.fulfill({ status: 503, json: { detail: "合成连接信息暂不可用" } })
      : route.continue(),
  );
  await page.goto("/settings");
  const connection = page.locator("#connection");
  await expect(connection.getByRole("alert")).toContainText(
    "合成连接信息暂不可用",
  );
  networkFails = false;
  await connection.getByRole("button", { name: "重新读取" }).click();
  await expect(connection.getByText("本机", { exact: true })).toBeVisible();
  for (const [index, accent] of ["teal", "clay", "indigo", "ink"].entries()) {
    await page.locator(".theme-options button").nth(index).click();
    await expect(page.locator("html")).toHaveAttribute("data-accent", accent);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth - innerWidth,
      ),
    ).toBeLessThanOrEqual(1);
  }
  for (const [index, background] of ["paper", "grid", "plain"].entries()) {
    await page.locator(".background-options button").nth(index).click();
    await expect(page.locator("html")).toHaveAttribute("data-bg", background);
  }
  await page.getByRole("button", { name: "Resend API", exact: true }).click();
  await expect(
    page.getByLabel("Resend API Key", { exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth - innerWidth,
    ),
  ).toBeLessThanOrEqual(1);
  await page.getByRole("button", { name: "SMTP 授权码", exact: true }).click();
  await expect(page.getByLabel("SMTP 服务器", { exact: true })).toBeVisible();
  await page.emulateMedia({ reducedMotion: "reduce", forcedColors: "active" });
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "让空间，贴近自己。" }),
  ).toBeVisible();
  await expect(page.locator(".theme-options button").nth(3)).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(
    await page.evaluate(() =>
      parseFloat(
        getComputedStyle(document.querySelector(".page-enter")!)
          .animationDuration,
      ),
    ),
  ).toBeLessThan(0.01);
});

test("退出：后端暂不可用时仍清除本机会话，错误有反馈", async ({
  page,
  request,
  isMobile,
}) => {
  await login(page, request);
  await page.route("**/api/v1/auth/logout", (route) =>
    route.fulfill({ status: 503, json: { detail: "合成退出失败" } }),
  );
  await page.goto("/");
  await expect(page.locator(".mission-card")).toBeVisible();
  if (isMobile)
    await page.getByRole("button", { name: "展开导航", exact: true }).click();
  await page.getByRole("button", { name: "退出登录", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "回到你的空间" }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("未能确认服务器会话撤销");
  expect(
    await page.evaluate(() => sessionStorage.getItem("xinxin-session")),
  ).toBeNull();
});
