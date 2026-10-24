# 发现、修复与未验证项

起点8fc0a83，前轮完整回归源码2a1fdf6：后端520通过/1项Caddy4551、浏览器143通过。桌面增量71e46ce另有8项定向回归通过，主人手工确认桌面已正常打开。数据与安全反例使用合成资料，新增桌面故障来自主人真实启动日志；不表示发生了私人数据事故。共26组发现，24组resolved、2组网关fixed_unverified。

## FND-001 / P2 / resolved — 设置窄屏溢出

实际反例：390px/320px设置表单强撑宽度

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：390px/320px设置表单强撑宽度

改动：可收缩网格和字段组断点

回归：设置：页面进入与已显示布局

场景：SCN-023；证据：EV-003；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-002 / P2 / resolved — 正文搜索/任务详情迟到与失败恢复

实际反例：旧搜索响应覆盖新状态、预览错误缺少重试

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：旧搜索响应覆盖新状态、预览错误缺少重试

改动：请求取消/所有权与错误重试

回归：私人资料：页面进入与已显示布局

场景：SCN-007；证据：EV-008；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-003 / P2 / resolved — 弹窗忙碌、隐藏字段焦点和通知

实际反例：隐藏file输入抢占初始焦点，外层通知被原生top layer遮挡

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：隐藏file输入抢占初始焦点，外层通知被原生top layer遮挡

改动：寻找真正可见字段，模态内通知，忙碌保护

回归：共用弹窗忙碌、焦点、通知与隐藏字段

场景：SCN-035；证据：EV-008；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-004 / P2 / resolved — 歌单被收藏请求阻塞

实际反例：保存成功但Promise.all等待收藏，歌单列表仍为空

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：保存成功但Promise.all等待收藏，歌单列表仍为空

改动：两类数据独立更新，保存结果立即反映

回归：音乐位移/四档/歌单独立刷新

场景：SCN-036；证据：EV-008；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-005 / P1 / resolved — Word公式与多级编号题干丢失

实际反例：定界符/noBar/未知结构被改义，编号问法被移出正文

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：定界符/noBar/未知结构被改义，编号问法被移出正文

改动：保留分隔符和全部base、genfrac、未知结构阻断、题干留正文

回归：扫描/混合/内联PDF和Word公式、编号题干完整性

场景：SCN-031；证据：EV-008；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-006 / P2 / resolved — 混合与内联扫描正文漏识别

实际反例：native页眉超过40字让扫描正文跳过OCR且标记完整

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：native页眉超过40字让扫描正文跳过OCR且标记完整

改动：逐页检查大幅图像含Form/inline；OCR覆盖和置信度警告

回归：扫描/混合/内联PDF和Word公式、编号题干完整性

场景：SCN-031；证据：EV-008；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-007 / P2 / resolved — 知识题误拒和有意义差异被误去重

实际反例：字节/page fault/如图像误拦，数学符号/字面量被归一化抹掉

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：字节/page fault/如图像误拦，数学符号/字面量被归一化抹掉

改动：定位语境约束、保守全字符匹配、恢复旧自动误隔离

回归：知识题误拒、完整题库去重及章节覆盖

场景：SCN-032；证据：EV-008；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-008 / P2 / resolved — 旧入口范围与总结状态不符

实际反例：章节只读取首片段，纯总结误要求原题

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：章节只读取首片段，纯总结误要求原题

改动：全章分配请求总量；analyze_only与出题策略分开

回归：资料理解、24题分批、原题标识与校对保护

场景：SCN-030；证据：EV-008；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-009 / P1 / fixed_unverified — 真实网关仍为64MiB

实际反例：后端256MiB但Caddy旧64MiB，配置更新还可能复用旧进程

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：后端256MiB但Caddy旧64MiB，配置更新还可能复用旧进程

改动：统一网关body预算并传配置指纹

回归：真实网关上传边界及清理

场景：SCN-034；证据：EV-008；修复证据：EV-029, EV-030。

## FND-010 / P2 / resolved — 缓存识别完成与书本链接快照竞态

实际反例：两次读取返回completed但book_id仍为空

影响：可能使对应资料/交互失败，或误导学习与保存结果。

根因：两次读取返回completed但book_id仍为空

改动：单SQL读取导入、run和进度快照

回归：扫描/混合/内联PDF和Word公式、编号题干完整性

场景：SCN-031；证据：EV-008；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-011 / P2 / resolved — 首页仍提前下载编辑器与Markdown依赖

实际反例：动态路由已有懒加载，但共享React/JSX模块被手动分块吸入可选功能，index.html仍modulepreload编辑器和Markdown。

影响：首页首屏下载并初始化尚未使用的大段代码。

根因：手动块以包入口定义，未固定共享内部模块及编辑器依赖归属。

改动：按包目录明确React/JSX/CJS与Tiptap/ProseMirror归属，onlyExplicitManualChunks限制依赖归并。

回归：3次冷缓存脚本体积和可选块缺席断言，导航Agent及损坏路由恢复。

场景：SCN-038；证据：EV-012；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-012 / P1 / resolved — 普通局域网 HTTP 缺少安全上下文 API，阻断核心提交

实际反例：crypto.randomUUID/subtle 在真实不安全 HTTP Edge 上不可用；上传、Agent 和学习任务会在发送前异常。

影响：普通局域网 HTTP 缺少安全上下文 API，阻断核心提交

根因：crypto.randomUUID/subtle 在真实不安全 HTTP Edge 上不可用；上传、Agent 和学习任务会在发送前异常。

改动：用 getRandomValues 构造 UUID，保持 SHA-256 指纹并为无 subtle 环境使用固定版本兼容实现；所有调用点共用。

回归：真实 HTTP 浏览器能力检查；requestIdentity 单元和 lan-http.pw.ts 跨旅程。

场景：SCN-041；证据：EV-015；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-013 / P2 / resolved — 明确停用网关后地址接口重新推测 LAN 地址

实际反例：saved.lan 为空被视为缺失，返回尚未运行的网关入口。

影响：明确停用网关后地址接口重新推测 LAN 地址

根因：saved.lan 为空被视为缺失，返回尚未运行的网关入口。

改动：区分键缺失与明确空值；网关停用时保持空地址。

回归：test_disabled_gateway_does_not_advertise_a_detected_lan

场景：SCN-042；证据：EV-015；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-014 / P1 / resolved — 模型回显凭据可进入事件、最终答复和运行记录

实际反例：真实调用无需发生即可合成复现：原始 delta/result/message 绕过已有脱敏器，分块会绕过逐块字符串替换。

影响：模型回显凭据可进入事件、最终答复和运行记录

根因：原始输出绕过过滤，随后组合规则和流式边界顺序也可能切穿已知值；quote完整性与JSON可解码性曾被混同。

改动：统一原文span合并和hold收敛，当前/历史凭据累积，完整有效JSON解码后处理；非法JSON走raw规则，未闭合尾部保守遮蔽；最终/异常进度统一过滤。

回归：test_public_text全部；test_project_review的raw_model/current_retained/incomplete_json正常及失败持久化；完整后端回归。

场景：SCN-043；证据：EV-015, EV-043；修复证据：EV-029, EV-030, EV-031, EV-034, EV-042, EV-044, EV-045, EV-046, EV-051。

## FND-015 / P2 / resolved — Agent 生图入口导入失效且线程取消未登记

实际反例：顶层 imagegen 不存在；async to_thread 未纳入同步工具 inflight，修正导入后可产生终态后迟到文件。

影响：Agent 生图入口导入失效且线程取消未登记

根因：顶层 imagegen 不存在；async to_thread 未纳入同步工具 inflight，修正导入后可产生终态后迟到文件。

改动：相对导入、同步受管执行、关联 run_id；外部请求前及登记前检查取消。

回归：test_actual_agent_image_tool_imports_and_registers_its_run_artifact; test_image_cancellation_waits_for_the_owned_thread_without_late_files

场景：SCN-044；证据：EV-015；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-016 / P1 / resolved — 删生成会话会误删学习书原件，并残留专属缓存

实际反例：学习书不计入共享引用；专属文件删除后 OCR 正文、提取元数据及预览仍留存。

影响：删生成会话会误删学习书原件，并残留专属缓存

根因：学习书不计入共享引用；专属文件删除后 OCR 正文、提取元数据及预览仍留存。

改动：事务保护书本/准备导入引用；只清理专属缓存，预览与原件一起移入可回滚暂存，失败保持回滚/待清理状态。

回归：test_conversation_deletion_preserves_book_originals_and_removes_exclusive_caches; existing rollback and path-escape tests

场景：SCN-045；证据：EV-015；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-017 / P2 / resolved — 题干保存及哈希折叠代码字符串空格与缩进

实际反例：print("1  2") 被改为单空格，题意与答案不再对应，且不同题干可能被错误去重。

影响：题干保存及哈希折叠代码字符串空格与缩进

根因：print("1  2") 被改为单空格，题意与答案不再对应，且不同题干可能被错误去重。

改动：仅清理外壳空白和非法 Unicode；保留内部字符及换行。

回归：test_question_validation_and_hash_preserve_meaningful_whitespace

场景：SCN-046；证据：EV-015；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-018 / P1 / resolved — 旧凭据登录可跨越改密/重置的会话失效边界

实际反例：校验/消费与签发不在同一临界区；已验证旧凭据可在改密撤销后再签发。

影响：旧凭据登录可跨越改密/重置的会话失效边界

根因：校验/消费与签发不在同一临界区；已验证旧凭据可在改密撤销后再签发。

改动：单 worker 运行时统一 RLock 覆盖完整验证、消费、变更、签发；敏感写入取得锁后复验 token。

回归：test_old_password_login_cannot_issue_after_completed_password_change; test_email_credential_transitions_are_serialized; test_revoked_identity_waiting_to_change_email_cannot_mutate_after_reset

场景：SCN-047；证据：EV-015；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-019 / P2 / resolved — 旧会话迟到 401 会清除新登录并中断新工作

实际反例：任何 401 都撤销当前身份，未核对发起请求时的会话。

影响：旧会话迟到 401 会清除新登录并中断新工作

根因：任何 401 都撤销当前身份，未核对发起请求时的会话。

改动：各传输入口捕获会话代际，只撤销同一身份；旧事件流不跨身份重连。

回归：api.test.ts delayed 401 cases for API, blob, upload and stream

场景：SCN-048；证据：EV-015；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-020 / P1 / resolved — 隧道控制按名字误停其他程序且会重启主人任务

实际反例：按 cloudflared 名称全机终止；启动隧道还改配置并停启当前后端，可能中断其他项目或工作。

影响：隧道控制按名字误停其他程序且会重启主人任务

根因：按 cloudflared 名称全机终止；启动隧道还改配置并停启当前后端，可能中断其他项目或工作。

改动：只校验本项目清单中的 PID/启动时间/可执行路径；校验受管网关；同源入口不改凭据、不重启服务；超时清理自身进程。

回归：test_tunnel_ownership.py; isolated PowerShell identity mocks

场景：SCN-049；证据：EV-015；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-021 / P1 / fixed_unverified — 自定义启动端口未传网关，上游可能串到其他实例

实际反例：网关固定连接 8010/5180，自定义服务启动后访问网关可 502 或进入默认实例。

影响：自定义启动端口未传网关，上游可能串到其他实例

根因：网关固定连接 8010/5180，自定义服务启动后访问网关可 502 或进入默认实例。

改动：后端/前端上游均参数化并写入专用 envfile，指纹包含三端口，配置改变重建网关。

回归：test_gateway_receives_both_upstream_ports_and_restarts_when_they_change; native Caddy integration pending OS permission

场景：SCN-050；证据：EV-015；修复证据：EV-029, EV-030。

## FND-022 / P2 / resolved — 机器上保留的旧入口暴露后端并丢失新网关归属

实际反例：旧 Phone 入口直绑 0.0.0.0，旧 Stop 会清掉包含网关的共享服务记录。

影响：机器上保留的旧入口暴露后端并丢失新网关归属

根因：旧 Phone 入口直绑 0.0.0.0，旧 Stop 会清掉包含网关的共享服务记录。

改动：原脚本先在 .runtime 私有备份，再改为当前 Local 启停的兼容别名；旧文件本来未跟踪，不强制加入 Git。

回归：本机ignored旧入口转发检查；完整test_local_launcher原生生命周期通过；Caddy真实转发仍单列阻塞。

场景：SCN-051；证据：EV-015；修复证据：EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-023 / P2 / resolved — 错误 Unicode 初始化码触发服务器异常

实际反例：hmac.compare_digest 的 str 比较仅支持 ASCII，普通中文错误输入触发 TypeError 而非拒绝响应。

影响：首次配置用户看到无意义的服务器异常，无法理解重试路径。

根因：直接对可能为 Unicode 的请求字符串调用仅支持 ASCII 的常量时间比较。

改动：UTF-8 编码后进行常量时间比较，保留初始化和单主人约束。

回归：test_initialization_is_private_and_single_owner：ASCII/中文错误码、正确码、重复创建与未认证访问。

场景：SCN-052；证据：EV-028；修复证据：EV-028, EV-029, EV-030, EV-031, EV-042, EV-045, EV-046。

## FND-024 / P2 / resolved — 预览缓存可在永久删除成功后迟到落盘

实际反例：预览已读取原图并暂停在PIL保存前，永久清理扫描后返回成功，预览恢复又生成专属JPEG。

影响：私人图片派生缓存可能在用户确认永久删除后仍落盘。

根因：预览缓存发布与删除缺少共享生命周期互斥。

改动：同一FileLibrary的预览、直接删除和永久清理/回滚取得同一可重入锁。

回归：test_inflight_preview_cannot_recreate_private_cache_after_deletion，两种删除模式+现有共享原件保护。

场景：SCN-053；证据：EV-036, EV-029；修复证据：EV-029, EV-030, EV-031, EV-035, EV-042, EV-045, EV-046。

## FND-025 / P2 / resolved — Agent配置尚未就绪但发送/继续按钮已可点击

实际反例：冷启动配置响应尚未返回时首次点击只有toast、没有POST；续接入口同样遗漏门控。移动端新提示还曾被旧hint样式隐藏。

影响：初次发送或恢复任务看似无反应，需额外点击。

根因：共享submit有配置守卫，两个可视入口的disabled条件没有该状态；移动hint选择器过宽。

改动：发送/续接统一要求settings.data，加载aria-busy/status和错误重读入口，独立响应式状态样式。

回归：frontend/e2e/agent-settings.pw.ts八项，完整浏览器回归。

场景：SCN-054；证据：EV-050；修复证据：EV-049, EV-046, EV-042, EV-051。

## FND-026 / P1 / resolved — 中文桌面启动未识别可选网关4551

实际反例：用户10:13—10:16双击桌面软件，回环前后端健康，但中文应用控制消息未被仅支持英文的helper识别，因此进入启动失败页。

修复：`71e46ce` 保留4551错误码识别，严格匹配完整中英文及混合语言消息；其他错误仍失败，系统策略不变。新增回归旧代码失败、补丁后8项桌面回归通过，包含中文UI/全流重定向下的真实隔离服务。

验收：自动审批曾阻止代为运行快捷方式，随后主人明确报告桌面“已能正常打开”，以手工确认记录真实开窗。重复点击激活和关闭重开不在本次反馈范围，另列待验证，不扩展此次通过范围。

场景：SCN-055/057 passed；证据：EV-053—058；任务：TASK-047/048 verified。另有SCN-056 / TASK-049保留重复点击与关闭重开的待验证状态。
