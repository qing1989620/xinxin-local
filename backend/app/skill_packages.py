"""Read pinned community resources as bounded data, never Python modules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from .config import ROOT


class SkillPackages:
    def __init__(self, root: Path = ROOT / "resources/skills"):
        self.root = root.resolve()
        catalog = json.loads((self.root / "catalog.json").read_text("utf-8"))
        self.cards = {item["id"]: item for item in catalog["skills"]}

    def read(self, name: str, path: str = "SKILL.md", offset: int = 0):
        if not 0 <= offset <= 2_000_000:
            raise ValueError("资源读取偏移无效")
        card = self.cards.get(name)
        if card is None:
            raise ValueError("此技能没有内置参考包")
        relative = PurePosixPath(path)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in path
            or ":" in path
        ):
            raise ValueError("参考资源路径无效")
        item = next((f for f in card["files"] if f["path"] == path), None)
        if item is None:
            raise ValueError("参考资源未列入已核对清单")
        package = self.root / "packages" / name
        target = (package / relative).resolve()
        if not target.is_relative_to(package.resolve()) or not target.is_relative_to(
            self.root
        ):
            raise ValueError("参考资源路径越界")
        raw = target.read_bytes()
        if (
            len(raw) != item["bytes"]
            or hashlib.sha256(raw).hexdigest() != item["sha256"]
        ):
            raise ValueError("参考资源完整性检查失败")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeError:
            raise ValueError("此参考资源不是可读取的 UTF-8 文本") from None
        end = min(offset + 6000, len(text))
        return {
            "name": name,
            "path": path,
            "text": text[offset:end],
            "offset": offset,
            "next_offset": end if end < len(text) else None,
            "total_chars": len(text),
            "sha256": item["sha256"],
            "source_url": card["source_url"],
            "license": card["license"],
            "execution_verified": False,
        }
