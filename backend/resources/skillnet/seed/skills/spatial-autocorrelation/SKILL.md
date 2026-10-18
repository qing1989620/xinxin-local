---
name: "spatial-autocorrelation"
description: "空间统计与地理加权：检验空间自相关、做空间回归与地理加权建模。当数据具有空间结构时使用。"
---

# spatial-autocorrelation

> 领域：生态与环境科学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

量化并控制空间自相关，产出未受空间结构干扰的统计结论

**输入**：带坐标的观测数据；空间权重定义；目标变量与协变量

**输出**：Moran's I 检验结果；空间回归模型；空间格局制图

**适用时机**：
- 数据存在地理聚集
- 需要做空间插值
- 普通回归残差存在空间结构

## 执行步骤

1. 定义空间权重矩阵并说明邻接或距离规则
2. 用 Moran's I 检验目标变量的空间自相关
3. 若残差存在空间结构则改用空间滞后/误差模型
4. 用 GWR 检查关系的空间非平稳性
5. 报告局部聚集位置与统计显著性

## 常见陷阱

- 用不同权重矩阵得到相反结论却不做敏感性分析
- 把空间相关当作因果
- 忽略可变面元问题

## 验证清单

- [ ] 权重矩阵定义已说明
- [ ] 残差空间结构已检验
- [ ] 敏感性分析已做

## 标签

`空间统计` `Moran` `地理加权` `空间回归`

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
