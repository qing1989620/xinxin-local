---
name: "molecular-descriptors"
description: "分子指纹与描述符：生成摩根指纹、理化描述符与骨架划分，用于建模与相似性分析。当需要把分子转成特征时使用。"
---

# molecular-descriptors

> 领域：化学、药物发现与药理学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出可复现的分子特征矩阵与骨架划分方案

**输入**：化合物 SMILES 列表；指纹类型与半径；目标建模任务

**输出**：分子特征矩阵；骨架划分结果；相似性矩阵

**适用时机**：
- 构建分子性质预测模型
- 做相似性检索与聚类
- 需要严格的骨架外推评估

## 执行步骤

1. 标准化 SMILES 并处理盐、互变异构与立体化学
2. 按任务选择指纹（ECFP4/6）或描述符组合
3. 用 Murcko 骨架做划分以评估外推能力
4. 检查特征维度与稀疏度，必要时做特征选择
5. 记录全部参数以保证可复现

## 常见陷阱

- 忽略立体化学导致同类分子被混淆
- 用随机划分高估外推性能
- 描述符含目标泄漏信息

## 验证清单

- [ ] 标准化步骤已记录
- [ ] 指纹参数已固定
- [ ] 划分方式支持外推评估

## 标签

`分子指纹` `摩根指纹` `描述符` `RDKit`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `compose_with` → `tabular-ml-baseline`
