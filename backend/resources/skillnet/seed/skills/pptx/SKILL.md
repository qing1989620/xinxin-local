---
name: "pptx"
description: "演示文稿制作：a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks。"
---

# pptx

> 领域：文档工程　|　来源：member-import（Nexus skills/pptx）　|　代际：G0

## 能力契约 / Capability

a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx or .potx file (even if the extracted content will be used elsewhere, like in an email or summary); editing

**输入**：演示主题与素材内容；可选 .pptx 模板

**输出**：生成的 .pptx 演示文稿；版式校验结果

**适用时机**：
- 涉及 .pptx/.potx 演示文稿的创建、解析、编辑或文本提取时触发

## 执行步骤

1. Set pres.layout before adding slides. The default canvas is LAYOUT16x9 = 10" × 5.625", not 13.3" wide. Coordinates past the edge are written, not clamped — the shape just isn't on the slide. (LAYOUTWIDE is 13.3" × 7.5".)
2. Hex colors: never #, never 8 digits. color: "FF0000". Both "#FF0000" and alpha baked into the hex ("00000020") corrupt the file. For translucency: transparency: 0-100 on fills and images, opacity: 0.0-1.0 on shadows — each is silently ignored on the other
3. pptxgenjs mutates option objects in place (converts values to EMU on first use). Never share one shadow/options object across two add calls — build a fresh object each time
4. Shadow offset must be ≥ 0 — a negative offset corrupts the file. To cast a shadow upward, use angle: 270 with a positive offset
5. letterSpacing is silently ignored — the real option is charSpacing

## 常见陷阱

- Shadow offset must be ≥ 0 — a negative offset corrupts the file. To cast a shadow upward, use angle: 270 with a positive offset
- letterSpacing is silently ignored — the real option is charSpacing
- One new pptxgen() per output file — never reuse an instance
- rectRadius only works on ROUNDEDRECTANGLE, not RECTANGLE
- Gradient fills aren't supported — use a gradient image as the background instead
- Text boxes have built-in internal padding — set margin: 0 whenever text must align with a shape, line, or icon at the same x

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`PPT` `pptxgenjs` `演示` `模板`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Good |
| maintainability | Good |
| cost_awareness | Average |

## 关联技能

- `compose_with` → `poster-slides`
- `similar_to` → `docx`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
