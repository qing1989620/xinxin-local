import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// 本地版后端端口：与 backend/.env 的 XINXIN_PORT 保持一致，
// Start-Xinxin-Local.ps1 启动 vite preview 时会注入该环境变量。
const backendPort = process.env.XINXIN_BACKEND_PORT || "8010";
const backendOrigin = `http://127.0.0.1:${backendPort}`;

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt",
      manifest: {
        name: "Xinxin本地版 · 私人工作空间",
        short_name: "Xinxin本地版",
        lang: "zh-CN",
        description: "运行在本机的私人 Agent，通过手机与电脑随时连接",
        theme_color: "#376c62",
        background_color: "#f7f5ef",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          {
            src: "/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        navigateFallbackDenylist: [/^\/api\//, /^\/health$/],
        cleanupOutdatedCaches: true,
      },
    }),
  ],
  // 公网隧道/自有域名进来时 Host 不是 localhost，Vite 7 默认会返回
  // 403 "Blocked request"（静态页面被拦、而 /api 走代理却正常，
  // 表现就是接口通、页面 403）。这里显式放行隧道域名族。
  server: {
    allowedHosts: [".trycloudflare.com", ".zhixuedu.cn", ".localhost"],
    watch: {
      ignored: ["**/android/**", "**/.toolchains/**", "**/releases/**"],
    },
    port: 5180,
    strictPort: true,
    proxy: {
      "/api": backendOrigin,
      "/health": backendOrigin,
    },
  },
  // 本地版用 vite preview 提供生产界面：/api 与 /health 同样转发给后端，
  // 使 http://127.0.0.1:5180 与公网隧道域名都可直接使用。
  preview: {
    allowedHosts: [".trycloudflare.com", ".zhixuedu.cn", ".localhost"],
    port: 5180,
    strictPort: true,
    proxy: {
      "/api": backendOrigin,
      "/health": backendOrigin,
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          editor: ["@tiptap/react", "@tiptap/starter-kit"],
          markdown: ["react-markdown", "remark-gfm"],
        },
      },
    },
  },
});
