---
name: "molecular-docking"
description: "分子对接：准备受体与配体、定义结合口袋、执行对接并用打分与相互作用分析筛选候选。当需要预测小分子与靶点结合模式时使用。"
---

# molecular-docking

> 领域：化学、药物发现与药理学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出对接构象与结合能排序并给出相互作用分析

**输入**：受体结构（PDB）；配体库（SDF/SMILES）；结合口袋坐标或残基

**输出**：对接构象文件；结合能排序表；相互作用残基清单

**适用时机**：
- 筛选潜在活性化合物
- 分析结合模式
- 为虚拟筛选排序

## 执行步骤

1. 预处理受体：加氢、去水、分配电荷、修复缺失残基
2. 用共晶配体或口袋检测定义格点盒
3. 对接参数需说明随机种子与穷举程度
4. 用重对接（redocking）验证协议可复现晶体构象
5. 对结果做相互作用分析与聚类去冗余

## 常见陷阱

- 未做重对接验证导致协议不可信
- 把对接打分当作结合自由能
- 忽略受体柔性导致假阴性

## 验证清单

- [ ] 重对接 RMSD 达标
- [ ] 打分与相互作用分析一致
- [ ] 构象聚类后无冗余

## 标签

`分子对接` `虚拟筛选` `结合能` `Autodock`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `protein-structure-predict`
