---
name: "eeg-preprocessing"
description: "EEG 预处理与分解：做重参考、滤波、伪迹去除、分段与基线校正，并用 ICA 分离伪迹成分。当处理脑电数据时使用。"
---

# eeg-preprocessing

> 领域：神经科学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出干净的分段 EEG 数据并保留伪迹处理记录

**输入**：原始 EEG 记录；电极位置文件；事件标记

**输出**：预处理后数据；伪迹成分标注；分段试次集

**适用时机**：
- 分析 EEG 事件相关电位
- 做脑电节律分析
- 去除眼动与肌电伪迹

## 执行步骤

1. 查看原始数据定位坏导与饱和段
2. 带通滤波并做重参考
3. 用 ICA 分解并人工/半自动标注伪迹成分
4. 分段并按事件对齐做基线校正
5. 剔除坏段并记录剔除比例

## 常见陷阱

- 未检查坏导直接分析
- 过度剔除试次造成条件间数量失衡
- ICA 成分标注未留痕

## 验证清单

- [ ] 坏导处理已记录
- [ ] 伪迹成分已可视化确认
- [ ] 各条件剩余试次数已报告

## 标签

`EEG` `ICA` `伪迹` `ERP`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `depend_on` → `signal-processing`
