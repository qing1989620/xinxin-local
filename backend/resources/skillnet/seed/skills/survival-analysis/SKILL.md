---
name: "survival-analysis"
description: "生存分析：处理删失数据，估计生存曲线并做 Cox 或参数化建模。当研究终点是时间到事件时使用。"
---

# survival-analysis

> 领域：临床与健康科学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

对含删失的时间到事件数据完成生存曲线估计与风险因素建模

**输入**：随访时间与事件状态；协变量表；删失机制说明

**输出**：KM 生存曲线；Cox 风险比与置信区间；比例风险假设检验

**适用时机**：
- 临床随访数据
- 需要评估预后因素
- 比较两组生存差异

## 执行步骤

1. 先画 KM 曲线并做 log-rank 检验做整体比较
2. 检查删失是否独立，非独立删失需换用竞争风险模型
3. 拟合 Cox 模型并检验比例风险假设
4. 对违反 PH 假设的变量引入时变系数或分层
5. 报告风险比、置信区间与中位生存期

## 常见陷阱

- 忽略竞争风险导致高估累积发生率
- 未检验比例风险假设
- 把风险比解释为绝对风险变化

## 验证清单

- [ ] 删失机制已说明
- [ ] PH 假设已检验
- [ ] 中位生存期与曲线一致

## 标签

`生存分析` `Cox` `KM曲线` `删失`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `statistical-testing`
- `depend_on` → `clinical-feature-engineering`
- `depend_on` → `leakage-guard`
