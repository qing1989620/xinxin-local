"""Copy a pinned, attributed subset as data. Never execute source package code."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

REVISION = "0af2de6a9c8b129e174e3442b67c5f7cb4324db9"
ROOT = Path(__file__).resolve().parents[1]
# A product-oriented selection, not an execution or quality certification.
SELECTION = [
    (
        "gh-claude-docker-development-521176",
        "Docker 与 Compose",
        "优化 Dockerfile、多阶段构建、容器配置和镜像体积",
        "运维",
        "server-deployment",
    ),
    (
        "gh-agentic-linux-troubleshooting-459c59",
        "Linux 故障诊断",
        "排查 Linux 服务、进程、磁盘、网络和日志异常",
        "运维",
        "server-deployment",
    ),
    (
        "gh-agentic-bash-defensive-patterns-9f6117",
        "可靠 Shell 脚本",
        "编写有错误处理、输入校验和清理逻辑的 Bash 脚本",
        "运维",
        "coding-workspace",
    ),
    (
        "gh-claude-git-worktree-manager-570eb8",
        "Git 工作树",
        "隔离分支工作区，检查工作树状态并保护未提交修改",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-git-commit-message-15195e",
        "Git 提交说明",
        "根据实际差异组织清晰的提交信息",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-git-pr-review-877d80",
        "代码变更审查",
        "检查代码差异、回归风险与可验证的修复建议",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-debugging-strategies-6d5343",
        "系统化排错",
        "复现错误，收集证据，定位根因并验证修复",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-async-python-patterns-9967de",
        "Python 异步编程",
        "处理 asyncio 并发、取消、超时和异步资源生命周期",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-python-packaging-e26fed",
        "Python 工程打包",
        "整理 Python 包结构、依赖、构建与发布配置",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-python-performance-optimization-e4a70b",
        "Python 性能分析",
        "先测量性能瓶颈，再优化 Python 的运行时间与内存",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-typescript-advanced-types-83dbbf",
        "TypeScript 类型设计",
        "设计泛型、条件类型和可靠的 TypeScript 接口",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-react-best-practices-022aa4",
        "React 性能与结构",
        "改善 React 组件的数据流、渲染和交互性能",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-accessibility-compliance-accessibility-audi-636324",
        "界面无障碍检查",
        "检查键盘操作、语义、焦点、对比度和辅助技术体验",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-javascript-testing-patterns-327510",
        "JavaScript 测试",
        "为 JavaScript 和 TypeScript 编写有价值的单元与集成测试",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-e2e-testing-patterns-19449c",
        "端到端测试",
        "验证关键用户流程，减少等待和脆弱定位造成的不稳定测试",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-ai-prompt-regression-testing-eb8570",
        "提示词回归检查",
        "用固定场景比较提示词行为、工具调用和输出约束",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-api-design-principles-b1df32",
        "API 接口设计",
        "设计一致的 REST 接口、错误、分页和版本契约",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-api-documentation-9c82df",
        "API 文档",
        "依据实现补全接口示例、参数、错误与使用说明",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-claude-database-schema-designer-aff360",
        "数据库结构设计",
        "设计表、关联、索引、约束与可迁移的数据库结构",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-claude-sql-database-assistant-670628",
        "SQL 查询分析",
        "理解 SQL、检查查询计划与索引并解释优化取舍",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-postgresql-optimization-2fea25",
        "PostgreSQL 优化",
        "检查慢查询、连接、索引与 PostgreSQL 运行参数",
        "运维",
        "coding-workspace",
    ),
    (
        "gh-agentic-security-scanning-security-dependencies-74c3a2",
        "依赖安全检查",
        "检查依赖版本、已知漏洞与有依据的升级方案",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-skill-security-audit-38e57e",
        "技能包检查",
        "阅读技能指令和脚本，识别越权、数据外发和不可信依赖",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-code-refactoring-tech-debt-1e85a8",
        "重构与技术债",
        "依据实际维护成本识别技术债并安排渐进重构",
        "开发",
        "coding-workspace",
    ),
    (
        "gh-agentic-markdown-rendering-ffb206",
        "Markdown 文档呈现",
        "整理 Markdown 文档结构、语法与安全呈现",
        "内容",
        "coding-workspace",
    ),
    (
        "gh-agentic-pdf-conversion-router-8ab07e",
        "PDF 转换规划",
        "识别 PDF 类型与转换目标，选择合适工具并核验产物",
        "资料",
        "private-documents",
    ),
    (
        "gh-scientific-exploratory-data-analysis-a64a41",
        "探索性数据分析",
        "分析 CSV、JSON 等数据的分布、缺失和异常，保留原始数据",
        "资料",
        "private-documents",
    ),
    (
        "gh-scientific-statistical-analysis-1c754f",
        "统计分析方法",
        "按数据和问题选择统计方法，检查假设并说明不确定性",
        "绘图",
        "scientific-plotting",
    ),
    (
        "gh-scientific-scientific-writing-49b296",
        "研究报告写作",
        "围绕真实证据组织研究报告、图表说明与引用",
        "内容",
        "coding-workspace",
    ),
    (
        "gh-agentic-code-documentation-doc-generate-c3c7d0",
        "工程文档生成",
        "阅读真实代码，编写架构、操作和维护文档",
        "内容",
        "coding-workspace",
    ),
]


def curate(source: Path, output: Path):
    revision = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != REVISION:
        raise ValueError("Source revision differs from the reviewed snapshot")
    manifest = json.loads((source / "seed/community/packages.json").read_text("utf-8"))
    catalog = {
        s["name"]: s
        for s in json.loads((source / "seed/community/catalog.json").read_text("utf-8"))
    }
    selected = []
    for ident, title, description, domain, base in SELECTION:
        package = manifest[ident]
        if package["license"] not in {"MIT", "Apache-2.0", "BSD-3-Clause", "CC0-1.0"}:
            raise ValueError("Package license needs manual review: " + ident)
        package_root = (source / package["package_path"]).resolve()
        expected_root = (source / "seed/community/skills" / ident).resolve()
        if package_root != expected_root:
            raise ValueError("Unexpected source package path")
        files = []
        for item in package["files"]:
            relative = PurePosixPath(item["path"])
            original = package_root / relative
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or original.is_symlink()
                or not original.resolve().is_relative_to(package_root)
            ):
                raise ValueError("Unsafe resource path")
            raw = original.read_bytes()
            if (
                len(raw) != item["bytes"]
                or hashlib.sha256(raw).hexdigest() != item["sha256"]
            ):
                raise ValueError(
                    "Source resource failed integrity verification: " + ident
                )
            target = output / "packages" / ident / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            files.append(item)
        selected.append(
            {
                "id": ident,
                "name": title,
                "description": description,
                "domain": domain,
                "base_skill": base,
                "original_description": catalog[ident]["description"],
                "repository": package["repository"],
                "revision": package["commit"],
                "source_url": package["source_url"],
                "license": "MIT (code); CC-BY-4.0 (original documentation)"
                if ident.startswith("gh-agentic-") and package["license"] == "MIT"
                else package["license"],
                "execution_verified": False,
                "files": files,
            }
        )
    output.mkdir(parents=True, exist_ok=True)
    (output / "catalog.json").write_text(
        json.dumps(
            {
                "version": 1,
                "source_repository": "qing1989620/skillnet-demo",
                "source_revision": REVISION,
                "adaptation": "Selected packages are unchanged reference data. Chinese summaries and base-tool relations are Xinxin adaptations; scripts are never auto-executed. Referenced third-party skills/services are not implicitly installed.",
                "skills": selected,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        "utf-8",
    )
    print(
        json.dumps(
            {
                "packages": len(selected),
                "resources": sum(len(s["files"]) for s in selected),
                "bytes": sum(f["bytes"] for s in selected for f in s["files"]),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "resources/skills")
    args = parser.parse_args()
    curate(args.source.resolve(), args.output.resolve())
