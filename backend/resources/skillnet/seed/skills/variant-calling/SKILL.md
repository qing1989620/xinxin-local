---
name: "variant-calling"
description: "变异检测：从测序数据做比对、去重、变异检测与过滤，产出经过质量控制的变异集。当需要从 FASTQ/BAM 得到变异时使用。"
---

# variant-calling

> 领域：基因组学与转录组学　|　来源：seed　|　代际：G0

## 能力契约 / Capability

产出可用的变异集并给出质量控制指标

**输入**：FASTQ 或 BAM 文件；参考基因组；已知位点资源（dbSNP/千人基因组）

**输出**：过滤后的 VCF；比对与变异质量指标；变异注释表

**适用时机**：
- 从测序数据识别 SNP/Indel
- 需要做基因分型

## 执行步骤

1. 比对后做重复标记与碱基质量重校准
2. 用标准流程做变异检测并保留中间文件
3. 用已知位点做 BQSR 与硬过滤或 VQSR
4. 评估 Ti/Tv 比、重复率、覆盖度等质量指标
5. 对候选变异做功能注释与致病性查询

## 常见陷阱

- 跳过碱基质量重校准导致假阳性
- 过滤阈值不适用于小 panel
- 忽略低覆盖区域的假阴性

## 验证清单

- [ ] 质量指标在合理范围
- [ ] Ti/Tv 比符合预期
- [ ] 关键变异有覆盖度支撑

## 标签

`变异检测` `GATK` `VCF` `测序`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |
