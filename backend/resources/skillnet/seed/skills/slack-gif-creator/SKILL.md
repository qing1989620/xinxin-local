---
name: "slack-gif-creator"
description: "Slack 动图制作：Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools。"
---

# slack-gif-creator

> 领域：设计与创意　|　来源：member-import（Nexus skills/slack-gif-creator）　|　代际：G0

## 能力契约 / Capability

Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts.

**输入**：动图创意与尺寸要求

**输出**：符合规格的 GIF 动图

**适用时机**：
- 用户要求制作适配 Slack 的动画 GIF（如 make me a GIF for Slack 类需求）时触发

## 执行步骤

1. Emoji GIFs: 128x128 (recommended)
2. Message GIFs: 480x480
3. FPS: 10-30 (lower is smaller file size)
4. Colors: 48-128 (fewer = smaller file size)
5. Duration: Keep under 3 seconds for emoji GIFs

## 常见陷阱

- 导入时未从原文提取到显式陷阱条目，执行前请复核原文正文

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`GIF` `动效` `消息表情`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Good |
| maintainability | Basic |
| cost_awareness | Average |

## 关联技能

- `similar_to` → `algorithmic-art`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
