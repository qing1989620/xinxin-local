---
name: "protein-structure-predict"
description: "蛋白质结构预测与评估：调用结构预测工具，并用 pLDDT、PAE 与实验结构比对评估可信度。当需要获得蛋白三维结构时使用。"
---

# protein-structure-predict

> 领域：蛋白质组学与结构生物学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出蛋白结构模型并给出可信度分区评估

**输入**：氨基酸序列或 FASTA；可选同源模板；寡聚状态信息

**输出**：PDB 结构文件；置信度图（pLDDT/PAE）；结构质量评估报告

**适用时机**：
- 需要预测蛋白结构
- 分析突变对结构的影响
- 为对接准备受体结构

## 执行步骤

1. 确认序列与物种、异构体版本一致
2. 提交预测并记录使用的模型版本
3. 按 pLDDT 分区判断哪些区域可信
4. 用 PAE 检查结构域间相对朝向是否可信
5. 与已知实验结构比对 RMSD 验证

## 常见陷阱

- 把低置信度柔性区当作刚性结构使用
- 忽略寡聚状态导致界面错误
- 越过模型版本不做记录

## 验证清单

- [ ] 置信度图已生成
- [ ] 低置信区已标注
- [ ] 与模板比对结果已给出

## 标签

`蛋白结构` `AlphaFold` `pLDDT` `结构预测`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `compose_with` → `md-simulation`
