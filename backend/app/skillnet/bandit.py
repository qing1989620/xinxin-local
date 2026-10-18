"""上下文老虎机：在有限预算下决定「接下来评估哪个技能」。

## 为什么重写

v0.2 及以前用的是「每个技能一个臂」的 LinUCB（per-arm A/b）。那是一个**错的实现选择**：
- `A[name]` / `b[name]` 相互独立，更新技能 A 之后，技能 B 的参数一点都不会变；
- 上下文只编码了技能本身，没有编码 task；
- 结果是 `predicted_reward` 恒为 0（b 初值为零向量，未 update 过的臂 θ 恒为零向量）。

而项目文档声称「一次评估的反馈能影响语义相近的未评估技能」——
per-arm 实现在数学上**不可能**做到这件事。v0.3 改为 **shared LinUCB**：
全局共享一套 `A`、`b`、因此共享 `θ`，每个 (task, skill) 对被编码成各自的 φ，
用同一个 θ 打分。

泛化是怎么发生的：更新时 `A += φφᵀ`、`b += r·φ`，于是 θ 变化。
对未评估的技能 B，只要 `φ(task, B)` 与 `φ(task, A)` 相似，
`θᵀφ(task,B)` 就会沿着 A 的反馈方向移动。这就是跨技能泛化的机制，
也是本文件必须共享 A/b 的原因。

## 特征设计（φ）

φ(task, skill) 由四段拼接而成，总维度 `CTX_DIM`：

| 段 | 维度 | 内容 |
|---|---|---|
| task 侧 | 24 | query 的 hashing-trick 词袋，L2 归一化 |
| skill 侧 | 24 | 技能 L1 文本的 hashing-trick 词袋，L2 归一化 |
| 交互 | 3 | cos(task, skill)、逐元素乘积的均值、Jaccard |
| 元特征 | 5 | 检索归一化分数、1/(1+rank)、质量分、代际、是否演化产生 |

**刻意不放进 φ 的特征**：该技能的历史 pulls / mean_reward。
把「已经被拉过多少次、拿到过多少奖励」当作特征会造成标签泄漏 ——
模型会直接学会「奖励高的臂奖励高」，而不是学会「什么样的技能适合什么样的任务」。
历史信息只用于探索奖励项（`√(φᵀA⁻¹φ)` 天然随观测次数衰减），不进入 φ 本身。

## 可复现性

所有哈希走 CRC32（跨进程、跨平台、跨版本稳定）。
**不要用内置 `hash()`** —— 它受 PYTHONHASHSEED 影响，每个进程结果都不同，
会导致上下文不可复现、模型无法持久化、两次实验无法比对。
"""
from __future__ import annotations

import math
import hashlib
import json
import random
import threading
import zlib
from functools import wraps
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .catalog import SkillLibrary
from .index import tokenize
from .schema import Skill, quality_score

# 维度选择说明：早期用 EMB_DIM=24 时，51 个技能的中文文本经 hashing-trick 后
# 碰撞严重，任意两个技能的 φ 余弦相似度都接近，导致「更新 A」对 B 与对 C 的影响
# 几乎相同（实测 ΔB=0.472 vs ΔC=0.463），泛化虽存在但不可用。
# 提到 64 维并加 IDF 加权后区分度才够。A 矩阵为 136×136，求逆是微秒级。
EMB_DIM = 64          # task / skill 各自的词袋维度
DOMAIN_DIM = 24       # 领域 one-hot（当前 17 个领域，留余量）
INTERACTION_DIM = 3
META_DIM = 5
CTX_DIM = EMB_DIM * 2 + DOMAIN_DIM + INTERACTION_DIM + META_DIM      # 152


def _locked(method):
    """Numpy 运算会释放 GIL：评分、反馈与参数快照必须共享同一把锁。"""
    @wraps(method)
    def call(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return call

# 关于 DOMAIN_DIM 的存在理由（实测得来，不是想当然）：
# 词袋计数向量**全部非负**，在 128 维下任意两个技能的余弦相似度都会「集中」在
# 0.88–0.90 区间 —— 这是非负高维向量的固有现象。实测 cos(φ_A, φ_B)=0.883
# 反而低于 cos(φ_A, φ_C)=0.898，也就是说「同领域」这件事在 φ 里根本体现不出来，
# 跨技能泛化因此退化成「所有技能一起涨」。
# 单独给领域一段特征后，同领域技能的 φ 才真正对齐。


def stable_hash(token: str, dim: int) -> int:
    """跨进程稳定的特征哈希。用 CRC32 而不是内置 hash()。"""
    return zlib.crc32(token.encode("utf-8")) % dim


def hashing_bag(
    text: str, dim: int, idf: dict[str, float] | None = None,
    default_weight: float = 1.0,
) -> np.ndarray:
    """把文本压成定长词袋向量（hashing trick），L2 归一化。

    带 IDF 权重时，稀有词（更能区分技能的词）获得更高权重，
    这显著提升了不同技能之间 φ 的可分性。
    """
    vec = np.zeros(dim, dtype=float)
    tokens = tokenize(text or "")
    if not tokens:
        return vec
    for tok in tokens:
        w = idf.get(tok, default_weight) if idf else 1.0
        vec[stable_hash(tok, dim)] += w
    norm = float(np.linalg.norm(vec))
    return vec / norm if norm else vec


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class ContextEncoder:
    """把 (task, skill) 对编码成上下文向量 φ。

    与 v0.2 的关键差别：**task 进来了**。同一个技能在不同任务下的 φ 必然不同，
    这既是 task conditioning 的前提，也是 `test_bandit_task_conditioning` 断言的内容。
    """

    def __init__(
        self, lib: SkillLibrary | None = None, dim: int = CTX_DIM, emb_dim: int = EMB_DIM
    ) -> None:
        self.lib = lib
        self.dim = dim
        self.emb_dim = emb_dim
        self._skill_cache: dict[str, np.ndarray] = {}
        self._idf: dict[str, float] | None = None
        self._idf_default: float = 1.0
        self._domains: list[str] | None = None

    # ------------------------------------------------------------------
    def _idf_table(self) -> dict[str, float]:
        """从技能库统计 IDF。稀有词更能区分技能，因此权重更高。

        未登录词（任务里出现但技能库没见过）取 df=0 对应的最大 idf ——
        这类词往往是任务特有的表述，正是最该给高权重的部分。
        """
        if self._idf is None:
            df: dict[str, int] = {}
            skills = self.lib.all() if self.lib is not None else []
            for s in skills:
                for tok in set(tokenize(s.l1_text())):
                    df[tok] = df.get(tok, 0) + 1
            n = max(1, len(skills))
            self._idf = {t: math.log(1 + n / (1 + c)) for t, c in df.items()}
            self._idf_default = math.log(1 + n)
        return self._idf

    # ------------------------------------------------------------------
    def skill_embedding(self, skill: Skill) -> np.ndarray:
        if skill.name not in self._skill_cache:
            # L1 文本 = 能力 + 描述 + 适用时机，是「这个技能是干什么的」最浓缩的表达
            self._skill_cache[skill.name] = hashing_bag(
                skill.l1_text(), self.emb_dim, self._idf_table(), self._idf_default
            )
        return self._skill_cache[skill.name]

    def task_embedding(self, query: str) -> np.ndarray:
        return hashing_bag(
            query or "", self.emb_dim, self._idf_table(), self._idf_default
        )

    def _domain_index(self, domain: str) -> int:
        """领域 -> 稳定索引。

        用「领域名排序后的下标」而不是 hashing：领域集合是封闭且有限的，
        排序下标跨进程稳定、无碰撞，比哈希更适合 one-hot 编码。
        """
        if self._domains is None:
            names = {s.domain for s in (self.lib.all() if self.lib is not None else [])}
            self._domains = sorted(names)
        return self._domains.index(domain) if domain in self._domains else -1

    def domain_embedding(self, skill: Skill) -> np.ndarray:
        """领域 one-hot。

        早先用词袋编码领域名，效果不好：领域名很短（如「文献与研究」），
        经 IDF 与归一化后几乎不携带信息，无法把同领域技能拉近。
        one-hot 让同领域技能的该段完全相同、异领域完全正交，区分度最大。
        """
        key = f"__domain__{skill.domain}"
        if key not in self._skill_cache:
            vec = np.zeros(DOMAIN_DIM, dtype=float)
            idx = self._domain_index(skill.domain)
            if idx >= 0:
                vec[idx % DOMAIN_DIM] = 1.0
            self._skill_cache[key] = vec
        return self._skill_cache[key]

    # ------------------------------------------------------------------
    def encode(
        self,
        task: str,
        skill: Skill,
        extra: dict[str, float] | None = None,
    ) -> np.ndarray:
        """φ(task, skill)。`extra` 可带 retrieval（归一化分数）与 rank。"""
        extra = extra or {}
        t_vec = self.task_embedding(task)
        s_vec = self.skill_embedding(skill)

        phi = np.zeros(self.dim, dtype=float)
        o = 0
        phi[o:o + self.emb_dim] = t_vec
        o += self.emb_dim
        phi[o:o + self.emb_dim] = s_vec
        o += self.emb_dim
        phi[o:o + DOMAIN_DIM] = self.domain_embedding(skill)
        o += DOMAIN_DIM

        inter = t_vec * s_vec
        phi[o + 0] = _cosine(t_vec, s_vec)
        phi[o + 1] = float(np.mean(inter)) if inter.size else 0.0
        phi[o + 2] = float(np.count_nonzero(inter)) / max(1, self.emb_dim)
        o += INTERACTION_DIM

        rank = float(extra.get("rank", 0.0))
        phi[o + 0] = float(extra.get("retrieval", 0.0))
        phi[o + 1] = 1.0 / (1.0 + max(0.0, rank))
        phi[o + 2] = quality_score(skill.quality)
        phi[o + 3] = min(skill.generation, 5) / 5.0
        phi[o + 4] = 1.0 if skill.source != "seed" else 0.0
        return phi

    def invalidate(self, name: str | None = None) -> None:
        if name is None:
            self._skill_cache.clear()
        else:
            self._skill_cache.pop(name, None)


@dataclass
class Pull:
    round: int
    skill: str
    predicted: float
    reward: float
    reason: str = ""
    exploration: float = 0.0
    task: str = ""


class SharedLinUCB:
    """共享参数的 LinUCB（disjoint 的反面：hybrid/shared 形态）。

    `优先级 = θᵀφ + α·√(φᵀA⁻¹φ)`
      - 第一项是预测收益，θ 由**全部**历史观测共同拟合 → 天然跨技能泛化；
      - 第二项是探索奖励，随该方向被观测的次数增加而收缩。

    只用一份 A、b，所以「评估 A 影响 B」是这个实现的默认行为，而不是需要额外机制。
    """

    name = "shared_linucb"

    def __init__(
        self,
        lib: SkillLibrary,
        *,
        alpha: float = 0.25,
        dim: int = CTX_DIM,
        seed: int = 17,
    ) -> None:
        self._lock = threading.RLock()
        self.lib = lib
        self.alpha = alpha
        self.dim = dim
        self.encoder = ContextEncoder(lib, dim)   # 需要 lib 来统计 IDF
        self.rng = random.Random(seed)
        self.A = np.eye(dim)          # 全局共享
        self.b = np.zeros(dim)        # 全局共享
        self.n_updates = 0
        self.history: list[Pull] = []

    # ------------------------------------------------------------------
    @property
    @_locked
    def theta(self) -> np.ndarray:
        return np.linalg.solve(self.A, self.b)

    def _phi(
        self, task: str, name: str, extra: dict[str, float] | None = None
    ) -> np.ndarray:
        s = self.lib.get(name)
        if s is None:
            return np.zeros(self.dim)
        return self.encoder.encode(task, s, extra)

    # ------------------------------------------------------------------
    @_locked
    def score(
        self, task: str, name: str, extra: dict[str, float] | None = None
    ) -> tuple[float, float, float]:
        """返回 (优先级, 预测收益, 探索奖励)。"""
        phi = self._phi(task, name, extra)
        theta = self.theta
        exploit = float(theta @ phi)
        A_inv_phi = np.linalg.solve(self.A, phi)
        explore = float(self.alpha * math.sqrt(max(0.0, float(phi @ A_inv_phi))))
        return exploit + explore, exploit, explore

    @_locked
    def select(
        self,
        task: str,
        candidates: list[str],
        *,
        extra: dict[str, dict[str, float]] | None = None,
    ) -> tuple[str | None, dict[str, float]]:
        best, best_p, info = None, -1e18, {}
        for n in candidates:
            if self.lib.get(n) is None:
                continue
            p, exploit, explore = self.score(task, n, (extra or {}).get(n))
            if p > best_p:
                best, best_p = n, p
                info = {
                    "priority": round(p, 5),
                    "predicted_reward": round(exploit, 5),
                    "exploration_bonus": round(explore, 5),
                }
        return best, info

    @_locked
    def rank(
        self,
        task: str,
        candidates: list[str],
        *,
        extra: dict[str, dict[str, float]] | None = None,
    ) -> list[tuple[str, float, float, float]]:
        """按优先级排序返回 (name, priority, exploit, explore)，便于对比与可视化。"""
        rows = []
        for n in candidates:
            if self.lib.get(n) is None:
                continue
            p, exploit, explore = self.score(task, n, (extra or {}).get(n))
            rows.append((n, p, exploit, explore))
        rows.sort(key=lambda r: -r[1])
        return rows

    @_locked
    def preview_feedback(self, task: str, rewards: dict[str, float]) -> dict:
        """Bounded association preview on copies; never change the serving policy.

        One trajectory has total weight 0.25, irrespective of its step count.
        This is a diagnostic, not a counterfactual estimate or measured gain.
        """
        valid = {name: float(value) for name, value in rewards.items()
                 if self.lib.get(name) is not None and type(value) in (int, float)
                 and math.isfinite(value) and 0 <= value <= 1}
        state_hash = hashlib.sha256(json.dumps(self.state_dict(), sort_keys=True,
            separators=(',', ':')).encode()).hexdigest()
        original = self.theta
        shadow_A, shadow_b = self.A.copy(), self.b.copy()
        weight = 0.25 / max(1, len(valid))
        vectors = {name: self._phi(task, name) for name in valid}
        for name, phi in vectors.items():
            shadow_A += weight * np.outer(phi, phi)
            shadow_b += weight * valid[name] * phi
        theta = np.linalg.solve(shadow_A, shadow_b)
        return dict(mode='shadow', applied=False, policy_state_sha256=state_hash,
                    rows=[dict(name=name, before=float(original @ phi),
                        after=float(theta @ phi), delta=float((theta-original) @ phi),
                        observed_score=valid[name], weight=weight)
                        for name, phi in vectors.items()])

    @_locked
    def update(
        self,
        task: str,
        name: str,
        reward: float,
        extra: dict[str, float] | None = None,
    ) -> None:
        phi = self._phi(task, name, extra)
        # 共享参数：一次更新会改变 θ，从而影响所有技能的预测分数
        self.A = self.A + np.outer(phi, phi)
        self.b = self.b + reward * phi
        self.n_updates += 1

        s = self.lib.get(name)
        if s is not None:
            s.stats["pulls"] = s.stats.get("pulls", 0) + 1
            s.stats["reward_sum"] = s.stats.get("reward_sum", 0) + reward
            s.stats["best"] = max(s.stats.get("best", 0.0), reward)
            self.lib.dirty = True

    @_locked
    def log(
        self,
        rnd: int,
        name: str,
        predicted: float,
        reward: float,
        reason: str = "",
        exploration: float = 0.0,
        task: str = "",
    ) -> None:
        self.history.append(Pull(rnd, name, predicted, reward, reason, exploration, task))

    @_locked
    def invalidate(self, name: str | None = None) -> None:
        self.encoder.invalidate(name)

    @_locked
    def rebind(self, lib: SkillLibrary) -> None:
        """刷新编码器，保留共享学习器本身，运行中持有它的请求不会丢失反馈。"""
        self.lib = lib
        self.encoder = ContextEncoder(lib, self.dim)

    # ------------------------------------------------------------------
    @_locked
    def best_by_actual(self, candidates: list[str] | None = None) -> Skill | None:
        """按历史实测平均奖励返回最佳技能（COBRA-Skills 的最终输出规则）。
        注意：**不是**按预测分数选。预测只用于安排评估顺序。"""
        pool = candidates or [s.name for s in self.lib]
        scored = [(n, self.lib.get(n)) for n in pool]
        scored = [(n, s) for n, s in scored if s is not None and s.stats.get("pulls", 0) > 0]
        if not scored:
            return None
        scored.sort(key=lambda kv: (-kv[1].mean_reward, -kv[1].stats.get("pulls", 0)))
        return scored[0][1]

    @_locked
    def snapshot(self) -> dict[str, Any]:
        return {
            "policy": self.name,
            "alpha": self.alpha,
            "dim": self.dim,
            "updates": self.n_updates,
            "theta_norm": round(float(np.linalg.norm(self.theta)), 4),
            "pulls": len(self.history),
            "curve": [
                {
                    "round": p.round, "task": p.task, "skill": p.skill,
                    "reward": round(p.reward, 4), "predicted": round(p.predicted, 4),
                    "exploration": round(p.exploration, 4), "reason": p.reason,
                }
                for p in self.history
            ],
            "arm_stats": {
                s.name: {
                    "pulls": int(s.stats.get("pulls", 0)),
                    "mean_reward": round(s.mean_reward, 4),
                    "best": round(s.stats.get("best", 0.0), 4),
                }
                for s in self.lib
                if s.stats.get("pulls", 0) > 0
            },
        }

    # ---- 持久化（共享参数很小，直接存）----
    @_locked
    def state_dict(self) -> dict[str, Any]:
        return {
            "policy": self.name,
            "alpha": self.alpha,
            "dim": self.dim,
            "A": self.A.tolist(),
            "b": self.b.tolist(),
            "n_updates": self.n_updates,
        }

    @_locked
    def load_state(self, st: dict[str, Any]) -> None:
        if not st or st.get("dim") != self.dim:
            return
        self.A = np.array(st["A"], dtype=float)
        self.b = np.array(st["b"], dtype=float)
        self.n_updates = int(st.get("n_updates", 0))


class RandomSelector:
    """消融对照：随机选择候选技能（保留进化、去掉选择策略）。

    它同样实现 `select/update/log/snapshot` 接口，因此可以和 SharedLinUCB 互换。
    注意它的 predicted_reward 恒为 0 —— 这不是 bug，是「无预测能力」的定义。
    """

    name = "random"

    def __init__(self, lib: SkillLibrary, seed: int = 17) -> None:
        self.lib = lib
        self.rng = random.Random(seed)
        self.history: list[Pull] = []
        self.n_updates = 0

    def select(
        self,
        task: str,
        candidates: list[str],
        *,
        extra: dict[str, dict[str, float]] | None = None,
    ) -> tuple[str | None, dict[str, float]]:
        pool = [n for n in candidates if self.lib.get(n)]
        if not pool:
            return None, {}
        return self.rng.choice(pool), {
            "priority": 0.0, "predicted_reward": 0.0, "exploration_bonus": 0.0,
        }

    def rank(
        self,
        task: str,
        candidates: list[str],
        *,
        extra: dict[str, dict[str, float]] | None = None,
    ) -> list[tuple[str, float, float, float]]:
        pool = [n for n in candidates if self.lib.get(n)]
        self.rng.shuffle(pool)
        return [(n, 0.0, 0.0, 0.0) for n in pool]

    def update(
        self, task: str, name: str, reward: float, extra: dict[str, float] | None = None
    ) -> None:
        self.n_updates += 1
        s = self.lib.get(name)
        if s is not None:
            s.stats["pulls"] = s.stats.get("pulls", 0) + 1
            s.stats["reward_sum"] = s.stats.get("reward_sum", 0) + reward
            s.stats["best"] = max(s.stats.get("best", 0.0), reward)

    def log(
        self, rnd: int, name: str, predicted: float, reward: float,
        reason: str = "", exploration: float = 0.0, task: str = "",
    ) -> None:
        self.history.append(Pull(rnd, name, predicted, reward, reason, exploration, task))

    def invalidate(self, name: str | None = None) -> None:
        return None

    def best_by_actual(self, candidates: list[str] | None = None) -> Skill | None:
        pool = candidates or [s.name for s in self.lib]
        scored = [
            (n, self.lib.get(n)) for n in pool
            if self.lib.get(n) is not None and self.lib.get(n).stats.get("pulls", 0) > 0
        ]
        if not scored:
            return None
        scored.sort(key=lambda kv: (-kv[1].mean_reward, -kv[1].stats.get("pulls", 0)))
        return scored[0][1]

    def snapshot(self) -> dict[str, Any]:
        return {
            "policy": self.name,
            "alpha": None,
            "dim": None,
            "updates": self.n_updates,
            "theta_norm": None,
            "pulls": len(self.history),
            "curve": [
                {
                    "round": p.round, "task": p.task, "skill": p.skill,
                    "reward": round(p.reward, 4), "predicted": 0.0,
                    "exploration": 0.0, "reason": p.reason,
                }
                for p in self.history
            ],
            "arm_stats": {
                s.name: {
                    "pulls": int(s.stats.get("pulls", 0)),
                    "mean_reward": round(s.mean_reward, 4),
                    "best": round(s.stats.get("best", 0.0), 4),
                }
                for s in self.lib
                if s.stats.get("pulls", 0) > 0
            },
        }

    def state_dict(self) -> dict[str, Any]:
        return {"policy": self.name}

    def load_state(self, st: dict[str, Any]) -> None:
        return None


# 兼容旧名字：老代码里的 `LinUCB` 现在指向共享参数版本
LinUCB = SharedLinUCB

__all__ = [
    "CTX_DIM", "ContextEncoder", "SharedLinUCB", "RandomSelector", "LinUCB",
    "Pull", "stable_hash", "hashing_bag",
]
