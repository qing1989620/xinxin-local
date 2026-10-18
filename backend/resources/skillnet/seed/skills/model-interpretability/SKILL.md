---
name: "model-interpretability"
description: "模型可解释性：用 SHAP、PDP/ICE 与代理模型解释预测依据，区分全局与局部归因。当需要解释模型决策或做特征机理分析时使用。"
---

# model-interpretability

> 领域：机器学习与人工智能　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出可辩护的模型归因分析并识别其局限

**输入**：训练好的模型；特征表；需要解释的样本或子群

**输出**：全局重要性排序；局部归因图；部分依赖曲线

**适用时机**：
- 需要解释模型为什么这样预测
- 论文要求机理解释
- 向业务方交付可解释结论

## 执行步骤

1. 先用置换重要性做全局排序
2. 用 SHAP 做局部归因并检查加性假设是否成立
3. 用 PDP/ICE 检查非线性与交互效应
4. 对相关特征做分组归因避免稀释
5. 显式声明归因方法的假设与失效条件

## 常见陷阱

- 把 SHAP 值当作因果效应
- 忽略特征相关性导致的归因偏移
- 用单一方法下结论

## 验证清单

- [ ] 至少两种归因方法互相印证
- [ ] 交互效应已检查
- [ ] 方法假设已声明

## 标签

`可解释性` `SHAP` `PDP` `归因`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `tabular-ml-baseline`
- `depend_on` → `flux-tower-ml`
