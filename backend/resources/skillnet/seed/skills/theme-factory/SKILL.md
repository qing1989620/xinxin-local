---
name: "theme-factory"
description: "主题样式工厂：Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing page。"
---

# theme-factory

> 领域：设计与创意　|　来源：member-import（Nexus skills/theme-factory）　|　代际：G0

## 能力契约 / Capability

Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc.

**输入**：待套用主题的产物（幻灯片/网页/文档）；主题偏好

**输出**：应用主题后的产物；主题定义文件

**适用时机**：
- 需要给幻灯片/文档/报告/网页等制品套用预设主题（10 套配色与字体）时触发

## 执行步骤

1. Ask for their choice: Ask which theme to apply to the deck
2. Wait for selection: Get explicit confirmation about the chosen theme
3. Apply the theme: Once a theme has been chosen, apply the selected theme's colors and fonts to the deck/artifact
4. Read the corresponding theme file from the themes/ directory
5. Apply the specified colors and fonts consistently throughout the deck
6. Ensure proper contrast and readability

## 常见陷阱

- 导入时未从原文提取到显式陷阱条目，执行前请复核原文正文

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`主题` `样式系统` `一致性`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Average |
| executability | Good |
| maintainability | Basic |
| cost_awareness | Average |

## 关联技能

- `compose_with` → `pptx`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
