---
name: "internal-comms"
description: "内部沟通文案：A set of resources to help me write all kinds of internal communications, using the formats that my company li。"
---

# internal-comms

> 领域：文档工程　|　来源：member-import（Nexus skills/internal-comms）　|　代际：G0

## 能力契约 / Capability

A set of resources to help me write all kinds of internal communications, using the formats that my company likes to use. Claude should use this skill whenever asked to write some sort of internal communications (status reports, leadership updates, 3P updates, company newsletters, FAQs, incident rep

**输入**：沟通场景与受众；要传达的事实要点

**输出**：内部通告/邮件/简报等文案

**适用时机**：
- 用户要求撰写企业内部沟通文案（公告、通知、周报等）时触发

## 执行步骤

1. Identify the communication type from the request
2. Load the appropriate guideline file from the examples/ directory:
3. examples/3p-updates.md - For Progress/Plans/Problems team updates
4. examples/company-newsletter.md - For company-wide newsletters
5. examples/faq-answers.md - For answering frequently asked questions
6. examples/general-comms.md - For anything else that doesn't explicitly match one of the above

## 常见陷阱

- 导入时未从原文提取到显式陷阱条目，执行前请复核原文正文

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`内部沟通` `文案` `通告`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Basic |
| executability | Good |
| maintainability | Basic |
| cost_awareness | Average |

## 关联技能

- `similar_to` → `doc-coauthoring`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
