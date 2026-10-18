---
name: "skill-creator"
description: "技能创作工坊：Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to c。"
---

# skill-creator

> 领域：技能工程　|　来源：member-import（Nexus skills/skill-creator）　|　代际：G0

## 能力契约 / Capability

Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better t

**输入**：待沉淀的能力描述与使用场景；可选参考材料

**输出**：符合规范的 SKILL.md 技能定义；技能评估与改进建议

**适用时机**：
- 用户想从零创建技能、改进现有技能或运行评测检验技能效果时触发

## 执行步骤

1. Decide what you want the skill to do and roughly how it should do it
2. Write a draft of the skill
3. Create a few test prompts and run claude-with-access-to-the-skill on them
4. Help the user evaluate the results both qualitatively and quantitatively
5. While the runs happen in the background, draft some quantitative evals if there aren't any (if there are some, you can either use as is or modify if you feel something needs to change about them). Then explain them to the user (or if they already existed, explain the ones that already exist)

## 常见陷阱

- 导入时未从原文提取到显式陷阱条目，执行前请复核原文正文

## 验证清单

- [ ] Skill path: <path-to-skill>
- [ ] Task: <eval prompt>
- [ ] Input files: <eval files if any, or "none">
- [ ] Save outputs to: <workspace>/iteration-<N>/eval-<ID>/withskill/outputs/
- [ ] Outputs to save: <what the user cares about — e.g., "the .docx file", "the final CSV">

## 标签

`技能创作` `SKILL.md` `规范` `元技能`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Good |
| maintainability | Good |
| cost_awareness | Average |

## 关联技能

- `compose_with` → `mcp-builder`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
