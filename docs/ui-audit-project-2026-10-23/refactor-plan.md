# 实施与补证任务

保留HTTP分层与既有页面状态所有者，按确证反例修复。verified只指所列场景；真实网关、实体设备和外部交付的blocked不作通过。

10月24日增量：TASK-047（中文/混合语言4551识别及真实隔离服务回归）verified；TASK-048（正式快捷方式实际开窗）由主人明确确认，verified，FND-026 resolved。TASK-049另列重复点击激活及关闭重开，仍blocked，不扩展本次反馈范围。详见[桌面报告](../desktop-startup-2026-10-24.md)与audit.json。

| 任务 | 阶段 / 状态 | 范围 | 位置 | 依赖 | 场景 |
| --- | --- | --- | --- | --- | --- |
| TASK-001 登录与初始化布局/窗口统一与本地验证 | 2 / verified | PAGE-001, CMP-001, CMP-002, CMP-003, CMP-004, CMP-005 | frontend/src/App.tsx: AuthScreen; frontend/src/polish.css |  | SCN-001 |
| TASK-002 连接与启动状态布局/窗口统一与本地验证 | 2 / verified | PAGE-002, CMP-006, CMP-007, CMP-008 | frontend/src/App.tsx: App; frontend/src/polish.css |  | SCN-002 |
| TASK-003 导航与全局搜索布局/窗口统一与本地验证 | 2 / verified | PAGE-003, CMP-009, CMP-010, CMP-011, CMP-012, CMP-013, CMP-014 | frontend/src/App.tsx: App; frontend/src/polish.css |  | SCN-003 |
| TASK-004 工作台布局/窗口统一与本地验证 | 2 / verified | PAGE-004, CMP-015, CMP-016, CMP-017, CMP-018, CMP-019, CMP-020 | frontend/src/pages/Dashboard.tsx: Dashboard; frontend/src/polish.css |  | SCN-004 |
| TASK-005 Agent 对话布局/窗口统一与本地验证 | 2 / verified | PAGE-005, CMP-021, CMP-022, CMP-023, CMP-024, CMP-025, CMP-026, CMP-027, CMP-028, CMP-136 | frontend/src/pages/AgentPage.tsx: AgentPage; frontend/src/polish.css |  | SCN-005 |
| TASK-006 任务与详情布局/窗口统一与本地验证 | 2 / verified | PAGE-006, CMP-029, CMP-030, CMP-031, CMP-032, CMP-033, CMP-034 | frontend/src/pages/TasksPage.tsx: TasksPage; frontend/src/polish.css |  | SCN-006 |
| TASK-007 私人资料布局/窗口统一与本地验证 | 2 / blocked | PAGE-007, CMP-035, CMP-036, CMP-037, CMP-038, CMP-039, CMP-040 | frontend/src/pages/FilesPage.tsx: FilesPage; frontend/src/polish.css |  | SCN-007, SCN-034 |
| TASK-008 服务器布局/窗口统一与本地验证 | 2 / verified | PAGE-008, CMP-041, CMP-042, CMP-043, CMP-044 | frontend/src/pages/WorkspacePages.tsx: ServersPage; frontend/src/polish.css |  | SCN-008 |
| TASK-009 能力星图布局/窗口统一与本地验证 | 2 / verified | PAGE-009, CMP-045, CMP-046, CMP-047, CMP-048 | frontend/src/pages/SkillsPage.tsx: SkillsPage; frontend/src/polish.css |  | SCN-009 |
| TASK-010 能力库布局/窗口统一与本地验证 | 2 / verified | PAGE-010, CMP-049, CMP-050, CMP-051, CMP-052 | frontend/src/pages/SkillsPage.tsx: SkillsPage; frontend/src/polish.css |  | SCN-010 |
| TASK-011 技能选择实验室布局/窗口统一与本地验证 | 2 / verified | PAGE-011, CMP-053, CMP-054, CMP-055, CMP-056 | frontend/src/pages/SkillsPage.tsx: SkillsPage; frontend/src/polish.css |  | SCN-011 |
| TASK-012 文章布局/窗口统一与本地验证 | 2 / verified | PAGE-012, CMP-057, CMP-058, CMP-059, CMP-060 | frontend/src/pages/ContentPage.tsx: ContentPage; frontend/src/polish.css |  | SCN-012 |
| TASK-013 合集布局/窗口统一与本地验证 | 2 / verified | PAGE-013, CMP-061, CMP-062, CMP-063, CMP-064 | frontend/src/pages/ContentPage.tsx: ContentPage; frontend/src/polish.css |  | SCN-013 |
| TASK-014 相册布局/窗口统一与本地验证 | 2 / verified | PAGE-014, CMP-065, CMP-066, CMP-067, CMP-068 | frontend/src/pages/ContentPage.tsx: ContentPage; frontend/src/polish.css |  | SCN-014 |
| TASK-015 诗词布局/窗口统一与本地验证 | 2 / verified | PAGE-015, CMP-069, CMP-070, CMP-071, CMP-072 | frontend/src/pages/ContentPage.tsx: ContentPage; frontend/src/polish.css |  | SCN-015 |
| TASK-016 简历布局/窗口统一与本地验证 | 2 / verified | PAGE-016, CMP-073, CMP-074, CMP-075, CMP-076 | frontend/src/pages/ContentPage.tsx: ContentPage; frontend/src/polish.css |  | SCN-016 |
| TASK-017 工具与图库布局/窗口统一与本地验证 | 2 / verified | PAGE-017, CMP-077, CMP-078, CMP-079, CMP-080, CMP-081, CMP-082 | frontend/src/pages/WorkspacePages.tsx: ToolsPage; frontend/src/polish.css |  | SCN-017 |
| TASK-018 音乐搜索布局/窗口统一与本地验证 | 2 / verified | PAGE-018, CMP-083, CMP-084, CMP-085, CMP-086, CMP-087, CMP-088 | frontend/src/pages/MusicPage.tsx: MusicPage; frontend/src/polish.css |  | SCN-018 |
| TASK-019 音乐收藏布局/窗口统一与本地验证 | 2 / verified | PAGE-019, CMP-089, CMP-090, CMP-091 | frontend/src/pages/MusicPage.tsx: MusicPage; frontend/src/polish.css |  | SCN-019 |
| TASK-020 音乐歌单布局/窗口统一与本地验证 | 2 / verified | PAGE-020, CMP-092, CMP-093, CMP-094 | frontend/src/pages/MusicPage.tsx: MusicPage; frontend/src/polish.css |  | SCN-020, SCN-036 |
| TASK-021 长期记忆布局/窗口统一与本地验证 | 2 / verified | PAGE-021, CMP-095, CMP-096, CMP-097 | frontend/src/pages/WorkspacePages.tsx: MemoriesPage; frontend/src/polish.css |  | SCN-021 |
| TASK-022 自动化布局/窗口统一与本地验证 | 2 / verified | PAGE-022, CMP-098, CMP-099, CMP-100 | frontend/src/pages/WorkspacePages.tsx: SchedulesPage; frontend/src/polish.css |  | SCN-022 |
| TASK-023 设置布局/窗口统一与本地验证 | 2 / verified | PAGE-023, CMP-101, CMP-102, CMP-103, CMP-104, CMP-105, CMP-106, CMP-107, CMP-108 | frontend/src/pages/WorkspacePages.tsx: SettingsPage; frontend/src/polish.css |  | SCN-023 |
| TASK-024 学习工作室布局/窗口统一与本地验证 | 2 / verified | PAGE-024, CMP-109, CMP-110, CMP-111, CMP-112, CMP-132 | frontend/src/pages/LearningPage.tsx: LearningPage; frontend/src/polish.css |  | SCN-024, SCN-035, SCN-031 |
| TASK-025 教材与出题工作室布局/窗口统一与本地验证 | 2 / verified | PAGE-025, CMP-113, CMP-114, CMP-115, CMP-116, CMP-117, CMP-118, CMP-119, CMP-133, CMP-134, CMP-135 | frontend/src/pages/BookPage.tsx: BookPage; frontend/src/polish.css |  | SCN-025, SCN-031, SCN-032, SCN-030 |
| TASK-026 练习与双辅导布局/窗口统一与本地验证 | 2 / verified | PAGE-026, CMP-120, CMP-121, CMP-122, CMP-123, CMP-124, CMP-125 | frontend/src/pages/QuizPage.tsx: QuizPage; frontend/src/polish.css |  | SCN-026 |
| TASK-027 页面不存在布局/窗口统一与本地验证 | 2 / verified | PAGE-027, CMP-126 | frontend/src/App.tsx: App; frontend/src/polish.css |  | SCN-027 |
| TASK-028 桌面启动窗口布局/窗口统一与本地验证 | 2 / verified | PAGE-028, CMP-127, CMP-128 | desktop/assets/starting.html: starting.html; frontend/src/polish.css |  | SCN-028 |
| TASK-029 桌面错误窗口布局/窗口统一与本地验证 | 2 / verified | PAGE-029, CMP-129, CMP-130, CMP-131 | desktop/assets/error-template.html: error-template.html; frontend/src/polish.css |  | SCN-029 |
| TASK-032 修复生产依赖分块并复验最终所有路由 | 3 / verified | PRJ-001, PAGE-003, PAGE-004, PAGE-005 | frontend/vite.config.ts; frontend/e2e/workspace-production.prod.ts |  | SCN-038 |
| TASK-033 普通局域网 HTTP 缺少安全上下文 API，阻断核心提交 | 3 / verified | PAGE-005, PAGE-007, PAGE-024, PAGE-025, CMP-024, CMP-035, CMP-112, CMP-115 | frontend/src/api.ts; src/Uploads.tsx; src/pages/AgentPage.tsx |  | SCN-041 |
| TASK-034 明确停用网关后地址接口重新推测 LAN 地址 | 3 / verified | PAGE-023, CMP-104 | backend/app/network.py:local_addresses |  | SCN-042 |
| TASK-035 模型回显凭据可进入事件、最终答复和运行记录 | 3 / verified | PAGE-005, PAGE-006, CMP-023, CMP-033, CMP-136 | backend/app/agent.py; backend/app/public_text.py |  | SCN-043 |
| TASK-036 Agent 生图入口导入失效且线程取消未登记 | 3 / verified | PAGE-005, PAGE-017, CMP-028, CMP-079 | backend/app/agent.py:generate_image_tool; backend/app/imagegen.py:generate |  | SCN-044 |
| TASK-037 删生成会话会误删学习书原件，并残留专属缓存 | 3 / verified | PAGE-005, PAGE-007, PAGE-025, CMP-027, CMP-038, CMP-134 | backend/app/conversations.py:shared_file/purge_conversations |  | SCN-045 |
| TASK-038 题干保存及哈希折叠代码字符串空格与缩进 | 3 / verified | PAGE-025, PAGE-026, CMP-117, CMP-121 | backend/app/learning.py:_clean_stem/_hash |  | SCN-046 |
| TASK-039 旧凭据登录可跨越改密/重置的会话失效边界 | 3 / verified | PAGE-001, PAGE-023, CMP-002, CMP-003, CMP-105, CMP-108 | backend/app/auth.py; backend/app/main.py:auth routes |  | SCN-047 |
| TASK-040 旧会话迟到 401 会清除新登录并中断新工作 | 3 / verified | PAGE-001, PAGE-003, PAGE-005, PAGE-007, CMP-002, CMP-013, CMP-023, CMP-036 | frontend/src/api.ts:responseError/watchRun |  | SCN-048 |
| TASK-041 隧道控制按名字误停其他程序且会重启主人任务 | 3 / verified | PAGE-023, CMP-104 | Start-Tunnel.ps1; Stop-Tunnel.ps1; desktop/Tunnel-State.ps1 |  | SCN-049 |
| TASK-042 自定义启动端口未传网关，上游可能串到其他实例 | 3 / blocked | PAGE-002, PAGE-023, CMP-008, CMP-104 | Caddyfile.local; Start-Xinxin-Local.ps1 |  | SCN-050 |
| TASK-043 机器上保留的旧入口暴露后端并丢失新网关归属 | 3 / verified | PAGE-028, PAGE-029, CMP-127, CMP-131 | ignored local Start-Xinxin.ps1; Start-Xinxin-Phone.ps1; Stop-Xinxin.ps1 |  | SCN-051 |
| TASK-044 修复 Unicode 初始化码错误处理 | 3 / verified | PAGE-001, CMP-002, CMP-005 | backend/app/main.py:setup; backend/tests/test_platform.py:test_initialization_is_private_and_single_owner |  | SCN-052 |
| TASK-045 串行化预览发布与私有资料清理 | 3 / verified | PAGE-005, PAGE-007, CMP-027, CMP-038, CMP-039 | backend/app/files.py:FileLibrary.lifecycle_lock/preview/delete; backend/app/conversations.py:purge_conversations; backend/tests/test_project_review.py |  | SCN-053 |
| TASK-046 统一Agent发送及续接配置就绪状态 | 3 / verified | PAGE-005, CMP-023, CMP-024 | frontend/src/pages/AgentPage.tsx; frontend/src/agent.css; frontend/e2e/agent-settings.pw.ts |  | SCN-054 |
| TASK-030 真实屏幕阅读器与实体手机输入 | 4 / blocked | PRJ-001 | docs/ui-audit-2026-10-22/review.md |  | SCN-039 |
| TASK-031 真实模型教学质量与外部服务交付 | 4 / blocked | PRJ-001 | docs/ui-audit-2026-10-22/review.md |  | SCN-040 |
