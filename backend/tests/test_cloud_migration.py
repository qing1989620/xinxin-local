import hashlib
from contextlib import closing
import sqlite3

import pytest

from app.store import Store
from scripts.prepare_cloud_data import prepare


def source_data(tmp_path):
    source = tmp_path / "source"
    store = Store(source)
    (source / "vault.key").write_bytes(b"private-test-vault")
    (source / "bootstrap.code").write_text("private-test-bootstrap")
    file_root = source / "files"
    file_root.mkdir()
    file = file_root / "test-id.txt"
    content = b"phone upload migration fixture"
    file.write_bytes(content)
    store.execute(
        "INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?)",
        ("test-id", "fixture.txt", "text/plain", len(content), hashlib.sha256(content).hexdigest(), str(file), "fixture", None, 1),
    )
    store.execute("INSERT INTO sessions VALUES('old-device-token',9999999999)")
    workspace = source / "workspaces" / "test-conversation"
    workspace.mkdir(parents=True)
    (workspace / "result.txt").write_text("keep workspace")
    return source, store, file


def test_migration_preserves_bytes_rewrites_paths_and_clears_only_snapshot_sessions(tmp_path):
    source, store, file = source_data(tmp_path)
    destination = tmp_path / "cloud"
    result = prepare(source, destination, "/var/lib/xinxin")
    assert result["files"] == 1
    assert not (destination / ".incomplete").exists()
    with closing(sqlite3.connect(destination / "xinxin.sqlite3")) as db:
        assert db.execute("SELECT path FROM files").fetchone()[0] == "/var/lib/xinxin/files/test-id.txt"
        assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
    assert store.one("SELECT COUNT(*) n FROM sessions")["n"] == 1
    assert store.one("SELECT path FROM files")["path"] == str(file)
    assert (destination / "files/test-id.txt").read_bytes() == file.read_bytes()
    assert (destination / "workspaces/test-conversation/result.txt").read_text() == "keep workspace"


@pytest.mark.parametrize("invalid", ["checksum", "outside", "active"])
def test_migration_refuses_invalid_resources_and_active_tasks(tmp_path, invalid):
    source, store, file = source_data(tmp_path)
    if invalid == "checksum":
        file.write_bytes(b"modified")
    elif invalid == "outside":
        outside = tmp_path / file.name
        outside.write_bytes(file.read_bytes())
        store.execute("UPDATE files SET path=?", (str(outside),))
    else:
        with store.connect() as db:
            db.execute("INSERT INTO runs(id,conversation_id,task,status,permission,max_calls,max_seconds,created,updated) VALUES('run','conversation','fixture','running','read',1,30,1,1)")
    destination = tmp_path / "cloud"
    with pytest.raises(ValueError):
        prepare(source, destination, "/var/lib/xinxin")
    assert (destination / ".incomplete").exists()


def test_migration_refuses_destination_inside_source_or_existing_destination(tmp_path):
    source, _, _ = source_data(tmp_path)
    with pytest.raises(ValueError):
        prepare(source, source / "cloud", "/var/lib/xinxin")
    destination = tmp_path / "existing"
    destination.mkdir()
    with pytest.raises(ValueError):
        prepare(source, destination, "/var/lib/xinxin")
