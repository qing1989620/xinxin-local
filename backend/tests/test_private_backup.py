from contextlib import closing
import hashlib
import sqlite3
import tarfile

import pytest

from app.store import Store
from scripts.backup_private_data import backup


def test_backup_contains_database_vault_and_resources_and_rotates_only_own_archives(tmp_path):
    source, output = tmp_path / "data", tmp_path / "backups"
    store = Store(source)
    store.execute("INSERT INTO owner VALUES(1,'fixture','hashed-password')")
    (source / "vault.key").write_bytes(b"private-fixture-key")
    (source / "bootstrap.code").write_text("fixture-bootstrap")
    files = source / "files"
    files.mkdir()
    (files / "fixture.txt").write_bytes(b"immutable resource")
    output.mkdir()
    unrelated = output / "owner-notes.txt"
    unrelated.write_text("keep")
    first = backup(source, output, keep=1)
    second = backup(source, output, keep=1)
    assert not first.exists() and second.exists() and unrelated.exists()
    with tarfile.open(second) as archive:
        assert archive.extractfile("data/vault.key").read() == b"private-fixture-key"
        assert archive.extractfile("data/files/fixture.txt").read() == b"immutable resource"
        restored = tmp_path / "restored.sqlite3"
        restored.write_bytes(archive.extractfile("data/xinxin.sqlite3").read())
    with closing(sqlite3.connect(restored)) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("SELECT name FROM owner").fetchone()[0] == "fixture"
    assert not list(output.glob("*.partial"))


@pytest.mark.parametrize("failure", ["vault", "delete", "modified"])
def test_failed_backup_preserves_last_good_archive(tmp_path, monkeypatch, failure):
    source, output = tmp_path / "data", tmp_path / "backups"
    store = Store(source)
    (source / "vault.key").write_bytes(b"fixture-key")
    (source / "bootstrap.code").write_text("fixture-bootstrap")
    (source / "files").mkdir()
    resource = source / "files/test-id.txt"
    content = b"registered immutable bytes"
    resource.write_bytes(content)
    store.execute("INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?)", ("test-id", "test.txt", "text/plain", len(content), hashlib.sha256(content).hexdigest(), str(resource), "", None, 1))
    good = backup(source, output, keep=1)
    if failure == "vault":
        (source / "vault.key").unlink()
    elif failure == "modified":
        resource.write_bytes(b"X" * len(content))
    else:
        original_add = tarfile.TarFile.add

        def delete_after_snapshot(archive, name, arcname=None, **kwargs):
            result = original_add(archive, name, arcname=arcname, **kwargs)
            if arcname == "data/xinxin.sqlite3":
                resource.unlink()
            return result

        monkeypatch.setattr(tarfile.TarFile, "add", delete_after_snapshot)
    with pytest.raises(ValueError):
        backup(source, output, keep=1)
    assert good.exists()
    assert list(output.glob("xinxin-*.tar.gz")) == [good]
    assert not list(output.glob("*.partial"))
