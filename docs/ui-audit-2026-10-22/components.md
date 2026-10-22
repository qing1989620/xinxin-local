# 逐页组件处置与证据边界

本清单覆盖全部已发现页面与区域。统一样式和窗口已经实施；源码静态通过不代替真实操作。`blocked` 保留实际缺口；本地正常态通过不表示所有业务分支/实机/外部能力均通过。

## 登录与初始化

/ [unauthenticated] · frontend/src/App.tsx: AuthScreen

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-001|登录与初始化 / 品牌叙事；/auth/status, setup, login, code/reset；匿名身份和邮箱验证|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-002|登录与初始化 / 登录方式与身份表单；/auth/status, setup, login, code/reset；匿名身份和邮箱验证|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-003|登录与初始化 / 验证码与重置；/auth/status, setup, login, code/reset；匿名身份和邮箱验证|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-004|登录与初始化 / 后端连接设置；/auth/status, setup, login, code/reset；匿名身份和邮箱验证|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-005|登录与初始化 / 错误与成功提示；/auth/status, setup, login, code/reset；匿名身份和邮箱验证|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 连接与启动状态

/ [boot/loading/offline] · frontend/src/App.tsx: App

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-006|连接与启动状态 / 启动标记；/health与服务地址；启动/离线/重试|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-007|连接与启动状态 / 离线错误；/health与服务地址；启动/离线/重试|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-008|连接与启动状态 / 后端地址与重连；/health与服务地址；启动/离线/重试|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 导航与全局搜索

/* [ready] · frontend/src/App.tsx: App

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-009|导航与全局搜索 / 桌面侧栏及收起；Routes、会话、主题、页面命令；导航只负责进入功能|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-010|导航与全局搜索 / 移动抽屉及底栏；Routes、会话、主题、页面命令；导航只负责进入功能|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-011|导航与全局搜索 / 顶部面包屑和搜索；Routes、会话、主题、页面命令；导航只负责进入功能|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-012|导航与全局搜索 / 全局页面搜索弹窗；Routes、会话、主题、页面命令；导航只负责进入功能|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-013|导航与全局搜索 / 主题与主人退出；Routes、会话、主题、页面命令；导航只负责进入功能|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-014|导航与全局搜索 / 安装更新通知；Routes、会话、主题、页面命令；导航只负责进入功能|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|

## 工作台

/ · frontend/src/pages/Dashboard.tsx: Dashboard

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-015|工作台 / 标题日期刷新；/dashboard资源和任务快照；目标转交Agent|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-016|工作台 / 目标输入和快捷行动；/dashboard资源和任务快照；目标转交Agent|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-017|工作台 / 资源星图；/dashboard资源和任务快照；目标转交Agent|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-018|工作台 / 概览指标；/dashboard资源和任务快照；目标转交Agent|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-019|工作台 / 最近行动筛选列表；/dashboard资源和任务快照；目标转交Agent|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-020|工作台 / 活动图与长期协作；/dashboard资源和任务快照；目标转交Agent|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|

## Agent 对话

/agent?conversation=:id · frontend/src/pages/AgentPage.tsx: AgentPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-021|Agent 对话 / 历史搜索归档选择；conversation/run、watchRun有序事件、附件、permission及SkillNet证据|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-022|Agent 对话 / 新对话及空态建议；conversation/run、watchRun有序事件、附件、permission及SkillNet证据|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-023|Agent 对话 / 消息流和工具活动；conversation/run、watchRun有序事件、附件、permission及SkillNet证据|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-024|Agent 对话 / 输入附件权限与上下文；conversation/run、watchRun有序事件、附件、permission及SkillNet证据|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-025|Agent 对话 / 资源选择弹窗；conversation/run、watchRun有序事件、附件、permission及SkillNet证据|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-026|Agent 对话 / 任务检查器及历史弹窗；conversation/run、watchRun有序事件、附件、permission及SkillNet证据|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-027|Agent 对话 / 对话管理删除确认；conversation/run、watchRun有序事件、附件、permission及SkillNet证据|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-028|Agent 对话 / 生图面板；conversation/run、watchRun有序事件、附件、permission及SkillNet证据|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-136|SkillNet 本轮路线与工具证据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 任务与详情

/tasks?run=:id · frontend/src/pages/TasksPage.tsx: TasksPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-029|任务与详情 / 标题新任务；/runs列表/详情/事件；权威快照与取消|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-030|任务与详情 / 搜索状态筛选刷新；/runs列表/详情/事件；权威快照与取消|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-031|任务与详情 / 任务列表；/runs列表/详情/事件；权威快照与取消|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-032|任务与详情 / 详情侧栏或模态；/runs列表/详情/事件；权威快照与取消|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-033|任务与详情 / 事件回放交付下载取消；/runs列表/详情/事件；权威快照与取消|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-034|任务与详情 / 失效详情错误；/runs列表/详情/事件；权威快照与取消|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 私人资料

/files?file=:id · frontend/src/pages/FilesPage.tsx: FilesPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-035|私人资料 / 标题上传；/files上传/列表/正文/预览；256 MiB和请求所有权|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-036|私人资料 / 文件拖放与上传队列；/files上传/列表/正文/预览；256 MiB和请求所有权|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-037|私人资料 / 名称搜索和正文检索；/files上传/列表/正文/预览；256 MiB和请求所有权|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-038|私人资料 / 资料行预览下载删除；/files上传/列表/正文/预览；256 MiB和请求所有权|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-039|私人资料 / 正文分页及图片预览弹窗；/files上传/列表/正文/预览；256 MiB和请求所有权|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-040|私人资料 / 预览错误和阅读跳转；/files上传/列表/正文/预览；256 MiB和请求所有权|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 服务器

/servers · frontend/src/pages/WorkspacePages.tsx: ServersPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-041|服务器 / 标题新增；/servers凭据状态和配置；执行授权在后端|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-042|服务器 / 权限说明；/servers凭据状态和配置；执行授权在后端|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-043|服务器 / 服务器卡片编辑删除；/servers凭据状态和配置；执行授权在后端|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-044|服务器 / SSH 表单弹窗；/servers凭据状态和配置；执行授权在后端|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|

## 能力星图

/skills [sphere] · frontend/src/pages/SkillsPage.tsx: SkillsPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-045|能力星图 / 标题与视图切换；/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-046|能力星图 / 星图画布及键盘替代列表；/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-047|能力星图 / 星图筛选缩放动效控制；/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-048|能力星图 / 能力详情弹窗；/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 能力库

/skills [library] · frontend/src/pages/SkillsPage.tsx: SkillsPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-049|能力库 / 搜索与布局；/skills列表、来源、领域、分页与护照|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-050|能力库 / 领域及来源筛选；/skills列表、来源、领域、分页与护照|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-051|能力库 / 能力卡片与加载更多；/skills列表、来源、领域、分页与护照|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-052|能力库 / 能力详情护照及 Agent 入口；/skills列表、来源、领域、分页与护照|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 技能选择实验室

/skills [lab] · frontend/src/pages/SkillsPage.tsx: SkillsPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-053|技能选择实验室 / 目标表单与示例；/skills/select目标预览；检索分数不授予执行权限|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-054|技能选择实验室 / 检索方法与降级提示；/skills/select目标预览；检索分数不授予执行权限|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-055|技能选择实验室 / 候选排序和依赖；/skills/select目标预览；检索分数不授予执行权限|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-056|技能选择实验室 / 进入对话与能力详情；/skills/select目标预览；检索分数不授予执行权限|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 文章

/content?kind=article · frontend/src/pages/ContentPage.tsx: ContentPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-057|文章 / 内容导航搜索新建；kind=article的/records、TipTap内容与附件|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-058|文章 / 文章卡片及行操作；kind=article的/records、TipTap内容与附件|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-059|文章 / 富文本编辑弹窗；kind=article的/records、TipTap内容与附件|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-060|文章 / 阅读预览及附件；kind=article的/records、TipTap内容与附件|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 合集

/content?kind=collection · frontend/src/pages/ContentPage.tsx: ContentPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-061|合集 / 内容导航搜索新建；kind=collection的/records及集合文章|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-062|合集 / 合集卡片及行操作；kind=collection的/records及集合文章|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-063|合集 / 封面描述编辑弹窗；kind=collection的/records及集合文章|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-064|合集 / 合集阅读与文章折叠；kind=collection的/records及集合文章|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 相册

/content?kind=photo · frontend/src/pages/ContentPage.tsx: ContentPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-065|相册 / 内容导航搜索新建；kind=photo的/records、私有图片URL与上传|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-066|相册 / 相册卡片与分类；kind=photo的/records、私有图片URL与上传|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-067|相册 / 图片上传编辑弹窗；kind=photo的/records、私有图片URL与上传|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-068|相册 / 私有照片预览；kind=photo的/records、私有图片URL与上传|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 诗词

/content?kind=poem · frontend/src/pages/ContentPage.tsx: ContentPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-069|诗词 / 内容导航搜索新建；kind=poem的/records与文本预览|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-070|诗词 / 诗词卡片及行操作；kind=poem的/records与文本预览|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-071|诗词 / 诗词编辑弹窗；kind=poem的/records与文本预览|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-072|诗词 / 诗词阅读弹窗；kind=poem的/records与文本预览|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 简历

/content?kind=resume · frontend/src/pages/ContentPage.tsx: ContentPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-073|简历 / 内容导航新建；kind=resume的/records、履历数组与打印|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-074|简历 / 简历文档与打印；kind=resume的/records、履历数组与打印|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-075|简历 / 履历教育技能编辑弹窗；kind=resume的/records、履历数组与打印|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-076|简历 / 删除与空态；kind=resume的/records、履历数组与打印|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 工具与图库

/tools · frontend/src/pages/WorkspacePages.tsx: ToolsPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-077|工具与图库 / 标题与双工具入口；/tools、CSV/图片资源上传与图库；请求期间受控字段组|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-078|工具与图库 / CSV 绘图表单弹窗；/tools、CSV/图片资源上传与图库；请求期间受控字段组|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-079|工具与图库 / 图片风格转换表单弹窗；/tools、CSV/图片资源上传与图库；请求期间受控字段组|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-080|工具与图库 / 上传及列选择状态；/tools、CSV/图片资源上传与图库；请求期间受控字段组|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-081|工具与图库 / 参考图库搜索筛选分页；/tools、CSV/图片资源上传与图库；请求期间受控字段组|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-082|工具与图库 / 图库详情代码复制下载；/tools、CSV/图片资源上传与图库；请求期间受控字段组|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 音乐搜索

/music [search] · frontend/src/pages/MusicPage.tsx: MusicPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-083|音乐搜索 / 标题播放状态；/music检索/取链/情绪、实际playing事件；Xinxin感受指数|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-084|音乐搜索 / 搜索与音乐源；/music检索/取链/情绪、实际playing事件；Xinxin感受指数|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-085|音乐搜索 / 曲目列表与操作；/music检索/取链/情绪、实际playing事件；Xinxin感受指数|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-086|音乐搜索 / 唱片播放控制音量进度；/music检索/取链/情绪、实际playing事件；Xinxin感受指数|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-087|音乐搜索 / 氛围和 Xinxin 感受档位；/music检索/取链/情绪、实际playing事件；Xinxin感受指数|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-088|音乐搜索 / 历史与说明；/music检索/取链/情绪、实际playing事件；Xinxin感受指数|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 音乐收藏

/music [favorites] · frontend/src/pages/MusicPage.tsx: MusicPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-089|音乐收藏 / 收藏导航及空态；/music/favorites及共享播放器；曲目键保持稳定|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|behavior、states、performance_lifecycle未实测|
|CMP-090|音乐收藏 / 收藏曲目播放和取消收藏；/music/favorites及共享播放器；曲目键保持稳定|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-091|音乐收藏 / 播放与氛围共用区；/music/favorites及共享播放器；曲目键保持稳定|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 音乐歌单

/music [playlists] · frontend/src/pages/MusicPage.tsx: MusicPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-092|音乐歌单 / 歌单新建编辑删除；/music/playlists与曲目详情；独立刷新及AbortController|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-093|音乐歌单 / 歌单曲目详情与返回；/music/playlists与曲目详情；独立刷新及AbortController|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-094|音乐歌单 / 添加到歌单弹窗；/music/playlists与曲目详情；独立刷新及AbortController|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 长期记忆

/memories · frontend/src/pages/WorkspacePages.tsx: MemoriesPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-095|长期记忆 / 标题新增；/memories CRUD；同步提交锁与失败保留|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-096|长期记忆 / 记忆卡片类别日期编辑删除；/memories CRUD；同步提交锁与失败保留|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-097|长期记忆 / 记忆保存弹窗；/memories CRUD；同步提交锁与失败保留|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 自动化

/schedules · frontend/src/pages/WorkspacePages.tsx: SchedulesPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-098|自动化 / 标题新增与权限说明；/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-099|自动化 / 定期任务行启停编辑删除；/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-100|自动化 / 自动化表单弹窗；/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 设置

/settings · frontend/src/pages/WorkspacePages.tsx: SettingsPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-101|设置 / 标题与分区导航；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-102|设置 / 强调色与背景；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-103|设置 / 自定义强调色；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-104|设置 / 连接地址复制；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-105|设置 / SMTP 或 Resend 邮箱表单；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-106|设置 / Resend 域名和 DNS；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-107|设置 / 对话及图像模型表单；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-108|设置 / 主人密码表单；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 学习工作室

/learning · frontend/src/pages/LearningPage.tsx: LearningPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-109|学习工作室 / 学习索引与导入；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-110|学习工作室 / 书库搜索与学习统计；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-111|学习工作室 / 错题复习入口；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-112|学习工作室 / 导入讲义弹窗；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-132|资料识别进度与取消恢复；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 教材与出题工作室

/learning/books/:id · frontend/src/pages/BookPage.tsx: BookPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-113|教材与出题工作室 / 返回标题和教材状态；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-114|教材与出题工作室 / 来源章节筛选；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-115|教材与出题工作室 / 出题配置表单；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-116|教材与出题工作室 / 持久化任务进度恢复取消；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-117|教材与出题工作室 / 题目分页预览；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-118|教材与出题工作室 / 原文阅读模态；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-119|教材与出题工作室 / 练习与删除入口；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-133|理解覆盖与片段摘要索引；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-134|知识证据与完整原题预览；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-135|出题前原文校对弹窗；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 练习与双辅导

/learning/quiz/:id · frontend/src/pages/QuizPage.tsx: QuizPage

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-120|练习与双辅导 / 标题进度与返回；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-121|练习与双辅导 / 题目选项及作答；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-122|练习与双辅导 / 提交批改和下一题；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-123|练习与双辅导 / 普通老师或 Xinxin 辅导；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-124|练习与双辅导 / 双模式历史和图表；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-125|练习与双辅导 / 原文提示与完成总结；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 页面不存在

/* [unknown] · frontend/src/App.tsx: App

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-126|页面不存在 / 错误标题与返回工作台；未知URL与返回工作台；无业务请求|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 桌面启动窗口

file:desktop/assets/starting.html · desktop/assets/starting.html: starting.html

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-127|桌面启动窗口 / 品牌和启动阶段；静态starting.html，桌面启动器持有服务阶段|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-128|桌面启动窗口 / 等待时间与关闭说明；静态starting.html，桌面启动器持有服务阶段|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

## 桌面错误窗口

file:desktop/assets/error-template.html · desktop/assets/error-template.html: error-template.html

|实例|区域与独有合同|处置|运行缺口|
|---|---|---|---|
|CMP-129|桌面错误窗口 / 失败标题和原因；静态error-template.html，脱敏日志与恢复说明|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-130|桌面错误窗口 / 脱敏日志及路径；静态error-template.html，脱敏日志与恢复说明|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|
|CMP-131|桌面错误窗口 / 恢复操作指引；静态error-template.html，脱敏日志与恢复说明|保留业务实现，配置统一主题/区域布局；完整BP见audit.json|performance_lifecycle未实测|

