# Xinxin Frontend

React + TypeScript 私人工作空间前端：工作台首页、Agent 一级入口、任务与产物、私人资料、服务器、技能星图与检索、个人内容、绘图/拾景、记忆、自动化和设置。

```powershell
npm ci
npm run dev
```

开发端口 `http://127.0.0.1:5180`，开发代理指向本机后端（见 `backend/.env` 的 `XINXIN_PORT`，默认 8010）。首次打开前端创建主人账号，初始化码在 `data/bootstrap.code`，随后在设置页配置模型密钥。登录/连接页面可指定自己的后端地址；切换后端会清除旧认证。

## 已确定的产品方向

- Agent 对话有一级直达入口。
- 响应式界面，暖白底、深灰文字、单一强调色、清晰网格和留白。
- 提供任务状态、文件和产物等有用交互。
- Android APK + 可安装 PWA，构建说明见 [android.md](docs/android.md)。
- 后端执行、数据库和密钥不进入此仓库。

```powershell
npm test
npm run build
./build-android.ps1
```

生产资源在 `dist/`，PWA 只缓存静态界面，不缓存私人 API/文件。

### 后端地址与构建参数

`VITE_API_BASE` 指定 API 地址：

- 局域网：`http://192.168.x.x:8080`（HTTP 仅限私网 IP）
- 公网：`https://域名`

HTTP 局域网地址必须配合 `VITE_LOCAL_PHONE_TEST=1` 放行混合内容，打包脚本 `build-android.ps1 -Local -Release -BackendUrl <地址>` 会自动处理。VITE 变量会进入产物，不能放密钥。Android 仅为客户端，任务在独立后端运行。

## 文档

- [需求规格](docs/product-spec.md)
- [快速审查与验收](docs/quick-review.md)
- [Android 构建与安装](docs/android.md)
