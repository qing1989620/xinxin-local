# 感受指数、桌面更新与 SkillNet 对话验证

需求与固定比较基线见 [需求](specs/2026-10-21-sensitivity-desktop-skillnet.md)，基线为 `243524ec15b9455a066d4b599f5f01377147f482`。

## 当前问题与修复

四档点击报「当前后端不支持该字段」的原因是本机旧后端仍健康，桌面启动器直接复用了它。现按启动时的后端源码指纹与前端构建指纹更新受管理服务；旧版接口缺少感受契约时，界面禁用设置并提示用桌面图标更新。旧 `influence_level` 接口与设置保持兼容。

四档改为 Xinxin 自己的感受指数：克制 ×0.4、自然 ×1.0、敏感 ×1.5、共鸣 ×2.2。单曲情绪强度由歌曲评分决定；近期音乐氛围、90 分钟半衰期及感受指数决定 Xinxin 实际感受，界面分别显示。重复播放不会通过堆积次数无限放大；歌曲本身的评分不随感受指数变化。提示按实际感受调语气，关闭后不注入音乐情绪。

先完成以上修复与隔离测试，并实际通过 `C:\Users\qing\Desktop\Xinxin.lnk` 打开桌面窗口、检查新版服务与缓存指纹，再进入 SkillNet 阶段。没有改写有效快捷方式，也没有清除主人数据库或凭据。

SkillNet 能力路线进入每轮 Agent 对话：目标匹配、选择理由、方法正文入口、参考读取次数、关联工具成功或失败返回，以及本轮结果与交付入口。复杂任务提示按实际需要解释方法用途，简单问答允许不选技能。理由标为模型建议；匹配本身不算执行，关联工具成功也不算整项方法或最终成果验收。

历史路线批量从 `skills` 和 `tool.completed.skill_evidence` 原始事件派生，没有新增平行结果表；SSE 与历史恢复按事件序号合并，避免重复计数。仅传递简短技能卡与证据元数据，不把工具参数、输出或令牌流放入历史摘要。旧记录缺少证据时不反推执行成功。

## 验证方式

```powershell
cd backend
.venv/Scripts/python.exe -m pytest -q --basetemp=.qa-data/full-sensitivity-skillnet-20261021-final --junitxml=.qa-data/sensitivity-skillnet-full-20261021.xml
cd ../frontend
npm test
npm run build
npm run test:e2e
```

测试服务使用独立合成数据库，不访问主人正在运行的数据库。浏览器使用真实 React、FastAPI、HTTP、SQLite 与执行器；音乐数据、音频和模型响应为合成或模拟。SkillNet 演示使用真实检索与重排函数，必要性选择与模型调用由确定性脚本驱动，不能据此判断真实模型选择质量。

桌面集成使用随机回环端口、隔离数据与进程清单，验证重复启动复用、旧版本更新、执行中任务阻止重启，以及前端更新。清理仅处理隔离测试清单中 PID 和启动时间一致的进程。

执行结果：后端全量 **256 passed**（349.91 秒），前端单元 **62 passed**，Playwright 桌面与手机 **56 passed**（2.8 分钟）；TypeScript / Vite / PWA 生产构建通过。构建保留既有单块大于 500 KB 的提示，没有构建错误。

桌面审查修复后另跑 `tests/test_desktop_updates.py tests/test_script_encoding.py`：保护同清单当前/旧版本的不同数据目录请求、未知数据目录保留进程、崩溃任务恢复，以及 PowerShell 5.1 的 BOM 编码。全量其他模块通过后没有再修改业务代码。

## 审查与边界

前端按 [BadGoods quick review](https://github.com/BadbotAI/BadGoods/blob/76d20b19c8b2a6513d1516d42fdcc42a2b8c394f/skills/review-frontend-production/SKILL.md) 检查新路线的折叠、原生键盘语义、方法对话框关闭、历史恢复、错误展示与手机布局。真实浏览器验证两个视口的实时路线、方法读取、工作区写入与交付、只读失败和历史恢复；相关流程没有未捕获页面异常，未出现横向溢出。截图为隔离合成数据，不代表真实模型效果。

后端按 [mattpocock code-review](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/code-review/SKILL.md) 进行 Standards / Spec 独立审查，固定比较 `243524e..caf58e6`。

- Standards 发现 P1：受管理服务清单未绑定真实数据目录，切换参数可能检查错误数据库后停止旧进程。修复为保存目录与端口，复用/更新前核对；未知配置保留进程，发布过的无指纹旧启动器仅按其固定默认目录契约迁移。
- Spec 发现 P2：读取清单后服务崩溃时，先查活动任务会误阻止当次恢复。修复为健康探测后重新验证进程身份，再检查活着的旧服务任务；补充崩溃残留任务恢复为 interrupted 的回归。
- SkillNet、四档独立性、旧接口兼容、权限与隐私边界未发现其他明确可行动缺陷。两项桌面修复的独立复核结果在最终合并前记录。

真实模型主观表现、全部外部音乐源实时可用性、实体手机软键盘和新打包 Android APK 没有纳入本次验收。所有测试通过表示已执行的回归通过，不表示任意输入与外部服务均无缺陷。
