import { test as base, expect, type Page } from "@playwright/test";

// 浏览器运行真实 React 页面；曲库、模型、音频使用合成数据，避免修改私人数据或调用付费模型。
const tracks = ["合成晴天", "合成夜曲", "合成远方"].map((name, index) => ({
  id: String(index + 1),
  name,
  source: "netease",
  artist: "测试歌手",
  album: "测试专辑",
  pic_id: String(index + 1),
  lyric_id: String(index + 1),
  emotion: { valence: 0.6, energy: 0.8, label: "乐", moods: ["热血"] },
}));
const questions = ["y=x^2 在 x=1 的导数？", "y=2x 的导数？"].map(
  (stem, index) => ({
    id: `q${index + 1}`,
    kind: "single",
    stem,
    tags: ["导数"],
    difficulty: 1,
    position: index,
    options: [
      { key: "A", text: "2" },
      { key: "B", text: "1" },
      { key: "C", text: "0" },
      { key: "D", text: "4" },
    ],
    answered: null as string | null,
    status: null as string | null,
  }),
);

const test = base.extend<{ mock: Awaited<ReturnType<typeof mockWorkspace>> }>({
  mock: async ({ page }, use) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    const state = await mockWorkspace(page);
    await use(state);
    expect(errors, "没有未捕获的页面异常").toEqual([]);
  },
});

async function mockWorkspace(page: Page) {
  const state = {
    calls: [] as Array<{ path: string; method: string; body: any }>,
    mood: {
      label: "乐",
      valence: 0.6,
      energy: 0.8,
      intensity: 0.8,
      tracks: 3,
      moods: [{ mood: "热血", share: 1 }],
      influence: true,
      influence_level: 2,
    },
    favorites: [] as typeof tracks,
    plays: [] as any[],
    histories: {} as Record<string, Array<{ role: string; content: string }>>,
    session: {
      id: "session",
      book_id: "book1",
      chapter_id: "chapter1",
      title: "合成导数练习",
      total: 2,
      answered: 0,
      correct: 0,
      status: "active",
      questions: structuredClone(questions) as any[],
    },
    historyFailures: 0,
    explainFailures: 0,
    explainDelay: 0,
    searchDelay: 0,
    answerDelay: 0,
  };
  await page.addInitScript(() => {
    sessionStorage.setItem("xinxin-session", "synthetic-browser-session");
    (window as any).__audioReject = false;
    HTMLMediaElement.prototype.play = async function () {
      if ((window as any).__audioReject)
        throw new DOMException("synthetic failure", "NotSupportedError");
      (this as any).__testPlaying = true;
      this.dispatchEvent(new Event("play"));
    };
    HTMLMediaElement.prototype.pause = function () {
      (this as any).__testPlaying = false;
      this.dispatchEvent(new Event("pause"));
    };
    Object.defineProperty(HTMLMediaElement.prototype, "paused", {
      get() {
        return !(this as any).__testPlaying;
      },
    });
    Object.defineProperty(HTMLMediaElement.prototype, "duration", {
      get() {
        return 180;
      },
    });
  });
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname.replace("/api/v1", "");
    const method = req.method();
    const body = req.postDataJSON();
    state.calls.push({ path, method, body });
    const send = (json: unknown, status = 200) =>
      route.fulfill({ json, status });
    const wait = (ms: number) =>
      new Promise((resolve) => setTimeout(resolve, ms));
    if (path === "/auth/status") return send({ configured: true });
    if (path === "/auth/me") return send({ name: "SyntheticOwner" });
    if (path === "/music/mood") {
      if (method === "DELETE") {
        state.plays = [];
        state.mood.intensity = 0;
      }
      return send({ mood: state.mood, plays: state.plays });
    }
    if (path === "/music/settings") {
      Object.assign(state.mood, body);
      return send({ mood: state.mood });
    }
    if (path === "/music/search") {
      await wait(state.searchDelay);
      return send({ tracks });
    }
    if (path === "/music/score") return send({ emotions: {}, scored: 0 });
    if (path === "/music/url")
      return send({
        url: `data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=#${url.searchParams.get("id")}`,
      });
    if (path === "/music/pic")
      return send({
        url: `data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="#376c62"/></svg>')}#${url.searchParams.get("id")}`,
      });
    if (path === "/music/lyric")
      return send({
        lyric: "[00:00.00]合成第一句\n[00:10.00]合成第二句",
        tlyric: "",
      });
    if (path === "/music/play") {
      state.plays.push(body);
      return send({ ok: true });
    }
    if (path === "/music/favorites") {
      if (method === "POST") state.favorites.push(body);
      if (method === "DELETE")
        state.favorites = state.favorites.filter(
          (track) =>
            `${track.source}:${track.id}` !== url.searchParams.get("key"),
        );
      return send({
        favorites: state.favorites,
        keys: state.favorites.map((track) => `${track.source}:${track.id}`),
      });
    }
    if (path === "/music/playlists") return send({ playlists: [] });
    if (/\/learning\/quiz\/[^/]+$/.test(path))
      return send({ session: { ...state.session, id: path.split("/").pop() } });
    if (path === "/learning/quiz")
      return send({ session: { ...state.session, id: "next-session" } });
    if (path.endsWith("/answer")) {
      await wait(state.answerDelay);
      const question = state.session.questions.find(
        (item) => item.id === body.question_id,
      );
      Object.assign(question, {
        answered: body.answer,
        status: body.answer === "A" ? "correct" : "wrong",
        ai_reason: "本地比对",
        answer: "A",
        explanation: "先求导，再代入。",
      });
      state.session.answered = state.session.questions.filter(
        (item) => item.status,
      ).length;
      state.session.correct = state.session.questions.filter(
        (item) => item.status === "correct",
      ).length;
      return send({ ...question, reason: "本地比对", state: state.session });
    }
    const tutor = path.match(
      /^\/learning\/questions\/([^/]+)\/(tutor|explain)$/,
    );
    if (tutor) {
      const mode = body?.mode || url.searchParams.get("mode") || "teacher";
      const key = `${tutor[1]}:${mode}`;
      if (tutor[2] === "tutor") {
        if (state.historyFailures-- > 0)
          return send({ detail: "合成读取失败" }, 503);
        return send({ history: state.histories[key] || [], mode });
      }
      await wait(state.explainDelay);
      if (state.explainFailures-- > 0)
        return send({ detail: "合成模型失败，请重试" }, 409);
      const reply = `${mode === "xinxin" ? "Xinxin：我们一起想想呀" : "老师：先看知识点"} ${tutor[1]}\n\n\`\`\`plot\ny=x^2\n\`\`\``;
      const history = (state.histories[key] ||= []);
      history.push(
        { role: "user", content: body.message || "这道题怎么想？" },
        { role: "assistant", content: reply },
      );
      return send({ reply, history, mode });
    }
    if (path === "/learning/books") return send({ books: [] });
    if (path === "/learning/stats")
      return send({
        books: 0,
        questions: 0,
        answered: 0,
        correct: 0,
        accuracy: 0,
        weak_tags: [],
        recent: [],
      });
    if (
      path === "/conversations" ||
      path === "/servers" ||
      path === "/files" ||
      path === "/memories" ||
      path === "/schedules" ||
      path === "/runs"
    )
      return send([]);
    return send({});
  });
  return state;
}

async function search(page: Page) {
  await page.goto("/music");
  await page.getByRole("textbox", { name: "搜索音乐" }).fill("合成测试");
  await page.getByRole("textbox", { name: "搜索音乐" }).press("Enter");
  await expect(page.locator(".track-row")).toHaveCount(3);
}

test("悬停在进度、收藏和校准刷新后保持 DOM、位移和焦点", async ({
  page,
  mock,
}, info) => {
  let finishScore!: () => void;
  const scoreGate = new Promise<void>((resolve) => {
    finishScore = resolve;
  });
  await page.route("**/api/v1/music/score", async (route) => {
    await scoreGate;
    await route.fulfill({
      json: {
        emotions: { "netease:1": { ...tracks[0].emotion, moods: ["温柔"] } },
        scored: 1,
      },
    });
  });
  await search(page);
  const row = page.locator(".track-row").first();
  await row.hover();
  await row.click();
  await row.focus();
  const element = await row.elementHandle();
  finishScore();
  await expect(row.locator(".mood-word")).toHaveText("温柔");
  expect(
    await row.evaluate((node, original) => node === original, element),
  ).toBe(true);
  await expect(row.locator(".track-title")).toHaveCSS(
    "transform",
    "matrix(1, 0, 0, 1, 6, 0)",
  );
  for (let i = 1; i <= 10; i++) {
    await page.locator("audio").evaluate((audio: HTMLAudioElement, current) => {
      audio.currentTime = current;
      audio.dispatchEvent(new Event("timeupdate"));
    }, i);
    expect(
      await row.evaluate((node, original) => node === original, element),
    ).toBe(true);
    await expect(row).toBeFocused();
    await expect(row.locator(".track-title")).toHaveCSS(
      "transform",
      "matrix(1, 0, 0, 1, 6, 0)",
    );
  }
  await page
    .locator(".track-item")
    .first()
    .getByRole("button", { name: "收藏", exact: true })
    .click();
  expect(
    await row.evaluate((node, original) => node === original, element),
  ).toBe(true);
  await expect
    .poll(
      () =>
        mock.calls.filter(
          (item) => item.path === "/music/url" && item.method === "GET",
        ).length,
    )
    .toBe(1);
  await expect.poll(() => mock.plays.length).toBe(1);
  await page.screenshot({ path: info.outputPath("music.png"), fullPage: true });
});

test("减少动态效果时没有悬停位移", async ({ page, mock }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await search(page);
  await page.locator(".track-row").first().hover();
  await expect(page.locator(".track-title").first()).toHaveCSS(
    "transform",
    "none",
  );
});

test("四档可切换、刷新保留、关闭再开启恢复档位", async ({ page, mock }) => {
  await page.goto("/music");
  for (const [index, name] of ["轻微", "自然", "明显", "沉浸"].entries()) {
    await page.getByRole("radio", { name, exact: true }).check();
    await expect.poll(() => mock.mood.influence_level).toBe(index + 1);
  }
  await page.reload();
  await expect(
    page.getByRole("radio", { name: "沉浸", exact: true }),
  ).toBeChecked();
  const influence = page.getByRole("switch", {
    name: "让音乐影响 Xinxin 的语气",
  });
  await influence.click();
  await expect(
    page.getByRole("radio", { name: "沉浸", exact: true }),
  ).toBeDisabled();
  await influence.click();
  await expect(
    page.getByRole("radio", { name: "沉浸", exact: true }),
  ).toBeEnabled();
  await expect(
    page.getByRole("radio", { name: "沉浸", exact: true }),
  ).toBeChecked();
});

test("清空检索后迟到的搜索响应不恢复结果", async ({ page, mock }) => {
  mock.searchDelay = 350;
  await page.goto("/music");
  await page.getByRole("textbox", { name: "搜索音乐" }).fill("延迟");
  await page.getByRole("textbox", { name: "搜索音乐" }).press("Enter");
  await page.getByRole("button", { name: "清空搜索" }).click();
  await expect(page.getByText("还没有检索。", { exact: false })).toBeVisible();
  await page.waitForTimeout(450);
  await expect(page.locator(".track-row")).toHaveCount(0);
});

test("实际播放失败不记播放和情绪", async ({ page, mock }) => {
  await search(page);
  await page.evaluate(() => {
    (window as any).__audioReject = true;
  });
  await page.locator(".track-row").first().click();
  await expect(page.getByRole("alert")).toContainText("暂时播不了");
  expect(mock.plays).toHaveLength(0);
});

test("暂停后恢复不重复记录同一首播放", async ({ page, mock }) => {
  await search(page);
  await page.locator(".track-row").first().click();
  await expect.poll(() => mock.plays.length).toBe(1);
  await page.locator(".transport-play").click();
  await page.locator(".transport-play").click();
  expect(mock.plays).toHaveLength(1);
});

test("快速切歌时较早的取链结果不会覆盖新歌曲", async ({ page, mock }) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/music/url?*", async (route) => {
    if (new URL(route.request().url()).searchParams.get("id") !== "1")
      return route.fallback();
    await gate;
    return route.fulfill({
      json: {
        url: "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
      },
    });
  });
  await search(page);
  await page.locator(".track-row").first().click();
  await page.locator(".track-row").nth(1).click();
  await expect(page.locator(".sleeve h2")).toHaveText("合成夜曲");
  release();
  await page.waitForTimeout(250);
  await expect(page.locator(".sleeve h2")).toHaveText("合成夜曲");
  expect(mock.plays.map((track) => track.id)).toEqual(["2"]);
});

test("停止播放后迟到的取链不会重新播放", async ({ page, mock, isMobile }) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/music/url?*", async (route) => {
    if (new URL(route.request().url()).searchParams.get("id") !== "2")
      return route.fallback();
    await gate;
    return route.fulfill({
      json: {
        url: "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
      },
    });
  });
  await search(page);
  await page.locator(".track-row").first().click();
  await expect.poll(() => mock.plays.length).toBe(1);
  await page.locator(".track-row").nth(1).click();
  if (isMobile)
    await page.getByRole("button", { name: "更多", exact: true }).click();
  await page.locator('.sidebar a[href="/learning"]').click();
  await page.getByRole("button", { name: "停止背景音乐" }).click();
  release();
  await page.waitForTimeout(250);
  await expect(page.locator(".mini-player")).toHaveCount(0);
  expect(mock.plays.map((track) => track.id)).toEqual(["1"]);
});

test("档位保存失败恢复原选择并允许重试", async ({ page, mock }) => {
  await page.route("**/api/v1/music/settings", (route) =>
    route.fulfill({ status: 409, json: { detail: "合成保存失败" } }),
  );
  await page.goto("/music");
  await page.getByRole("radio", { name: "沉浸", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("合成保存失败");
  await expect(
    page.getByRole("radio", { name: "自然", exact: true }),
  ).toBeChecked();
  await expect(
    page.getByRole("radio", { name: "沉浸", exact: true }),
  ).toBeEnabled();
});

test("辅导切换隔离历史并支持追问与函数画布", async ({ page, mock }, info) => {
  await page.goto("/learning/quiz/session");
  await page.getByRole("button", { name: "让老师讲这道" }).click();
  await expect(page.locator(".tutor-log")).toContainText("老师：先看知识点 q1");
  await page.getByRole("button", { name: "Xinxin 辅导", exact: true }).click();
  await expect(page.locator(".tutor-log")).not.toContainText(
    "老师：先看知识点",
  );
  await page.getByRole("button", { name: "让Xinxin讲这道" }).click();
  await expect(page.locator(".tutor-log")).toContainText(
    "Xinxin：我们一起想想呀 q1",
  );
  await page
    .getByRole("textbox", { name: "向Xinxin提问" })
    .fill("为什么先求导");
  await page.getByRole("button", { name: "发送追问" }).click();
  await expect.poll(() => mock.histories["q1:xinxin"]?.length).toBe(4);
  await expect(page.locator('.canvas-block svg[role="img"]')).toBeVisible();
  await page.getByRole("button", { name: "普通老师", exact: true }).click();
  await expect(page.locator(".tutor-log")).toContainText("老师：先看知识点 q1");
  await expect(page.locator(".tutor-log")).not.toContainText("Xinxin：");
  await page.screenshot({ path: info.outputPath("quiz.png"), fullPage: true });
});

test("切题时迟到的讲解不会串题", async ({ page, mock }) => {
  mock.explainDelay = 350;
  await page.goto("/learning/quiz/session");
  await page.getByRole("button", { name: "让老师讲这道" }).click();
  await page.getByRole("button", { name: "第 2 题", exact: true }).click();
  await expect(page.locator(".quiz-stem")).toContainText("y=2x");
  await page.waitForTimeout(450);
  await expect(page.locator(".tutor-log")).not.toContainText("q1");
  await page.getByRole("button", { name: "让老师讲这道" }).click();
  await expect(page.locator(".tutor-log")).toContainText("老师：先看知识点 q2");
});

test("切换辅导时迟到回复不会覆盖新模式", async ({ page, mock }) => {
  mock.explainDelay = 350;
  await page.goto("/learning/quiz/session");
  await page.getByRole("button", { name: "让老师讲这道" }).click();
  await page.getByRole("button", { name: "Xinxin 辅导", exact: true }).click();
  await page.waitForTimeout(450);
  await expect(page.locator(".tutor-log")).not.toContainText("老师：");
  await page.getByRole("button", { name: "让Xinxin讲这道" }).click();
  await expect(page.locator(".tutor-log")).toContainText("Xinxin：");
});

test("判分不会刷新掉当前题目的辅导历史", async ({ page, mock }) => {
  await page.goto("/learning/quiz/session");
  await page.getByRole("button", { name: "让老师讲这道" }).click();
  await expect(page.locator(".tutor-log")).toContainText("老师：");
  const historyReads = mock.calls.filter((item) =>
    item.path.endsWith("/tutor"),
  ).length;
  await page.locator(".quiz-option").first().click();
  await page.getByRole("button", { name: "提交", exact: true }).click();
  await expect(page.locator(".quiz-verdict")).toContainText("答对了");
  await expect(page.locator(".tutor-log")).toContainText("老师：");
  expect(
    mock.calls.filter((item) => item.path.endsWith("/tutor")),
  ).toHaveLength(historyReads);
});

test("判分期间切题不会把反馈放到另一题", async ({ page, mock }) => {
  mock.answerDelay = 350;
  await page.goto("/learning/quiz/session");
  await page.locator(".quiz-option").first().click();
  await page.getByRole("button", { name: "提交", exact: true }).click();
  await page.getByRole("button", { name: "第 2 题", exact: true }).click();
  await page.waitForTimeout(450);
  await expect(page.locator(".quiz-stem")).toContainText("y=2x");
  await expect(page.locator(".quiz-feedback")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "提交", exact: true }),
  ).toBeEnabled();
});

test("讲解失败保留草稿，重试不留下假的用户消息", async ({ page, mock }) => {
  mock.explainFailures = 1;
  await page.goto("/learning/quiz/session");
  const input = page.getByRole("textbox", { name: "向老师提问" });
  await expect(input).toBeEnabled();
  await input.fill("保留这句追问");
  await page.getByRole("button", { name: "发送追问" }).click();
  await expect(page.getByRole("alert")).toContainText("合成模型失败");
  await expect(input).toHaveValue("保留这句追问");
  await expect(page.locator(".tutor-log li.user")).toHaveCount(0);
  await page.getByRole("button", { name: "发送追问" }).click();
  await expect(page.locator(".tutor-log li.user")).toHaveCount(1);
  await expect(input).toHaveValue("");
});

test("历史读取失败有重试入口并避免覆盖旧对话", async ({ page, mock }) => {
  mock.historyFailures = 1;
  await page.goto("/learning/quiz/session");
  await expect(
    page.getByRole("button", { name: "让老师讲这道" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "重试", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "让老师讲这道" }),
  ).toBeEnabled();
});

test("练完可讲错题，再来一组保留书本与章节", async ({ page, mock }) => {
  await page.goto("/learning/quiz/session");
  await page.locator(".quiz-option").nth(1).click();
  await page.getByRole("button", { name: "提交", exact: true }).click();
  await page.getByRole("button", { name: "下一题", exact: true }).click();
  await page.locator(".quiz-option").first().click();
  await page.getByRole("button", { name: "提交", exact: true }).click();
  await expect(page.locator(".quiz-summary")).toBeVisible();
  await page.getByRole("button", { name: "查看讲解", exact: true }).click();
  await expect(page.locator(".quiz-feedback")).toContainText("答错了");
  await page.getByRole("button", { name: "让老师讲这道" }).click();
  await expect(page.locator(".tutor-log")).toContainText("老师：");
  await page.getByRole("button", { name: "查看总结", exact: true }).click();
  await page.getByRole("button", { name: "再来一组", exact: true }).click();
  await expect
    .poll(
      () =>
        mock.calls.find(
          (item) => item.path === "/learning/quiz" && item.method === "POST",
        )?.body,
    )
    .toEqual({ book_id: "book1", chapter_id: "chapter1", count: 2 });
});

test("音乐和学习在当前视口没有横向溢出", async ({ page, mock }) => {
  await search(page);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.goto("/learning/quiz/session");
  await expect(page.locator(".quiz-stem")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
