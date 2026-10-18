import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.main import create_app
from app.progress import ProgressNarrator
from app.store import uid
from test_platform import client, frames, wait_run
from test_conversation_deletion import fixture_run


@pytest.mark.parametrize("budget_kind", ["calls", "tokens"])
def test_explicit_continuation_after_restart_keeps_goal_and_evidence_with_a_fresh_budget(tmp_path, budget_kind):
    config = Config(tmp_path, "resume-bootstrap")
    with TestClient(create_app(config)) as first:
        token = first.post("/api/v1/auth/setup", json={"name": "fixture", "password": "resume-fixture-password", "setup_code": "resume-bootstrap"}).json()["token"]
        first.headers["Authorization"] = "Bearer " + token
        first.put("/api/v1/settings", json={"model_api_key": "offline-resume-key"})
        first.app.state.manager.model_transport = httpx.MockTransport(lambda request: httpx.Response(200, content=frames(tool={"name": "write_file", "arguments": {"path": "stage.txt", "content": "unique-stage-evidence"}}).replace('"total_tokens": 12', '"total_tokens": 5500').encode()))
        run = first.post("/api/v1/runs", json={"task": "Create stage.txt then use its evidence to create done.txt; preserve existing stage file.", "permission": "workspace", "max_calls": 1 if budget_kind == "calls" else 4, "max_total_tokens": 50000 if budget_kind == "calls" else 5000, "context_window_tokens": 80000, "request_key": "resume-first-" + budget_kind}).json()
        stopped = wait_run(first, run["id"])
        assert stopped["status"] == "failed" and "预算" in stopped["error"]
        stage = tmp_path / "workspaces" / run["conversation_id"] / "stage.txt"
        original_stat = stage.stat()

    with TestClient(create_app(config)) as restarted:
        restarted.headers["Authorization"] = "Bearer " + token
        calls = 0

        def provider(request):
            nonlocal calls
            calls += 1
            wire = json.loads(request.content)
            history = json.dumps(wire["messages"], ensure_ascii=False)
            assert "Create stage.txt" in history and "unique-stage-evidence" in history
            assert "当前要求：仅完成剩余步骤" in history
            reply = frames(tool={"name": "read_file", "arguments": {"path": "stage.txt"}}) if calls == 1 else frames(tool={"name": "write_file", "arguments": {"path": "done.txt", "content": "continued-and-verified"}}) if calls == 2 else frames(content="remaining step completed")
            return httpx.Response(200, content=reply.encode())

        restarted.app.state.manager.model_transport = httpx.MockTransport(provider)
        body = {"instruction": "当前要求：仅完成剩余步骤", "permission": "workspace", "max_calls": 4, "max_total_tokens": 100000, "request_key": "resume-next-" + budget_kind}
        continued = restarted.post(f"/api/v1/runs/{run['id']}/continue", json=body)
        assert continued.status_code == 200, continued.text
        new = wait_run(restarted, continued.json()["id"])
        assert new["status"] == "completed" and new["resume_of"] == run["id"]
        assert new["conversation_id"] == run["conversation_id"] and new["context_window_tokens"] == 80000
        assert json.loads(new["usage"])["calls"] == 3
        assert stage.stat().st_mtime_ns == original_stat.st_mtime_ns and stage.stat().st_ino == original_stat.st_ino
        assert (stage.parent / "done.txt").read_text() == "continued-and-verified"
        assert restarted.post(f"/api/v1/runs/{run['id']}/continue", json=body).json()["id"] == new["id"]
        assert restarted.post(f"/api/v1/runs/{run['id']}/continue", json={**body, "request_key": "new-stale-retry"}).status_code == 400
        detail = restarted.get(f"/api/v1/conversations/{new['conversation_id']}").json()
        assert any(message["content"].startswith("继续原任务。") and len(message["content"]) < 100 for message in detail["messages"])


def test_continuation_uses_current_read_permission_without_reusing_old_write_authority(client):
    client.put("/api/v1/settings", json={"model_api_key": "offline-read-key"})
    client.app.state.manager.model_transport = httpx.MockTransport(lambda request: httpx.Response(200, content=frames(content="first done").encode()))
    first = wait_run(client, client.post("/api/v1/runs", json={"task": "original write task", "permission": "full", "request_key": "resume-authority-first"}).json()["id"])
    calls = 0

    def provider(request):
        nonlocal calls
        calls += 1
        wire = json.loads(request.content)
        system = next(item["content"] for item in wire["messages"] if item["role"] == "system")
        assert '"permission": "read"' in system
        return httpx.Response(200, content=(frames(tool={"name": "write_file", "arguments": {"path": "forbidden.txt", "content": "denied"}}) if calls == 1 else frames(content="permission denied")).encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    response = client.post(f"/api/v1/runs/{first['id']}/continue", json={"permission": "read", "request_key": "resume-current-read", "max_calls": 3})
    assert response.status_code == 200
    continued = wait_run(client, response.json()["id"])
    assert continued["status"] == "failed"
    assert not (client.app.state.store.directory / "workspaces" / first["conversation_id"] / "forbidden.txt").exists()


def test_waiting_explanations_are_bounded_honest_redacted_and_settled(client):
    events = []
    narrator = ProgressNarrator(lambda kind, data: events.append({"kind": kind, **data}), client.app.state.manager.redact)
    secret = "sk-" + "a" * 30
    narrator.before("run_remote_command", {"purpose": "安装依赖 " + secret})
    narrator.command("one", "run_remote_command", "安装依赖 " + secret, "Downloading dependency\n", 20, 30)
    narrator.command("one", "run_remote_command", "安装依赖", "Downloading dependency\n", 28, 30)
    assert len(events) == 2
    narrator.command("one", "run_remote_command", "安装依赖", "Downloading dependency\n", 52, 30)
    assert "不能仅凭静默判断" in events[-1]["text"]
    assert secret not in json.dumps(events)
    narrator.after("run_remote_command", True, '{"ok":true,"exit_code":0}')
    assert events[-1]["finished"] and "退出码 0" in events[-2]["text"]


def test_batch_delete_is_atomic_and_excludes_only_selected_references(client):
    store, library = client.app.state.store, client.app.state.library
    ids = [client.post("/api/v1/conversations", json={"title": "batch fixture"}).json()["id"] for _ in range(3)]
    run = fixture_run(client, ids[0])
    inside = library.save("shared-only-selected.txt", b"selected output", run_id=run)
    outside = library.save("shared-with-retained.txt", b"retained output", run_id=run)
    upload = library.save("independent.txt", b"independent")
    store.message(ids[1], "user", "reuse " + inside["id"])
    store.message(ids[2], "user", "reuse " + outside["id"])
    for cid in ids[:2]:
        directory = store.directory / "workspaces" / cid
        directory.mkdir(parents=True)
        (directory / "data.txt").write_text("batch data")
    preview = client.post("/api/v1/conversations/batch/deletion-preview", json={"ids": ids[:2]})
    assert preview.status_code == 200 and preview.json()["conversations"] == 2
    response = client.post("/api/v1/conversations/batch/permanent", json={"ids": ids[:2]})
    assert response.status_code == 200, response.text
    assert response.json()["deleted_ids"] == ids[:2] and response.json()["shared_generated_files_retained"] == 1
    assert not store.one("SELECT id FROM files WHERE id=?", (inside["id"],))
    assert library.path(outside["id"]).is_file() and library.path(upload["id"]).is_file()
    assert client.get(f"/api/v1/conversations/{ids[2]}").status_code == 200


def test_batch_failure_restores_every_workspace_file_and_row(client, tmp_path):
    store, library = client.app.state.store, client.app.state.library
    ids = [client.post("/api/v1/conversations", json={"title": "rollback batch"}).json()["id"] for _ in range(2)]
    for cid in ids:
        workspace = store.directory / "workspaces" / cid
        workspace.mkdir(parents=True)
        (workspace / "retain.txt").write_text(cid)
    run = fixture_run(client, ids[-1])
    artifact = library.save("bad-path.txt", b"artifact", run_id=run)
    sentinel = tmp_path.parent / (uid() + ".txt")
    sentinel.write_text("outside data")
    store.execute("UPDATE files SET path=? WHERE id=?", (str(sentinel), artifact["id"]))
    try:
        response = client.post("/api/v1/conversations/batch/permanent", json={"ids": ids})
        assert response.status_code == 400
        for cid in ids:
            assert client.get(f"/api/v1/conversations/{cid}").status_code == 200
            assert (store.directory / "workspaces" / cid / "retain.txt").read_text() == cid
        assert sentinel.read_text() == "outside data"
        assert not client.app.state.manager.maintenance.is_set()
    finally:
        sentinel.unlink()


@pytest.mark.parametrize("ids", [[], ["invalid"], ["a" * 32] * 2, ["a" * 32], ["b" * 32] * 101])
def test_batch_delete_rejects_invalid_or_stale_selection(client, ids):
    assert client.post("/api/v1/conversations/batch/permanent", json={"ids": ids}).status_code in {400, 422}
    assert not client.app.state.manager.maintenance.is_set()
