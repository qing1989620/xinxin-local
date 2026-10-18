---
name: "differential-expression"
description: "差异表达分析：做统计建模、表达倍数收缩、多重校正与结果可视化。当需要比较不同条件间的基因表达时使用。"
---

# differential-expression

> 领域：基因组学与转录组学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出校正后的差异表达基因表与可视化结果

**输入**：计数矩阵或标准化表达量；样本分组与协变量；对照与处理定义

**输出**：差异表达基因表；火山图与热图；富集分析输入

**适用时机**：
- 比较处理组与对照组表达差异
- 筛选候选生物标志物

## 执行步骤

1. 确认输入为原始计数并纳入协变量设计
2. 用负二项模型拟合并做离散度估计
3. 做表达倍数收缩避免低表达基因虚高
4. 多重检验校正后按 FDR 阈值筛选
5. 检查结果对阈值与协变量的稳健性

## 常见陷阱

- 对标准化数据而非计数做负二项建模
- 未纳入批次等协变量
- 用未校正 p 值筛选

## 验证清单

- [ ] 设计矩阵与实验设计匹配
- [ ] FDR 已校正
- [ ] 结果可视化与表格一致

## 标签

`差异表达` `DESeq2` `FDR` `火山图`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `scrna-qc-clustering`
