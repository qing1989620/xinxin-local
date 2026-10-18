---
name: "docx"
description: "Word 文档处理：create, read, edit, or manipulate Word documents (.docx files) or Word templates (.dotx files). Triggers inclu。"
---

# docx

> 领域：文档工程　|　来源：member-import（Nexus skills/docx）　|　代际：G0

## 能力契约 / Capability

create, read, edit, or manipulate Word documents (.docx files) or Word templates (.dotx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', '.dotx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterhead

**输入**：待处理的 .docx/.dotx 文件或文档需求说明；正文内容与格式要求

**输出**：处理完成的 Word 文档；渲染校验截图

**适用时机**：
- 用户需要创建、读取、编辑 Word 文档（.docx/.dotx），或提到 Word 文档/模板相关任务时触发
- 用户提到 any mention of 'Word doc 时
- 用户提到 word document 时
- 用户提到 .docx 时

## 执行步骤

1. Page size defaults to A4. For US Letter set page: { size: { width: 12240, height: 15840 } } (DXA; 1440 = 1″)
2. Landscape: pass portrait dimensions and orientation: PageOrientation.LANDSCAPE — docx-js swaps width/height internally
3. Tables need dual widths: set columnWidths on the table AND width on every cell, both in WidthType.DXA (PERCENTAGE breaks in Google Docs). Column widths must sum to the table width
4. Table shading: use ShadingType.CLEAR, never SOLID (renders black)
5. Lists: never insert • literally; use a numbering config with LevelFormat.BULLET

## 常见陷阱

- Page size defaults to A4. For US Letter set page: { size: { width: 12240, height: 15840 } } (DXA; 1440 = 1″)
- Landscape: pass portrait dimensions and orientation: PageOrientation.LANDSCAPE — docx-js swaps width/height internally
- Table shading: use ShadingType.CLEAR, never SOLID (renders black)
- Lists: never insert • literally; use a numbering config with LevelFormat.BULLET
- ImageRun requires type: ("png", "jpg", …)
- PageBreak must be inside a Paragraph

## 验证清单

- [ ] After writing a .docx, render it and look at it:
- [ ] python scripts/office/soffice.py --headless --convert-to pdf output.docx

## 标签

`Word` `docx` `文档生成` `docx-js` `版式`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Average |
| executability | Good |
| maintainability | Good |
| cost_awareness | Average |

## 关联技能

- `compose_with` → `scientific-writing`
- `similar_to` → `pdf`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
