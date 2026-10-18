---
name: "doc-coauthoring"
description: "文档协同创作：Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documen。"
---

# doc-coauthoring

> 领域：文档工程　|　来源：member-import（Nexus skills/doc-coauthoring）　|　代际：G0

## 能力契约 / Capability

Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content.

**输入**：文档目标与读者；已有素材与上下文

**输出**：分阶段打磨后的文档；结构与措辞修订记录

**适用时机**：
- 用户需要撰写文档、提案、技术规格或决策文档等结构化内容并希望协同打磨时触发

## 执行步骤

1. User mentions writing documentation: "write a doc", "draft a proposal", "create a spec", "write up"
2. User mentions specific doc types: "PRD", "design doc", "decision doc", "RFC"
3. User seems to be starting a substantial writing task
4. Context Gathering: User provides all relevant context while Claude asks clarifying questions
5. Refinement & Structure: Iteratively build each section through brainstorming and editing
6. Reader Testing: Test the doc with a fresh Claude (no context) to catch blind spots before others read it

## 常见陷阱

- 导入时未从原文提取到显式陷阱条目，执行前请复核原文正文

## 验证清单

- [ ] Open a fresh Claude conversation: https://claude.ai
- [ ] Paste or share the document content (if using a shared doc platform with connectors enabled, provide the link)
- [ ] Ask Reader Claude the generated questions
- [ ] The answer
- [ ] Whether anything was ambiguous or unclear

## 标签

`协同写作` `工作流` `审阅` `修订`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Good |
| maintainability | Good |
| cost_awareness | Average |

## 关联技能

- `compose_with` → `docx`
- `compose_with` → `scientific-writing`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
