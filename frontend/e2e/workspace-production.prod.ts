import { test, expect } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";

test("生产构建：冷缓存首屏与按需路由加载", async ({ browser, request }) => {
  test.setTimeout(90_000);
  const response = await request.post("/api/v1/auth/login", {
    data: { name: "BrowserOwner", password: "synthetic-browser-password-123" },
  });
  expect(response.ok()).toBe(true);
  const token = (await response.json()).token;
  const samples = [];
  for (let index = 0; index < 3; index += 1) {
    const context = await browser.newContext({
      serviceWorkers: "block",
      viewport: { width: 1440, height: 1000 },
    });
    await context.addInitScript((value) => {
      sessionStorage.setItem("xinxin-session", value);
      const metrics = { lcp: 0, cls: 0, longTasks: 0 };
      (window as any).__studioMetrics = metrics;
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) metrics.lcp = entry.startTime;
      }).observe({ type: "largest-contentful-paint", buffered: true });
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries() as any[])
          if (!entry.hadRecentInput) metrics.cls += entry.value;
      }).observe({ type: "layout-shift", buffered: true });
      new PerformanceObserver((list) => {
        metrics.longTasks += list.getEntries().length;
      }).observe({ type: "longtask", buffered: true });
    }, token);
    const page = await context.newPage();
    await page.goto("http://127.0.0.1:5197/");
    await expect(page.locator(".mission-card")).toBeVisible();
    const initial = await page.evaluate(async () => {
      await new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      );
      return {
        ...(window as any).__studioMetrics,
        readyMs: performance.now(),
        scripts: performance
          .getEntriesByType("resource")
          .filter((entry) => /\/assets\/.*\.js$/.test(entry.name))
          .map((entry: any) => ({
            name: entry.name.split("/").at(-1),
            bytes: entry.decodedBodySize,
          })),
      };
    });
    expect(
      initial.scripts.some((entry: { name: string }) =>
        /^(editor|StudySource|AgentPage|ContentPage)-/.test(entry.name),
      ),
    ).toBe(false);
    expect(
      initial.scripts.reduce(
        (sum: number, entry: { bytes: number }) => sum + entry.bytes,
        0,
      ),
    ).toBeLessThan(500_000);
    const start = Date.now();
    await page
      .getByRole("navigation", { name: "主导航" })
      .getByRole("link", { name: "Agent", exact: true })
      .click();
    await expect(
      page.getByRole("textbox", { name: "给 Agent 的任务" }),
    ).toBeVisible();
    const agentReadyMs = Date.now() - start;
    const chunks = await page.evaluate(() =>
      performance.getEntriesByType("resource").map((entry) => entry.name),
    );
    expect(chunks.some((name) => /\/AgentPage-.*\.js$/.test(name))).toBe(true);
    samples.push({ sample: index + 1, ...initial, agentReadyMs });
    await context.close();
  }
  await mkdir(".qa-data/production", { recursive: true });
  await writeFile(
    ".qa-data/production/measurements.json",
    JSON.stringify(
      {
        environment:
          "Windows Edge, production preview, synthetic local backend, fresh context x3, service workers blocked; laboratory results, not field p75 or INP",
        samples,
      },
      null,
      2,
    ),
  );
});

test("生产构建：路由资源读取失败可回到工作台并重新加载恢复", async ({
  page,
  request,
}) => {
  const response = await request.post("/api/v1/auth/login", {
    data: { name: "BrowserOwner", password: "synthetic-browser-password-123" },
  });
  const token = (await response.json()).token;
  await page.addInitScript(
    (value) => sessionStorage.setItem("xinxin-session", value),
    token,
  );
  await page.goto("/");
  await expect(page.locator(".mission-card")).toBeVisible();
  await page.route("**/assets/AgentPage-*.js", (route) => route.abort());
  await page
    .getByRole("navigation", { name: "主导航" })
    .getByRole("link", { name: "Agent", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "界面出了一点问题" }),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "主导航" })
    .getByRole("link", { name: "工作台", exact: true })
    .click();
  await expect(page.locator(".mission-card")).toBeVisible();
  await page.unroute("**/assets/AgentPage-*.js");
  await page.goto("/agent");
  await expect(
    page.getByRole("textbox", { name: "给 Agent 的任务" }),
  ).toBeVisible();
});
