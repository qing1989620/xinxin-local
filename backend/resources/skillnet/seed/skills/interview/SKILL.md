---
name: "interview"
description: "SDE 面试备考教练：SDE interview preparation daily workflow and weekly mock interviews. Triggers on /interview or natural phrases。"
---

# interview

> 领域：职业与学习　|　来源：member-import（Nexus skills/interview）　|　代际：G0

## 能力契约 / Capability

SDE interview preparation daily workflow and weekly mock interviews. Triggers on /interview or natural phrases like "daily problem", "practice today", "interview drill", "mock interview", "interview session", "show me today's problem", "interview practice", "start interview prep".

**输入**：面试目标岗位与时间线；当前准备状态

**输出**：分阶段备考计划；模拟面试与反馈

**适用时机**：
- 用户触发 /interview 或提到每日一题、练习、面试演练、模拟面试等备考场景时触发

## 执行步骤

1. Type /interview in any Claude Code session
2. The skill detects today's mode (daily or mock) and begins
3. Follow the interactive prompts to solve problems or complete the mock
4. Your progress is logged automatically

## 常见陷阱

- Keep EVERY response within ~2000 tokens (the system enforces maxtokens=2000). Prefer lean over long
- Get straight to the point: no preamble, no restating the user's question, no filler or boilerplate summaries
- Code output: clean core code with essential comments only — no duplicate equivalent implementations, no line-by-line essay
- When the user explicitly asks for a fuller trace, more rounds, or complete detail, the user's request overrides these defaults — then be as complete as needed
- This skill runs your daily SDE interview prep workflow. It has two modes:
- Daily Mode (Mon–Fri, Sun): ~30–45 min interactive practice session on a single DSA problem

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`面试` `职业发展` `模拟问答`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Average |

## 关联技能

- `similar_to` → `leetcode-hot100-coach`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
