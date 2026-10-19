# Xinxin

**一个住在你自己电脑里的私人 Agent。** 对话、任务、文件、记忆、技能、绘图和自动化，全部收在一台机器上，用手机随时操作。

不需要云账号，不需要域名，不需要把数据交出去。

<p align="center">
  <img src="docs/screenshots/dashboard.jpg" alt="工作台" width="100%">
</p>

---

## 它是什么

Xinxin 是一个**单主人、本地优先**的 Agent 工作空间。它把「聊天」和「真正把事做完」放在同一条链路上：

- 你说目标，它拆解、调用工具、读写文件、跑命令，最后把产物交回来
- 每一轮任务都有事件流，断线可回放，超预算会停下并保留现场
- 技能不是一张固定的工具表，而是从 1800+ 个技能里按任务检索、扩展、重排后选出最必要的那几个
- 所有数据、模型密钥、生成文件都留在本机；后端只监听回环，局域网只开一个端口

它最初为云服务器而写，现在以**本机版**分发：开箱即用，手机连同一个 Wi-Fi 就能用。

---

## 界面导览

### 工作台

一屏看清今天的状态：最近的任务、执行节奏、资料库、可用技能，以及一个可以直接下发任务的入口（见上方首图）。

- 左侧是固定的功能区：Agent、任务、资料、服务器、技能、内容、工具、记忆、自动化
- 「从一个目标开始」直接把话交给 Agent，不用先想清楚要用哪个工具
- 右侧把「连接的工作区」可视化：技能、Agent、资料、服务器四个节点
- 最近 7 天的执行节奏和待处理任务一眼可见

### Agent

对话只是入口，真正的价值是它能在你的电脑上**持续把事做完**。下面是一轮演示对话：输入一句话，Agent 执行并流式回复；右侧可以展开本轮的过程、产物和技能轨迹。

<p align="center">
  <img src="docs/screenshots/agent.jpg" alt="Agent 对话" width="100%">
</p>

- 支持附件、图片、代码块和 Markdown 渲染
- 进度说明与最终答复分开记录：断流时的草稿只算过程，不污染历史
- 右侧「任务上下文」按过程 / 产物 / 技能分组，能点开看每一步
- 可以随时停止；停止后已执行的工具记录仍然保留，支持「继续原任务」续接

### 任务与交付

任务不是一次性的请求，而是可追踪、可回放、可续接的执行单元。

<p align="center">
  <img src="docs/screenshots/tasks.jpg" alt="任务与交付" width="100%">
</p>

- 状态：排队、进行中、已完成、失败、已取消
- 每个任务保留事件流（`started` / `skills` / `tool.started` / `tool.completed` / `delta` / `finished`）
- 失败会写清原因（例如预算耗尽），不会被假装成「完成」
- 支持按状态筛选、按关键词搜索、查看单次任务的完整过程

### 私人资料

手机上传，Agent 直接读写；文件永远留在你的电脑上。

<p align="center">
  <img src="docs/screenshots/files.jpg" alt="私人资料" width="100%">
</p>

- 单文件上限 64 MB，上传前先认证，超大请求在解析表单之前就被拒绝
- 同名重试用 `X-Upload-ID` 做幂等：网络抖动不会留下两份文件
- 文本、Markdown、CSV、PDF、DOCX 等自动抽取正文，可被 Agent 检索
- 下载走认证接口，不暴露真实路径

### 技能中心

这是 Xinxin 和「一堆固定工具」的 Agent 最大的不同。

<p align="center">
  <img src="docs/screenshots/skills.jpg" alt="技能中心" width="100%">
</p>

- 内置 1800+ 个技能，带契约（能力、输入、输出、适用场景）、质量评级和依赖关系
- 技能球按领域聚类，可拖拽、缩放、搜索、按领域筛选
- 每个技能都能看到来源、许可证、依赖和「平台是否真的能执行它」
- 社区技能按**只读资料**处理：正文懒加载、哈希校验，绝不自动执行其中的脚本

### 创作工具

数据图、图像处理、拾景，都是可以直接交给 Agent 的工具，也可以单独使用。

<p align="center">
  <img src="docs/screenshots/tools.jpg" alt="创作工具" width="100%">
</p>

- 内置 20+ 种论文级图表模板：森林图、火山图、生存曲线、ROC、SHAP、UMAP 等
- 支持 CSV 直接出图，也支持把绘图需求交给 Agent 生成可复现脚本
- 图像处理包括去水印、增强、修复、人像美化、抠图

### 个人内容

文章、相册、诗词、简历，都放在自己的私人空间里。

<p align="center">
  <img src="docs/screenshots/content.jpg" alt="个人内容" width="100%">
</p>

- 五种内容形态，各自有适合的展示方式
- 草稿与已发布分开，默认全部私有
- 可以附图、附件，Agent 也能读取这些内容作为上下文

### 记忆

少解释几遍，多一点长期理解。

<p align="center">
  <img src="docs/screenshots/memories.jpg" alt="长期记忆" width="100%">
</p>

- 偏好、事实、项目、习惯四类记忆
- 可以在设置里手动维护，也可以在对话中让 Agent 记住
- 记忆不进入云端；每轮只注入最近的少量条目，避免挤占上下文

### 自动化

把重复的事交给定时任务。

<p align="center">
  <img src="docs/screenshots/schedules.jpg" alt="自动化" width="100%">
</p>

- 固定间隔执行，权限和目标服务器随任务保存
- 停机期间不补跑，避免堆积副作用
- 每次执行都产生独立的任务记录，可回放、可停止

### 设置

模型、密钥、邮箱、背景、连接地址，都在一个地方。

<p align="center">
  <img src="docs/screenshots/settings.jpg" alt="设置" width="100%">
</p>

- 模型走任意 OpenAI 兼容接口，默认 DeepSeek；密钥加密存储，不回显
- 三档背景（纸纹 / 网格 / 纯净）和四种强调色，跟随你的习惯
- 「连接地址」直接显示本机、局域网和当前外部地址，可一键复制——不用记 IP

### 手机端

手机是控制端，不是执行端：命令始终在电脑上跑，手机只负责下发和查看。

<p align="center">
  <img src="docs/screenshots/mobile.jpg" alt="手机端" width="320">
</p>

- 响应式布局，手机浏览器可用，也可以「添加到主屏幕」当 PWA
- 支持打包 APK，预填局域网地址
- 抽屉式导航、触控友好的任务卡片、移动端输入框

---

## 它能做什么

| 类别 | 具体能力 |
| --- | --- |
| 对话与执行 | 多轮对话、任务拆解、工具调用、文件读写、命令执行、进度说明 |
| 研究与资料 | 文件上传、正文抽取、全文检索、引用阅读、论文级绘图、图片处理 |
| 内容生产 | 文章、合集、相册、诗词、简历；草稿与发布状态 |
| 长期协作 | 记忆、定时任务、任务续接、断线回放 |
| 技能体系 | 1800+ 技能检索、关系扩展、必要性重排、依赖排序、证据门控学习 |
| 多端 | 桌面浏览器、手机浏览器/PWA、Android APK |
| 模型 | 任意 OpenAI 兼容 Chat Completions 接口；密钥本地加密 |

---

## 和市面上的 Agent 有什么不同

### 一句话概括

> 市面上的 Agent 多是「把工具清单塞给模型」；Xinxin 是「先检索出候选技能，再让模型判断必要性，最后只把需要的交给它」——而且所有证据、预算和执行记录都留在本地。

### 功能差异

| 维度 | 常见云端 Agent | Xinxin |
| --- | --- | --- |
| 数据位置 | 平台账号与租户空间 | 本机 SQLite + 本地文件，默认不出机器 |
| 模型密钥 | 平台托管 | 本地加密（`vault.key`），不回传前端 |
| 工具来源 | 固定插件 / 应用市场安装代码 | 1800+ 只读技能语料；只有注册了工具的技能才能真正执行 |
| 技能选择 | 全量工具塞进提示，或向量 Top-K | 三通道融合 → 质量先验 → 关系扩展 → LLM 必要性重排 → 置信度分流 |
| 可以「不选」 | 通常强行调用一个工具 | 允许明确弃权（返回空选择），交给通用模型直答 |
| 学习机制 | 无，或简单的点击反馈 | 有工具成功证据才更新共享 LinUCB；没有证据不学习 |
| 任务模型 | 一次请求一次响应 | 持久化任务队列 + 事件流 + 断点续接 + 预算控制 |
| 失败处理 | 重试或直接报错 | 记录失败原因，保留已执行证据，可续接 |
| 网络形态 | SaaS，必须有公网入口 | 局域网优先，只开一个端口；外部访问是可选叠加 |
| 手机形态 | 官方 App | 手机浏览器 / PWA / 自签 APK，地址可预填 |

### 机制差异（重点）

#### 1. 技能路由：不是「工具列表」，是「检索 + 判断」

```
任务
 ├─ BM25 词汇召回
 ├─ E5 稠密语义召回
 └─ 领域 / 标签结构召回
        ↓ 加权融合（稠密 0.35 / 0.55 / 0.10）
   质量先验 0.85 + 0.3 × quality
        ↓
   关系图扩展（compose_with 0.88 / depend_on 0.80）
        ↓
   LLM 任务必要性重排（可少选、可不选，给出理由）
        ↓
   置信度分流：BM25 原始分 ≥15 自动 / ≥2 确认 / <2 直答
        ↓
   依赖拓扑排序 → 只把必要的技能卡交给 Agent
```

大多数 Agent 把所有工具定义塞进系统提示，技能一多就上下文爆炸；或者只做向量 Top-K，容易把「同领域但没用」的技能带进来。Xinxin 把「缩小空间」和「判断必要性」拆成两步，并且允许模型**明确说不**。

#### 2. 学习：没有执行证据，就不更新策略

技能被选中不等于它有用。只有同时满足：

- 本轮 `skills` 事件里确实选中了它
- 对应的工具真的执行成功（`tool.completed.ok = true`）

才允许提交反馈，更新共享 LinUCB。这样避免「模型说它好 → 它被排得更前 → 更常被选中」的自我强化。

#### 3. 执行：任务是有状态的，不是一次 HTTP 请求

```
queued → running → completed / failed / cancelled
events: queued · started · skills · usage · tool.* · delta · progress · finished
```

- 事件落 SQLite，SSE 推送；断线带上 `Last-Event-ID` 可以从游标续传
- 预算同时限制调用次数和令牌；耗尽时停止并保留现场，不清空已做的工具结果
- 同一 `request_key` 幂等，重复提交不会重复执行
- 单进程单 worker，避免多进程争抢同一份 SQLite

#### 4. 安全边界：把「能访问」和「能执行」分开

- 后端和前端只绑 `127.0.0.1`，局域网唯一入口是 Caddy 的 `8080`
- 认证是单主人账号；CORS 是精确来源白名单，不是 `*`
- 上传在解析 multipart 之前就校验身份和长度；落盘用 staging + 原子提交
- 社区技能语料只读，正文按需加载并做 SHA-256 校验，不 import 其中的 Python
- 密钥、密码、令牌不进入回答、产物和日志

---

## 内在逻辑

### 架构

```
┌────────────────────────── 这台电脑 ──────────────────────────┐
│                                                              │
│   浏览器 / PWA / APK                                          │
│          │ HTTP（局域网）                                     │
│          ▼                                                   │
│   Caddy 网关 :8080  ──反代──┐                                 │
│                             ├──> frontend 127.0.0.1:5180     │
│                             │     静态站点 + /api 代理        │
│                             └──> backend  127.0.0.1:8010     │
│                                   FastAPI + SQLite(WAL)      │
│                                   TaskManager / ModelGateway │
│                                   SkillRouter / 工具执行器     │
│                                                              │
│   backend/data/  ← 账号、密钥、文件、记忆、任务、事件          │
│   backend/resources/skillnet/  ← 只读技能语料                 │
└──────────────────────────────────────────────────────────────┘
```

- 只有一个对外端口；没有公网 IP 也能在局域网完整使用
- 数据层是 SQLite（WAL），任务、事件、会话、记忆同库事务
- 模型层是 OpenAI 兼容的 `Chat Completions`，可以换任意兼容服务

### 一轮任务的完整链路

```
1. 浏览器 POST /runs              → 持久化任务，返回 run_id
2. TaskManager 取队              → started 事件
3. SkillRouter.search            → 召回 / 扩展 / 重排 / 置信度
4. build_system_prompt           → 只注入选中的技能卡和工具证据
5. ModelGateway.apredict         → 流式输出；工具调用进入执行器
6. 工具执行                      → tool.started / tool.completed（含证据）
7. 事件写入 SQLite + SSE 推送     → 手机/浏览器实时看到进度
8. finished                      → 结果、用量、错误一起落库
```

### 提示空间怎么被控制

- 候选技能超过预算时，先压缩技能卡为 `selected_ids`，**再**裁剪前轮工具证据
- 检索审计数据（`candidates` / `graph_added`）只用于展示，不进入系统提示
- 上一轮的工具证据带 `seq`、参数和结果摘要，续接任务不靠模型记忆

---

## 快速开始

前置：Python 3.12+、Node.js 20+、Git；手机访问还需要 Caddy（`winget install Caddy.Caddy`，或放到 `tools/caddy.exe`）。

```powershell
# 每次开机启动（会自动建虚拟环境、装依赖、构建前端）
./Start-Xinxin-Local.ps1

# 或双击
启动Xinxin本地版.cmd
```

启动后终端会打印：

```
Xinxin本地版 已启动
  本机浏览器:    http://127.0.0.1:5180
  手机/局域网:   http://10.0.0.x:8080   （同一 WiFi，无需服务器）
  防火墙：已放行网关（程序规则），手机与电脑在同一 WiFi 即可访问
```

首次打开会要求创建主人账号；模型密钥在「设置 → 对话模型」里填。

### 常用命令

| 操作 | 命令 |
| --- | --- |
| 只本机调试（不起网关） | `./Start-Xinxin-Local.ps1 -NoGateway` |
| 不自动开浏览器 | `./Start-Xinxin-Local.ps1 -NoBrowser` |
| 换网关端口 | `./Start-Xinxin-Local.ps1 -GatewayPort 9090` |
| 停止 | `./Stop-Xinxin-Local.ps1` |
| 测试 | `cd backend && .venv/Scripts/python -m pytest -q`；`cd frontend && npx vitest run` |

### 手机

1. 手机与电脑连同一个 Wi-Fi
2. 浏览器打开 `http://<电脑局域网IP>:8080`，或安装预填地址的 APK

```powershell
cd frontend
.\build-android.ps1 -Local -Release -BackendUrl http://<本机局域网IP>:8080
```

APK 生成在 `frontend/releases/Xinxin-0.1.0-local.apk`，使用你自己的签名。

---

## 验证与边界

当前状态（2026-10-19）：

- 后端 **172** 项测试、前端 **37** 项测试通过；TypeScript 与生产构建通过
- 14 个页面 + 1 个对话态用无头浏览器逐页检查：**0 控制台错误、0 未捕获异常**
- 公网链路 20 项验收：HTTPS 登录、CORS、上传/下载（中文文件名）、401 CORS、SSE 到结束、断点续传、真实 Agent 任务、Fabric 重排
- 真实浏览器点击流程：登录表单 → Agent 输入 → 模型流式回复，全链路通过

明确的边界：

- 单主人、单进程；不是多租户 SaaS
- 本机版默认只在局域网可用；跨网络访问属于可选叠加，不是运行前提
- 社区技能是参考资料，不代表已经在本机验证过
- 模型的质量决定任务质量；平台不承诺「任何任务都能自动完成」

---

## 数据与备份

- 账号、密钥、文件、记忆、任务都在 `backend/data/`
- **`backend/data/vault.key` 不能丢**：丢失后加密凭据不可恢复
- 停服后复制整个 `backend/data/` 即完整备份
- `backend/resources/skillnet/` 随仓库分发，可离线校验

---

## 仓库结构

```
.
├── Start-Xinxin-Local.ps1 / Stop-Xinxin-Local.ps1   # 三角色启停
├── Start-Tunnel.ps1 / Stop-Tunnel.ps1               # 可选：外部访问
├── Caddyfile.local                                  # 单端口网关
├── backend/                                         # FastAPI + SQLite
│   ├── app/            # 路由、任务、技能、模型、工具
│   ├── tests/          # 172 项后端测试
│   ├── scripts/        # 冒烟、全链路、演示数据
│   └── resources/      # SkillNet 语料、绘图参考
├── frontend/                                        # React + TypeScript
│   ├── src/            # 页面、组件、样式
│   └── build-android.ps1
└── docs/               # 部署、验收与截图
```

前后端只通过版本化 HTTP 接口和事件契约协作，不跨目录 import，不直连数据库。

---

## 许可

本项目代码采用 MIT 许可（见 [LICENSE](LICENSE)）。`backend/resources/` 与 `vendor/` 中的第三方组件保留各自许可，详见 [`backend/THIRD_PARTY.md`](backend/THIRD_PARTY.md)。
