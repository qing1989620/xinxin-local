---
name: "pathway-enrichment"
description: "通路富集分析：对基因列表做 ORA 或 GSEA 富集，处理背景基因集与多重比较。当需要解释基因列表的生物学意义时使用。"
---

# pathway-enrichment

> 领域：基因组学与转录组学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

把基因列表转化为有统计支撑的通路与功能富集结论

**输入**：基因列表及排序依据；背景基因集；注释数据库版本

**输出**：富集通路表；富集气泡图/GSEA 图；主导功能模块归纳

**适用时机**：
- 需要解释差异基因的生物学含义
- 验证假设通路是否被激活

## 执行步骤

1. 确定背景基因集，避免用全基因组不当背景
2. 有排序信息时优先用 GSEA 而非 ORA
3. 对多重比较做 FDR 校正
4. 合并冗余通路并按基因重叠聚类
5. 区分被激活与抑制的通路方向

## 常见陷阱

- 背景基因集选择不当导致假富集
- 只报最显著通路忽略冗余
- 忽略通路方向性

## 验证清单

- [ ] 背景基因集已说明
- [ ] FDR 已校正
- [ ] 冗余通路已合并

## 标签

`通路富集` `GSEA` `GO` `KEGG`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `differential-expression`
