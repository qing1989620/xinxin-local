# 部署指南

在自己电脑上跑起来只需要三步。全程数据留在本机，不需要域名、证书、公网 IP。

## 1. 准备环境

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| Python | 3.12+ | 后端运行时 |
| Node.js | 20+ | 前端构建与预览 |
| Git | 任意 | 拉取代码 |
| Caddy | 2.x | 手机/局域网网关（**手机连接必需**） |
| JDK 21 + Android SDK 36 | — | 仅打 APK 时需要 |

Caddy 安装（任选一种）：

```powershell
winget install Caddy.Caddy
# 或从 https://caddyserver.com/download 下载 Windows amd64 标准版（无需插件），
# 放到项目根目录下的 tools/caddy.exe
```

脚本会优先用 PATH 里的 `caddy`，找不到再退回 `tools/caddy.exe`。

## 2. 一次性配置

```powershell
./Setup-Lan-Access.ps1
```

**要管理员权限**（用来放行 Windows 防火墙）。脚本检测到非管理员会自动弹 UAC 提权重启，也可以直接双击根目录的 `放行局域网防火墙.cmd`。

它会：

1. 探测本机局域网 IP，写入 `.runtime/lan-access.json`（已 git 忽略）
2. 创建防火墙入站规则「Xinxin本地版网关 (TCP 8080)」
3. 校验 Caddy 配置
4. 打印手机连接地址

如果当前 Wi-Fi 被识别为「公用网络」，脚本会提示改成专用网络——公用网络下 Windows 对入站的拦截更严格。手动改法：设置 → 网络和 Internet → Wi-Fi → 点击当前网络 → 网络配置文件类型 → 专用。

## 3. 启动与连接

```powershell
./Start-Xinxin-Local.ps1
```

首次启动会自动建虚拟环境、装依赖、构建前端。看到三个 `ready` 后会打印：

```
  本机浏览器:    http://127.0.0.1:5180
  手机/局域网:   http://10.0.0.x:8080   （手机需连同一 WiFi）
```

- **电脑**：浏览器开 `http://127.0.0.1:5180`
- **手机**：连同一个 Wi-Fi，浏览器开 `http://<电脑IP>:8080`，或安装打包好的 APK
- 停止：`./Stop-Xinxin-Local.ps1`（只停本启动器管理的三个进程）

也可以双击 `启动Xinxin本地版.cmd`。

### 端口

| 角色 | 端口 | 绑定 |
| --- | --- | --- |
| backend | 8010 | 127.0.0.1 |
| frontend | 5180 | 127.0.0.1 |
| gateway | 8080 | 所有网卡 |

换端口：`./Start-Xinxin-Local.ps1 -GatewayPort 9090`；改服务端口编辑 `backend/.env` 的 `XINXIN_PORT` / `XINXIN_FRONTEND_PORT`。

## 打包手机 APK（可选）

需要 JDK 21 + Android SDK 36：

```powershell
cd frontend
.\build-android.ps1 -Local -Release -BackendUrl http://<电脑局域网IP>:8080
```

产物 `frontend/releases/Xinxin-0.1.0-local.apk`，用你自己的发布签名（首次生成后一直复用）。HTTP 只允许私网 IP，公网地址必须用 HTTPS。

## 数据与备份

- 账号、模型密钥、SSH 凭据、文件、记忆、数据库都在 `backend/data/`，已 git 忽略。
- **`backend/data/vault.key` 不能丢**，凭据解密靠它，丢失不可恢复。
- 停服后整目录复制即完整备份。访问日志在 `logs/caddy-access.log`（自动滚动）。

## 安全边界

- 对外只开网关一个端口；后端与前端只绑 127.0.0.1。
- **不要把网关端口做路由器端口映射**：局域网 HTTP 明文只适合可信网络，外网访问须另配 HTTPS 域名方案。
- 登录走主人账号，知道地址不等于能登录。CORS 是精确来源白名单。

## 连不上怎么办

看 [局域网连接排查.md](局域网连接排查.md)（三步定位：服务是否活着 → 防火墙是否放行 → 是否同一网段）。
