from __future__ import annotations

import json
import re
import threading
from pathlib import Path

import yaml

from .config import ROOT
from . import skillnet_corpus
from .skillnet.catalog import SkillLibrary
from .skillnet.index import BM25Index, weighted_fuse
from .skillnet.semantic import make_index, DENSE_WEIGHTS, WEIGHTS
from .skillnet.schema import Skill
from .skillnet.bandit import SharedLinUCB
from .skill_packages import SkillPackages

BUILTINS = [
    (
        "server-deployment",
        "服务器部署",
        "从 GitHub 仓库检查构建方式，使用 Docker Compose Nginx HTTPS 部署网站并核验健康状态",
        "运维",
        ["list_servers", "run_remote_command", "deploy_repository"],
        [],
    ),
    (
        "private-documents",
        "私人资料",
        "搜索私人文件 文档 PDF Word Markdown CSV，引用原始文件片段回答问题",
        "资料",
        ["search_documents", "read_document", "copy_document_to_workspace"],
        [],
    ),
    (
        "coding-workspace",
        "代码工作区",
        "编写修改代码 创建文件 分析仓库运行测试 修复错误",
        "开发",
        ["list_files", "read_file", "write_file", "execute_command", "publish_file"],
        [],
    ),
    (
        "scientific-plotting",
        "数据绘图",
        "读取 CSV 表格 销售数据 选择质感参考图 绘制趋势 折线 柱状 散点 分布图 导出 PNG PDF 可复现脚本",
        "绘图",
        ["plot_csv_tool", "list_gallery", "read_plot_resource"],
        [("depend_on", "private-documents")],
    ),
    (
        "personal-content",
        "个人内容",
        "管理文章 合集 相册 诗词 简历 保存内容草稿",
        "内容",
        ["search_content", "create_content_draft"],
        [],
    ),
    (
        "owner-memory",
        "主人记忆",
        "记住主人的偏好 习惯 项目事实 长期记忆",
        "记忆",
        ["list_memories", "remember"],
        [],
    ),
    (
        "gathered-scenes-zine",
        "拾景 · 图片转换",
        "将照片进行实景拼贴或影像蒸馏，生成有纸张质感的 zine 海报 图片风格转换",
        "图片",
        ["transform_image_tool"],
        [],
    ),
]

_ZINE_TITLES = {
    "scene-distillation-zine-v1-3": "拾景 · 影像蒸馏",
    "scenes-gathered-zine-v1-3": "拾景 · 实景拼贴",
}
_ZINE_DESCRIPTIONS = {
    "scene-distillation-zine-v1-3": "从照片提炼情绪、形状和色彩，以源自原图的插画重新构成留白充足的独立海报。",
    "scenes-gathered-zine-v1-3": "保留真实照片，结合撕纸边缘、简化插画和纸张质感，制作安静的实景拼贴海报。",
}

# 社区技能 id 形如 gh-scientific-13c-metabolic-flux-d6d252：
# 展示时去掉 gh- 前缀与末尾的内容寻址短哈希，只保留可读主干。
_ID_HASH_SUFFIX = re.compile(r"-[0-9a-f]{6,}$")


def _trim_skill_id(name: str) -> str:
    trimmed = _ID_HASH_SUFFIX.sub("", name)
    if trimmed.startswith("gh-"):
        trimmed = trimmed[3:]
    return trimmed or name


# Task-shaped contracts improve the encoder input; no duplicated description.
# These are activation examples, not execution certification or extra authority.
CONTRACTS = {
    "server-deployment": [
        "把 GitHub 上的项目上线，发布网站，部署云服务器",
        "配置域名、HTTPS、Docker Compose，排查网站服务故障",
        "Deploy a GitHub repository to a server and check website health",
    ],
    "private-documents": [
        "阅读上传的 PDF、Word、扫描资料或文档，提炼内容并引用来源",
        "从私人文件查找问题的答案，检查完整文档而非只看开头",
        "Read and summarize private documents with citations",
    ],
    "coding-workspace": [
        "在本地电脑创建或修改程序，修复 Python、JavaScript 等代码，运行测试",
        "检查本地仓库，编写脚本，整理工程文件",
        "Write code, fix a bug, run tests, inspect a local repository",
    ],
    "scientific-plotting": [
        "把月度销售额、实验结果等 CSV 数据画成折线图、柱状图或散点图",
        "查看图表参考样式，输出可下载图片、PDF 和可复现代码",
        "Visualize monthly revenue in a line chart; plot scientific data",
        "Turn measurements into a scatter diagram, bar chart or distribution plot",
        "Plot CSV data and export the chart with a reproducible script",
    ],
    "personal-content": [
        "编辑个人文章、合集、诗词、相册和简历，保存新的内容草稿",
        "查找已写的文章或整理作品集",
        "Manage personal posts, albums, poems and resume content",
    ],
    "owner-memory": [
        "用户明确要求记住偏好或事实，留待以后使用",
        "查看已经保存的长期记忆",
        "记住我喜欢的颜色、习惯、偏好和项目事实，以后用得上",
        "Explicitly remember a preference or recall stored long-term memory",
        "Remember my favorite colors, habits and facts for later use",
    ],
    "gathered-scenes-zine": [
        "把照片转换为拼贴海报、纸张质感 zine 或插画，处理图片风格",
        "Transform a photograph into an illustrated zine or collage",
    ],
}


# 平台可执行技能（注册了工具）的路由优先分。
# SkillNet 语料是只读参考资料：没有平台工具的技能无法真正执行任务，
# 检索分接近时，优先把能办事的技能交给本轮。这是路由先验，
# 不构成对任何技能执行能力的认证。
EXECUTABLE_PRIOR = 0.06


class SkillRouter:
    def __init__(self, store):
        self.store = store
        self.lock = threading.RLock()
        self.directory = store.directory / "skills"
        self.directory.mkdir(exist_ok=True)
        self.corpus_status = {"available": False, "reason": "尚未加载"}
        self.refresh()

    # ---- SkillNet 完整语料（resources/skillnet/，1881 个技能）----
    def _corpus_skills(self):
        """加载完整技能语料；缺失或损坏时平台仍以自有技能启动。"""
        try:
            corpus = skillnet_corpus.load()
        except Exception as exc:  # 语料是增强项，不是启动前提
            self.corpus_status = {"available": False, "reason": type(exc).__name__}
            return []
        status = dict(corpus["status"])
        status.pop("domain_names", None)
        self.corpus_status = status
        return corpus["skills"]

    def _display_name(self, skill: Skill) -> str:
        for builtin in BUILTINS:
            if builtin[0] == skill.name:
                return builtin[1]
        if skill.name in _ZINE_TITLES:
            return _ZINE_TITLES[skill.name]
        if skill.name in self.packages.cards:
            return self.packages.cards[skill.name].get("name", skill.name)
        if skill.source in ("seed", "github") or skill.generation > 0:
            return _trim_skill_id(skill.name)
        return skill.name

    def _github_assets(self, skill: Skill) -> tuple[list, dict]:
        """社区（github）技能的资源清单与来源信息；非社区技能返回空。"""
        if skill.source != "github":
            return [], {}
        manifest = skillnet_corpus.package_manifest(skill) or {}
        resources = manifest.get("files", [])
        provenance = {
            key: skill.metadata.get(key)
            for key in ("repository", "commit", "source_url", "license")
        }
        return resources, provenance

    def refresh(self):
        with self.lock:
            skills, bodies, tools = [], {}, {}
            for name, title, description, domain, tool_names, relations in BUILTINS:
                skill = Skill(
                    name=name,
                    description=description,
                    domain=domain,
                    capability=title,
                    tags=[domain],
                    use_when=CONTRACTS[name],
                    relations=relations,
                )
                skills.append(skill)
                bodies[name] = (
                    f"# {title}\n\n{description}\n\n只调用平台注册的工具。先检查输入和授权，记录真实结果。不能用推测代替实际执行验收。\n\n工具：{', '.join(tool_names)}"
                )
                tools[name] = tool_names
            plot_entry = ROOT / "resources/plot/SKILL.md"
            if plot_entry.exists():
                bodies["scientific-plotting"] = (
                    plot_entry.read_text(encoding="utf-8")
                    + "\n\n平台工具：plot_csv_tool 生成基础图表，list_gallery 查看样图，read_plot_resource 按相对路径读取样式卡、阶段说明与参考脚本。复杂图可用 copy_document_to_workspace 读取所选 CSV，在获准完整权限后编写脚本执行，publish_file 交付实际生成的文件。"
                )
            self.packages = SkillPackages()
            builtin_tools = dict(tools)
            for card in self.packages.cards.values():
                name, base = card["id"], card["base_skill"]
                skills.append(
                    Skill(
                        name=name,
                        description=card["description"],
                        domain=card["domain"],
                        tags=[card["domain"]],
                        capability=card["name"],
                        use_when=[card["original_description"]],
                        relations=[("depend_on", base)],
                        source="github",
                        license=card["license"],
                    )
                )
                # Full reference bodies are loaded lazily and rehashed on every read.
                tools[name] = list(builtin_tools[base])
            for path in sorted(self.directory.glob("*/SKILL.md")):
                text = path.read_text(encoding="utf-8")
                if len(text) > 150000:
                    continue
                header = (
                    yaml.safe_load(text.split("---", 2)[1])
                    if text.startswith("---")
                    else {}
                )
                name = (header or {}).get("name", path.parent.name)
                if not isinstance(name, str) or not re.fullmatch(
                    r"[a-z0-9]+(?:-[a-z0-9]+)*", name
                ):
                    continue
                skills.append(
                    Skill(
                        name=name,
                        description=str((header or {}).get("description", "")),
                        domain="图片" if "zine" in name else "自定义",
                        capability=str((header or {}).get("description", "")),
                    )
                )
                bodies[name] = text
                tools[name] = ["transform_image_tool"] if "zine" in name else []
            # SkillNet 完整语料：1881 个技能（种子 / 社区 / 演化）
            corpus = self._corpus_skills()
            if corpus:
                present = {s.name for s in skills}
                for skill in corpus:
                    if skill.name in present:
                        continue
                    skills.append(skill)
                    tools[skill.name] = []
            self.library = SkillLibrary(skills)
            self.bodies, self.tools = bodies, tools
            self.bm25 = BM25Index()
            if not hasattr(self, "vector"):
                self.vector = make_index(self.store.directory)
            ids = [s.name for s in skills]
            texts = [s.l1_text() for s in skills]
            self.bm25.fit(ids, texts)
            self.vector.fit(ids, texts)
            self.bandit = SharedLinUCB(self.library)
            state = self.store.setting("skill-policy")
            if state:
                try:
                    self.bandit.load_state(state)
                except (ValueError, KeyError, TypeError):
                    pass

    def all(self):
        with self.lock:
            cards = self.packages.cards
            result = []
            for s in self.library:
                name = self._display_name(s)
                description = _ZINE_DESCRIPTIONS.get(s.name, s.description)
                result.append(
                    {
                        "id": s.name,
                        "name": name,
                        "description": description,
                        "domain": s.domain,
                        "tools": self.tools[s.name],
                        "relations": s.relations,
                        "source": "skillnet-community"
                        if s.name in cards
                        else (
                            "personal"
                            if s.domain in {"图片", "自定义"}
                            and s.name not in {b[0] for b in BUILTINS}
                            else "xinxin"
                        ),
                        "provenance": {
                            key: cards[s.name][key]
                            for key in (
                                "repository",
                                "revision",
                                "source_url",
                                "license",
                                "execution_verified",
                            )
                        }
                        if s.name in cards
                        else None,
                        "enabled": True,
                        # SkillNet 语料分层：seed / github / 演化代际
                        "corpus_source": s.source,
                        "generation": s.generation,
                        "capability": s.capability,
                        "tags": list(s.tags),
                        "stats": {
                            "pulls": int(s.stats.get("pulls", 0) or 0),
                            "best": round(float(s.stats.get("best", 0) or 0), 3),
                            "mean_reward": round(s.mean_reward, 3)
                            if s.stats.get("pulls")
                            else None,
                        },
                        "license": s.license,
                    }
                )
            return result

    def search(self, query, k=4):
        with self.lock:
            bm25 = self.bm25.search(query, top_k=20)
            vector = self.vector.search(query, top_k=20)
            structural = self._structural_hits(query)
            weights = self.status()["weights"]
            fused = weighted_fuse(
                [bm25, vector, structural],
                weights,
            )
            fused = [
                (name, score + (EXECUTABLE_PRIOR if self.tools.get(name) else 0.0))
                for name, score in fused
            ]
            if self.bandit.n_updates:
                fused = sorted(
                    [
                        (name, score + 0.1 * self.bandit.score(query, name)[0])
                        for name, score in fused
                    ],
                    key=lambda item: -item[1],
                )
            # An explicit registered ID from the skill chooser is an intentional
            # selection, not a grant of authority or evidence of execution.
            # 先用子串粗筛（C 速度），再对候选做边界校验，避免为上千个技能
            # 逐个编译正则。
            query_lower = query.lower()
            explicit = [
                s.name
                for s in self.library
                if s.name in query_lower
                and re.search(
                    r"(?<![a-z0-9-])" + re.escape(s.name) + r"(?![a-z0-9-])",
                    query_lower,
                )
            ]
            if explicit:
                lookup = dict(fused)
                fused = [(name, lookup.get(name, 0)) for name in explicit] + [
                    (name, score) for name, score in fused if name not in explicit
                ]
            by_name = {s["id"]: s for s in self.all()}
            channels = {
                "bm25": dict(bm25),
                "vector": dict(vector),
                "structural": dict(structural),
            }
            selected = [
                {
                    **by_name[name],
                    "score": round(score, 4),
                    "channels": {
                        channel: hits[name]
                        for channel, hits in channels.items()
                        if name in hits
                    },
                }
                for name, score in fused[:k]
            ]
            names = {s["id"] for s in selected}
            dependencies = []
            ordered, visiting, visited = [], set(), set()

            def visit(name):
                if name in visiting:
                    raise ValueError("技能依赖包含循环")
                if name in visited:
                    return
                visiting.add(name)
                skill = self.library.get(name)
                if skill:
                    for relation, target in skill.relations:
                        if relation == "depend_on" and target in by_name:
                            if target not in names:
                                names.add(target)
                                dependencies.append(by_name[target])
                            visit(target)
                visiting.remove(name)
                visited.add(name)
                ordered.append(name)

            # Preserve relevance order among independent candidates. DFS only
            # moves genuine prerequisites ahead of their dependent skill.
            for candidate in selected:
                visit(candidate["id"])
            return {
                "query": query,
                "skills": selected,
                "dependencies": dependencies,
                "order": ordered,
                "learning_updates": self.bandit.n_updates,
                **self.status(),
                "score_kind": "relative_ranking_not_probability",
                "authorization": "independent",
                "execution_verified": False,
            }

    def _structural_hits(self, query):
        # Same exact domain/tag matching as SkillNet Retriever, not substring tokens.
        q, hits = query.lower(), []
        for skill in self.library:
            segments = [s for s in re.split(r"[与、，,/]", skill.domain) if len(s) >= 2]
            score = 0.7 if any(s.lower() in q for s in segments) else 0
            score += sum(
                0.3 for tag in skill.tags if len(tag) >= 2 and tag.lower() in q
            )
            if score:
                hits.append((skill.name, round(min(score, 2.0), 4)))
        return sorted(hits, key=lambda item: -item[1])[:20]

    def status(self):
        with self.lock:
            encoder = dict(self.vector.status)
            dense = encoder["kind"] == "dense-onnx"
            return {
                "encoder": encoder,
                "weights": list(DENSE_WEIGHTS if dense else WEIGHTS),
                "skill_count": len(self.library),
                "learning_updates": self.bandit.n_updates,
                "algorithm": "SkillNet BM25 + "
                + ("E5 semantic" if dense else "lexical")
                + " + structural weighted fusion + evidence-gated shared LinUCB",
                "source_revision": "0af2de6a9c8b129e174e3442b67c5f7cb4324db9",
                "components": {
                    "bm25": True,
                    "vector": True,
                    "structural": True,
                    "dependency_graph": True,
                    "llm_rerank": False,
                    "executable_prior": EXECUTABLE_PRIOR,
                },
            }

    def load(self, name, offset=None):
        with self.lock:
            if offset is not None and not 0 <= offset <= 2_000_000:
                raise ValueError("技能读取偏移无效")
            if name in self.packages.cards:
                card = self.packages.cards[name]
                if offset is None:
                    pages, cursor = [], 0
                    while True:
                        page = self.packages.read(name, offset=cursor)
                        pages.append(page["text"])
                        if page["next_offset"] is None:
                            break
                        cursor = page["next_offset"]
                    text = "".join(pages)
                else:
                    page = self.packages.read(name, offset=offset)
                    text = page["text"]
                return {
                    "name": name,
                    "markdown": text,
                    "tools": self.tools[name],
                    "next_offset": None if offset is None else page["next_offset"],
                    "resources": [f["path"] for f in card["files"]],
                    "provenance": {
                        key: card[key]
                        for key in ("repository", "revision", "source_url", "license")
                    },
                    "adaptation": "这是只读方法与脚本参考。用 read_skill_resource 分页读取列出的资源；不要直接执行包中的脚本。正文提到的外部技能、工具、服务不一定已安装，应先检查。平台工具权限独立判断，需安装依赖或运行脚本时检查环境与内容，再按本轮授权处理。",
                }
            skill = self.library.get(name)
            corpus_skill = skill is not None and name not in self.bodies and (
                skill.source in ("seed", "github") or skill.generation > 0
            )
            if corpus_skill:
                # SkillNet 语料技能：正文与资源按需从 resources/skillnet/ 读取
                resources, provenance = self._github_assets(skill)
                text = skillnet_corpus.body(skill)
                start = 0 if offset is None else offset
                chunk = text[start : start + 6000]
                return {
                    "name": name,
                    "markdown": chunk,
                    "tools": self.tools[name],
                    "next_offset": start + 6000 if start + 6000 < len(text) else None,
                    "total_chars": len(text),
                    "resources": resources,
                    "provenance": provenance,
                    "corpus_source": skill.source,
                    "adaptation": "这是 SkillNet 社区/种子资料的只读副本。正文提到的外部技能、工具、服务不一定已安装，应先检查；包内脚本不要直接执行。平台工具权限独立判断。",
                }
            if name not in self.bodies:
                raise ValueError("技能不存在")
            return {
                "name": name,
                "markdown": self.bodies[name]
                if offset is None
                else self.bodies[name][offset : offset + 6000],
                "next_offset": offset + 6000
                if offset is not None and offset + 6000 < len(self.bodies[name])
                else None,
                "tools": self.tools[name],
            }

    def graph(self):
        """能力网络：节点 + 目录声明的关系边（球体可视化数据源）。"""
        with self.lock:
            nodes = [
                {
                    "id": s.name,
                    "name": self._display_name(s),
                    "domain": s.domain,
                    "generation": s.generation,
                    "source": s.source,
                    "pulls": int(s.stats.get("pulls", 0) or 0),
                    "mean_reward": round(s.mean_reward, 3)
                    if s.stats.get("pulls")
                    else None,
                    "description": (s.capability or s.description)[:160],
                    "tools": len(self.tools.get(s.name, [])),
                    "relations": [
                        [rel, tgt]
                        for rel, tgt in s.relations
                        if tgt in self.library.skills
                    ],
                }
                for s in self.library
            ]
            present = {s.name for s in self.library}
            edges = [
                {"source": s.name, "target": tgt, "type": rel}
                for s in self.library
                for rel, tgt in s.relations
                if tgt in present
            ]
            return {
                "nodes": nodes,
                "edges": edges,
                "corpus": self.corpus_status,
                "skill_count": len(nodes),
                "edge_count": len(edges),
                "relation_types": sorted({e["type"] for e in edges}),
            }

    def detail(self, name):
        """技能护照：能力契约 + 正文 + 资源清单 + 运行统计。"""
        with self.lock:
            skill = self.library.get(name)
            if skill is None:
                raise ValueError("技能不存在")
            entry = next((item for item in self.all() if item["id"] == name), None)
            resources, provenance = self._github_assets(skill)
            markdown = (
                skillnet_corpus.body(skill)
                if name not in self.bodies
                else self.bodies[name]
            )
            return {
                "name": name,
                "skill": entry,
                "passport": {
                    "capability": skill.capability or skill.description,
                    "use_when": list(skill.use_when),
                    "inputs": list(skill.inputs),
                    "outputs": list(skill.outputs),
                    "pitfalls": list(skill.pitfalls),
                    "verification": list(skill.verification),
                    "steps": list(skill.steps),
                    "boundary": "这是当前版本声明；被检索、有关联或曾被调用，都不证明已通过执行认证。",
                    "environment": skill.compatibility or "环境要求未声明",
                    "skill_sha256": None,
                },
                "markdown": markdown,
                "resources": resources,
                "provenance": provenance,
                "corpus_source": skill.source,
                "generation": skill.generation,
                "relations": [
                    {"type": rel, "target": tgt}
                    for rel, tgt in skill.relations
                    if tgt in self.library.skills
                ],
            }

    def read_skill_resource(self, name, path):
        """按 sha256 清单校验后读取社区技能资源文件。"""
        with self.lock:
            skill = self.library.get(name)
            if skill is None:
                raise ValueError("技能不存在")
            raw, item = skillnet_corpus.read_resource(skill, path)
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                raise ValueError("此资源不是可读取的 UTF-8 文本") from None
            return {
                "name": name,
                "path": path,
                "text": text,
                "bytes": item["bytes"],
                "sha256": item["sha256"],
            }

    def network_model(self):
        """训练产物（网络模型适配器）状态卡。"""
        return skillnet_corpus.network_model_card()
