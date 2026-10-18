"""技能数据模型。

对照三篇文献的抽象：
- SkillNet (arXiv:2603.04448) 的三层本体：Taxonomy / Relation Graph / Package，
  以及 Skill Contract（capability / inputs / outputs / use_when）。
- DisCo (arXiv:2609.02749) 的「技能图 + 验证记录」。
- COBRA-Skills (arXiv:2609.11682) 把技能看作可被评估与改写的候选臂。
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

RELATION_TYPES = ("depend_on", "compose_with", "similar_to", "belong_to")
QUALITY_DIMENSIONS = (
    "safety",
    "completeness",
    "executability",
    "maintainability",
    "cost_awareness",
)
GRADES = ("Good", "Average", "Poor")


@dataclass
class SkillContract:
    """技能卡：让检索与关系构建可以只读摘要而不读全文（Fabric 的 contract）。"""

    capability: str = ""
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    use_when: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def flat(self) -> str:
        return " ".join(
            [self.capability, *self.inputs, *self.outputs, *self.use_when]
        )


@dataclass
class Skill:
    """一个可被 Agent 加载执行的技能。"""

    name: str
    description: str
    domain: str
    tags: list[str] = field(default_factory=list)
    capability: str = ""
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    use_when: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    pitfalls: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    quality: dict[str, str] = field(default_factory=dict)
    relations: list[tuple[str, str]] = field(default_factory=list)
    source: str = "seed"
    origin_task: str | None = None       # 由哪条任务蒸馏而来
    parent: list[str] = field(default_factory=list)  # 变异/交叉的父技能
    generation: int = 0                  # 0 = 种子技能
    version: int = 1

    # ---- agentskills.io 规范的可选 frontmatter 字段 ----
    # 补齐它们的好处很实际：技能被分发到别的团队/仓库时，
    # 接收方能一眼看出它需要什么环境、用什么许可、由谁在什么版本产出。
    license: str = "MIT"
    compatibility: str = ""              # 环境要求，如「Python 3.10+，需要网络」
    metadata: dict[str, str] = field(default_factory=dict)  # author / version 等自定义键值
    allowed_tools: str = ""              # 实验性字段：预授权工具，空格分隔

    # ---- 运行期统计（老虎机 / 评估回填）----
    stats: dict[str, float] = field(
        default_factory=lambda: {"pulls": 0.0, "reward_sum": 0.0, "best": 0.0}
    )

    # ------------------------------------------------------------------
    @property
    def contract(self) -> SkillContract:
        return SkillContract(
            capability=self.capability,
            inputs=list(self.inputs),
            outputs=list(self.outputs),
            use_when=list(self.use_when),
        )

    @property
    def mean_reward(self) -> float:
        pulls = self.stats.get("pulls", 0.0)
        return self.stats.get("reward_sum", 0.0) / pulls if pulls else 0.0

    @property
    def uid(self) -> str:
        return hashlib.md5(self.name.encode("utf-8")).hexdigest()[:10]

    # ---- 检索文本（L1 metadata，对标 ADK 渐进披露的第一层）----
    def l1_text(self) -> str:
        """只含 name + description + contract 的轻量检索文本。"""
        return " ".join(
            [
                self.name.replace("-", " "),
                self.description,
                self.domain,
                " ".join(self.tags),
                self.capability,
                " ".join(self.use_when),
            ]
        )

    def l2_text(self) -> str:
        """完整 SKILL.md 正文文本。"""
        return " ".join(
            [self.l1_text(), *self.steps, *self.pitfalls, *self.verification]
        )

    def reference_body(self) -> str:
        """Read attributed community data lazily; never import its executable modules."""
        if self.source != 'github':
            return ''
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        base = (root / 'seed/community/skills').resolve()
        package = (root / self.metadata.get('package_path', '')).resolve()
        if not package.is_relative_to(base):
            return ''
        try:
            raw = (package / 'SKILL.md').read_text(encoding='utf-8-sig')
        except OSError:
            return ''
        match = re.match(r'\A---\s*\n.*?\n---\s*\n(.*)', raw, re.S)
        return match[1] if match else raw

    # ---- 序列化 ----
    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["relations"] = [list(r) for r in self.relations]
        return d

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Skill":
        d = dict(d)
        d["relations"] = [tuple(r) for r in d.get("relations", [])]
        known = {f for f in Skill.__dataclass_fields__}
        return Skill(**{k: v for k, v in d.items() if k in known})

    # ---- 渲染为 SKILL.md（agentskills.io / Claude Code / ADK 通用格式）----
    # ---- 规范符合性自检 ----
    def validate(self) -> list[str]:
        """检查是否符合 agentskills.io 规范，返回问题列表（空列表表示合规）。

        规则来自规范原文：name 1–64 字符、小写字母数字连字符、无首尾或连续连字符，
        且**必须与所在目录名一致**；description 1–1024 字符。
        """
        issues: list[str] = []
        if not (1 <= len(self.name) <= 64):
            issues.append(f"name 长度 {len(self.name)} 超出 1–64")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", self.name or ""):
            issues.append(f"name「{self.name}」不符合 kebab-case（小写字母/数字/连字符）")
        if not (1 <= len(self.description) <= 1024):
            issues.append(f"description 长度 {len(self.description)} 超出 1–1024")
        if self.compatibility and len(self.compatibility) > 500:
            issues.append(f"compatibility 长度超出 500（实际 {len(self.compatibility)}）")
        return issues

    @property
    def body_stats(self) -> dict[str, int]:
        """正文规模。规范建议正文控制在 ~500 行 / ~5000 token 以内，
        超出的内容应拆到 references/ 按需加载。"""
        md = self.to_skill_md()
        body = md.split("---\n", 2)[-1] if md.startswith("---") else md
        lines = body.count("\n") + 1
        # 中文按 1 字 ≈ 1 token 的保守估计，英文按 4 字符 ≈ 1 token
        cjk = sum(1 for ch in body if "\u4e00" <= ch <= "\u9fff")
        other = len(body) - cjk
        return {"lines": lines, "tokens_est": cjk + other // 4}

    def to_skill_md(self) -> str:
        # frontmatter 顺序：必填字段在前，可选项在后
        fm: dict[str, Any] = {"name": self.name, "description": self.description}
        if self.license:
            fm["license"] = self.license
        if self.compatibility:
            fm["compatibility"] = self.compatibility
        if self.allowed_tools:
            fm["allowed-tools"] = self.allowed_tools

        meta = dict(self.metadata)
        meta.setdefault("domain", self.domain)
        meta.setdefault("generation", str(self.generation))
        meta.setdefault("source", self.source)
        if meta:
            fm["metadata"] = meta

        lines = ["---"]
        for k, v in fm.items():
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        lines.append("---")
        lines.append("")
        original = self.reference_body()
        if original:
            return '\n'.join(lines) + original.rstrip() + '\n'
        lines.append(f"# {self.name}")
        lines.append("")
        lines.append(f"> 领域：{self.domain}　|　来源：{self.source}"
                     f"　|　代际：G{self.generation}")
        lines.append("")
        lines.append("## 能力契约 / Capability")
        lines.append("")
        lines.append(self.capability)
        lines.append("")
        lines.append("**输入**：" + "；".join(self.inputs))
        lines.append("")
        lines.append("**输出**：" + "；".join(self.outputs))
        lines.append("")
        lines.append("**适用时机**：")
        lines.extend(f"- {u}" for u in self.use_when)
        lines.append("")
        lines.append("## 执行步骤")
        lines.append("")
        for i, s in enumerate(self.steps, 1):
            lines.append(f"{i}. {s}")
        if self.pitfalls:
            lines.append("")
            lines.append("## 常见陷阱")
            lines.append("")
            lines.extend(f"- {p}" for p in self.pitfalls)
        if self.verification:
            lines.append("")
            lines.append("## 验证清单")
            lines.append("")
            lines.extend(f"- [ ] {v}" for v in self.verification)
        if self.tags:
            lines.append("")
            lines.append("## 标签")
            lines.append("")
            lines.append("`" + "` `".join(self.tags) + "`")
        if self.quality:
            lines.append("")
            lines.append("## 质量评估")
            lines.append("")
            lines.append("| 维度 | 评级 |")
            lines.append("| --- | --- |")
            for dim in QUALITY_DIMENSIONS:
                lines.append(f"| {dim} | {self.quality.get(dim, 'Average')} |")
        if self.relations:
            lines.append("")
            lines.append("## 关联技能")
            lines.append("")
            for rel, target in self.relations:
                lines.append(f"- `{rel}` → `{target}`")
        if self.parent:
            lines.append("")
            lines.append(f"<!-- 演化自：{', '.join(self.parent)} -->")
        return "\n".join(lines) + "\n"


def quality_score(quality: dict[str, Any]) -> float:
    """把五维评级折算成 0-1 的权重，用于检索排序的先验。

    兼容两种形态：`{"safety": "Good"}` 与
    `{"safety": {"level": "Good", "reason": "..."}}`（后者是 `assess_quality` 的输出）。
    """
    grade = {"Good": 1.0, "Average": 0.6, "Poor": 0.25}
    if not quality:
        return 0.6
    vals: list[float] = []
    for d in QUALITY_DIMENSIONS:
        v = quality.get(d)
        if isinstance(v, dict):
            v = v.get("level")
        vals.append(grade.get(v, 0.6))
    return sum(vals) / len(vals) if vals else 0.6


# 危险操作关键词。技能会在沙箱里被执行，且会被导出给别的 Agent 直接遵循，
# 因此在准入阶段就扫一遍语义级风险（对应 SkillNet 五维里的 Safety）。
_DANGEROUS_KEYWORDS = (
    "rm -rf", "sudo rm", "删除文件", "永久删除", "格式化", "drop table",
    "drop database", "覆盖原文件", "清空数据库", "关闭防火墙", "导出密钥",
)
_VAGUE_KEYWORDS = ("根据需要", "酌情", "适当调整", "视情况而定", "等等", "若干", "尽量")
_CONCRETE_RE = re.compile(
    r"\d|[A-Za-z]{2,}|`|参数|阈值|版本|格式|API|工具|库|软件|模型|命令|函数"
)
_COST_KEYWORDS = ("算力", "显存", "耗时", "成本", "预算", "小时", "分钟", "样本量", "token", "内存")


def assess_quality(skill: "Skill") -> dict[str, dict[str, str]]:
    """对技能做启发式五维评估，每个维度给出**等级 + 理由**。

    为什么需要它：进化生成的新技能原先一律被写成 `Average`，
    这会让 `quality_score()` 的质量先验退化成常数，检索排序里的质量加权完全失效。

    为什么要带理由：对齐 `skillnet-ai` 官方 `evaluate()` 的输出形态
    （`{"safety": {"level": "Good", "reason": "..."}}`）。
    只有等级没有理由时，人在复核时无法判断这个等级是怎么来的。

    这里刻意不调用大模型：准入发生在每次技能生成时，规则法足够区分
    「明显有问题」与「结构完整」，且成本为零、结果可复现。
    """
    text = " ".join([skill.description, skill.capability, *skill.steps, *skill.pitfalls])
    out: dict[str, dict[str, str]] = {}

    # 1) 安全性
    hits = [w for w in _DANGEROUS_KEYWORDS if w in text]
    out["safety"] = {
        "level": "Poor" if hits else "Good",
        "reason": f"命中危险操作关键词 {hits[:2]}" if hits else "未见危险系统操作或越权指令",
    }

    # 2) 完整性
    n_steps, n_pit, n_ver = len(skill.steps), len(skill.pitfalls), len(skill.verification)
    if n_steps >= 4 and n_pit >= 2 and n_ver >= 2:
        out["completeness"] = {
            "level": "Good",
            "reason": f"{n_steps} 个步骤 + {n_pit} 条陷阱 + {n_ver} 条验证，覆盖完整",
        }
    elif n_steps >= 3 and (n_pit or n_ver):
        out["completeness"] = {
            "level": "Average",
            "reason": f"{n_steps} 个步骤，但陷阱({n_pit})或验证({n_ver})偏少",
        }
    else:
        out["completeness"] = {
            "level": "Poor",
            "reason": f"步骤/陷阱/验证不足（{n_steps}/{n_pit}/{n_ver}）",
        }

    # 3) 可执行性
    concrete = sum(1 for s in skill.steps if _CONCRETE_RE.search(s))
    ratio = concrete / max(1, n_steps)
    vague = [w for w in _VAGUE_KEYWORDS if w in text]
    if ratio >= 0.8 and not vague:
        out["executability"] = {
            "level": "Good",
            "reason": f"{concrete}/{n_steps} 个步骤含具体工具或参数，无模糊表述",
        }
    elif ratio >= 0.5:
        tail = f"，但含模糊词 {vague[:2]}" if vague else ""
        out["executability"] = {
            "level": "Average", "reason": f"{concrete}/{n_steps} 个步骤具体可执行{tail}"
        }
    else:
        out["executability"] = {
            "level": "Poor", "reason": f"仅 {concrete}/{n_steps} 个步骤给出具体做法，偏抽象"
        }

    # 4) 可维护性
    n_rel = len(skill.relations)
    if n_rel and n_steps <= 12:
        out["maintainability"] = {
            "level": "Good", "reason": f"与 {n_rel} 个技能建立关联，步骤数适中"
        }
    elif n_rel:
        out["maintainability"] = {
            "level": "Average", "reason": f"有关联但步骤偏多（{n_steps}），局部修改成本高"
        }
    else:
        out["maintainability"] = {
            "level": "Average", "reason": "未与其他技能建立关系，可能孤立"
        }

    # 5) 成本感知
    cost_hits = [w for w in _COST_KEYWORDS if w in text]
    out["cost_awareness"] = {
        "level": "Good" if cost_hits else "Average",
        "reason": f"提及资源约束 {cost_hits[:3]}" if cost_hits else "未说明资源或耗时约束",
    }
    return out


def dedup_key(skill: Skill) -> str:
    return hashlib.md5(skill.to_skill_md().encode("utf-8")).hexdigest()


def iter_targets(skills: Iterable[Skill]) -> list[str]:
    return [s.name for s in skills]
