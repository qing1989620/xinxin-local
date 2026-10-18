"""Create a private, verified Linux migration snapshot; never edit the source."""

from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sqlite3


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def copy_private_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    source_root = source.resolve()
    for item in [source, *source.rglob("*")]:
        if item.is_symlink() or not item.resolve().is_relative_to(source_root):
            raise ValueError("Migration source contains a link outside its directory")
    shutil.copytree(source, destination)


def prepare(source: Path, destination: Path, target_root: str) -> dict:
    source = source.resolve(strict=True)
    destination = destination.resolve()
    target = PurePosixPath(target_root)
    if not target.is_absolute() or ".." in target.parts or "\\" in target_root:
        raise ValueError("Target data directory must be an absolute Linux path")
    if destination.exists() or destination.is_relative_to(source):
        raise ValueError("Destination must be a new directory outside source data")
    destination.mkdir(parents=True, mode=0o700)
    marker = destination / ".incomplete"
    marker.touch(mode=0o600)
    # SQLite backup captures WAL state consistently. An incomplete snapshot is
    # retained privately on error and is never considered ready for transfer.
    db_path = source / "xinxin.sqlite3"
    with closing(sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)) as original:
        active = original.execute(
            "SELECT COUNT(*) FROM runs WHERE status IN ('queued','running','cancelling')"
        ).fetchone()[0]
        if active:
            raise ValueError("Finish active tasks and stop the local API before migration")
        with closing(sqlite3.connect(destination / "xinxin.sqlite3")) as snapshot:
            original.backup(snapshot)
    with closing(sqlite3.connect(destination / "xinxin.sqlite3")) as snapshot, snapshot:
        snapshot.row_factory = sqlite3.Row
        files = list(snapshot.execute("SELECT id,path,size,sha256 FROM files"))
        file_root = (source / "files").resolve()
        output = destination / "files"
        output.mkdir(mode=0o700)
        for row in files:
            local = Path(row["path"])
            if not local.is_absolute():
                local = source / local
            if local.is_symlink():
                raise ValueError("Registered resource must not be a symbolic link")
            local = local.resolve(strict=True)
            if not local.is_relative_to(file_root) or local.stem != row["id"]:
                raise ValueError("Registered resource is outside the private file directory")
            if local.stat().st_size != row["size"] or checksum(local) != row["sha256"]:
                raise ValueError("Registered resource size or checksum does not match")
            shutil.copy2(local, output / local.name)
            snapshot.execute(
                "UPDATE files SET path=? WHERE id=?",
                (str(target / "files" / local.name), row["id"]),
            )
        snapshot.execute("DELETE FROM sessions")
        result = {
            "files": len(files),
            "conversations": snapshot.execute(
                "SELECT COUNT(*) FROM conversations"
            ).fetchone()[0],
            "sessions_invalidated": True,
            "target_root": str(target),
        }
        if snapshot.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Migration database integrity check failed")
    for name in ("vault.key", "bootstrap.code"):
        private = source / name
        if not private.is_file() or private.is_symlink():
            raise ValueError("Missing private vault or initialization file")
        shutil.copy2(private, destination / name)
    for name in ("skills", "semantic-model", "workspaces"):
        copy_private_tree(source / name, destination / name)
    (destination / "migration.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    marker.unlink()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--target-root", default="/var/lib/xinxin")
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.destination, args.target_root)))
