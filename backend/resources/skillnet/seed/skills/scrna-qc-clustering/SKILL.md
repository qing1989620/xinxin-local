---
name: "scrna-qc-clustering"
description: "单细胞转录组标准分析：完成质控、归一化、高变基因、降维、聚类与标记基因鉴定。当拿到 scRNA-seq 计数矩阵时使用。"
---

# scrna-qc-clustering

> 领域：细胞生物学与单细胞　|　来源：seed　|　代际：G0

## 能力契约 / Capability

从原始计数矩阵产出带注释的细胞亚群与标记基因表

**输入**：10x 计数矩阵（h5/mtx）；样本元数据；线粒体基因比例阈值

**输出**：AnnData 对象；UMAP/tSNE 降维图；聚类标签与标记基因表

**适用时机**：
- 处理 scRNA-seq 原始矩阵
- 需要识别细胞亚群
- 比较不同条件下的细胞组成

## 执行步骤

1. 按 nGene/nUMI/线粒体比例做质控过滤并记录去除细胞数
2. 做归一化与对数变换，选取高变基因
3. 做 PCA 后用肘部图与轮廓系数确定主成分数
4. 用 Leiden 做图聚类并做批次效应校正
5. 用 Wilcoxon 检验鉴定标记基因并与已知标记比对

## 常见陷阱

- 用统一的线粒体阈值忽略组织差异
- 未做批次校正导致聚类被批次主导
- 用 tSNE 距离解释细胞相似度

## 验证清单

- [ ] 质控前后细胞数可追溯
- [ ] 聚类数经多分辨率验证
- [ ] 标记基因有已知生物学对应

## 标签

`单细胞` `scRNA-seq` `scanpy` `聚类` `质控`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Average |
| maintainability | Good |
| cost_awareness | Good |

## 关联技能

- `compose_with` → `pathway-enrichment`
- `compose_with` → `scientific-visualization`
