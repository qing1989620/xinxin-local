import json
import os
import subprocess

import pytest

from app.store import uid
from test_platform import client


def fixture_run(client, cid, status="completed"):
    ident = uid()
    client.app.state.store.execute(
        "INSERT INTO runs(id,conversation_id,task,status,permission,max_calls,max_seconds,created,updated) VALUES(?,?,?,?, 'read',1,30,1,1)",
        (ident, cid, "synthetic deletion fixture", status),
    )
    return ident


def test_permanent_delete_reclaims_owned_data_and_preserves_shared_resources(client):
    store, library = client.app.state.store, client.app.state.library
    cid = client.post("/api/v1/conversations", json={"title": "delete fixture"}).json()["id"]
    other = client.post("/api/v1/conversations", json={"title": "retain fixture"}).json()["id"]
    run = fixture_run(client, cid)
    message = store.message(cid, "user", "delete these messages", run_id=run)
    store.event(run, "assistant.progress", {"text": "synthetic progress"})
    store.execute("INSERT INTO run_context VALUES(?,?,?,?,?)", (run, cid, "[]", 1, 1))
    store.execute("INSERT INTO run_plan VALUES(?,?,?,?)", (run, cid, "[]", 1))
    uploaded = library.save("independent.txt", b"independent upload")
    owned = library.save("owned.txt", b"owned generated result", run_id=run)
    shared = library.save("shared.txt", b"shared generated result", run_id=run)
    store.message(other, "user", "reuse file " + shared["id"])
    workspace = store.directory / "workspaces" / cid
    workspace.mkdir(parents=True)
    (workspace / "scratch.bin").write_bytes(b"scratch" * 100)
    preview = client.get(f"/api/v1/conversations/{cid}/deletion-preview").json()
    assert preview["messages"] == 1 and preview["events"] == 1 and preview["workspace_bytes"] == 700
    response = client.delete(f"/api/v1/conversations/{cid}/permanent")
    assert response.status_code == 200, response.text
    assert response.json()["database_compacted"] and response.json()["shared_generated_files_retained"] == 1
    assert client.get(f"/api/v1/conversations/{cid}").status_code == 404
    assert client.get(f"/api/v1/conversations/{other}").status_code == 200
    assert not workspace.exists()
    assert not store.one("SELECT id FROM files WHERE id=?", (owned["id"],))
    for table in ("events", "message_runs", "run_context", "run_plan"):
        assert not store.one(f"SELECT * FROM {table} WHERE run_id=?", (run,))
    assert library.path(uploaded["id"]).is_file() and library.path(shared["id"]).is_file()


def test_deletion_refuses_active_tasks_and_preserves_the_conversation(client):
    cid = client.post("/api/v1/conversations", json={"title": "busy fixture"}).json()["id"]
    fixture_run(client, cid, "cancelling")
    assert client.delete(f"/api/v1/conversations/{cid}/permanent").status_code == 409
    assert client.get(f"/api/v1/conversations/{cid}").status_code == 200
    assert not client.app.state.manager.maintenance.is_set()


def test_invalid_artifact_path_rolls_back_workspace_and_database(client, tmp_path):
    store, library = client.app.state.store, client.app.state.library
    cid = client.post("/api/v1/conversations", json={"title": "rollback fixture"}).json()["id"]
    run = fixture_run(client, cid)
    file = library.save("invalid.txt", b"generated", run_id=run)
    outside = tmp_path.parent / (uid() + ".txt")
    outside.write_text("outside sentinel")
    workspace = store.directory / "workspaces" / cid
    workspace.mkdir(parents=True)
    (workspace / "retain.txt").write_text("retained workspace")
    store.execute("UPDATE files SET path=? WHERE id=?", (str(outside), file["id"]))
    try:
        response = client.delete(f"/api/v1/conversations/{cid}/permanent")
        assert response.status_code == 400
        assert (workspace / "retain.txt").read_text() == "retained workspace"
        assert outside.read_text() == "outside sentinel"
        assert store.one("SELECT id FROM conversations WHERE id=?", (cid,))
        assert not client.app.state.manager.maintenance.is_set()
    finally:
        outside.unlink()


@pytest.mark.parametrize("name", ["workspaces", "files", ".deletion-trash"])
def test_deletion_rejects_linked_private_roots_without_touching_external_data(client, tmp_path, name):
    store = client.app.state.store
    cid = client.post("/api/v1/conversations", json={"title": "linked-root fixture"}).json()["id"]
    outside = tmp_path.parent / ("external-" + uid())
    (outside / cid).mkdir(parents=True)
    sentinel = outside / cid / "retain.txt"
    sentinel.write_text("external data remains")
    link = store.directory / name
    if link.exists():
        link.rmdir()  # The isolated fixture has an empty files directory only.
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        quote = lambda value: str(value).replace("'", "''")
        subprocess.run([
            "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
            f"New-Item -ItemType Junction -Path '{quote(link)}' -Target '{quote(outside)}' | Out-Null",
        ], check=True, capture_output=True)
    try:
        response = client.delete(f"/api/v1/conversations/{cid}/permanent")
        assert response.status_code == 400
        assert sentinel.read_text() == "external data remains"
        assert store.one("SELECT id FROM conversations WHERE id=?", (cid,))
    finally:
        if link.is_symlink():
            link.unlink()
        elif link.is_junction():
            os.rmdir(link)  # Removes the junction itself, never the target tree.
