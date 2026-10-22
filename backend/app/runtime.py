"""Public build identity and local-launcher checks, without importing the ASGI app."""

import hashlib
import sqlite3
from pathlib import Path
from importlib import metadata


def missing_dependencies(root: Path) -> list[str]:
    """Compare the installed venv with exact lock pins without network access."""
    try:
        from packaging.requirements import Requirement
    except ImportError:
        return ["packaging"]
    missing = []
    for line in (root / "requirements.lock").read_text(encoding="utf-8").splitlines():
        line = line.partition("#")[0].strip()
        if not line:
            continue
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate():
            continue
        pins = list(requirement.specifier)
        if len(pins) != 1 or pins[0].operator != "==" or "*" in pins[0].version:
            raise ValueError("Runtime lock must contain exact package pins")
        try:
            if not requirement.specifier.contains(metadata.version(requirement.name), prereleases=True):
                missing.append(requirement.name)
        except metadata.PackageNotFoundError:
            missing.append(requirement.name)
    return missing


def source_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted((root / "app").rglob("*.py")) + [root / "requirements.lock"]
    for path in paths:
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def active_tasks(directory: Path) -> int:
    database = directory / "xinxin.sqlite3"
    if not database.exists():
        return 0
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=3) as db:
        return db.execute("SELECT count(*) FROM runs WHERE status IN ('queued','running','cancelling')").fetchone()[0]
