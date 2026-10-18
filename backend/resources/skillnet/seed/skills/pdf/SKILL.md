---
name: "pdf"
description: "PDF 文档处理：do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging mu。"
---

# pdf

> 领域：文档工程　|　来源：member-import（Nexus skills/pdf）　|　代际：G0

## 能力契约 / Capability

do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to

**输入**：PDF 文件或生成 PDF 的内容源；页面/提取/合并等操作需求

**输出**：处理后的 PDF 文件；文本或表格提取结果

**适用时机**：
- 用户需要对 PDF 做任何操作——读取提取、合并拆分、生成、表单处理等触发

## 执行步骤

1. For advanced pypdfium2 usage, see REFERENCE.md
2. For JavaScript libraries (pdf-lib), see REFERENCE.md
3. If you need to fill out a PDF form, follow the instructions in FORMS.md
4. For troubleshooting guides, see REFERENCE.md

## 常见陷阱

- 导入时未从原文提取到显式陷阱条目，执行前请复核原文正文

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`PDF` `文本提取` `表单` `文档转换`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Basic |
| cost_awareness | Average |

## 关联技能

- `compose_with` → `literature-review`
- `similar_to` → `docx`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
