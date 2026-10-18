---
name: "econometric-panel"
description: "面板数据计量：选择固定/随机效应、处理内生性与稳健标准误。当使用多年多主体的面板数据时使用。"
---

# econometric-panel

> 领域：金融与经济学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

为面板数据选择正确设定并处理内生性

**输入**：面板数据结构；被解释与解释变量；潜在内生性来源

**输出**：模型估计结果；内生性检验；稳健标准误结论

**适用时机**：
- 多年多公司/地区数据
- 需要控制不可观测异质性
- 评估政策效应

## 执行步骤

1. 用 Hausman 检验在固定与随机效应间选择
2. 检验序列相关与异方差，选择聚类标准误层级
3. 识别内生性并选择工具变量或动态面板方法
4. 做弱工具变量与过度识别检验
5. 报告稳健性与安慰剂检验

## 常见陷阱

- 聚类层级选择随意导致标准误偏小
- 弱工具变量导致估计有偏
- 忽略时间趋势造成伪回归

## 验证清单

- [ ] Hausman 检验结果已报告
- [ ] 标准误聚类层级已论证
- [ ] 工具变量有效性已检验

## 标签

`面板数据` `固定效应` `内生性` `工具变量`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `causal-inference`
- `compose_with` → `statistical-testing`
