---
name: "cross-validation-protocol"
description: "验证协议设计：按数据结构选择 K 折、分组折、时间序列折或嵌套交叉验证，并给出外部验证方案。当需要设计可信评估流程时使用。"
---

# cross-validation-protocol

> 领域：机器学习与人工智能　|　来源：seed　|　代际：G0

## 能力契约 / Capability

为给定数据结构设计无偏的验证与外部验证协议

**输入**：数据结构说明（时间/分组/嵌套）；样本量；调参需求

**输出**：验证协议说明；评估脚本；性能不确定性估计

**适用时机**：
- 需要报告泛化性能
- 数据存在分组或时间结构
- 需要做超参搜索

## 执行步骤

1. 判断数据结构：是否独立同分布、是否分组、是否时序
2. 选择对应折法：StratifiedKFold / GroupKFold / TimeSeriesSplit
3. 调参使用嵌套交叉验证避免乐观偏差
4. 重复多次划分报告均值与标准差
5. 若可行，保留独立外部验证集做最终评估

## 常见陷阱

- 用同一折既调参又评估
- 忽略分组结构导致同源样本跨折
- 只报单次划分结果

## 验证清单

- [ ] 折法匹配数据结构
- [ ] 调参与评估分离
- [ ] 报告了性能波动范围

## 标签

`交叉验证` `泛化` `外部验证` `评估协议`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `leakage-guard`
