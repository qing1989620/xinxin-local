import sqlite3

from app.runtime import active_tasks, source_fingerprint


def test_dependency_sync_detects_missing_and_changed_pins_offline(tmp_path, monkeypatch):
    from app.runtime import missing_dependencies
    from importlib import metadata
    (tmp_path / "requirements.lock").write_text("# fixture\nfirst==1.0\nchanged==2.0\nmissing==3.0\n")
    def installed(name):
        if name == "missing":
            raise metadata.PackageNotFoundError(name)
        return "1.0"
    monkeypatch.setattr(metadata, "version", installed)
    assert missing_dependencies(tmp_path) == ["changed", "missing"]


def test_source_fingerprint_changes_with_code_or_lock_but_not_private_data(tmp_path):
    (tmp_path / "app").mkdir()
    code = tmp_path / "app/main.py"
    code.write_text("first")
    lock = tmp_path / "requirements.lock"
    lock.write_text("first")
    first = source_fingerprint(tmp_path)
    (tmp_path / "private.db").write_text("synthetic")
    assert source_fingerprint(tmp_path) == first
    code.write_text("second")
    second = source_fingerprint(tmp_path)
    assert second != first
    lock.write_text("second")
    assert source_fingerprint(tmp_path) != second


def test_active_tasks_reads_only_counts_and_does_not_create_missing_database(tmp_path):
    assert active_tasks(tmp_path) == 0
    assert list(tmp_path.iterdir()) == []
    with sqlite3.connect(tmp_path / "xinxin.sqlite3") as db:
        db.execute("CREATE TABLE runs(status TEXT)")
        db.executemany("INSERT INTO runs VALUES(?)", [(status,) for status in ["queued", "running", "cancelling", "completed", "failed"]])
    assert active_tasks(tmp_path) == 3
