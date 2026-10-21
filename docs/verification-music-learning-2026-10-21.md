# 音乐与学习优化验证（2026-10-21）

实施基线：`0ad684cb8795b3d9f821ef9e5eeecdeeb4f8084f`。需求见 [本次需求](specs/2026-10-21-music-learning.md)。

## 改动与复验范围

- 歌曲列表移出父组件，播放器进度更新不再重建列表；使用固定命中区域和内容位移，减少动态效果时不位移。
- 轻微、自然、明显、沉浸四档保存到后端，默认自然。情绪词按播放半衰期计算，并参与 Agent / Xinxin 辅导的表达指引。
- 普通老师与 Xinxin 辅导分别保存每题历史，旧数据库历史迁移为普通老师；讲题使用完整选项、参考答案和实际作答，未作答时不直接返回参考答案字段。
- 修复换题、切辅导、清空搜索的迟到响应；保存失败回退、讲解失败保留草稿且不留下半轮消息；练完可以继续讲错题，再练保留书本与章节。
- 播放地址预取合并与短期缓存；快速换歌和停止使旧取链失效，旧封面不能覆盖新歌曲；实际开始播放才记氛围，暂停恢复不重复记账。
- 浏览器实测发现并修复手机导航遮挡讲题输入、浮动播放器遮挡手机导航。
- 将公式库升级到 KaTeX 0.18.10（[上游修复说明](https://github.com/KaTeX/KaTeX/security/advisories/GHSA-238p-pmpm-9mq7)），保留不信任 HTML 的渲染配置。

## 验证记录

| 检查 | 结果 |
| --- | --- |
| 后端全套 pytest | 233 项通过，362.60 秒；独立合成数据库 |
| 新增音乐/辅导回归 | 16 项通过，包括档位、历史迁移、模式隔离、空回复和模型失败 |
| 前端原有 Vitest | 51 项通过；补充公式库回归后待最终复验 |
| 首轮浏览器交互 | 修复首轮发现后 30/30 通过 |
| 扩展浏览器与前后端联调 | 首轮 39/40，通过两视口全部一级页面与持久化联调；发现手机小播放器遮挡导航，修复后待最终复验 |
| 类型检查与生产构建 | 通过；公式库升级后待最终复验 |
| npm 依赖审计 | 公式库升级后 0 vulnerabilities |

浏览器回归使用 Edge 无头模式、1440×1000 桌面和 iPhone 13 视口。交互用例使用合成曲库、模拟音频与模型；联调用例运行真实 FastAPI HTTP 和 SQLite，只有模型为模拟响应。测试服务只监听回环 `8017` / `5187`，在 `backend/.qa-data/` 为每轮新建数据库，不使用主人运行中的 `data/`。

## 命令与证据

```powershell
cd backend
.venv/Scripts/python.exe -m pytest -q --basetemp=.qa-data/full-music-learning-20261021-1 --junitxml=.qa-data/music-learning-full-20261021.xml
cd ../frontend
npm test
npm run build
npm run test:e2e
npm audit
```

Playwright 会启动并关闭专用测试服务。Windows 默认使用已安装的 Edge；其他 Chromium 可设 `PLAYWRIGHT_CHANNEL`。后端依赖须先安装到 `.venv`。报告与截图在 `frontend/.qa-data/playwright/`，均不进入 Git；后端全套 JUnit 位于命令指定路径。

## 审查与未验证范围

前端按 [BadGoods review-frontend-production](https://github.com/BadbotAI/BadGoods/blob/76d20b19c8b2a6513d1516d42fdcc42a2b8c394f/skills/review-frontend-production/SKILL.md) 的 quick 实施流程，深查音乐、练习、辅导及手机交互；一级页面执行冒烟，不等于所有页面状态与组件的完整审查。

后端按 [mattpocock code-review](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/code-review/SKILL.md) 对固定基线执行 Standards / Spec 两轴独立审查；最终结果将在复验后补充。

未验证：真实模型主观表达质量、所有外部音乐源/CDN 的实时可用性、实体手机软键盘、重新打包的 Android APK。自动化测试不代表这些外部链路或全部输入没有缺陷。
