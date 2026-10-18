"""把 skillnet-demo 的完整技能语料与网络模型导入后端 resources/skillnet/。

一次性导入脚本（可重复执行，幂等）：
  - 种子技能目录        seed/skills/                     -> resources/skillnet/seed/skills/
  - 种子结构化目录数据   seed/catalog_data.py 等           -> resources/skillnet/seed/
  - 社区技能目录        seed/community/skills/            -> resources/skillnet/community/skills/
  - 社区目录与完整性清单 seed/community/catalog.json 等    -> resources/skillnet/community/
  - 演化技能与运行统计   data/library.json                 -> resources/skillnet/evolved.json
  - 训练产物（网络模型） data/network-model{,-v2}/         -> resources/skillnet/network-model{,-v2}/

用法：
  python scripts/import_skillnet.py --source <skillnet-demo 路径>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
TARGET = BACKEND / "resources" / "skillnet"

COPY_TREE = [
    # (源相对路径, 目标相对路径)
    ("seed/skills", "seed/skills"),
    ("seed/community/skills", "community/skills"),
    ("seed/community/licenses", "community/licenses"),
    ("data/network-model", "network-model"),
    ("data/network-model-v2", "network-model-v2"),
]

COPY_FILE = [
    ("seed/catalog_data.py", "seed/catalog_data.py"),
    ("seed/business_skills.py", "seed/business_skills.py"),
    ("seed/__init__.py", "seed/__init__.py"),
    ("seed/community/catalog.json", "community/catalog.json"),
    ("seed/community/packages.json", "community/packages.json"),
    ("data/library.json", "evolved.json"),
    ("data/library.baseline.json", "evolved.baseline.json"),
    ("THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.md"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def count_files(root: Path) -> tuple[int, int]:
    files = [p for p in root.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default=os.environ.get("SKILLNET_SOURCE", "skillnet-demo"),
        help="skillnet-demo 仓库路径（也可用环境变量 SKILLNET_SOURCE 指定）",
    )
    parser.add_argument("--clean", action="store_true", help="先清空目标目录再导入")
    args = parser.parse_args()
    source = Path(args.source).resolve()
    if not (source / "seed").is_dir():
        print(f"[import] 源目录缺少 seed/：{source}", file=sys.stderr)
        return 1

    if args.clean and TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True, exist_ok=True)

    for rel_src, rel_dst in COPY_TREE:
        src, dst = source / rel_src, TARGET / rel_dst
        if not src.is_dir():
            print(f"[import] 跳过（不存在）：{rel_src}")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        n, size = count_files(dst)
        print(f"[import] {rel_src} -> {rel_dst}：{n} 个文件，{size / 1e6:.1f}MB")

    for rel_src, rel_dst in COPY_FILE:
        src, dst = source / rel_src, TARGET / rel_dst
        if not src.is_file():
            print(f"[import] 跳过（不存在）：{rel_src}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        print(f"[import] {rel_src} -> {rel_dst}：{dst.stat().st_size / 1e3:.0f}KB")

    # 目录数据里保存技能数量，供启动时快速核对
    seed_count = len(list((TARGET / "seed/skills").glob("*/SKILL.md"))) if (TARGET / "seed/skills").is_dir() else 0
    community_count = len(list((TARGET / "community/skills").glob("*/SKILL.md"))) if (TARGET / "community/skills").is_dir() else 0
    evolved_count = 0
    evolved_file = TARGET / "evolved.json"
    if evolved_file.is_file():
        try:
            evolved_count = len(json.loads(evolved_file.read_text("utf-8")).get("evolved") or [])
        except (json.JSONDecodeError, OSError):
            pass
    total_files, total_bytes = count_files(TARGET)
    manifest = {
        "imported_at": datetime.now(timezone.utc).isoformat(),
        # 只记录来源仓库名，避免把导入者的本地绝对路径写进受版本控制的清单
        "source": Path(args.source).name,
        "seed_skills": seed_count,
        "community_skills": community_count,
        "evolved_skills": evolved_count,
        "total_skills": seed_count + community_count + evolved_count,
        "files": total_files,
        "bytes": total_bytes,
        "catalog_sha256": sha256(TARGET / "community/catalog.json")
        if (TARGET / "community/catalog.json").is_file()
        else None,
    }
    (TARGET / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[import] 完成：{manifest['total_skills']} 个技能"
          f"（种子 {seed_count} / 社区 {community_count} / 演化 {evolved_count}），"
          f"{total_files} 个文件，{total_bytes / 1e6:.1f}MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
