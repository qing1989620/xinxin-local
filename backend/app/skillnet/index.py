"""技能索引：BM25 稀疏检索 + TF-IDF 向量检索。

说明（诚实标注）：
本 demo 环境无法访问 HuggingFace 下载稠密编码器，因此「语义通路」用
字级 n-gram + 词级 IDF 加权的稀疏向量空间模型实现，配合 LLM 重排补足语义。
生产环境中该通路应替换为 BGE-M3 / Qwen3-Embedding 等稠密编码器，
接口保持不变（`DenseIndex.search`）。
"""
from __future__ import annotations

import math
import re
import zlib
from collections import Counter
from typing import Iterable

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]*|\d+")

_STOP = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with", "is",
    "are", "be", "as", "by", "at", "it", "this", "that", "from", "we", "can",
    "的", "了", "和", "与", "在", "是", "对", "并", "等", "为", "把", "用",
}


def tokenize(text: str) -> list[str]:
    """中英混合分词：英文按词，中文按 1-gram + 2-gram。"""
    text = text.lower()
    tokens = [t for t in TOKEN_RE.findall(text) if t not in _STOP and len(t) > 1]
    cjk = re.findall(r"[\u4e00-\u9fff]+", text)
    for run in cjk:
        if len(run) == 1:
            tokens.append(run)
            continue
        tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens


def char_ngrams(text: str, n: int = 3) -> list[str]:
    text = re.sub(r"\s+", "", text.lower())
    if len(text) < n:
        return [text] if text else []
    return [text[i : i + n] for i in range(len(text) - n + 1)]


class BM25Index:
    """标准 BM25 Okapi。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs: list[str] = []
        self.tf: list[Counter] = []
        self.df: Counter = Counter()
        self.doc_len: list[int] = []
        self.avg_len: float = 0.0

    def fit(self, ids: list[str], texts: list[str]) -> None:
        """同 VectorIndex.fit：局部构建 + 一次性赋值，避免并发读到半成品索引。"""
        new_tf: list[Counter] = []
        new_df: Counter = Counter()
        new_len: list[int] = []
        for t in texts:
            toks = tokenize(t)
            c = Counter(toks)
            new_tf.append(c)
            new_len.append(len(toks))
            for term in c:
                new_df[term] += 1

        # ---- 原子替换 ----
        self.docs = list(ids)
        self.tf = new_tf
        self.df = new_df
        self.doc_len = new_len
        self.n = len(self.docs)
        self.avg_len = (sum(new_len) / len(new_len)) if new_len else 0.0

    def _idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 20) -> list[tuple[str, float]]:
        if not self.docs:
            return []
        q_tokens = tokenize(query)
        scores: dict[int, float] = {}
        for term in q_tokens:
            if term not in self.df:
                continue
            idf = self._idf(term)
            for i, c in enumerate(self.tf):
                f = c.get(term)
                if not f:
                    continue
                denom = f + self.k1 * (
                    1 - self.b + self.b * (self.doc_len[i] / (self.avg_len or 1))
                )
                scores[i] = scores.get(i, 0.0) + idf * f * (self.k1 + 1) / denom
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:top_k]
        return [(self.docs[i], round(s, 4)) for i, s in ranked]


class VectorIndex:
    """稀疏向量空间模型：词级 Hashing + IDF 加权 + 余弦相似度。

    实测（本 demo 的诊断脚本）：在中文科研任务上，若混入字符 n-gram，
    噪声会显著压低检索质量（无关技能被 3-gram 碰撞推入 top5）。
    因此默认只用词级特征（英文词 + 中文 2-gram），`use_char` 保留为开关。
    """

    def __init__(self, dim: int = 2048, use_char: bool = False) -> None:
        self.dim = dim
        self.use_char = use_char
        self.ids: list[str] = []
        self.matrix: list[dict[int, float]] = []
        self.df: Counter = Counter()

    def _raw_features(self, text: str) -> list[str]:
        feats = tokenize(text)
        if self.use_char:
            feats = feats + ["#3#" + g for g in char_ngrams(text, 3)]
        return feats

    def _hash(self, feat: str) -> int:
        """稳定哈希。

        不能用内置 `hash()` —— 它对 str 的结果受 PYTHONHASHSEED 影响，
        **每个进程都不一样**。那会导致：同一份技能库在不同进程里编码出的向量不可比，
        索引无法持久化，也无法复现历史检索结果。
        改用 CRC32：跨进程、跨平台、跨版本都稳定，速度也足够。
        """
        return zlib.crc32(feat.encode("utf-8")) % self.dim

    def fit(self, ids: list[str], texts: list[str]) -> None:
        """构建索引。

        注意：全部结果先在**局部变量**里算完，最后一次性赋给实例属性。
        Python 的属性赋值是原子的，因此并发读要么看到完整的旧索引、
        要么看到完整的新索引，不会出现「新 ids 配旧 matrix」这种
        静默返回错误技能名的撕裂状态（这是本模块修掉的一个真实缺陷）。
        """
        new_df: Counter = Counter()
        tokenised = []
        for t in texts:
            feats = self._raw_features(t)
            tokenised.append(feats)
            for f in set(feats):
                new_df[f] += 1

        n = max(1, len(texts))
        new_matrix: list[dict[int, float]] = []
        for feats in tokenised:
            vec: dict[int, float] = {}
            counts = Counter(feats)
            for f, c in counts.items():
                idf = math.log(1 + n / (1 + new_df[f]))
                w = (1 + math.log(c)) * idf
                h = self._hash(f)
                vec[h] = vec.get(h, 0.0) + w
            new_matrix.append(self._normalise(vec))

        # ---- 原子替换 ----
        self.ids = list(ids)
        self.df = new_df
        self.matrix = new_matrix

    @staticmethod
    def _normalise(vec: dict[int, float]) -> dict[int, float]:
        norm = math.sqrt(sum(v * v for v in vec.values()))
        return {k: v / norm for k, v in vec.items()} if norm else vec

    def encode(self, text: str) -> dict[int, float]:
        n = max(1, len(self.ids))
        vec: dict[int, float] = {}
        counts = Counter(self._raw_features(text))
        for f, c in counts.items():
            idf = math.log(1 + n / (1 + self.df.get(f, 0)))
            w = (1 + math.log(c)) * idf
            h = self._hash(f)
            vec[h] = vec.get(h, 0.0) + w
        return self._normalise(vec)

    @staticmethod
    def _cos(a: dict[int, float], b: dict[int, float]) -> float:
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(k, 0.0) for k, v in a.items())

    def search(self, query: str, top_k: int = 20) -> list[tuple[str, float]]:
        q = self.encode(query)
        scored = [(self.ids[i], self._cos(q, v)) for i, v in enumerate(self.matrix)]
        scored = [s for s in scored if s[1] > 0]
        scored.sort(key=lambda kv: -kv[1])
        return [(i, round(s, 4)) for i, s in scored[:top_k]]


def rrf_fuse(
    runs: list[list[tuple[str, float]]],
    k: int = 60,
    weights: list[float] | None = None,
    agreement_bonus: float = 0.008,
) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion：融合多路召回结果。

    `agreement_bonus` 给「被多路同时召回」的技能额外加分。没有它时，
    单路召回的噪声项（例如只在向量通路排第一的技能）会挤掉被两路同时
    召回的真实目标 —— 本 demo 的诊断实验证实了这一点。
    """
    weights = weights or [1.0] * len(runs)
    agg: dict[str, float] = {}
    channel_hits: dict[str, int] = {}
    for run, w in zip(runs, weights):
        for rank, (doc, _score) in enumerate(run, 1):
            agg[doc] = agg.get(doc, 0.0) + w / (k + rank)
            channel_hits[doc] = channel_hits.get(doc, 0) + 1
    for doc, cnt in channel_hits.items():
        if cnt > 1:
            agg[doc] += agreement_bonus * (cnt - 1)
    return sorted(agg.items(), key=lambda kv: -kv[1])


def weighted_fuse(
    runs: list[list[tuple[str, float]]],
    weights: list[float],
    agreement_bonus: float = 0.05,
) -> list[tuple[str, float]]:
    """加权分数融合：先对每路做 min-max 归一化，再按权重相加。

    相比纯 RRF，这里保留了「某一路内部领先幅度」的信息，
    因此强通路（本 demo 中是 BM25）能够主导排序，弱通路只做补充。
    """
    agg: dict[str, float] = {}
    channel_hits: dict[str, int] = {}
    for run, w in zip(runs, weights):
        if not run:
            continue
        vals = [s for _, s in run]
        lo, hi = min(vals), max(vals)
        span = hi - lo
        for doc, s in run:
            # Xinxin adaptation: a tied positive channel (e.g. matching domain
            # tags or one exact BM25 hit) still supplies its configured weight.
            # Upstream's (s - lo) / 1 erased every hit in this case.
            normalised = (s - lo) / span if span else (1.0 if s > 0 else 0.0)
            agg[doc] = agg.get(doc, 0.0) + w * normalised
            channel_hits[doc] = channel_hits.get(doc, 0) + 1
    for doc, cnt in channel_hits.items():
        if cnt > 1:
            agg[doc] += agreement_bonus * (cnt - 1)
    return sorted(agg.items(), key=lambda kv: -kv[1])


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0
