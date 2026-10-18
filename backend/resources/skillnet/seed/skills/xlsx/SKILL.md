---
name: "xlsx"
description: "Excel 表格处理：a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, ed。"
---

# xlsx

> 领域：文档工程　|　来源：member-import（Nexus skills/xlsx）　|　代际：G0

## 能力契约 / Capability

a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .xltx, .csv, or .tsv file (e.g., adding columns, computing formulas, formatting, charting, cleaning messy data); create a new spreadsheet from scratch or

**输入**：表格数据或 .xlsx 文件；公式/图表/格式要求

**输出**：生成的表格文件；公式重算校验结果

**适用时机**：
- 以电子表格为主要输入或输出的任务——打开/读取/编辑 .xlsx/.csv、写公式、格式化、图表分析等触发

## 执行步骤

1. Professional font (Arial, Times New Roman) throughout, unless the user says otherwise
2. Zero formula errors. Never ship while recalc.py reports errorsfound. If you think an error predates you, prove it: load the original with dataonly=True and look at that cell. An error you introduced looks exactly like one you inherited
3. Use formulas, never hardcoded results. Write sheet['B10'] = '=SUM(B2:B9)', not the Python-computed total. The sheet must recalculate when its inputs change
4. Follow the user's spec literally. Exact tab names, exact column headers, and the formula they spelled out. A redesign that computes something else fails, however elegant
5. Document every assumption and hardcoded number where the reader will see it — a cell comment, or an adjacent cell at a table's end. Cite a real source when one exists (Source: Company 10-K, FY2024, Page 45, Revenue Note, [SEC EDGAR URL]); when the number came from the user, say so plainly

## 常见陷阱

- openpyxl writes formulas as strings with no cached values. Until you recalculate, every
- formula cell reads back as None to anything reading cached values — pandas,
- loadworkbook(dataonly=True), and most previewers
- python scripts/recalc.py output.xlsx [timeoutseconds] # default 30
- LibreOffice computes every formula, the file is rewritten in place, and you get JSON:
- status (success | errorsfound), totalformulas, totalerrors, and an

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`Excel` `xlsx` `公式` `数据表`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Average |
| executability | Good |
| maintainability | Good |
| cost_awareness | Average |

## 关联技能

- `compose_with` → `eda-profiling`
- `similar_to` → `docx`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
