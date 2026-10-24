# 组件合同与逐实例处置

132个定义、136个责任实例。内部纯装饰和重复数据行随状态所有者审查；不重复扩充分母。实际测试和缺口见 audit.json 与 coverage.md。

## BP-001 / DEF-001

frontend/src/App.tsx: AuthScreen / 品牌叙事；当前职责 品牌叙事

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 登录与初始化内负责品牌叙事；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：/auth/status, setup, login, code/reset；匿名身份和邮箱验证；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / [unauthenticated] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: AuthScreen 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/auth/status, setup, login, code/reset；匿名身份和邮箱验证的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: AuthScreen 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-001 / configure | frontend/src/App.tsx: AuthScreen; 可观察区域 品牌叙事; 归属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 | 登录与初始化 / 品牌叙事保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-001 |

## BP-002 / DEF-002

frontend/src/App.tsx: AuthScreen / 登录方式与身份表单；当前职责 登录方式与身份表单

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 登录与初始化内负责登录方式与身份表单；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/auth/status, setup, login, code/reset；匿名身份和邮箱验证；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / [unauthenticated] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: AuthScreen 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/auth/status, setup, login, code/reset；匿名身份和邮箱验证的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: AuthScreen 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-002 / configure | frontend/src/App.tsx: AuthScreen; 可观察区域 登录方式与身份表单; 归属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 | 登录与初始化 / 登录方式与身份表单保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-001 |

## BP-003 / DEF-003

frontend/src/App.tsx: AuthScreen / 验证码与重置；当前职责 验证码与重置

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 登录与初始化内负责验证码与重置；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/auth/status, setup, login, code/reset；匿名身份和邮箱验证；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / [unauthenticated] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: AuthScreen 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/auth/status, setup, login, code/reset；匿名身份和邮箱验证的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: AuthScreen 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-003 / configure | frontend/src/App.tsx: AuthScreen; 可观察区域 验证码与重置; 归属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 | 登录与初始化 / 验证码与重置保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-001 |

## BP-004 / DEF-004

frontend/src/App.tsx: AuthScreen / 后端连接设置；当前职责 后端连接设置

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 登录与初始化内负责后端连接设置；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/auth/status, setup, login, code/reset；匿名身份和邮箱验证；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / [unauthenticated] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: AuthScreen 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/auth/status, setup, login, code/reset；匿名身份和邮箱验证的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: AuthScreen 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-004 / configure | frontend/src/App.tsx: AuthScreen; 可观察区域 后端连接设置; 归属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 | 登录与初始化 / 后端连接设置保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-001 |

## BP-005 / DEF-005

frontend/src/App.tsx: AuthScreen / 错误与成功提示；当前职责 错误与成功提示

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 登录与初始化内负责错误与成功提示；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/auth/status, setup, login, code/reset；匿名身份和邮箱验证；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / [unauthenticated] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: AuthScreen 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/auth/status, setup, login, code/reset；匿名身份和邮箱验证的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: AuthScreen 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-005 / configure | frontend/src/App.tsx: AuthScreen; 可观察区域 错误与成功提示; 归属接口：/auth/status, setup, login, code/reset；匿名身份和邮箱验证 | 登录与初始化 / 错误与成功提示保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-001 |

## BP-006 / DEF-006

frontend/src/App.tsx: App / 启动标记；当前职责 启动标记

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 连接与启动状态内负责启动标记；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/health与服务地址；启动/离线/重试 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/health与服务地址；启动/离线/重试；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / [boot/loading/offline] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/health与服务地址；启动/离线/重试的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-006 / configure | frontend/src/App.tsx: App; 可观察区域 启动标记; 归属接口：/health与服务地址；启动/离线/重试 | 连接与启动状态 / 启动标记保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-002 |

## BP-007 / DEF-007

frontend/src/App.tsx: App / 离线错误；当前职责 离线错误

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 连接与启动状态内负责离线错误；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/health与服务地址；启动/离线/重试 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/health与服务地址；启动/离线/重试；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / [boot/loading/offline] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/health与服务地址；启动/离线/重试的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-007 / configure | frontend/src/App.tsx: App; 可观察区域 离线错误; 归属接口：/health与服务地址；启动/离线/重试 | 连接与启动状态 / 离线错误保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-002 |

## BP-008 / DEF-008

frontend/src/App.tsx: App / 后端地址与重连；当前职责 后端地址与重连

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 连接与启动状态内负责后端地址与重连；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/health与服务地址；启动/离线/重试 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/health与服务地址；启动/离线/重试；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / [boot/loading/offline] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/health与服务地址；启动/离线/重试的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-008 / configure | frontend/src/App.tsx: App; 可观察区域 后端地址与重连; 归属接口：/health与服务地址；启动/离线/重试 | 连接与启动状态 / 后端地址与重连保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-002 |

## BP-009 / DEF-009

frontend/src/App.tsx: App / 桌面侧栏及收起；当前职责 桌面侧栏及收起

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 导航与全局搜索内负责桌面侧栏及收起；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：Routes、会话、主题、页面命令；导航只负责进入功能 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：Routes、会话、主题、页面命令；导航只负责进入功能；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /* [ready] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；Routes、会话、主题、页面命令；导航只负责进入功能的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-009 / configure | frontend/src/App.tsx: App; 可观察区域 桌面侧栏及收起; 归属接口：Routes、会话、主题、页面命令；导航只负责进入功能 | 导航与全局搜索 / 桌面侧栏及收起保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-003 |

## BP-010 / DEF-010

frontend/src/App.tsx: App / 移动抽屉及底栏；当前职责 移动抽屉及底栏

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 导航与全局搜索内负责移动抽屉及底栏；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：Routes、会话、主题、页面命令；导航只负责进入功能 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：Routes、会话、主题、页面命令；导航只负责进入功能；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /* [ready] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；Routes、会话、主题、页面命令；导航只负责进入功能的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-010 / configure | frontend/src/App.tsx: App; 可观察区域 移动抽屉及底栏; 归属接口：Routes、会话、主题、页面命令；导航只负责进入功能 | 导航与全局搜索 / 移动抽屉及底栏保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-003 |

## BP-011 / DEF-011

frontend/src/App.tsx: App / 顶部面包屑和搜索；当前职责 顶部面包屑和搜索

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 导航与全局搜索内负责顶部面包屑和搜索；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：Routes、会话、主题、页面命令；导航只负责进入功能 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：Routes、会话、主题、页面命令；导航只负责进入功能；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /* [ready] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；Routes、会话、主题、页面命令；导航只负责进入功能的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-011 / configure | frontend/src/App.tsx: App; 可观察区域 顶部面包屑和搜索; 归属接口：Routes、会话、主题、页面命令；导航只负责进入功能 | 导航与全局搜索 / 顶部面包屑和搜索保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-003 |

## BP-012 / DEF-012

frontend/src/App.tsx: App / 全局页面搜索弹窗；当前职责 全局页面搜索弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 导航与全局搜索内负责全局页面搜索弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：Routes、会话、主题、页面命令；导航只负责进入功能 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：Routes、会话、主题、页面命令；导航只负责进入功能；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /* [ready] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；Routes、会话、主题、页面命令；导航只负责进入功能的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-012 / configure | frontend/src/App.tsx: App; 可观察区域 全局页面搜索弹窗; 归属接口：Routes、会话、主题、页面命令；导航只负责进入功能 | 导航与全局搜索 / 全局页面搜索弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-003 |

## BP-013 / DEF-013

frontend/src/App.tsx: App / 主题与主人退出；当前职责 主题与主人退出

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 导航与全局搜索内负责主题与主人退出；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：Routes、会话、主题、页面命令；导航只负责进入功能 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：Routes、会话、主题、页面命令；导航只负责进入功能；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /* [ready] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；Routes、会话、主题、页面命令；导航只负责进入功能的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-013 / configure | frontend/src/App.tsx: App; 可观察区域 主题与主人退出; 归属接口：Routes、会话、主题、页面命令；导航只负责进入功能 | 导航与全局搜索 / 主题与主人退出保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-003 |

## BP-014 / DEF-014

frontend/src/App.tsx: App / 安装更新通知；当前职责 安装更新通知

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 导航与全局搜索内负责安装更新通知；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：Routes、会话、主题、页面命令；导航只负责进入功能 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：Routes、会话、主题、页面命令；导航只负责进入功能；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /* [ready] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；Routes、会话、主题、页面命令；导航只负责进入功能的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-014 / configure | frontend/src/App.tsx: App; 可观察区域 安装更新通知; 归属接口：Routes、会话、主题、页面命令；导航只负责进入功能 | 导航与全局搜索 / 安装更新通知保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-003 |

## BP-015 / DEF-015

frontend/src/pages/Dashboard.tsx: Dashboard / 标题日期刷新；当前职责 标题日期刷新

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工作台内负责标题日期刷新；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/dashboard资源和任务快照；目标转交Agent |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/dashboard资源和任务快照；目标转交Agent；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/Dashboard.tsx: Dashboard 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/dashboard资源和任务快照；目标转交Agent的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/Dashboard.tsx: Dashboard 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-015 / configure | frontend/src/pages/Dashboard.tsx: Dashboard; 可观察区域 标题日期刷新; 归属接口：/dashboard资源和任务快照；目标转交Agent | 工作台 / 标题日期刷新保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-004 |

## BP-016 / DEF-016

frontend/src/pages/Dashboard.tsx: Dashboard / 目标输入和快捷行动；当前职责 目标输入和快捷行动

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工作台内负责目标输入和快捷行动；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/dashboard资源和任务快照；目标转交Agent |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/dashboard资源和任务快照；目标转交Agent；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/Dashboard.tsx: Dashboard 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/dashboard资源和任务快照；目标转交Agent的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/Dashboard.tsx: Dashboard 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-016 / configure | frontend/src/pages/Dashboard.tsx: Dashboard; 可观察区域 目标输入和快捷行动; 归属接口：/dashboard资源和任务快照；目标转交Agent | 工作台 / 目标输入和快捷行动保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-004 |

## BP-017 / DEF-017

frontend/src/pages/Dashboard.tsx: Dashboard / 资源星图；当前职责 资源星图

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工作台内负责资源星图；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/dashboard资源和任务快照；目标转交Agent |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/dashboard资源和任务快照；目标转交Agent；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/Dashboard.tsx: Dashboard 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/dashboard资源和任务快照；目标转交Agent的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/Dashboard.tsx: Dashboard 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-017 / configure | frontend/src/pages/Dashboard.tsx: Dashboard; 可观察区域 资源星图; 归属接口：/dashboard资源和任务快照；目标转交Agent | 工作台 / 资源星图保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-004 |

## BP-018 / DEF-018

frontend/src/pages/Dashboard.tsx: Dashboard / 概览指标；当前职责 概览指标

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工作台内负责概览指标；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/dashboard资源和任务快照；目标转交Agent |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：/dashboard资源和任务快照；目标转交Agent；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/Dashboard.tsx: Dashboard 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/dashboard资源和任务快照；目标转交Agent的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/Dashboard.tsx: Dashboard 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-018 / configure | frontend/src/pages/Dashboard.tsx: Dashboard; 可观察区域 概览指标; 归属接口：/dashboard资源和任务快照；目标转交Agent | 工作台 / 概览指标保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-004 |

## BP-019 / DEF-019

frontend/src/pages/Dashboard.tsx: Dashboard / 最近行动筛选列表；当前职责 最近行动筛选列表

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工作台内负责最近行动筛选列表；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/dashboard资源和任务快照；目标转交Agent |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/dashboard资源和任务快照；目标转交Agent；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/Dashboard.tsx: Dashboard 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/dashboard资源和任务快照；目标转交Agent的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/Dashboard.tsx: Dashboard 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-019 / configure | frontend/src/pages/Dashboard.tsx: Dashboard; 可观察区域 最近行动筛选列表; 归属接口：/dashboard资源和任务快照；目标转交Agent | 工作台 / 最近行动筛选列表保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-004 |

## BP-020 / DEF-020

frontend/src/pages/Dashboard.tsx: Dashboard / 活动图与长期协作；当前职责 活动图与长期协作

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工作台内负责活动图与长期协作；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/dashboard资源和任务快照；目标转交Agent |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/dashboard资源和任务快照；目标转交Agent；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 / 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/Dashboard.tsx: Dashboard 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/dashboard资源和任务快照；目标转交Agent的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/Dashboard.tsx: Dashboard 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-020 / configure | frontend/src/pages/Dashboard.tsx: Dashboard; 可观察区域 活动图与长期协作; 归属接口：/dashboard资源和任务快照；目标转交Agent | 工作台 / 活动图与长期协作保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-004 |

## BP-021 / DEF-021

frontend/src/pages/AgentPage.tsx: AgentPage / 历史搜索归档选择；当前职责 历史搜索归档选择

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | Agent 对话内负责历史搜索归档选择；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：conversation/run、watchRun有序事件、附件、permission及SkillNet证据；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /agent?conversation=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/AgentPage.tsx: AgentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/AgentPage.tsx: AgentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-021 / configure | frontend/src/pages/AgentPage.tsx: AgentPage; 可观察区域 历史搜索归档选择; 归属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 | Agent 对话 / 历史搜索归档选择保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-005 |

## BP-022 / DEF-022

frontend/src/pages/AgentPage.tsx: AgentPage / 新对话及空态建议；当前职责 新对话及空态建议

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | Agent 对话内负责新对话及空态建议；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：conversation/run、watchRun有序事件、附件、permission及SkillNet证据；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /agent?conversation=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/AgentPage.tsx: AgentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/AgentPage.tsx: AgentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-022 / configure | frontend/src/pages/AgentPage.tsx: AgentPage; 可观察区域 新对话及空态建议; 归属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 | Agent 对话 / 新对话及空态建议保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-005 |

## BP-023 / DEF-023

frontend/src/pages/AgentPage.tsx: AgentPage / 消息流和工具活动；当前职责 消息流和工具活动

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | Agent 对话内负责消息流和工具活动；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 配置loading/error/ready决定发送及恢复是否可用；重读不清草稿。 |
| data_effects | 权威数据及关联：conversation/run、watchRun有序事件、附件、permission及SkillNet证据；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /agent?conversation=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/AgentPage.tsx: AgentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/AgentPage.tsx: AgentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-023 / configure | frontend/src/pages/AgentPage.tsx: AgentPage; 可观察区域 消息流和工具活动; 归属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据; 配置未就绪时发送与续接禁用；延迟/失败状态可见，草稿保留并可重读。 | Agent 对话 / 消息流和工具活动保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-005, SCN-054 |

## BP-024 / DEF-024

frontend/src/pages/AgentPage.tsx: AgentPage / 输入附件权限与上下文；当前职责 输入附件权限与上下文

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | Agent 对话内负责输入附件权限与上下文；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 配置loading/error/ready决定发送及恢复是否可用；重读不清草稿。 |
| data_effects | 权威数据及关联：conversation/run、watchRun有序事件、附件、permission及SkillNet证据；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /agent?conversation=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/AgentPage.tsx: AgentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/AgentPage.tsx: AgentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-024 / configure | frontend/src/pages/AgentPage.tsx: AgentPage; 可观察区域 输入附件权限与上下文; 归属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据; 配置未就绪时发送与续接禁用；延迟/失败状态可见，草稿保留并可重读。 | Agent 对话 / 输入附件权限与上下文保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-005, SCN-054 |

## BP-025 / DEF-025

frontend/src/pages/AgentPage.tsx: AgentPage / 资源选择弹窗；当前职责 资源选择弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | Agent 对话内负责资源选择弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：conversation/run、watchRun有序事件、附件、permission及SkillNet证据；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /agent?conversation=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/AgentPage.tsx: AgentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/AgentPage.tsx: AgentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-025 / configure | frontend/src/pages/AgentPage.tsx: AgentPage; 可观察区域 资源选择弹窗; 归属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 | Agent 对话 / 资源选择弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-005 |

## BP-026 / DEF-026

frontend/src/pages/AgentPage.tsx: AgentPage / 任务检查器及历史弹窗；当前职责 任务检查器及历史弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | Agent 对话内负责任务检查器及历史弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：conversation/run、watchRun有序事件、附件、permission及SkillNet证据；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /agent?conversation=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/AgentPage.tsx: AgentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/AgentPage.tsx: AgentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-026 / configure | frontend/src/pages/AgentPage.tsx: AgentPage; 可观察区域 任务检查器及历史弹窗; 归属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 | Agent 对话 / 任务检查器及历史弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-005 |

## BP-027 / DEF-027

frontend/src/pages/AgentPage.tsx: AgentPage / 对话管理删除确认；当前职责 对话管理删除确认

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | Agent 对话内负责对话管理删除确认；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：conversation/run、watchRun有序事件、附件、permission及SkillNet证据；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /agent?conversation=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/AgentPage.tsx: AgentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 后端预览/删除/永久清理使用同一文件库生命周期锁，防止删除后发布专属缓存，保留共享学习引用。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/AgentPage.tsx: AgentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-027 / configure | frontend/src/pages/AgentPage.tsx: AgentPage; 可观察区域 对话管理删除确认; 归属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据; 后台预览与删除共用生命周期锁，删除完成后不再产生专属缓存；共享学习原件仍保留。 | Agent 对话 / 对话管理删除确认保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-005, SCN-053 |

## BP-028 / DEF-028

frontend/src/pages/AgentPage.tsx: AgentPage / 生图面板；当前职责 生图面板

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | Agent 对话内负责生图面板；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：conversation/run、watchRun有序事件、附件、permission及SkillNet证据；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /agent?conversation=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/AgentPage.tsx: AgentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/AgentPage.tsx: AgentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-028 / configure | frontend/src/pages/AgentPage.tsx: AgentPage; 可观察区域 生图面板; 归属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 | Agent 对话 / 生图面板保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-005 |

## BP-029 / DEF-029

frontend/src/pages/TasksPage.tsx: TasksPage / 标题新任务；当前职责 标题新任务

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 任务与详情内负责标题新任务；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/runs列表/详情/事件；权威快照与取消 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：/runs列表/详情/事件；权威快照与取消；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tasks?run=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/TasksPage.tsx: TasksPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/runs列表/详情/事件；权威快照与取消的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/TasksPage.tsx: TasksPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-029 / configure | frontend/src/pages/TasksPage.tsx: TasksPage; 可观察区域 标题新任务; 归属接口：/runs列表/详情/事件；权威快照与取消 | 任务与详情 / 标题新任务保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-006 |

## BP-030 / DEF-030

frontend/src/pages/TasksPage.tsx: TasksPage / 搜索状态筛选刷新；当前职责 搜索状态筛选刷新

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 任务与详情内负责搜索状态筛选刷新；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/runs列表/详情/事件；权威快照与取消 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/runs列表/详情/事件；权威快照与取消；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tasks?run=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/TasksPage.tsx: TasksPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/runs列表/详情/事件；权威快照与取消的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/TasksPage.tsx: TasksPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-030 / configure | frontend/src/pages/TasksPage.tsx: TasksPage; 可观察区域 搜索状态筛选刷新; 归属接口：/runs列表/详情/事件；权威快照与取消 | 任务与详情 / 搜索状态筛选刷新保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-006 |

## BP-031 / DEF-031

frontend/src/pages/TasksPage.tsx: TasksPage / 任务列表；当前职责 任务列表

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 任务与详情内负责任务列表；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/runs列表/详情/事件；权威快照与取消 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/runs列表/详情/事件；权威快照与取消；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tasks?run=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/TasksPage.tsx: TasksPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/runs列表/详情/事件；权威快照与取消的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/TasksPage.tsx: TasksPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-031 / configure | frontend/src/pages/TasksPage.tsx: TasksPage; 可观察区域 任务列表; 归属接口：/runs列表/详情/事件；权威快照与取消 | 任务与详情 / 任务列表保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-006 |

## BP-032 / DEF-032

frontend/src/pages/TasksPage.tsx: TasksPage / 详情侧栏或模态；当前职责 详情侧栏或模态

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 任务与详情内负责详情侧栏或模态；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/runs列表/详情/事件；权威快照与取消 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/runs列表/详情/事件；权威快照与取消；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tasks?run=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/TasksPage.tsx: TasksPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/runs列表/详情/事件；权威快照与取消的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/TasksPage.tsx: TasksPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-032 / configure | frontend/src/pages/TasksPage.tsx: TasksPage; 可观察区域 详情侧栏或模态; 归属接口：/runs列表/详情/事件；权威快照与取消 | 任务与详情 / 详情侧栏或模态保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-006 |

## BP-033 / DEF-033

frontend/src/pages/TasksPage.tsx: TasksPage / 事件回放交付下载取消；当前职责 事件回放交付下载取消

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 任务与详情内负责事件回放交付下载取消；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/runs列表/详情/事件；权威快照与取消 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/runs列表/详情/事件；权威快照与取消；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tasks?run=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/TasksPage.tsx: TasksPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/runs列表/详情/事件；权威快照与取消的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/TasksPage.tsx: TasksPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-033 / configure | frontend/src/pages/TasksPage.tsx: TasksPage; 可观察区域 事件回放交付下载取消; 归属接口：/runs列表/详情/事件；权威快照与取消 | 任务与详情 / 事件回放交付下载取消保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-006 |

## BP-034 / DEF-034

frontend/src/pages/TasksPage.tsx: TasksPage / 失效详情错误；当前职责 失效详情错误

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 任务与详情内负责失效详情错误；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/runs列表/详情/事件；权威快照与取消 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/runs列表/详情/事件；权威快照与取消；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tasks?run=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/TasksPage.tsx: TasksPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/runs列表/详情/事件；权威快照与取消的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/TasksPage.tsx: TasksPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-034 / configure | frontend/src/pages/TasksPage.tsx: TasksPage; 可观察区域 失效详情错误; 归属接口：/runs列表/详情/事件；权威快照与取消 | 任务与详情 / 失效详情错误保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-006 |

## BP-035 / DEF-035

frontend/src/pages/FilesPage.tsx: FilesPage / 标题上传；当前职责 标题上传

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 私人资料内负责标题上传；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/files上传/列表/正文/预览；256 MiB和请求所有权；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /files?file=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/FilesPage.tsx: FilesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/files上传/列表/正文/预览；256 MiB和请求所有权的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/FilesPage.tsx: FilesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-035 / configure | frontend/src/pages/FilesPage.tsx: FilesPage; 可观察区域 标题上传; 归属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 | 私人资料 / 标题上传保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-007 |

## BP-036 / DEF-036

frontend/src/pages/FilesPage.tsx: FilesPage / 文件拖放与上传队列；当前职责 文件拖放与上传队列

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 私人资料内负责文件拖放与上传队列；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/files上传/列表/正文/预览；256 MiB和请求所有权；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /files?file=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/FilesPage.tsx: FilesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/files上传/列表/正文/预览；256 MiB和请求所有权的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/FilesPage.tsx: FilesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-036 / configure | frontend/src/pages/FilesPage.tsx: FilesPage; 可观察区域 文件拖放与上传队列; 归属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 | 私人资料 / 文件拖放与上传队列保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-007 |

## BP-037 / DEF-037

frontend/src/pages/FilesPage.tsx: FilesPage / 名称搜索和正文检索；当前职责 名称搜索和正文检索

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 私人资料内负责名称搜索和正文检索；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/files上传/列表/正文/预览；256 MiB和请求所有权；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /files?file=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/FilesPage.tsx: FilesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/files上传/列表/正文/预览；256 MiB和请求所有权的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/FilesPage.tsx: FilesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-037 / configure | frontend/src/pages/FilesPage.tsx: FilesPage; 可观察区域 名称搜索和正文检索; 归属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 | 私人资料 / 名称搜索和正文检索保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-007 |

## BP-038 / DEF-038

frontend/src/pages/FilesPage.tsx: FilesPage / 资料行预览下载删除；当前职责 资料行预览下载删除

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 私人资料内负责资料行预览下载删除；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/files上传/列表/正文/预览；256 MiB和请求所有权；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /files?file=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/FilesPage.tsx: FilesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/files上传/列表/正文/预览；256 MiB和请求所有权的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 后端预览/删除/永久清理使用同一文件库生命周期锁，防止删除后发布专属缓存，保留共享学习引用。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/FilesPage.tsx: FilesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-038 / configure | frontend/src/pages/FilesPage.tsx: FilesPage; 可观察区域 资料行预览下载删除; 归属接口：/files上传/列表/正文/预览；256 MiB和请求所有权; 后台预览与删除共用生命周期锁，删除完成后不再产生专属缓存；共享学习原件仍保留。 | 私人资料 / 资料行预览下载删除保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-007, SCN-053 |

## BP-039 / DEF-039

frontend/src/pages/FilesPage.tsx: FilesPage / 正文分页及图片预览弹窗；当前职责 正文分页及图片预览弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 私人资料内负责正文分页及图片预览弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/files上传/列表/正文/预览；256 MiB和请求所有权；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /files?file=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/FilesPage.tsx: FilesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/files上传/列表/正文/预览；256 MiB和请求所有权的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 后端预览/删除/永久清理使用同一文件库生命周期锁，防止删除后发布专属缓存，保留共享学习引用。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/FilesPage.tsx: FilesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-039 / configure | frontend/src/pages/FilesPage.tsx: FilesPage; 可观察区域 正文分页及图片预览弹窗; 归属接口：/files上传/列表/正文/预览；256 MiB和请求所有权; 后台预览与删除共用生命周期锁，删除完成后不再产生专属缓存；共享学习原件仍保留。 | 私人资料 / 正文分页及图片预览弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-007, SCN-053 |

## BP-040 / DEF-040

frontend/src/pages/FilesPage.tsx: FilesPage / 预览错误和阅读跳转；当前职责 预览错误和阅读跳转

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 私人资料内负责预览错误和阅读跳转；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/files上传/列表/正文/预览；256 MiB和请求所有权；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /files?file=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/FilesPage.tsx: FilesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/files上传/列表/正文/预览；256 MiB和请求所有权的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/FilesPage.tsx: FilesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-040 / configure | frontend/src/pages/FilesPage.tsx: FilesPage; 可观察区域 预览错误和阅读跳转; 归属接口：/files上传/列表/正文/预览；256 MiB和请求所有权 | 私人资料 / 预览错误和阅读跳转保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-007 |

## BP-041 / DEF-041

frontend/src/pages/WorkspacePages.tsx: ServersPage / 标题新增；当前职责 标题新增

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 服务器内负责标题新增；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/servers凭据状态和配置；执行授权在后端 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/servers凭据状态和配置；执行授权在后端；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /servers 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ServersPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/servers凭据状态和配置；执行授权在后端的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ServersPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-041 / configure | frontend/src/pages/WorkspacePages.tsx: ServersPage; 可观察区域 标题新增; 归属接口：/servers凭据状态和配置；执行授权在后端 | 服务器 / 标题新增保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-008 |
| CMP-095 / configure | frontend/src/pages/WorkspacePages.tsx: MemoriesPage; 可观察区域 标题新增; 归属接口：/memories CRUD；同步提交锁与失败保留 | 长期记忆 / 标题新增保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-021 |

## BP-042 / DEF-042

frontend/src/pages/WorkspacePages.tsx: ServersPage / 权限说明；当前职责 权限说明

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 服务器内负责权限说明；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/servers凭据状态和配置；执行授权在后端 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：/servers凭据状态和配置；执行授权在后端；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /servers 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ServersPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/servers凭据状态和配置；执行授权在后端的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ServersPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-042 / configure | frontend/src/pages/WorkspacePages.tsx: ServersPage; 可观察区域 权限说明; 归属接口：/servers凭据状态和配置；执行授权在后端 | 服务器 / 权限说明保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-008 |

## BP-043 / DEF-043

frontend/src/pages/WorkspacePages.tsx: ServersPage / 服务器卡片编辑删除；当前职责 服务器卡片编辑删除

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 服务器内负责服务器卡片编辑删除；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/servers凭据状态和配置；执行授权在后端 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/servers凭据状态和配置；执行授权在后端；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /servers 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ServersPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/servers凭据状态和配置；执行授权在后端的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ServersPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-043 / configure | frontend/src/pages/WorkspacePages.tsx: ServersPage; 可观察区域 服务器卡片编辑删除; 归属接口：/servers凭据状态和配置；执行授权在后端 | 服务器 / 服务器卡片编辑删除保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-008 |

## BP-044 / DEF-044

frontend/src/pages/WorkspacePages.tsx: ServersPage / SSH 表单弹窗；当前职责 SSH 表单弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 服务器内负责SSH 表单弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/servers凭据状态和配置；执行授权在后端 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/servers凭据状态和配置；执行授权在后端；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /servers 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ServersPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/servers凭据状态和配置；执行授权在后端的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ServersPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-044 / configure | frontend/src/pages/WorkspacePages.tsx: ServersPage; 可观察区域 SSH 表单弹窗; 归属接口：/servers凭据状态和配置；执行授权在后端 | 服务器 / SSH 表单弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-008 |

## BP-045 / DEF-045

frontend/src/pages/SkillsPage.tsx: SkillsPage / 标题与视图切换；当前职责 标题与视图切换

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 能力星图内负责标题与视图切换；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [sphere] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-045 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 标题与视图切换; 归属接口：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom | 能力星图 / 标题与视图切换保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-009 |

## BP-046 / DEF-046

frontend/src/pages/SkillsPage.tsx: SkillsPage / 星图画布及键盘替代列表；当前职责 星图画布及键盘替代列表

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 能力星图内负责星图画布及键盘替代列表；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [sphere] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-046 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 星图画布及键盘替代列表; 归属接口：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom | 能力星图 / 星图画布及键盘替代列表保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-009 |

## BP-047 / DEF-047

frontend/src/pages/SkillsPage.tsx: SkillsPage / 星图筛选缩放动效控制；当前职责 星图筛选缩放动效控制

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 能力星图内负责星图筛选缩放动效控制；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [sphere] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-047 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 星图筛选缩放动效控制; 归属接口：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom | 能力星图 / 星图筛选缩放动效控制保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-009 |

## BP-048 / DEF-048

frontend/src/pages/SkillsPage.tsx: SkillsPage / 能力详情弹窗；当前职责 能力详情弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 能力星图内负责能力详情弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [sphere] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-048 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 能力详情弹窗; 归属接口：/skills目录/关系；Canvas视觉索引与键盘目录，query/domain/selected/zoom | 能力星图 / 能力详情弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-009 |

## BP-049 / DEF-049

frontend/src/pages/SkillsPage.tsx: SkillsPage / 搜索与布局；当前职责 搜索与布局

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 能力库内负责搜索与布局；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills列表、来源、领域、分页与护照 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills列表、来源、领域、分页与护照；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [library] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills列表、来源、领域、分页与护照的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-049 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 搜索与布局; 归属接口：/skills列表、来源、领域、分页与护照 | 能力库 / 搜索与布局保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-010 |

## BP-050 / DEF-050

frontend/src/pages/SkillsPage.tsx: SkillsPage / 领域及来源筛选；当前职责 领域及来源筛选

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 能力库内负责领域及来源筛选；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills列表、来源、领域、分页与护照 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills列表、来源、领域、分页与护照；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [library] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills列表、来源、领域、分页与护照的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-050 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 领域及来源筛选; 归属接口：/skills列表、来源、领域、分页与护照 | 能力库 / 领域及来源筛选保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-010 |

## BP-051 / DEF-051

frontend/src/pages/SkillsPage.tsx: SkillsPage / 能力卡片与加载更多；当前职责 能力卡片与加载更多

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 能力库内负责能力卡片与加载更多；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills列表、来源、领域、分页与护照 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills列表、来源、领域、分页与护照；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [library] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills列表、来源、领域、分页与护照的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-051 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 能力卡片与加载更多; 归属接口：/skills列表、来源、领域、分页与护照 | 能力库 / 能力卡片与加载更多保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-010 |

## BP-052 / DEF-052

frontend/src/pages/SkillsPage.tsx: SkillsPage / 能力详情护照及 Agent 入口；当前职责 能力详情护照及 Agent 入口

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 能力库内负责能力详情护照及 Agent 入口；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills列表、来源、领域、分页与护照 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills列表、来源、领域、分页与护照；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [library] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills列表、来源、领域、分页与护照的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-052 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 能力详情护照及 Agent 入口; 归属接口：/skills列表、来源、领域、分页与护照 | 能力库 / 能力详情护照及 Agent 入口保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-010 |

## BP-053 / DEF-053

frontend/src/pages/SkillsPage.tsx: SkillsPage / 目标表单与示例；当前职责 目标表单与示例

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 技能选择实验室内负责目标表单与示例；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills/select目标预览；检索分数不授予执行权限 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills/select目标预览；检索分数不授予执行权限；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [lab] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills/select目标预览；检索分数不授予执行权限的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-053 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 目标表单与示例; 归属接口：/skills/select目标预览；检索分数不授予执行权限 | 技能选择实验室 / 目标表单与示例保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-011 |

## BP-054 / DEF-054

frontend/src/pages/SkillsPage.tsx: SkillsPage / 检索方法与降级提示；当前职责 检索方法与降级提示

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 技能选择实验室内负责检索方法与降级提示；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills/select目标预览；检索分数不授予执行权限 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills/select目标预览；检索分数不授予执行权限；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [lab] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills/select目标预览；检索分数不授予执行权限的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-054 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 检索方法与降级提示; 归属接口：/skills/select目标预览；检索分数不授予执行权限 | 技能选择实验室 / 检索方法与降级提示保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-011 |

## BP-055 / DEF-055

frontend/src/pages/SkillsPage.tsx: SkillsPage / 候选排序和依赖；当前职责 候选排序和依赖

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 技能选择实验室内负责候选排序和依赖；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills/select目标预览；检索分数不授予执行权限 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills/select目标预览；检索分数不授予执行权限；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [lab] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills/select目标预览；检索分数不授予执行权限的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-055 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 候选排序和依赖; 归属接口：/skills/select目标预览；检索分数不授予执行权限 | 技能选择实验室 / 候选排序和依赖保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-011 |

## BP-056 / DEF-056

frontend/src/pages/SkillsPage.tsx: SkillsPage / 进入对话与能力详情；当前职责 进入对话与能力详情

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 技能选择实验室内负责进入对话与能力详情；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/skills/select目标预览；检索分数不授予执行权限 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/skills/select目标预览；检索分数不授予执行权限；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /skills [lab] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/SkillsPage.tsx: SkillsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/skills/select目标预览；检索分数不授予执行权限的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/SkillsPage.tsx: SkillsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-056 / configure | frontend/src/pages/SkillsPage.tsx: SkillsPage; 可观察区域 进入对话与能力详情; 归属接口：/skills/select目标预览；检索分数不授予执行权限 | 技能选择实验室 / 进入对话与能力详情保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-011 |

## BP-057 / DEF-057

frontend/src/pages/ContentPage.tsx: ContentPage / 内容导航搜索新建；当前职责 内容导航搜索新建

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 文章内负责内容导航搜索新建；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=article的/records、TipTap内容与附件 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=article的/records、TipTap内容与附件；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=article 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=article的/records、TipTap内容与附件的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-057 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 内容导航搜索新建; 归属接口：kind=article的/records、TipTap内容与附件 | 文章 / 内容导航搜索新建保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-012 |
| CMP-061 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 内容导航搜索新建; 归属接口：kind=collection的/records及集合文章 | 合集 / 内容导航搜索新建保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-013 |
| CMP-065 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 内容导航搜索新建; 归属接口：kind=photo的/records、私有图片URL与上传 | 相册 / 内容导航搜索新建保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-014 |
| CMP-069 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 内容导航搜索新建; 归属接口：kind=poem的/records与文本预览 | 诗词 / 内容导航搜索新建保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-015 |

## BP-058 / DEF-058

frontend/src/pages/ContentPage.tsx: ContentPage / 文章卡片及行操作；当前职责 文章卡片及行操作

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 文章内负责文章卡片及行操作；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=article的/records、TipTap内容与附件 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=article的/records、TipTap内容与附件；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=article 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=article的/records、TipTap内容与附件的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-058 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 文章卡片及行操作; 归属接口：kind=article的/records、TipTap内容与附件 | 文章 / 文章卡片及行操作保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-012 |

## BP-059 / DEF-059

frontend/src/pages/ContentPage.tsx: ContentPage / 富文本编辑弹窗；当前职责 富文本编辑弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 文章内负责富文本编辑弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=article的/records、TipTap内容与附件 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=article的/records、TipTap内容与附件；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=article 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=article的/records、TipTap内容与附件的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-059 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 富文本编辑弹窗; 归属接口：kind=article的/records、TipTap内容与附件 | 文章 / 富文本编辑弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-012 |

## BP-060 / DEF-060

frontend/src/pages/ContentPage.tsx: ContentPage / 阅读预览及附件；当前职责 阅读预览及附件

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 文章内负责阅读预览及附件；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=article的/records、TipTap内容与附件 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=article的/records、TipTap内容与附件；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=article 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=article的/records、TipTap内容与附件的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-060 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 阅读预览及附件; 归属接口：kind=article的/records、TipTap内容与附件 | 文章 / 阅读预览及附件保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-012 |

## BP-061 / DEF-061

frontend/src/pages/ContentPage.tsx: ContentPage / 合集卡片及行操作；当前职责 合集卡片及行操作

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 合集内负责合集卡片及行操作；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=collection的/records及集合文章 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=collection的/records及集合文章；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=collection 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=collection的/records及集合文章的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-062 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 合集卡片及行操作; 归属接口：kind=collection的/records及集合文章 | 合集 / 合集卡片及行操作保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-013 |

## BP-062 / DEF-062

frontend/src/pages/ContentPage.tsx: ContentPage / 封面描述编辑弹窗；当前职责 封面描述编辑弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 合集内负责封面描述编辑弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=collection的/records及集合文章 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=collection的/records及集合文章；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=collection 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=collection的/records及集合文章的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-063 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 封面描述编辑弹窗; 归属接口：kind=collection的/records及集合文章 | 合集 / 封面描述编辑弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-013 |

## BP-063 / DEF-063

frontend/src/pages/ContentPage.tsx: ContentPage / 合集阅读与文章折叠；当前职责 合集阅读与文章折叠

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 合集内负责合集阅读与文章折叠；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=collection的/records及集合文章 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=collection的/records及集合文章；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=collection 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=collection的/records及集合文章的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-064 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 合集阅读与文章折叠; 归属接口：kind=collection的/records及集合文章 | 合集 / 合集阅读与文章折叠保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-013 |

## BP-064 / DEF-064

frontend/src/pages/ContentPage.tsx: ContentPage / 相册卡片与分类；当前职责 相册卡片与分类

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 相册内负责相册卡片与分类；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=photo的/records、私有图片URL与上传 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=photo的/records、私有图片URL与上传；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=photo 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=photo的/records、私有图片URL与上传的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-066 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 相册卡片与分类; 归属接口：kind=photo的/records、私有图片URL与上传 | 相册 / 相册卡片与分类保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-014 |

## BP-065 / DEF-065

frontend/src/pages/ContentPage.tsx: ContentPage / 图片上传编辑弹窗；当前职责 图片上传编辑弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 相册内负责图片上传编辑弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=photo的/records、私有图片URL与上传 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=photo的/records、私有图片URL与上传；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=photo 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=photo的/records、私有图片URL与上传的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-067 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 图片上传编辑弹窗; 归属接口：kind=photo的/records、私有图片URL与上传 | 相册 / 图片上传编辑弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-014 |

## BP-066 / DEF-066

frontend/src/pages/ContentPage.tsx: ContentPage / 私有照片预览；当前职责 私有照片预览

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 相册内负责私有照片预览；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=photo的/records、私有图片URL与上传 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=photo的/records、私有图片URL与上传；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=photo 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=photo的/records、私有图片URL与上传的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-068 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 私有照片预览; 归属接口：kind=photo的/records、私有图片URL与上传 | 相册 / 私有照片预览保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-014 |

## BP-067 / DEF-067

frontend/src/pages/ContentPage.tsx: ContentPage / 诗词卡片及行操作；当前职责 诗词卡片及行操作

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 诗词内负责诗词卡片及行操作；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=poem的/records与文本预览 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=poem的/records与文本预览；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=poem 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=poem的/records与文本预览的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-070 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 诗词卡片及行操作; 归属接口：kind=poem的/records与文本预览 | 诗词 / 诗词卡片及行操作保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-015 |

## BP-068 / DEF-068

frontend/src/pages/ContentPage.tsx: ContentPage / 诗词编辑弹窗；当前职责 诗词编辑弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 诗词内负责诗词编辑弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=poem的/records与文本预览 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=poem的/records与文本预览；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=poem 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=poem的/records与文本预览的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-071 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 诗词编辑弹窗; 归属接口：kind=poem的/records与文本预览 | 诗词 / 诗词编辑弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-015 |

## BP-069 / DEF-069

frontend/src/pages/ContentPage.tsx: ContentPage / 诗词阅读弹窗；当前职责 诗词阅读弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 诗词内负责诗词阅读弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=poem的/records与文本预览 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=poem的/records与文本预览；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=poem 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=poem的/records与文本预览的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-072 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 诗词阅读弹窗; 归属接口：kind=poem的/records与文本预览 | 诗词 / 诗词阅读弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-015 |

## BP-070 / DEF-070

frontend/src/pages/ContentPage.tsx: ContentPage / 内容导航新建；当前职责 内容导航新建

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 简历内负责内容导航新建；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=resume的/records、履历数组与打印 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=resume的/records、履历数组与打印；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=resume 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=resume的/records、履历数组与打印的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-073 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 内容导航新建; 归属接口：kind=resume的/records、履历数组与打印 | 简历 / 内容导航新建保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-016 |

## BP-071 / DEF-071

frontend/src/pages/ContentPage.tsx: ContentPage / 简历文档与打印；当前职责 简历文档与打印

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 简历内负责简历文档与打印；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=resume的/records、履历数组与打印 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=resume的/records、履历数组与打印；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=resume 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=resume的/records、履历数组与打印的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-074 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 简历文档与打印; 归属接口：kind=resume的/records、履历数组与打印 | 简历 / 简历文档与打印保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-016 |

## BP-072 / DEF-072

frontend/src/pages/ContentPage.tsx: ContentPage / 履历教育技能编辑弹窗；当前职责 履历教育技能编辑弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 简历内负责履历教育技能编辑弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=resume的/records、履历数组与打印 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=resume的/records、履历数组与打印；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=resume 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=resume的/records、履历数组与打印的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-075 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 履历教育技能编辑弹窗; 归属接口：kind=resume的/records、履历数组与打印 | 简历 / 履历教育技能编辑弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-016 |

## BP-073 / DEF-073

frontend/src/pages/ContentPage.tsx: ContentPage / 删除与空态；当前职责 删除与空态

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 简历内负责删除与空态；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：kind=resume的/records、履历数组与打印 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：kind=resume的/records、履历数组与打印；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /content?kind=resume 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/ContentPage.tsx: ContentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；kind=resume的/records、履历数组与打印的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/ContentPage.tsx: ContentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-076 / configure | frontend/src/pages/ContentPage.tsx: ContentPage; 可观察区域 删除与空态; 归属接口：kind=resume的/records、履历数组与打印 | 简历 / 删除与空态保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-016 |

## BP-074 / DEF-074

frontend/src/pages/WorkspacePages.tsx: ToolsPage / 标题与双工具入口；当前职责 标题与双工具入口

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工具与图库内负责标题与双工具入口；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：/tools、CSV/图片资源上传与图库；请求期间受控字段组；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tools 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ToolsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/tools、CSV/图片资源上传与图库；请求期间受控字段组的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ToolsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-077 / configure | frontend/src/pages/WorkspacePages.tsx: ToolsPage; 可观察区域 标题与双工具入口; 归属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 | 工具与图库 / 标题与双工具入口保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-017 |

## BP-075 / DEF-075

frontend/src/pages/WorkspacePages.tsx: ToolsPage / CSV 绘图表单弹窗；当前职责 CSV 绘图表单弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工具与图库内负责CSV 绘图表单弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/tools、CSV/图片资源上传与图库；请求期间受控字段组；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tools 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ToolsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/tools、CSV/图片资源上传与图库；请求期间受控字段组的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ToolsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-078 / configure | frontend/src/pages/WorkspacePages.tsx: ToolsPage; 可观察区域 CSV 绘图表单弹窗; 归属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 | 工具与图库 / CSV 绘图表单弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-017 |

## BP-076 / DEF-076

frontend/src/pages/WorkspacePages.tsx: ToolsPage / 图片风格转换表单弹窗；当前职责 图片风格转换表单弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工具与图库内负责图片风格转换表单弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/tools、CSV/图片资源上传与图库；请求期间受控字段组；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tools 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ToolsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/tools、CSV/图片资源上传与图库；请求期间受控字段组的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ToolsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-079 / configure | frontend/src/pages/WorkspacePages.tsx: ToolsPage; 可观察区域 图片风格转换表单弹窗; 归属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 | 工具与图库 / 图片风格转换表单弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-017 |

## BP-077 / DEF-077

frontend/src/pages/WorkspacePages.tsx: ToolsPage / 上传及列选择状态；当前职责 上传及列选择状态

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工具与图库内负责上传及列选择状态；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/tools、CSV/图片资源上传与图库；请求期间受控字段组；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tools 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ToolsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/tools、CSV/图片资源上传与图库；请求期间受控字段组的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ToolsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-080 / configure | frontend/src/pages/WorkspacePages.tsx: ToolsPage; 可观察区域 上传及列选择状态; 归属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 | 工具与图库 / 上传及列选择状态保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-017 |

## BP-078 / DEF-078

frontend/src/pages/WorkspacePages.tsx: ToolsPage / 参考图库搜索筛选分页；当前职责 参考图库搜索筛选分页

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工具与图库内负责参考图库搜索筛选分页；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/tools、CSV/图片资源上传与图库；请求期间受控字段组；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tools 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ToolsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/tools、CSV/图片资源上传与图库；请求期间受控字段组的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ToolsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-081 / configure | frontend/src/pages/WorkspacePages.tsx: ToolsPage; 可观察区域 参考图库搜索筛选分页; 归属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 | 工具与图库 / 参考图库搜索筛选分页保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-017 |

## BP-079 / DEF-079

frontend/src/pages/WorkspacePages.tsx: ToolsPage / 图库详情代码复制下载；当前职责 图库详情代码复制下载

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 工具与图库内负责图库详情代码复制下载；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/tools、CSV/图片资源上传与图库；请求期间受控字段组；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /tools 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: ToolsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/tools、CSV/图片资源上传与图库；请求期间受控字段组的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: ToolsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-082 / configure | frontend/src/pages/WorkspacePages.tsx: ToolsPage; 可观察区域 图库详情代码复制下载; 归属接口：/tools、CSV/图片资源上传与图库；请求期间受控字段组 | 工具与图库 / 图库详情代码复制下载保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-017 |

## BP-080 / DEF-080

frontend/src/pages/MusicPage.tsx: MusicPage / 标题播放状态；当前职责 标题播放状态

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐搜索内负责标题播放状态；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：/music检索/取链/情绪、实际playing事件；Xinxin感受指数；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [search] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music检索/取链/情绪、实际playing事件；Xinxin感受指数的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-083 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 标题播放状态; 归属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 | 音乐搜索 / 标题播放状态保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-018 |

## BP-081 / DEF-081

frontend/src/pages/MusicPage.tsx: MusicPage / 搜索与音乐源；当前职责 搜索与音乐源

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐搜索内负责搜索与音乐源；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music检索/取链/情绪、实际playing事件；Xinxin感受指数；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [search] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music检索/取链/情绪、实际playing事件；Xinxin感受指数的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-084 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 搜索与音乐源; 归属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 | 音乐搜索 / 搜索与音乐源保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-018 |

## BP-082 / DEF-082

frontend/src/pages/MusicPage.tsx: MusicPage / 曲目列表与操作；当前职责 曲目列表与操作

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐搜索内负责曲目列表与操作；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music检索/取链/情绪、实际playing事件；Xinxin感受指数；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [search] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music检索/取链/情绪、实际playing事件；Xinxin感受指数的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-085 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 曲目列表与操作; 归属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 | 音乐搜索 / 曲目列表与操作保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-018 |

## BP-083 / DEF-083

frontend/src/pages/MusicPage.tsx: MusicPage / 唱片播放控制音量进度；当前职责 唱片播放控制音量进度

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐搜索内负责唱片播放控制音量进度；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music检索/取链/情绪、实际playing事件；Xinxin感受指数；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [search] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music检索/取链/情绪、实际playing事件；Xinxin感受指数的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-086 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 唱片播放控制音量进度; 归属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 | 音乐搜索 / 唱片播放控制音量进度保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-018 |

## BP-084 / DEF-084

frontend/src/pages/MusicPage.tsx: MusicPage / 氛围和 Xinxin 感受档位；当前职责 氛围和 Xinxin 感受档位

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐搜索内负责氛围和 Xinxin 感受档位；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music检索/取链/情绪、实际playing事件；Xinxin感受指数；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [search] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music检索/取链/情绪、实际playing事件；Xinxin感受指数的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-087 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 氛围和 Xinxin 感受档位; 归属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 | 音乐搜索 / 氛围和 Xinxin 感受档位保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-018 |

## BP-085 / DEF-085

frontend/src/pages/MusicPage.tsx: MusicPage / 历史与说明；当前职责 历史与说明

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐搜索内负责历史与说明；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：/music检索/取链/情绪、实际playing事件；Xinxin感受指数；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [search] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music检索/取链/情绪、实际playing事件；Xinxin感受指数的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-088 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 历史与说明; 归属接口：/music检索/取链/情绪、实际playing事件；Xinxin感受指数 | 音乐搜索 / 历史与说明保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-018 |

## BP-086 / DEF-086

frontend/src/pages/MusicPage.tsx: MusicPage / 收藏导航及空态；当前职责 收藏导航及空态

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐收藏内负责收藏导航及空态；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music/favorites及共享播放器；曲目键保持稳定 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music/favorites及共享播放器；曲目键保持稳定；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [favorites] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music/favorites及共享播放器；曲目键保持稳定的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-089 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 收藏导航及空态; 归属接口：/music/favorites及共享播放器；曲目键保持稳定 | 音乐收藏 / 收藏导航及空态保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-019 |

## BP-087 / DEF-087

frontend/src/pages/MusicPage.tsx: MusicPage / 收藏曲目播放和取消收藏；当前职责 收藏曲目播放和取消收藏

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐收藏内负责收藏曲目播放和取消收藏；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music/favorites及共享播放器；曲目键保持稳定 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music/favorites及共享播放器；曲目键保持稳定；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [favorites] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music/favorites及共享播放器；曲目键保持稳定的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-090 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 收藏曲目播放和取消收藏; 归属接口：/music/favorites及共享播放器；曲目键保持稳定 | 音乐收藏 / 收藏曲目播放和取消收藏保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-019 |

## BP-088 / DEF-088

frontend/src/pages/MusicPage.tsx: MusicPage / 播放与氛围共用区；当前职责 播放与氛围共用区

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐收藏内负责播放与氛围共用区；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music/favorites及共享播放器；曲目键保持稳定 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music/favorites及共享播放器；曲目键保持稳定；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [favorites] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music/favorites及共享播放器；曲目键保持稳定的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-091 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 播放与氛围共用区; 归属接口：/music/favorites及共享播放器；曲目键保持稳定 | 音乐收藏 / 播放与氛围共用区保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-019 |

## BP-089 / DEF-089

frontend/src/pages/MusicPage.tsx: MusicPage / 歌单新建编辑删除；当前职责 歌单新建编辑删除

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐歌单内负责歌单新建编辑删除；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music/playlists与曲目详情；独立刷新及AbortController |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music/playlists与曲目详情；独立刷新及AbortController；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [playlists] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music/playlists与曲目详情；独立刷新及AbortController的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-092 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 歌单新建编辑删除; 归属接口：/music/playlists与曲目详情；独立刷新及AbortController | 音乐歌单 / 歌单新建编辑删除保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-020 |

## BP-090 / DEF-090

frontend/src/pages/MusicPage.tsx: MusicPage / 歌单曲目详情与返回；当前职责 歌单曲目详情与返回

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐歌单内负责歌单曲目详情与返回；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music/playlists与曲目详情；独立刷新及AbortController |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music/playlists与曲目详情；独立刷新及AbortController；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [playlists] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music/playlists与曲目详情；独立刷新及AbortController的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-093 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 歌单曲目详情与返回; 归属接口：/music/playlists与曲目详情；独立刷新及AbortController | 音乐歌单 / 歌单曲目详情与返回保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-020 |

## BP-091 / DEF-091

frontend/src/pages/MusicPage.tsx: MusicPage / 添加到歌单弹窗；当前职责 添加到歌单弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 音乐歌单内负责添加到歌单弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/music/playlists与曲目详情；独立刷新及AbortController |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/music/playlists与曲目详情；独立刷新及AbortController；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /music [playlists] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/MusicPage.tsx: MusicPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/music/playlists与曲目详情；独立刷新及AbortController的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/MusicPage.tsx: MusicPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-094 / configure | frontend/src/pages/MusicPage.tsx: MusicPage; 可观察区域 添加到歌单弹窗; 归属接口：/music/playlists与曲目详情；独立刷新及AbortController | 音乐歌单 / 添加到歌单弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-020 |

## BP-092 / DEF-092

frontend/src/pages/WorkspacePages.tsx: MemoriesPage / 记忆卡片类别日期编辑删除；当前职责 记忆卡片类别日期编辑删除

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 长期记忆内负责记忆卡片类别日期编辑删除；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/memories CRUD；同步提交锁与失败保留 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/memories CRUD；同步提交锁与失败保留；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /memories 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: MemoriesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/memories CRUD；同步提交锁与失败保留的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: MemoriesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-096 / configure | frontend/src/pages/WorkspacePages.tsx: MemoriesPage; 可观察区域 记忆卡片类别日期编辑删除; 归属接口：/memories CRUD；同步提交锁与失败保留 | 长期记忆 / 记忆卡片类别日期编辑删除保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-021 |

## BP-093 / DEF-093

frontend/src/pages/WorkspacePages.tsx: MemoriesPage / 记忆保存弹窗；当前职责 记忆保存弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 长期记忆内负责记忆保存弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/memories CRUD；同步提交锁与失败保留 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/memories CRUD；同步提交锁与失败保留；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /memories 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: MemoriesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/memories CRUD；同步提交锁与失败保留的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: MemoriesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-097 / configure | frontend/src/pages/WorkspacePages.tsx: MemoriesPage; 可观察区域 记忆保存弹窗; 归属接口：/memories CRUD；同步提交锁与失败保留 | 长期记忆 / 记忆保存弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-021 |

## BP-094 / DEF-094

frontend/src/pages/WorkspacePages.tsx: SchedulesPage / 标题新增与权限说明；当前职责 标题新增与权限说明

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 自动化内负责标题新增与权限说明；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /schedules 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SchedulesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SchedulesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-098 / configure | frontend/src/pages/WorkspacePages.tsx: SchedulesPage; 可观察区域 标题新增与权限说明; 归属接口：/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束 | 自动化 / 标题新增与权限说明保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-022 |

## BP-095 / DEF-095

frontend/src/pages/WorkspacePages.tsx: SchedulesPage / 定期任务行启停编辑删除；当前职责 定期任务行启停编辑删除

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 自动化内负责定期任务行启停编辑删除；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /schedules 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SchedulesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SchedulesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-099 / configure | frontend/src/pages/WorkspacePages.tsx: SchedulesPage; 可观察区域 定期任务行启停编辑删除; 归属接口：/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束 | 自动化 / 定期任务行启停编辑删除保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-022 |

## BP-096 / DEF-096

frontend/src/pages/WorkspacePages.tsx: SchedulesPage / 自动化表单弹窗；当前职责 自动化表单弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 自动化内负责自动化表单弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /schedules 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SchedulesPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SchedulesPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-100 / configure | frontend/src/pages/WorkspacePages.tsx: SchedulesPage; 可观察区域 自动化表单弹窗; 归属接口：/schedules CRUD；interval/enabled/next_at，后台任务仍受权限约束 | 自动化 / 自动化表单弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-022 |

## BP-097 / DEF-097

frontend/src/pages/WorkspacePages.tsx: SettingsPage / 标题与分区导航；当前职责 标题与分区导航

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 设置内负责标题与分区导航；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /settings 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SettingsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SettingsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-101 / configure | frontend/src/pages/WorkspacePages.tsx: SettingsPage; 可观察区域 标题与分区导航; 归属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 | 设置 / 标题与分区导航保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-023 |

## BP-098 / DEF-098

frontend/src/pages/WorkspacePages.tsx: SettingsPage / 强调色与背景；当前职责 强调色与背景

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 设置内负责强调色与背景；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /settings 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SettingsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SettingsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-102 / configure | frontend/src/pages/WorkspacePages.tsx: SettingsPage; 可观察区域 强调色与背景; 归属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 | 设置 / 强调色与背景保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-023 |

## BP-099 / DEF-099

frontend/src/pages/WorkspacePages.tsx: SettingsPage / 自定义强调色；当前职责 自定义强调色

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 设置内负责自定义强调色；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /settings 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SettingsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SettingsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-103 / configure | frontend/src/pages/WorkspacePages.tsx: SettingsPage; 可观察区域 自定义强调色; 归属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 | 设置 / 自定义强调色保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-023 |

## BP-100 / DEF-100

frontend/src/pages/WorkspacePages.tsx: SettingsPage / 连接地址复制；当前职责 连接地址复制

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 设置内负责连接地址复制；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /settings 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SettingsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SettingsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-104 / configure | frontend/src/pages/WorkspacePages.tsx: SettingsPage; 可观察区域 连接地址复制; 归属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 | 设置 / 连接地址复制保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-023 |

## BP-101 / DEF-101

frontend/src/pages/WorkspacePages.tsx: SettingsPage / SMTP 或 Resend 邮箱表单；当前职责 SMTP 或 Resend 邮箱表单

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 设置内负责SMTP 或 Resend 邮箱表单；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /settings 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SettingsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SettingsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-105 / configure | frontend/src/pages/WorkspacePages.tsx: SettingsPage; 可观察区域 SMTP 或 Resend 邮箱表单; 归属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 | 设置 / SMTP 或 Resend 邮箱表单保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-023 |

## BP-102 / DEF-102

frontend/src/pages/WorkspacePages.tsx: SettingsPage / Resend 域名和 DNS；当前职责 Resend 域名和 DNS

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 设置内负责Resend 域名和 DNS；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /settings 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SettingsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SettingsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-106 / configure | frontend/src/pages/WorkspacePages.tsx: SettingsPage; 可观察区域 Resend 域名和 DNS; 归属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 | 设置 / Resend 域名和 DNS保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-023 |

## BP-103 / DEF-103

frontend/src/pages/WorkspacePages.tsx: SettingsPage / 对话及图像模型表单；当前职责 对话及图像模型表单

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 设置内负责对话及图像模型表单；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /settings 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SettingsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SettingsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-107 / configure | frontend/src/pages/WorkspacePages.tsx: SettingsPage; 可观察区域 对话及图像模型表单; 归属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 | 设置 / 对话及图像模型表单保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-023 |

## BP-104 / DEF-104

frontend/src/pages/WorkspacePages.tsx: SettingsPage / 主人密码表单；当前职责 主人密码表单

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 设置内负责主人密码表单；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /settings 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/WorkspacePages.tsx: SettingsPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/WorkspacePages.tsx: SettingsPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-108 / configure | frontend/src/pages/WorkspacePages.tsx: SettingsPage; 可观察区域 主人密码表单; 归属接口：/settings公开配置及只写密钥状态、邮件/连接/密码；客户端主题 | 设置 / 主人密码表单保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-023 |

## BP-105 / DEF-105

frontend/src/pages/LearningPage.tsx: LearningPage / 学习索引与导入；当前职责 学习索引与导入

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 学习工作室内负责学习索引与导入；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/LearningPage.tsx: LearningPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/LearningPage.tsx: LearningPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-109 / configure | frontend/src/pages/LearningPage.tsx: LearningPage; 可观察区域 学习索引与导入; 归属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 | 学习工作室 / 学习索引与导入保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-024 |

## BP-106 / DEF-106

frontend/src/pages/LearningPage.tsx: LearningPage / 书库搜索与学习统计；当前职责 书库搜索与学习统计

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 学习工作室内负责书库搜索与学习统计；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/LearningPage.tsx: LearningPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/LearningPage.tsx: LearningPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-110 / configure | frontend/src/pages/LearningPage.tsx: LearningPage; 可观察区域 书库搜索与学习统计; 归属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 | 学习工作室 / 书库搜索与学习统计保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-024 |

## BP-107 / DEF-107

frontend/src/pages/LearningPage.tsx: LearningPage / 错题复习入口；当前职责 错题复习入口

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 学习工作室内负责错题复习入口；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/LearningPage.tsx: LearningPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/LearningPage.tsx: LearningPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-111 / configure | frontend/src/pages/LearningPage.tsx: LearningPage; 可观察区域 错题复习入口; 归属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 | 学习工作室 / 错题复习入口保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-024 |

## BP-108 / DEF-108

frontend/src/pages/LearningPage.tsx: LearningPage / 导入讲义弹窗；当前职责 导入讲义弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 学习工作室内负责导入讲义弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/LearningPage.tsx: LearningPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/LearningPage.tsx: LearningPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-112 / configure | frontend/src/pages/LearningPage.tsx: LearningPage; 可观察区域 导入讲义弹窗; 归属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 | 学习工作室 / 导入讲义弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-024 |

## BP-109 / DEF-109

frontend/src/pages/BookPage.tsx: BookPage / 返回标题和教材状态；当前职责 返回标题和教材状态

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责返回标题和教材状态；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-113 / configure | frontend/src/pages/BookPage.tsx: BookPage; 可观察区域 返回标题和教材状态; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 教材与出题工作室 / 返回标题和教材状态保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-110 / DEF-110

frontend/src/pages/BookPage.tsx: BookPage / 来源章节筛选；当前职责 来源章节筛选

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责来源章节筛选；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-114 / configure | frontend/src/pages/BookPage.tsx: BookPage; 可观察区域 来源章节筛选; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 教材与出题工作室 / 来源章节筛选保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-111 / DEF-111

frontend/src/pages/BookPage.tsx: BookPage / 出题配置表单；当前职责 出题配置表单

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责出题配置表单；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-115 / configure | frontend/src/pages/BookPage.tsx: BookPage; 可观察区域 出题配置表单; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 教材与出题工作室 / 出题配置表单保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-112 / DEF-112

frontend/src/pages/BookPage.tsx: BookPage / 持久化任务进度恢复取消；当前职责 持久化任务进度恢复取消

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责持久化任务进度恢复取消；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-116 / configure | frontend/src/pages/BookPage.tsx: BookPage; 可观察区域 持久化任务进度恢复取消; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 教材与出题工作室 / 持久化任务进度恢复取消保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-113 / DEF-113

frontend/src/pages/BookPage.tsx: BookPage / 题目分页预览；当前职责 题目分页预览

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责题目分页预览；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-117 / configure | frontend/src/pages/BookPage.tsx: BookPage; 可观察区域 题目分页预览; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 教材与出题工作室 / 题目分页预览保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-114 / DEF-114

frontend/src/pages/BookPage.tsx: BookPage / 原文阅读模态；当前职责 原文阅读模态

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责原文阅读模态；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-118 / configure | frontend/src/pages/BookPage.tsx: BookPage; 可观察区域 原文阅读模态; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 教材与出题工作室 / 原文阅读模态保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-115 / DEF-115

frontend/src/pages/BookPage.tsx: BookPage / 练习与删除入口；当前职责 练习与删除入口

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责练习与删除入口；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-119 / configure | frontend/src/pages/BookPage.tsx: BookPage; 可观察区域 练习与删除入口; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 教材与出题工作室 / 练习与删除入口保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-116 / DEF-116

frontend/src/pages/QuizPage.tsx: QuizPage / 标题进度与返回；当前职责 标题进度与返回

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 练习与双辅导内负责标题进度与返回；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/quiz/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/QuizPage.tsx: QuizPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/QuizPage.tsx: QuizPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-120 / configure | frontend/src/pages/QuizPage.tsx: QuizPage; 可观察区域 标题进度与返回; 归属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 | 练习与双辅导 / 标题进度与返回保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-026 |

## BP-117 / DEF-117

frontend/src/pages/QuizPage.tsx: QuizPage / 题目选项及作答；当前职责 题目选项及作答

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 练习与双辅导内负责题目选项及作答；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/quiz/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/QuizPage.tsx: QuizPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/QuizPage.tsx: QuizPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-121 / configure | frontend/src/pages/QuizPage.tsx: QuizPage; 可观察区域 题目选项及作答; 归属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 | 练习与双辅导 / 题目选项及作答保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-026 |

## BP-118 / DEF-118

frontend/src/pages/QuizPage.tsx: QuizPage / 提交批改和下一题；当前职责 提交批改和下一题

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 练习与双辅导内负责提交批改和下一题；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/quiz/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/QuizPage.tsx: QuizPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/QuizPage.tsx: QuizPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-122 / configure | frontend/src/pages/QuizPage.tsx: QuizPage; 可观察区域 提交批改和下一题; 归属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 | 练习与双辅导 / 提交批改和下一题保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-026 |

## BP-119 / DEF-119

frontend/src/pages/QuizPage.tsx: QuizPage / 普通老师或 Xinxin 辅导；当前职责 普通老师或 Xinxin 辅导

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 练习与双辅导内负责普通老师或 Xinxin 辅导；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/quiz/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/QuizPage.tsx: QuizPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/QuizPage.tsx: QuizPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-123 / configure | frontend/src/pages/QuizPage.tsx: QuizPage; 可观察区域 普通老师或 Xinxin 辅导; 归属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 | 练习与双辅导 / 普通老师或 Xinxin 辅导保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-026 |

## BP-120 / DEF-120

frontend/src/pages/QuizPage.tsx: QuizPage / 双模式历史和图表；当前职责 双模式历史和图表

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 练习与双辅导内负责双模式历史和图表；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/quiz/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/QuizPage.tsx: QuizPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/QuizPage.tsx: QuizPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-124 / configure | frontend/src/pages/QuizPage.tsx: QuizPage; 可观察区域 双模式历史和图表; 归属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 | 练习与双辅导 / 双模式历史和图表保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-026 |

## BP-121 / DEF-121

frontend/src/pages/QuizPage.tsx: QuizPage / 原文提示与完成总结；当前职责 原文提示与完成总结

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 练习与双辅导内负责原文提示与完成总结；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/quiz/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/QuizPage.tsx: QuizPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/QuizPage.tsx: QuizPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-125 / configure | frontend/src/pages/QuizPage.tsx: QuizPage; 可观察区域 原文提示与完成总结; 归属接口：quiz/question_id、提交/判分、tutor_mode/history、受限函数画布；未答隐藏答案 | 练习与双辅导 / 原文提示与完成总结保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-026 |

## BP-122 / DEF-122

frontend/src/App.tsx: App / 错误标题与返回工作台；当前职责 错误标题与返回工作台

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 页面不存在内负责错误标题与返回工作台；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：未知URL与返回工作台；无业务请求 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：未知URL与返回工作台；无业务请求；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /* [unknown] 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/App.tsx: App 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；未知URL与返回工作台；无业务请求的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/App.tsx: App 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-126 / configure | frontend/src/App.tsx: App; 可观察区域 错误标题与返回工作台; 归属接口：未知URL与返回工作台；无业务请求 | 页面不存在 / 错误标题与返回工作台保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-027 |

## BP-123 / DEF-123

desktop/assets/starting.html: starting.html / 品牌和启动阶段；当前职责 品牌和启动阶段

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 桌面启动窗口内负责品牌和启动阶段；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：静态starting.html，桌面启动器持有服务阶段 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：静态starting.html，桌面启动器持有服务阶段；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 file:desktop/assets/starting.html 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 desktop/assets/starting.html: starting.html 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；静态starting.html，桌面启动器持有服务阶段的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 desktop/assets/starting.html: starting.html 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-127 / configure | desktop/assets/starting.html: starting.html; 可观察区域 品牌和启动阶段; 归属接口：静态starting.html，桌面启动器持有服务阶段 | 桌面启动窗口 / 品牌和启动阶段保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-028 |

## BP-124 / DEF-124

desktop/assets/starting.html: starting.html / 等待时间与关闭说明；当前职责 等待时间与关闭说明

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 桌面启动窗口内负责等待时间与关闭说明；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：静态starting.html，桌面启动器持有服务阶段 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：静态starting.html，桌面启动器持有服务阶段；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 file:desktop/assets/starting.html 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 desktop/assets/starting.html: starting.html 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；静态starting.html，桌面启动器持有服务阶段的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 desktop/assets/starting.html: starting.html 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-128 / configure | desktop/assets/starting.html: starting.html; 可观察区域 等待时间与关闭说明; 归属接口：静态starting.html，桌面启动器持有服务阶段 | 桌面启动窗口 / 等待时间与关闭说明保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-028 |

## BP-125 / DEF-125

desktop/assets/error-template.html: error-template.html / 失败标题和原因；当前职责 失败标题和原因

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 桌面错误窗口内负责失败标题和原因；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：静态error-template.html，脱敏日志与恢复说明 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：静态error-template.html，脱敏日志与恢复说明；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 file:desktop/assets/error-template.html 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 desktop/assets/error-template.html: error-template.html 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；静态error-template.html，脱敏日志与恢复说明的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 desktop/assets/error-template.html: error-template.html 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-129 / configure | desktop/assets/error-template.html: error-template.html; 可观察区域 失败标题和原因; 归属接口：静态error-template.html，脱敏日志与恢复说明 | 桌面错误窗口 / 失败标题和原因保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-029 |

## BP-126 / DEF-126

desktop/assets/error-template.html: error-template.html / 脱敏日志及路径；当前职责 脱敏日志及路径

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 桌面错误窗口内负责脱敏日志及路径；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：静态error-template.html，脱敏日志与恢复说明 |
| states | 由父级状态驱动文字/标记；此区域不自行提交请求。 |
| data_effects | 权威数据及关联：静态error-template.html，脱敏日志与恢复说明；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 file:desktop/assets/error-template.html 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 desktop/assets/error-template.html: error-template.html 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；静态error-template.html，脱敏日志与恢复说明的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 desktop/assets/error-template.html: error-template.html 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-130 / configure | desktop/assets/error-template.html: error-template.html; 可观察区域 脱敏日志及路径; 归属接口：静态error-template.html，脱敏日志与恢复说明 | 桌面错误窗口 / 脱敏日志及路径保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-029 |

## BP-127 / DEF-127

desktop/assets/error-template.html: error-template.html / 恢复操作指引；当前职责 恢复操作指引

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 桌面错误窗口内负责恢复操作指引；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：静态error-template.html，脱敏日志与恢复说明 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：静态error-template.html，脱敏日志与恢复说明；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 file:desktop/assets/error-template.html 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 desktop/assets/error-template.html: error-template.html 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；静态error-template.html，脱敏日志与恢复说明的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 desktop/assets/error-template.html: error-template.html 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-131 / configure | desktop/assets/error-template.html: error-template.html; 可观察区域 恢复操作指引; 归属接口：静态error-template.html，脱敏日志与恢复说明 | 桌面错误窗口 / 恢复操作指引保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-029 |

## BP-128 / DEF-128

frontend/src/pages/LearningPage.tsx: importJob；当前职责 资料识别进度与取消恢复

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 学习工作室内负责资料识别进度与取消恢复；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/LearningPage.tsx: LearningPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；/learning/books、持久化/learning/imports；上传/OCR/取消/恢复的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/LearningPage.tsx: LearningPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-132 / configure | frontend/src/pages/LearningPage.tsx: importJob; 归属接口：/learning/books、持久化/learning/imports；上传/OCR/取消/恢复 | 资料识别进度与取消恢复保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-024 |

## BP-129 / DEF-129

frontend/src/pages/BookPage.tsx: study-understanding；当前职责 理解覆盖与片段摘要索引

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责理解覆盖与片段摘要索引；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-133 / configure | frontend/src/pages/BookPage.tsx: study-understanding; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 理解覆盖与片段摘要索引保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-130 / DEF-130

frontend/src/pages/BookPage.tsx: preview.analysis；当前职责 知识证据与完整原题预览

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责知识证据与完整原题预览；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-134 / configure | frontend/src/pages/BookPage.tsx: preview.analysis; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 知识证据与完整原题预览保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-131 / DEF-131

frontend/src/pages/BookPage.tsx: correcting；当前职责 出题前原文校对弹窗

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | 教材与出题工作室内负责出题前原文校对弹窗；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /learning/books/:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/BookPage.tsx: BookPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/BookPage.tsx: BookPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-135 / configure | frontend/src/pages/BookPage.tsx: correcting; 归属接口：sources/analysis/correction/generations/questions；source_ids/count/mode/analyze_only，来源不可被已有题覆盖 | 出题前原文校对弹窗保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-025 |

## BP-132 / DEF-132

frontend/src/pages/SkillNetTrace.tsx; AgentPage.tsx: SkillNetTrace；当前职责 SkillNet 本轮路线与工具证据

| 合同维度 | 当前目标 |
| --- | --- |
| responsibility | Agent 对话内负责SkillNet 本轮路线与工具证据；不替代后端授权或外部质量验收。 |
| interface | 保留该区域既有宿主页受控状态与原生事件；所属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 |
| states | 沿用宿主页的空/加载/正常/失败状态；输入、选择或弹窗在本区域状态所有者内变更；已执行的忙碌/关闭/迟到请求见专项。 |
| data_effects | 权威数据及关联：conversation/run、watchRun有序事件、附件、permission及SkillNet证据；纯标题/提示不另设数据写入口。 |
| semantics_accessibility | 本区域字段沿用原生label/输入/按钮，模态沿用Dialog；真实键盘路径按专项，未运行的完整交互保持blocked。 |
| styling_layout | 在 /agent?conversation=:id 复用polish.css暖白/深灰/单强调色；功能布局由宿主页样式持有，320px与长内容不强撑固定最小宽度。 |
| performance_lifecycle | 沿用 frontend/src/pages/AgentPage.tsx: AgentPage 的状态生命周期；静态内容无定时器；异步分支不得用卸载后的结果覆盖新选择。性能测量范围仅生产专项。 |
| security_privacy | 输入、资料与模型输出视为数据；conversation/run、watchRun有序事件、附件、permission及SkillNet证据的授权由后端完成；此区域不保存宿主凭据或开放执行权限。 |
| observability | 保留区域现有空/忙碌/错误提示；模型与网络失败不计作真实完成；不输出凭据/私密原文到审计产物。 |
| integration | 在 frontend/src/pages/AgentPage.tsx: AgentPage 内保持既有路由和其他区域调用；共享Dialog/PageHeader/Loading/ErrorState及主题不复制不同版本。 |

| 实例 / 处置 | 位置及变化 | 验收与场景 |
| --- | --- | --- |
| CMP-136 / configure | frontend/src/pages/SkillNetTrace.tsx; AgentPage.tsx: SkillNetTrace; 归属接口：conversation/run、watchRun有序事件、附件、permission及SkillNet证据 | SkillNet 本轮路线与工具证据保留现有入口/语义并采用全站主题; 源码核对与实际交互证据分开；缺少运行证据的分支不计通过；SCN-005 |
