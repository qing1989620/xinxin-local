---
name: "gwas-prs"
description: "多基因风险评分流程：构建或移植 PRS 计算管线，处理基因组版本、位点对齐与等位基因方向。当需要从基因型计算 PRS 时使用。"
---

# gwas-prs

> 领域：临床与健康科学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出经过对齐与校验的 PRS 计算流程与自检方案

**输入**：目标基因型数据（VCF/PLINK）；权重文件（PGS Catalog）；参考面板与基因组版本信息

**输出**：个体 PRS 值；流程校验报告；人群分层评估

**适用时机**：
- 需要计算多基因风险评分
- 验证 PRS 流程是否失效
- 跨人群移植性评估

## 执行步骤

1. 统一基因组版本（如 GRCh38）并转换坐标
2. 取权重与基因型位点的交集并记录覆盖率
3. 处理等位基因方向与链翻转
4. 用合成表型做非平庸性自检与校准度检验
5. 评估跨人群移植性能差异

## 常见陷阱

- 忽略基因组版本不匹配导致大量位点错配
- 等位基因方向反转导致评分符号错误
- 直接用欧洲人群权重解释东亚人群

## 验证清单

- [ ] 位点覆盖率已报告
- [ ] 自检显示评分与合成表型相关
- [ ] 校准度指标已给出

## 标签

`PRS` `多基因风险` `基因组版本` `位点对齐`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `variant-calling`
- `compose_with` → `clinical-feature-engineering`
