"""SkillNet 完整语料：种子 76 + 社区 1769 + 演化 36 = 1881 个技能。

数据位置：`resources/skillnet/`（由 `scripts/import_skillnet.py` 从
skillnet-demo 一次性导入，含社区资源包与训练产物）。

设计约束（与 demo 一致）：
- 社区数据按**只读资料**处理：正文与资源文件按需懒加载，绝不 import 其
  Python 模块；资源读取带 sha256 完整性校验。
- 关系图只收录目录声明（depend_on / compose_with / similar_to），
  规范化规则与 demo 相同：depend_on 优先，双向 compose_with 去重。
- 演化技能与运行统计来自 `evolved.json`（library.json 的导入副本）。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import threading
from pathlib import Path
from typing import Any

from .skillnet.schema import Skill

CORPUS = Path(__file__).resolve().parents[1] / "resources" / "skillnet"

SEED_CATALOG = CORPUS / "seed/catalog_data.py"
SEED_BUSINESS = CORPUS / "seed/business_skills.py"
COMMUNITY_CATALOG = CORPUS / "community/catalog.json"
COMMUNITY_PACKAGES = CORPUS / "community/packages.json"
EVOLVED = CORPUS / "evolved.json"
MANIFEST = CORPUS / "manifest.json"

MAX_BODY_CHARS = 400_000

_lock = threading.RLock()
_cache: dict[str, Any] | None = None


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载数据模块：{path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # 纯数据模块，无可执行副作用
    return module


def _read_manifest() -> dict[str, Any]:
    if not MANIFEST.is_file():
        return {}
    try:
        return json.loads(MANIFEST.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _verify_seed_modules(manifest: dict[str, Any]) -> None:
    """种子数据模块经 importlib 执行，必须与 manifest 登记的 sha256 一致。

    与社区资源的完整性校验同标准：未登记者无法校验（旧 manifest），
    登记了但对不上的一律拒绝加载，避免被篡改的数据模块进入技能库。
    """
    declared = manifest.get("seed_modules")
    if not isinstance(declared, dict) or not declared:
        return
    for relative, expected in declared.items():
        path = (CORPUS / relative).resolve()
        if not path.is_relative_to(CORPUS) or not path.is_file():
            raise ValueError(f"种子模块缺失或路径非法：{relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"种子模块完整性检查失败：{relative}")


def _remap_package_path(metadata: dict) -> dict:
    """把 demo 相对路径（seed/community/skills/<name>）改写到本仓库语料根下。"""
    meta = dict(metadata or {})
    package = str(meta.get("package_path") or "")
    if package.startswith("seed/community/skills/"):
        meta["package_path"] = package[len("seed/") :]
    return meta


def _normalize_relations(skills: list[Skill]) -> int:
    """与 demo `normalize_relations` 相同：depend_on 优先 + 双向 compose 去重。"""
    by = {s.name: s for s in skills}
    removed = 0
    for s in skills:
        for rel, tgt in list(s.relations):
            if rel != "depend_on":
                continue
            other = by.get(tgt)
            if not other:
                continue
            before = len(other.relations)
            other.relations = [
                (r, t)
                for r, t in other.relations
                if not (t == s.name and r in ("compose_with", "depend_on"))
            ]
            removed += before - len(other.relations)
    for s in skills:
        for rel, tgt in list(s.relations):
            if rel != "compose_with":
                continue
            other = by.get(tgt)
            if not other:
                continue
            if any(r == "compose_with" and t == s.name for r, t in other.relations):
                if s.name < tgt:
                    continue
                s.relations = [
                    (r, t) for r, t in s.relations if not (r == "compose_with" and t == tgt)
                ]
                removed += 1
    return removed


def _apply_stats(skills: list[Skill], stats: dict) -> None:
    for skill in skills:
        st = stats.get(skill.name)
        if isinstance(st, dict):
            skill.stats = {**skill.stats, **st}


def _build() -> dict[str, Any]:
    if not CORPUS.is_dir():
        raise FileNotFoundError(
            "SkillNet 语料未导入：请先运行 backend/scripts/import_skillnet.py"
        )
    manifest = _read_manifest()
    _verify_seed_modules(manifest)
    skills: list[Skill] = []

    # 1) 种子技能（结构化目录数据 + 业务技能补充）
    raw: list[dict] = []
    for path, name in ((SEED_CATALOG, "skillnet_seed_catalog"), (SEED_BUSINESS, "skillnet_seed_business")):
        if path.is_file():
            raw.extend(_load_module(path, name).RAW)
    skills.extend(Skill(**{k: v for k, v in item.items()}) for item in raw)

    # 2) 社区技能（catalog.json，source=github）
    community = 0
    if COMMUNITY_CATALOG.is_file():
        for item in json.loads(COMMUNITY_CATALOG.read_text("utf-8")):
            try:
                skill = Skill.from_dict(item)
            except (TypeError, ValueError):
                continue
            skill.metadata = _remap_package_path(skill.metadata)
            skills.append(skill)
            community += 1

    # 3) 演化技能与运行统计（evolved.json；缺省回退基线快照）
    evolved = 0
    stats: dict[str, Any] = {}
    for candidate in (EVOLVED, EVOLVED.with_name("evolved.baseline.json")):
        if not candidate.is_file():
            continue
        try:
            data = json.loads(candidate.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for entry in data.get("evolved") or []:
            try:
                skills.append(Skill.from_dict(entry))
                evolved += 1
            except (TypeError, ValueError):
                continue
        stats = data.get("stats") or {}
        break

    # 4) 关系目标存在性校验 + 规范化
    names = {s.name for s in skills}
    dropped = 0
    for skill in skills:
        valid = [(rel, tgt) for rel, tgt in skill.relations if tgt in names]
        dropped += len(skill.relations) - len(valid)
        skill.relations = valid
    removed = _normalize_relations(skills)
    _apply_stats(skills, stats)

    domains = sorted({s.domain for s in skills if s.domain})
    status = {
        "available": True,
        "skills": len(skills),
        "seed": sum(1 for s in skills if s.source == "seed"),
        "community": community,
        "evolved": evolved,
        "domains": len(domains),
        "domain_names": domains,
        "edges": sum(len(s.relations) for s in skills),
        "relations_dropped": dropped,
        "relations_normalized": removed,
        "manifest": manifest,
    }
    return {"skills": skills, "status": status}


def load(force: bool = False) -> dict[str, Any]:
    """加载（并缓存）语料。失败时抛出，由调用方决定降级。"""
    global _cache
    with _lock:
        if _cache is None or force:
            _cache = _build()
        return _cache


def relation_edges() -> list[dict[str, str]]:
    corpus = load()
    present = {s.name for s in corpus["skills"]}
    return [
        {"source": s.name, "target": tgt, "type": rel}
        for s in corpus["skills"]
        for rel, tgt in s.relations
        if tgt in present
    ]


# ----------------------------------------------------------------------
# 正文与资源（懒加载 + 完整性校验）
# ----------------------------------------------------------------------

def _strip_frontmatter(text: str) -> str:
    match = re.match(r"\A---\s*\n.*?\n---\s*\n(.*)", text, re.S)
    return match[1] if match else text


def _package_dir(skill: Skill) -> Path | None:
    package = str(skill.metadata.get("package_path") or "")
    if not package:
        # 种子技能：包目录按名字约定
        candidate = CORPUS / "seed/skills" / skill.name
        return candidate if candidate.is_dir() else None
    base = (CORPUS / package).resolve()
    root = CORPUS.resolve()
    if not base.is_relative_to(root) or not base.is_dir():
        return None
    return base


def _read_package_file(skill: Skill, relative: str) -> bytes | None:
    directory = _package_dir(skill)
    if directory is None:
        return None
    target = (directory / relative).resolve()
    if not target.is_relative_to(directory.resolve()):
        return None
    try:
        return target.read_bytes()
    except OSError:
        return None


def body(skill: Skill) -> str:
    """技能正文：社区/种子读 SKILL.md，演化技能按结构化数据渲染。"""
    if skill.source != "github":
        if skill.steps or skill.capability:
            rendered = skill.to_skill_md()
            if rendered.strip():
                return _strip_frontmatter(rendered)
    raw = _read_package_file(skill, "SKILL.md")
    if raw is None:
        return skill.to_skill_md()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return skill.to_skill_md()
    if len(text) > MAX_BODY_CHARS:
        text = text[:MAX_BODY_CHARS]
    return _strip_frontmatter(text)


def package_manifest(skill: Skill) -> dict | None:
    """社区资源包完整性清单（packages.json 中该技能的条目）。"""
    if skill.source != "github" or not COMMUNITY_PACKAGES.is_file():
        return None
    try:
        packages = json.loads(COMMUNITY_PACKAGES.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    entry = packages.get(skill.name)
    if not isinstance(entry, dict):
        return None
    return {
        "name": entry.get("name"),
        "repository": entry.get("repository"),
        "commit": entry.get("commit"),
        "source_url": entry.get("source_url"),
        "license": entry.get("license"),
        "skill_md_sha256": entry.get("skill_md_sha256"),
        "files": [
            {"path": f.get("path"), "bytes": f.get("bytes"), "sha256": f.get("sha256")}
            for f in entry.get("files") or []
            if isinstance(f, dict) and f.get("path")
        ],
    }


def read_resource(skill: Skill, path: str) -> tuple[bytes, dict]:
    """按清单校验后读取社区资源文件；任何不一致都拒绝交付。"""
    if not isinstance(path, str) or not path or len(path) > 400:
        raise ValueError("资源路径无效")
    if path.startswith("/") or ".." in path.replace("\\", "/").split("/") or ":" in path:
        raise ValueError("资源路径无效")
    manifest = package_manifest(skill)
    if manifest is None:
        raise ValueError("此技能没有已登记的资源包")
    item = next((f for f in manifest["files"] if f["path"] == path), None)
    if item is None:
        raise ValueError("资源未列入已核对清单")
    raw = _read_package_file(skill, path)
    if raw is None:
        raise FileNotFoundError("资源不存在")
    if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
        raise ValueError("资源完整性检查失败")
    return raw, item


# ----------------------------------------------------------------------
# 网络模型（训练产物状态，诚实呈现）
# ----------------------------------------------------------------------

_ADAPTER_CACHE: dict[str, Any] | None = None


def adapter_shadow_probe(version: str = "network-model-v2") -> dict:
    """适配器只读探针：验证封存权重 + 表示漂移对照。**绝不参与排序。**

    - numpy 不可用：返回 available=False（探针是增强信息，不是前提）；
    - 校验 model.npz 的 sha256 与 manifest 声明一致；
    - 交叉核对秩 / 维度 / 参数量与 manifest 声明；
    - 逐个低秩投影（q/s/g）以原始强度施加到封存 catalog 特征，
      报告平均余弦漂移——这是"若启用会怎样"的对照数值。
      线上 recommended_shadow_alpha=0，即零强度、零影响、零收益。
    """
    global _ADAPTER_CACHE
    if _ADAPTER_CACHE is not None:
        return _ADAPTER_CACHE
    directory = CORPUS / version
    manifest_path = directory / "manifest.json"
    weights_path = directory / "model.npz"
    catalog_path = directory / "catalog.npz"
    if not (manifest_path.is_file() and weights_path.is_file() and catalog_path.is_file()):
        return {"available": False, "reason": "适配器产物不完整"}
    try:
        import numpy as np
    except ImportError:
        return {"available": False, "reason": "numpy 未安装，跳过适配器探针"}
    try:
        manifest = json.loads(manifest_path.read_text("utf-8"))
        weights = np.load(weights_path)
        catalog = np.load(catalog_path)
    except (OSError, ValueError):
        return {"available": False, "reason": "适配器产物读取失败"}
    digest = hashlib.sha256(weights_path.read_bytes()).hexdigest()
    rank = int(manifest.get("rank") or 0)
    dimension = int(manifest.get("dimension") or 0)
    declared_params = int(manifest.get("trainable_parameters") or 0)
    pairs = {name: (weights[f"{name}_down"], weights[f"{name}_up"]) for name in ("q", "s", "g")}
    structural = {
        "rank": rank,
        "dimension": dimension,
        "shapes_ok": all(
            down.shape == (dimension, rank) and up.shape == (rank, dimension)
            for down, up in pairs.values()
        ),
        "parameters_actual": int(sum(int(a.size) + int(b.size) for a, b in pairs.values()))
        + int(weights["relation_logits"].size),
        "parameters_declared": declared_params,
        "weights_sha256_ok": digest == manifest.get("weights_sha256"),
    }
    features = np.asarray(catalog["features"], dtype=np.float32)
    try:
        corpus_skills = len(load()["skills"])
    except Exception:  # 探针不依赖语料加载成功
        corpus_skills = None
    drift: dict[str, Any] = {}
    for name, (down, up) in pairs.items():
        adapted = features + features @ down @ up
        numerator = np.sum(features * adapted, axis=1)
        denominator = np.linalg.norm(features, axis=1) * np.linalg.norm(adapted, axis=1)
        cosine = float(np.mean(numerator / np.maximum(denominator, 1e-9)))
        drift[name] = round(cosine, 4)
    probe = {
        "available": True,
        "version": version,
        "weights_sha256_ok": structural["weights_sha256_ok"],
        "structural": structural,
        "catalog_rows": int(features.shape[0]),
        "corpus_skills": corpus_skills,
        "relation_logits": [round(float(v), 4) for v in weights["relation_logits"]],
        "drift_cosine": drift,
        "note": (
            "漂移是原始低秩增量以强度 1 施加的对照；线上 recommended_shadow_alpha=0，"
            "适配器不参与排序，其分数也不是成功概率。"
        ),
    }
    _ADAPTER_CACHE = probe
    return probe


def network_model_card() -> dict:
    """network-model-v2 适配器的模型卡。

    它是 LoRA 式适配器（E5-small 之上 rank-48 增量，110,596 个可训练参数），
    manifest 明确标注 `research_candidate_not_admitted` 且
    `recommended_shadow_alpha = 0.0`：**不作为排序依据**，只作为研究产物
    随语料一起交付，供复现实验使用。`probe` 是只读结构探针（权重校验 +
    表示漂移对照），同样不参与任何路由决策。
    """
    card: dict[str, Any] = {"available": False, "versions": []}
    for version in ("network-model", "network-model-v2"):
        directory = CORPUS / version
        manifest_path = directory / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            data = json.loads(manifest_path.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        card["available"] = True
        entry = {
            "version": version,
            "stage": data.get("stage"),
            "model_id": data.get("model_id"),
            "encoder": data.get("encoder", {}).get("repository"),
            "dimension": data.get("dimension"),
            "rank": data.get("rank"),
            "trainable_parameters": data.get("trainable_parameters"),
            "selected_epoch": data.get("selected_epoch"),
            "recommended_shadow_alpha": data.get("recommended_shadow_alpha"),
            "score_kind": data.get("score_kind"),
            "weights_sha256": data.get("weights_sha256"),
        }
        if version == "network-model-v2":
            entry["probe"] = adapter_shadow_probe(version)
        card["versions"].append(entry)
    return card
