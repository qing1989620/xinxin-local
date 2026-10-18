import type { CapacitorConfig } from "@capacitor/cli";
const config: CapacitorConfig = {
  appId: "com.xinxin.local",
  appName: "Xinxin本地版",
  webDir: "dist",
  server: { androidScheme: "https" },
  android: {
    backgroundColor: "#f7f5ef",
    allowMixedContent: process.env.VITE_LOCAL_PHONE_TEST === "1",
  },
};
export default config;
