"""Install the pinned personal, non-commercial zine skill into private data only."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Config

COMMIT = "b9edb836c9dd5c5d80995e89ebcaba34b75fd58f"
REPOSITORY = "https://github.com/Zeejay0/gathered-scenes-zine-skill.git"
NAMES = ("scenes-gathered-zine-v1-3", "scene-distillation-zine-v1-3")


def install(source, destination):
    head = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != COMMIT:
        raise ValueError("技能提交与锁定版本不一致")
    destination.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        target = destination / name
        if target.exists():
            if (target / "SKILL.md").read_bytes() != (
                source / "skills" / name / "SKILL.md"
            ).read_bytes():
                raise ValueError("已安装内容有修改，保留原文件，请先备份后手动处理")
            continue
        shutil.copytree(source / "skills" / name, target)
    shutil.copy2(source / "LICENSE", destination / "GATHERED-SCENES-LICENSE")
    print(
        "已安装拾景的两种转换方式。Visual Skill by @Zeejay0；仅供个人非商业使用。重启后端后生效。"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, help="Optional explicit, pinned local checkout"
    )
    args = parser.parse_args()
    destination = Config.from_env().data_dir / "skills"
    if args.source:
        install(args.source.resolve(), destination)
    else:
        with tempfile.TemporaryDirectory(prefix="xinxin-zine-") as temporary:
            source = Path(temporary) / "source"
            subprocess.run(
                ["git", "clone", "--no-checkout", REPOSITORY, str(source)], check=True
            )
            subprocess.run(
                ["git", "-C", str(source), "checkout", "--detach", COMMIT], check=True
            )
            install(source, destination)
