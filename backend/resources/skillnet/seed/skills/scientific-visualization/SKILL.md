---
name: "scientific-visualization"
description: "科研数据绘图：产出出版级图表，含配色、误差带、显著性标注与矢量导出。当需要把结果可视化或重绘不合格图表时使用。"
---

# scientific-visualization

> 领域：学术写作与可视化　|　来源：seed　|　代际：G0

## 能力契约 / Capability

生成可直接用于发表的矢量图表，含统计标注与可复现脚本

**输入**：清洗后的数据表；图表类型与目标期刊风格要求；统计检验结果

**输出**：矢量图（PDF/SVG）；绘图脚本；图注文本

**适用时机**：
- 论文或报告需要图表
- 需要重绘不符合规范的图
- 需要统一的配色体系

## 执行步骤

1. 按数据关系选图形：分布用箱线/小提琴，趋势用折线+误差带，关系用散点+拟合
2. 统一字体、字号、线宽，确保缩放到单栏宽度仍可读
3. 显式绘制误差条与样本量，标注显著性水平与检验方法
4. 导出矢量格式并保留绘图脚本
5. 为每张图写自解释图注

## 常见陷阱

- 用双轴图制造虚假相关
- 截断坐标轴夸大差异
- 配色对色觉障碍不友好

## 验证清单

- [ ] 坐标轴与单位标注完整
- [ ] 误差条与样本量齐备
- [ ] 图为矢量且字号达标

## 标签

`科研绘图` `可视化` `出版级` `matplotlib`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `differential-expression`
- `depend_on` → `statistical-testing`
