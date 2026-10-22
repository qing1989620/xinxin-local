# 学习工作室的实现与接口

这轮实现以 `bc170cd` 为基线，需求见 [学习工作室合同](specs/2026-10-22-learning-studio.md)。设计参考公开的 zhixu-backend issues [#16](https://github.com/pfx43/zhixu-backend/issues/16)、[#17](https://github.com/pfx43/zhixu-backend/issues/17)、[#19](https://github.com/pfx43/zhixu-backend/issues/19)、[#20](https://github.com/pfx43/zhixu-backend/issues/20)，借鉴范围与来源、真实进度、真实学习行为的原则，不复制实现或人员分工。本轮没有引入每日任务、目标管理、多用户或聊天出题工具。

## 一条出题链

```mermaid
flowchart LR
  A[本地原资料] --> B[按标题切章 / 完整分段]
  B --> C[选择最多 10 个来源片段]
  C --> D[持久化 generation 与 items]
  D --> E[既有 TaskManager / runs]
  E --> F[逐片段模型调用 / 最多两次]
  F --> G[结构与原文摘录核验 / 去重]
  G --> H[题目和片段进度同事务提交]
  H --> I[有序事件 / SSE / 快照恢复]
  I --> J[练习 / 双辅导 / 回看原文 / 错题复习]
```

`backend/app/learning_studio.py` 管来源索引、质量门槛、出题调度与快照。`learning.py` 保留书架、题库、判分与辅导。前端通过 HTTP / SSE 工作，不读取后端文件或 SQLite。`learning.css` 限定学习页样式，避免污染音乐和 Agent。

`learning_sources` 保存每章至多 4000 字的非重叠片段，优先在段落或句子边界切开，所有字符保留。新资料单章超过 24000 字时继续分段；超出 60 章明确拒绝，不再静默截断。旧书的来源按已有章节懒加载，不改动题目和辅导历史。旧版本已经丢失的正文需要重新加入原文件。

PDF 源文件仍通过 FileLibrary 的库内路径校验读取。逐页文本与片段正文在去除空白后精确匹配，匹配成功才记录 `page_from/page_to`（从 1 开始的物理页序，可能跨页）；未匹配、原件缺失、Word 与文本全部显示片段，无推测页码。已有来源索引不随每次 GET 重建。扫描 PDF 不提供 OCR。

## 请求合同

全部接口位于 `/api/v1`，要求主人认证。

| 接口 | 用途 |
| --- | --- |
| GET `/learning/books/{id}/sources` | 来源目录：稳定 ID、所属章、片段序号、字数、可靠页序、已有题数、`max_sources=10` |
| GET `/learning/sources/{id}?offset=0` | 已选来源正文；offset 仅允许 -1 / 0 / 1，严格限制在同章相邻片段 |
| POST `/learning/books/{id}/generations` | 持久化异步出题任务，立即返回 job 快照；HTTP 成功不等于题目已生成 |
| GET `/learning/books/{id}/generation` | 该书最新任务，便于离页返回 |
| GET `/learning/generations/{id}` | 任务快照：运行状态、各片段目标与实际入库数、过滤与失败原因 |
| GET `/runs/{id}/events?after={seq}` | 复用有序持久化事件，支持重连回放；新增 `learning.source.started/finished` |
| POST `/runs/{id}/cancel` | 复用取消语义，停止后续调用 / 入库；已经入库的题保留 |
| POST `/learning/quiz` | 全书 / 单章练习，支持 `mode=all/mistakes`，同书同章校验 |

出题请求示例（来源 ID 必须来自目录）：

```json
{
  "source_ids": ["source-id-from-directory"],
  "count": 3,
  "kinds": ["single", "fill"],
  "difficulty": 2,
  "focus": "比较易混概念，给出合理干扰项",
  "request_key": "a-unique-stable-request-key",
  "resume_job_id": ""
}
```

每片段 1–6 题，题型至少一个，difficulty 为 0（混合）/ 1 / 2 / 3，重点不超过 240 字。幂等键相同且请求相同返回已有 job，不再次调用模型；同键异参拒绝。同书同时最多一个活跃任务。创建 / 删除在应用内串行调度，书本删除与题目入库各自使用 SQLite 写事务。服务按项目默认运行单个后端进程。

补出时提供新 `request_key` 与本书最新已结束的 `resume_job_id`，服务端复用原设置，只为未达标的片段分配剩余数量，忽略客户端的替换范围。不自动重试已完成片段，不自动续跑服务中断任务。

## 为什么进度可信

题目及对应进度在一次 SQLite 写事务中提交，不能先显示成功再写库。模型返回的数量不直接当进度，只有通过校验且实际插入的题计入 `created_count`。部分入库显示 partial，零入库显示 failed。cancelled / interrupted / failed 都有独立状态。通用 run 可以执行成功而 job 仅部分完成：前者说明工作器执行结束，后者说明实际出题目标达成情况。

每段最多两次模型请求，总调用预算为片段数 × 2，累计令牌预算为片段数 × 12000，总时限 900 秒。调用走现有 ModelGateway，使用量写回 runs。单次已发出的外部请求不能撤回，取消后本地不再提交迟到的响应。每个片段的主内容最多 4000 字，相邻上下文各最多 600 字；相邻上下文不能用作本段题目的引用依据。

客户端先恢复快照，再通过 watchRun 接续有序事件；定期读取快照作为事件与终态竞态的恢复手段。断开页面不取消后台任务。停止按钮明确触发后端取消，不只是中断浏览器连接。

## 质量与练习边界

单选检查 A/B/C/D、四个非空不同选项和单一有效答案；填空检查 `___` 数量与答案数组一致；简答检查参考要点；所有题检查难度、知识点、解释与 12–280 字的原文摘录。摘录必须能在所选正文中核对；模型不能自造来源 ID 或页码。题干 hash 去重。一次修复仍不足目标就停止并显示缺额，不无限调用模型。

这些门槛验证结构与来源，不能证明语义、推理和唯一正确性完全可靠。普通老师 / Xinxin 辅导均保留，风格不改变标准答案和判分规则。未作答的练习响应隐藏答案、解析与摘录；用户可以主动打开原文寻找线索。

错题采用每道题最新一次实际作答的状态，wrong / partial / unknown 进入复习。`attempt_seq` 在判分事务内递增，避免同一秒内重答旧记录被误认为更早；旧数据默认 0，再用既有时间 / rowid 排序。主观判分返回后重新核对会话和题目仍存在、会话仍可提交，避免删题或结束后的迟到写入。进度按不同题数计算，正确率明确按作答记录计算。

兼容接口 POST `/learning/books/{id}/questions` 保留旧版同步按章出题，供旧客户端使用；新工作室不调用该接口，它不具备本轮的来源与异步进度合同。
