import asyncio
import json
import os
import sys
import threading
import time

import httpx
from fastapi.testclient import TestClient

from app.config import Config
from app.main import create_app
from app.context import complete_history, token_count
from test_platform import frames, wait_run, client


def test_repeated_cancel_and_shutdown_cannot_interrupt_cleanup_or_release_the_slot(client, monkeypatch):
    entered, release = threading.Event(), threading.Event()

    def blocking_command(*args, **kwargs):
        entered.set()
        assert release.wait(4)
        return {"ok": False, "stopped": "cancelled", "output": "", "exit_code": -9}

    monkeypatch.setattr("app.agent.run_command", blocking_command)
    client.put("/api/v1/settings", json={"model_api_key": "offline-lifecycle-key"})
    requests = []

    def provider(request):
        requests.append(json.loads(request.content))
        body = frames(tool={"name": "execute_command", "arguments": {"command": "synthetic"}}) if len(requests) == 1 else frames(content="second completed")
        return httpx.Response(200, content=body.encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    first = client.post("/api/v1/runs", json={"task": "cancel repeatedly", "permission": "full", "request_key": "repeat-cancel"}).json()["id"]
    assert entered.wait(3)
    started = time.monotonic()
    client.post(f"/api/v1/runs/{first}/cancel")
    for _ in range(15):
        assert client.post(f"/api/v1/runs/{first}/cancel").status_code == 200
    second = client.post("/api/v1/runs", json={"task": "another conversation", "request_key": "after-cancel"}).json()["id"]
    assert client.get(f"/api/v1/runs/{second}").json()["status"] == "queued"

    async def interrupt_finalization():
        client.app.state.manager.tasks[first].cancel()
        await asyncio.sleep(.02)

    client.portal.call(interrupt_finalization)
    assert len(requests) == 1
    release.set()
    assert wait_run(client, first)["status"] == "cancelled"
    assert wait_run(client, second)["status"] == "completed"
    assert time.monotonic() - started < 2
    events = client.app.state.store.events(first)
    assert sum(event["kind"] == "cancelling" for event in events) == 1
    assert sum(event["kind"] == "finished" for event in events) == 1


def test_command_output_is_visible_before_completion_and_credentials_stay_redacted(client, caplog):
    secret = "sk-" + "a" * 30
    client.put("/api/v1/settings", json={"model_api_key": secret})
    command = ('& ' if os.name == 'nt' else '') + f'"{sys.executable}" -u -c "import time;print(\'STEP_ONE\',flush=True);print(\'{secret}\',flush=True);time.sleep(2);print(\'STEP_TWO\',flush=True)"'
    calls = 0

    def provider(request):
        nonlocal calls
        calls += 1
        body = frames(tool={"name": "execute_command", "arguments": {"command": command}}) if calls == 1 else frames(content="done")
        return httpx.Response(200, content=body.encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    ident = client.post("/api/v1/runs", json={"task": "live output", "permission": "full", "request_key": "live-output"}).json()["id"]
    deadline = time.monotonic() + 4
    while True:
        events = client.app.state.store.events(ident)
        if any(event["kind"] == "command.progress" and "STEP_ONE" in event["data"]["output"] for event in events):
            break
        assert time.monotonic() < deadline
        time.sleep(.02)
    assert not any(event["kind"] == "finished" for event in events)
    assert secret not in json.dumps(events)
    assert wait_run(client, ident)["status"] == "completed"
    assert "STEP_TWO" in json.dumps(client.app.state.store.events(ident))
    assert secret not in caplog.text


def test_long_conversation_and_tool_exchange_survive_a_real_app_restart(tmp_path):
    configuration = Config(tmp_path, "fixture-bootstrap")
    with TestClient(create_app(configuration)) as first:
        session = first.post("/api/v1/auth/setup", json={"name": "fixture", "password": "fixture-password", "setup_code": "fixture-bootstrap"}).json()["token"]
        first.headers["Authorization"] = "Bearer " + session
        first.put("/api/v1/settings", json={"model_api_key": "offline-checkpoint-key"})
        manager = first.app.state.manager
        cid = manager.conversation("long history fixture")
        for number in range(32):
            manager.store.message(cid, "user" if number % 2 == 0 else "assistant", f"history-anchor-{number}:" + "保留这段真实历史资料。" * 250)
        calls = 0

        def provider(request):
            nonlocal calls
            calls += 1
            body = json.loads(request.content)
            history = json.dumps(body["messages"], ensure_ascii=False)
            assert len(history) > 60000 and "history-anchor-0" in history and "history-anchor-31" in history
            answer = frames(tool={"name": "write_file", "arguments": {"path": "checkpoint.txt", "content": "actual-checkpoint-evidence"}}) if calls == 1 else frames(tool={"name": "read_file", "arguments": {"path": "checkpoint.txt"}}) if calls == 2 else frames(content="first task completed")
            return httpx.Response(200, content=answer.encode())

        manager.model_transport = httpx.MockTransport(provider)
        ident = first.post("/api/v1/runs", json={"conversation_id": cid, "task": "long context fixture", "permission": "workspace", "request_key": "checkpoint-first"}).json()["id"]
        assert wait_run(first, ident)["status"] == "completed"

    with TestClient(create_app(configuration)) as restarted:
        restarted.headers["Authorization"] = "Bearer " + session

        def resumed(request):
            messages = json.loads(request.content)["messages"]
            serialized = json.dumps(messages, ensure_ascii=False)
            assert "history-anchor-0" in serialized and "history-anchor-31" in serialized
            assert any(item["role"] == "tool" and "actual-checkpoint-evidence" in item["content"] for item in messages)
            assert sum(item.get("content") == "first task completed" for item in messages) == 1
            assert token_count(serialized) < 1048576
            return httpx.Response(200, content=frames(content="checkpoint restored").encode())

        restarted.app.state.manager.model_transport = httpx.MockTransport(resumed)
        ident = restarted.post("/api/v1/runs", json={"conversation_id": cid, "task": "continue after restart", "permission": "read", "request_key": "checkpoint-second"}).json()["id"]
        assert wait_run(restarted, ident)["status"] == "completed"
        events = restarted.app.state.store.events(ident)
        assert any(event["kind"] == "context.checkpoint_restored" and event["data"]["from_checkpoint"] for event in events)


def test_incomplete_parallel_tool_group_is_not_replayed_as_completed_evidence():
    messages = [
        {"role": "user", "content": "original goal"},
        {"role": "assistant", "tool_calls": [{"id": "one"}, {"id": "two"}]},
        {"role": "tool", "tool_call_id": "one", "content": "only first result"},
    ]
    assert complete_history(messages) == messages[:1]
