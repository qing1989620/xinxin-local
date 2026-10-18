# 后端专属约定

本仓库对应 `qing1989620/xinxin-backend`。只在此仓库写后端、数据模型、任务 Worker、技能适配和后端测试。

- 不修改兄弟 `frontend/` 仓库，不混入 React/页面样式，不在运行时依赖其源码目录。
- 通过 HTTP/事件契约服务前端；模型和服务器凭据只在后端配置，禁止写入仓库或日志。
- 首版为单主人、关闭公开注册；DeepSeek Flash 为默认模型，需求见 docs/product-spec.md。
- myself 的文章、合集、相册等业务模型按最终选择迁移；保留它独有的能力，不能用 lankhub 覆盖。
- SkillNet 路由负责选技能，执行授权和预算由平台独立判断。未验证技能包视为数据，不能自动当作可信可执行代码。
- Tina 固定提交适配，显式给每个会话创建 ToolsExecutor。线程超时不是安全终止，副作用工具交给受控进程或 Worker。
- 私人数据、数据库、上传目录和原仓库 `.env` 不进入 Git。
- 审查使用 mattpocock `code-review`，分别检查编码标准与需求；实施前后保存固定比较基线。

审查说明见 `docs/audit-plan.md`。
