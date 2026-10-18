"""Install the pinned public E5 model, from SkillNet's ZIP or official HTTPS.

python scripts/setup_semantic_model.py --bundle /path/multilingual-e5-small.zip
python scripts/setup_semantic_model.py  # download the exact Hugging Face revision
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.request
import uuid
import zipfile
from contextlib import nullcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.config import Config
from app.skillnet.semantic import MANIFEST, digest, verify_model


def install(target: Path, bundle: Path | None = None):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    archive_context = zipfile.ZipFile(bundle) if bundle else nullcontext()
    with archive_context as archive:
        expected = manifest["files"]
        if archive and (
            set(archive.namelist()) != set(expected)
            or len(archive.namelist()) != len(expected)
        ):
            raise ValueError("Unexpected files in model bundle")
        for name, info in expected.items():
            destination = target / name
            if (
                destination.is_file()
                and destination.stat().st_size == info["bytes"]
                and digest(destination) == info["sha256"]
            ):
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(
                destination.name + "." + uuid.uuid4().hex + ".partial"
            )
            try:
                if archive:
                    if archive.getinfo(name).file_size != info["bytes"]:
                        raise ValueError("Unexpected model size")
                    source = archive.open(name)
                else:
                    url = f"https://huggingface.co/{manifest['repository']}/resolve/{manifest['revision']}/{name}"
                    source = urllib.request.urlopen(url, timeout=90)
                with source, temporary.open("wb") as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                if (
                    temporary.stat().st_size != info["bytes"]
                    or digest(temporary) != info["sha256"]
                ):
                    raise ValueError("Model download integrity check failed")
                temporary.replace(destination)
            finally:
                temporary.unlink(missing_ok=True)
    verify_model(target)
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "Pinned multilingual E5 model verified and installed. Restart the backend to activate."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--target", type=Path)
    args = parser.parse_args()
    install(args.target or Config.from_env().data_dir / "semantic-model", args.bundle)
