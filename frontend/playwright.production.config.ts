import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

// A separate, isolated production preview; never attach to the owner's app.
export default defineConfig({
  ...base,
  testMatch: "**/*.prod.ts",
  outputDir: ".qa-data/production/results",
  reporter: [
    ["list"],
    ["json", { outputFile: ".qa-data/production/report.json" }],
  ],
  use: { ...base.use, baseURL: "http://127.0.0.1:5197" },
  projects: [
    { name: "production", use: { viewport: { width: 1440, height: 1000 } } },
  ],
  webServer: [
    (base.webServer as { command: string; cwd?: string; url: string }[])[0],
    {
      command:
        "node node_modules/vite/bin/vite.js preview --outDir .qa-data/preview-dist --host 127.0.0.1 --port 5197",
      env: { XINXIN_BACKEND_PORT: "8017" },
      url: "http://127.0.0.1:5197",
      reuseExistingServer: false,
    },
  ],
});
