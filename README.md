# Xinxin

多功能个性化私人 AI Agent。项目最初是**为云服务器打造**的：一个单主人的私人工作空间，把 Agent 对话、任务执行、文件与资料、个人内容、技能检索、绘图和自动化，全部收敛到自己掌控的一台机器上，用手机随时操作。

它支持两种运行形态：

| 形态 | 运行在哪 | 手机怎么连 |
| --- | --- | --- |
| 云服务器部署 | 一台自己的 Linux 云主机（systemd + Caddy） | 用 HTTPS 域名或私有网络地址访问 |
| **本机部署**（本仓库交付形态） | 自己的 Windows 电脑，数据只在本机 | 连同一个 Wi-Fi，用局域网 IP 直连 |

本仓库以**本机部署（Xinxin本地版）**的形态分发：开箱即用，**不需要域名、证书或公网 IP**，也不需要路由器端口映射。

若想自行部署到云服务器：后端是标准 ASGI 服务（`uvicorn app.main:app`），前端是构建好的静态站点，只需用任意反向代理（Caddy/Nginx 均可）托管静态文件，并把 `/api`、`/health` 反代到后端即可；注意后端要保持**单进程**、CORS 用精确来源白名单。

## 手机怎么操控

手机是**控制端，不是执行端**——命令始终在电脑（或服务器）上执行，手机只负责下发指令和查看结果。

打开方式二选一：

- 手机浏览器打开 `http://<电脑局域网IP>:8080`，登录主人账号；可「添加到主屏幕」当独立 App 用
- 或安装本机打包的 APK（地址已预填，见下方打包步骤）

在手机上能做的事：

- 发起 Agent 对话，让它干活、问问题、陪你聊
- 下发任务并实时看进度、阶段说明和最终产物
- 上传文件到电脑、从电脑下载产物到本地
- 浏览和管理资料库（文章、合集、相册、诗词、简历）
- 查看任务事件流，断线后能回放
- 停止/取消正在跑的任务

不需要在手机里填任何模型密钥——密钥只保存在后端。

## 架构

```
┌────────────────────── 这台电脑 ──────────────────────┐
│  backend  127.0.0.1:8010   FastAPI + SQLite          │
│  frontend 127.0.0.1:5180   vite preview（含 /api 代理）│
│        ▲ Caddy 网关 :8080（纯 HTTP 单入口）             │
└────────┼─────────────────────────────────────────────┘
         │ 唯一对外出口是 8080；后端/前端只绑 127.0.0.1
   ┌─────┴──────┐         ┌──────────────┐      ┌──────────┐
   │ 家里/公司 Wi-Fi │ ─────→ │ 同一局域网任意设备 │ ────→ │ 手机 APK │
   └────────────┘         └──────────────┘      └──────────┘
```

三个角色由根目录脚本统一启停：

| 角色 | 端口 | 绑定 | 说明 |
| --- | --- | --- | --- |
| backend | 8010 | 127.0.0.1 | 业务与数据，SQLite 持久化 |
| frontend | 5180 | 127.0.0.1 | 静态站点 + `/api`、`/health` 代理 |
| gateway | 8080 | 所有网卡 | Caddy 纯 HTTP，手机/局域网唯一入口 |

## 快速开始

前置条件：Python 3.12+、Node.js 20+、Git。手机连接还需要 [Caddy](https://caddyserver.com/download)（Windows amd64 标准版即可，无需插件），可 `winget install Caddy.Caddy` 安装，或下载后放到 `tools/caddy.exe`。

```powershell
# 一次性配置（探测局域网 IP、放行 Windows 防火墙）：建议管理员权限
./Setup-Lan-Access.ps1

# 每次开机启动
./Start-Xinxin-Local.ps1
```

首次启动会自动创建虚拟环境、安装依赖并构建前端。启动完成后会打印实际地址：

```
Xinxin本地版 已启动
  本机浏览器:    http://127.0.0.1:5180
  手机/局域网:   http://10.0.0.x:8080   （手机需连同一 WiFi）
  停止: ./Stop-Xinxin-Local.ps1
```

也可以双击 `启动Xinxin本地版.cmd`。停止用 `./Stop-Xinxin-Local.ps1`，只停这个启动器记录的三个进程。

### 常用参数

| 操作 | 命令 |
| --- | --- |
| 不启动网关（仅本机调试） | `./Start-Xinxin-Local.ps1 -NoGateway` |
| 不自动打开浏览器 | `./Start-Xinxin-Local.ps1 -NoBrowser` |
| 换网关端口 | `./Start-Xinxin-Local.ps1 -GatewayPort 9090` |
| 换服务端口 | 改 `backend/.env` 的 `XINXIN_PORT` / `XINXIN_FRONTEND_PORT` |

## 手机连接

1. 手机与电脑连同一个 Wi-Fi。
2. 电脑执行 `./Setup-Lan-Access.ps1`（放行防火墙 TCP 8080），再 `./Start-Xinxin-Local.ps1`，记下打印的 `http://<局域网IP>:8080`。
3. 手机二选一：
   - 浏览器直接打开该地址（可添加到主屏当 PWA 用）；
   - 安装本机打包的 APK（见下），用主人账号登录。

打包预填局域网地址的 APK（在 `frontend/` 下执行，需要 JDK 21 + Android SDK 36）：

```powershell
.\build-android.ps1 -Local -Release -BackendUrl http://<本机局域网IP>:8080
```

APK 使用你自己的发布签名；生成在 `frontend/releases/Xinxin-0.1.0-local.apk`。HTTP 只允许私网 IP（10.x / 172.16–31.x / 192.168.x），公网地址必须用 HTTPS。

局域网 IP 变化后（换路由器/换网络），app 设置页里改服务器地址即可，或用上面的命令重新打包。

## 数据与备份

- 账号、模型密钥、SSH 凭据、文件、记忆、数据库都在 `backend/data/`，已被 Git 忽略。
- **`backend/data/vault.key` 不能丢**：密钥加密的凭据靠它解密，丢失不可恢复。
- 停服后整目录复制即完整备份；不需要同步到任何云端。
- 访问日志在 `logs/caddy-access.log`（自动滚动，单文件 10MiB、保留 5 个）。
- 技能语料在 `backend/resources/skillnet/`，随仓库分发，可离线校验。

## 安全边界

- 对外只开 `8080` 一个端口（纯 HTTP，仅局域网）；后端与前端只听 `127.0.0.1`，所有外部流量必须经 Caddy。
- **不要把 8080 在路由器上做端口映射**：HTTP 明文只适合局域网。跨网络访问用反向隧道（本机主动出网、Cloudflare 终止 TLS），见 [远程访问.md](docs/远程访问.md)。
- 登录走 Xinxin 自己的主人账号；知道地址不等于能登录。
- CORS 是精确来源白名单，未列名的来源即使打到 API 也会被浏览器拦截。
- 不需要远程访问时，跑 `./Stop-Xinxin-Local.ps1` 即从局域网消失。
- 密钥、密码、令牌不得写入回答、产物或日志。

## 仓库结构

```
.
├── Start-Xinxin-Local.ps1   # 启动三角色（backend/frontend/gateway）
├── Stop-Xinxin-Local.ps1    # 停止
├── Setup-Lan-Access.ps1     # 一次性：探测局域网 IP + 放行防火墙
├── Caddyfile.local          # 局域网网关配置（纯 HTTP）
├── 启动Xinxin本地版.cmd      # 双击启动
├── Xinxin本地版.md           # 使用指南
├── backend/                 # FastAPI 后端（Python）
│   ├── app/ tests/ scripts/ deploy/ vendor/
│   └── resources/           # 技能语料、绘图参考、分词器、许可
├── frontend/                # React + TypeScript 前端与 Android 壳
│   ├── src/ tests/ docs/ deploy/
│   └── build-android.ps1    # APK 打包脚本
└── docs/                    # 部署与运维文档
```

前后端通过版本化 HTTP 接口和事件契约协作，禁止跨目录源码 import、运行时读取兄弟仓库、前端直连数据库。

## 常见问题

- **手机连不上**：① 确认手机和电脑连的是同一个 Wi-Fi（访客网络隔离是常见坑）；② Windows 防火墙是否放行 8080（管理员跑 `./Setup-Lan-Access.ps1`）；③ 启动时打印的局域网 IP 是否已变；④ 公司网络可能做了客户端隔离，换手机热点验证。
- **端口被占用**：启动器会明确报错；加 `-GatewayPort` 换端口，或改 `backend/.env` 里的服务端口后重启。
- **手机能打开界面但一直转圈**：APK 预填的地址过期了，去设置页改成当前的 `http://<局域网IP>:8080`。
- **手机在外网（移动流量/别的城市）想连回这台电脑**：局域网方案要求同一网络，跨网络访问见 [远程访问.md](docs/远程访问.md)。里面先讲怎么判断你家宽带有没有公网 IP，再说明为什么「给 IP 套 SSL」单独解决不了这个问题，最后给出已在本机验证通过的云隧道方案与操作步骤。

## 许可

本项目自身代码采用 MIT 许可（见 [LICENSE](LICENSE)）。

`backend/resources/`、 `vendor/` 中的第三方组件保留各自许可与来源信息，随对应文件分发，详见 [`backend/THIRD_PARTY.md`](backend/THIRD_PARTY.md)。
