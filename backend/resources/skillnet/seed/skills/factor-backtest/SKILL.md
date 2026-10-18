---
name: "factor-backtest"
description: "因子回测：构建因子并做分组收益、IC 分析与交易成本敏感性测试，防止前视偏差。当需要验证量化选股因子时使用。"
---

# factor-backtest

> 领域：金融与经济学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出无前视偏差的因子有效性评估与成本敏感分析

**输入**：价格与财务数据；因子定义；调仓频率与交易成本假设

**输出**：因子分组收益曲线；IC/RankIC 序列；成本敏感性与换手率

**适用时机**：
- 验证选股因子有效性
- 比较多个因子
- 评估策略容量

## 执行步骤

1. 严格按公告日对齐财务数据避免前视
2. 对因子做行业与市值中性化
3. 按因子值分组并计算多空组合收益
4. 计算 IC 序列并做统计显著性检验
5. 扣除交易成本并评估换手率影响

## 常见陷阱

- 用财报期而非公告日造成前视偏差
- 忽略停牌与涨跌停导致的不可交易
- 未扣成本高估收益

## 验证清单

- [ ] 数据时点严格对齐
- [ ] 已剔除不可交易样本
- [ ] 成本敏感性已展示

## 标签

`因子` `回测` `IC` `量化`

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
- `compose_with` → `econometric-panel`
