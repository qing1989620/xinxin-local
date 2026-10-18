---
name: "admet-prediction"
description: "ADMET 成药性预测：预测吸收、分布、代谢、排泄与毒性属性，标注模型适用域与预测不确定性。当需要早期筛选候选化合物时使用。"
---

# admet-prediction

> 领域：化学、药物发现与药理学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出多终点 ADMET 预测与适用域评估

**输入**：化合物 SMILES 列表；候选终点选择；参考化合物（对照）

**输出**：ADMET 预测表；适用域与置信标注；风险化合物清单

**适用时机**：
- 需要评估成药性
- 早期淘汰高风险化合物
- 优化先导化合物的药代性质

## 执行步骤

1. 标准化 SMILES 并去盐、去重复
2. 按终点分别预测并记录模型版本
3. 用适用域方法判断分子是否在训练分布内
4. 对关键终点用实验数据或已知药物做校准检查
5. 输出风险排序与结构改造建议

## 常见陷阱

- 无视适用域直接采信预测
- 把预测值当作实验值
- 忽略立体化学导致预测偏差

## 验证清单

- [ ] 分子标准化步骤已记录
- [ ] 适用域已标注
- [ ] 关键终点有校准对照

## 标签

`ADMET` `成药性` `毒性预测` `药物发现`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `molecular-descriptors`
- `depend_on` → `molecular-docking`
