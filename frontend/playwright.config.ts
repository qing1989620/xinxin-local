import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.pw.ts",
  fullyParallel: true,
  workers: 2,
  timeout: 25_000,
  expect: { timeout: 5_000 },
  outputDir: ".qa-data/playwright/results",
  reporter: [
    ["list"],
    ["json", { outputFile: ".qa-data/playwright/report.json" }],
  ],
  use: {
    baseURL: "http://127.0.0.1:5187",
    channel: process.env.PLAYWRIGHT_CHANNEL || "msedge",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    serviceWorkers: "block",
  },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 1000 } } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command:
        process.platform === "win32"
          ? ".venv\\Scripts\\python.exe scripts/browser_fixture.py"
          : ".venv/bin/python scripts/browser_fixture.py",
      cwd: "../backend",
      url: "http://127.0.0.1:8017/health",
      reuseExistingServer: false,
    },
    {
      command:
        "node node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 5187",
      env: { XINXIN_BACKEND_PORT: "8017" },
      url: "http://127.0.0.1:5187",
      reuseExistingServer: false,
    },
  ],
});
