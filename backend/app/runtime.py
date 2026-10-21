"""Public build identity and local-launcher checks, without importing the ASGI app."""

import hashlib
import sqlite3
from pathlib import Path


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
