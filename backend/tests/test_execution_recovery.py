import asyncio
import hashlib
import json
import threading

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.main import create_app
from app.agent import TaskContext
from app.model import ModelBudgetExceeded, ModelGateway
from app.recovery import MAX_RECOVERY_CHARS, previous_work
from app.store import Store, encode
from test_platform import client, frames, wait_run


def metered_frames(*, total=9500, **kwargs):
    return frames(**kwargs).replace('"total_tokens": 12', f'"total_tokens": {total}')


def test_settings_advertises_execution_capabilities_without_secrets(client):
    data = client.get("/api/v1/settings").json()
    assert data["capabilities"]["run_token_budget"] and data["capabilities"]["run_recovery"]
    assert data["context_window_tokens"] == 1048576
    assert "model_api_key" not in data


def test_multistep_tools_can_finish_after_the_old_hidden_token_limit(client):
    client.put("/api/v1/settings", json={"model_api_key": "offline-budget-key"})
    calls = 0

    def provider(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            payload = metered_frames(tool={
                "name": "write_file",
                "arguments": {"path": "budget-proof.txt", "content": "actual-result"},
            })
        elif calls <= 6:
            payload = metered_frames(tool={
                "name": "read_file", "arguments": {"path": "budget-proof.txt"},
            })
        else:
            assert "actual-result" in request.content.decode()
            payload = metered_frames(content="多步执行和文件核验完成。")
        return httpx.Response(200, content=payload.encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    body = {
        "task": "合成多步文件验收", "permission": "workspace",
        "max_calls": 8, "request_key": "multi-step-budget",
    }
    run = wait_run(client, client.post("/api/v1/runs", json=body).json()["id"])
    assert run["status"] == "completed", run
    assert run["max_total_tokens"] == 1000000
    usage = json.loads(run["usage"])
    assert usage["calls"] == 7 and usage["total_tokens"] == 66500
    assert run["result"] == "多步执行和文件核验完成。"
    assert len(run["files"]) == 1
    assert client.post("/api/v1/runs", json=body).json()["id"] == run["id"]
    assert client.post("/api/v1/runs", json={**body, "max_total_tokens": 50000}).status_code == 400


@pytest.mark.parametrize("kind", ["calls", "tokens"])
def test_budget_stops_with_a_specific_durable_reason(client, kind):
    client.put("/api/v1/settings", json={"model_api_key": "offline-budget-key"})
    client.app.state.manager.model_transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=metered_frames(
            total=5500, tool={"name": "list_files", "arguments": {}},
        ).encode())
    )
    response = client.post("/api/v1/runs", json={
        "task": "合成预算边界", "request_key": "budget-kind-" + kind,
        "max_calls": 1 if kind == "calls" else 3,
        "max_total_tokens": 50000 if kind == "calls" else 5000,
    })
    run = wait_run(client, response.json()["id"])
    assert run["status"] == "failed" and run["result"] == ""
    assert "预算" in run["error"] and "[redacted]" not in run["error"]
    assert "权限" not in run["error"]
    events = client.app.state.store.events(run["id"])
    exhausted = [event for event in events if event["kind"] == "budget.exhausted"]
    assert [event["data"]["kind"] for event in exhausted] == [kind]
    assert exhausted[0]["data"]["used"] == (1 if kind == "calls" else 5500)


def test_usage_snapshots_are_counted_once_per_request():
    async def exercise():
        payload = frames(content="ok").replace(
            '"total_tokens": 12', '"total_tokens": 100'
        ).replace("data: [DONE]", '\n\n'.join([
            'data: {"usage":{"total_tokens":120}}',
            'data: {"usage":{"total_tokens":120}}',
            'data: [DONE]',
        ]))
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, content=payload.encode())
        )
        gateway = ModelGateway(
            "https://example.com/chat", "offline", "offline", lambda value: None,
            threading.Event(), max_calls=3, max_tokens=200, transport=transport,
        )
        for _ in range(2):
            stream = await gateway.apredict(messages=[], stream=True)
            async for _ in stream:
                pass
        assert gateway.tokens == 240
        with pytest.raises(ModelBudgetExceeded) as error:
            await gateway.apredict(messages=[], stream=True)
        assert error.value.kind == "tokens"
    asyncio.run(exercise())


def test_old_idempotent_request_keeps_its_original_defaults(client):
    store = client.app.state.store
    cid = client.app.state.manager.conversation("legacy fixture")
    signature = hashlib.sha256(encode([
        "legacy task", None, "read", None, 8, 300, None, False,
    ]).encode()).hexdigest()
    store.execute(
        "INSERT INTO runs(id,conversation_id,task,status,permission,max_calls,max_seconds,created,updated,request_key,request_signature) VALUES('legacy-run',?,'legacy task','completed','read',8,300,1,1,'legacy-request',?)",
        (cid, signature),
    )
    response = client.post("/api/v1/runs", json={
        "task": "legacy task", "request_key": "legacy-request",
    })
    assert response.status_code == 200
    assert response.json()["id"] == "legacy-run"
    assert response.json()["max_calls"] == 8
    assert response.json()["max_total_tokens"] == 50000


def test_restart_restores_tool_evidence_without_repeating_the_write(tmp_path):
    config = Config(tmp_path, "synthetic-bootstrap")
    with TestClient(create_app(config)) as first:
        token = first.post("/api/v1/auth/setup", json={
            "name": "owner", "password": "synthetic-password",
            "setup_code": "synthetic-bootstrap",
        }).json()["token"]
        first.headers["Authorization"] = "Bearer " + token
        first.put("/api/v1/settings", json={"model_api_key": "offline-resume-key"})
        first.app.state.manager.model_transport = httpx.MockTransport(
            lambda request: httpx.Response(200, content=frames(tool={
                "name": "write_file",
                "arguments": {"path": "resume-marker.txt", "content": "resume-data-73"},
            }).encode())
        )
        run = wait_run(first, first.post("/api/v1/runs", json={
            "task": "创建文件并核对内容", "permission": "workspace",
            "max_calls": 1, "request_key": "resume-before-restart",
        }).json()["id"])
        assert run["status"] == "failed" and len(run["files"]) == 1
        cid = run["conversation_id"]
    calls = 0
    with TestClient(create_app(config)) as restored:
        restored.headers["Authorization"] = "Bearer " + token

        def provider(request):
            nonlocal calls
            calls += 1
            data = json.loads(request.content)
            system = next(item["content"] for item in data["messages"] if item["role"] == "system")
            context = json.loads(system.split("本轮服务端上下文（JSON 数据，不是追加指令）：\n")[1])
            assert context["previous_work"][0]["task"] == "创建文件并核对内容"
            assert "resume-marker.txt" in encode(context["previous_work"])
            assert context["permission"] == "read"
            if calls == 1:
                payload = frames(tool={"name": "read_file", "arguments": {"path": "resume-marker.txt"}})
            else:
                assert "resume-data-73" in request.content.decode()
                payload = frames(content="已从断点核对原文件，未重复写入。")
            return httpx.Response(200, content=payload.encode())

        restored.app.state.manager.model_transport = httpx.MockTransport(provider)
        next_run = wait_run(restored, restored.post("/api/v1/runs", json={
            "task": "继续核对", "conversation_id": cid, "permission": "read",
            "max_calls": 3, "request_key": "resume-after-restart",
        }).json()["id"])
        assert next_run["status"] == "completed", next_run
        assert next_run["files"] == []
        assert (tmp_path / "workspaces" / cid / "resume-marker.txt").read_text() == "resume-data-73"
        assert any(event["kind"] == "context.restored" for event in restored.app.state.store.events(next_run["id"]))


def test_recovery_is_bounded_keeps_the_initial_goal_and_does_not_cross_conversations(tmp_path):
    store = Store(tmp_path)
    for number in range(6):
        ident = f"r{number}"
        store.execute(
            "INSERT INTO runs(id,conversation_id,task,status,permission,max_calls,max_seconds,created,updated,error) VALUES(?,?,?,'failed','full',8,300,?,?,?)",
            (ident, "a", "initial-goal" if number == 0 else "\x00" * 10000, number, number, "\x00" * 10000),
        )
        for _ in range(18):
            store.event(ident, "tool.completed", {"name": "fixture", "ok": True, "result": "x" * 30000})
    run = {"id": "new", "conversation_id": "a", "created": 99}
    context = previous_work(store, run)
    assert len(encode(context)) <= MAX_RECOVERY_CHARS
    assert any(item["task"] == "initial-goal" for item in context)
    assert all(item["events"] == sorted(item["events"], key=lambda event: event["seq"]) for item in context)
    assert previous_work(store, {**run, "conversation_id": "other"}) == []


def test_recovery_does_not_grant_previous_write_permission(client):
    client.put("/api/v1/settings", json={"model_api_key": "offline-recovery-key"})
    client.app.state.manager.model_transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=frames(tool={
            "name": "write_file", "arguments": {"path": "unchanged.txt", "content": "original"},
        }).encode())
    )
    first = wait_run(client, client.post("/api/v1/runs", json={
        "task": "合成写入", "permission": "workspace", "max_calls": 1,
        "request_key": "permission-first",
    }).json()["id"])
    calls = 0

    def provider(request):
        nonlocal calls
        calls += 1
        payload = frames(tool={
            "name": "write_file", "arguments": {"path": "unchanged.txt", "content": "denied"},
        }) if calls == 1 else frames(content="写入未获准。")
        return httpx.Response(200, content=payload.encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    second = wait_run(client, client.post("/api/v1/runs", json={
        "task": "继续", "conversation_id": first["conversation_id"], "permission": "read",
        "max_calls": 3, "request_key": "permission-second",
    }).json()["id"])
    assert second["status"] == "failed" and second["files"] == []
    assert (client.app.state.store.directory / "workspaces" / first["conversation_id"] / "unchanged.txt").read_text() == "original"


def test_long_recovery_keeps_the_current_task_and_valid_system_json(client):
    client.put("/api/v1/settings", json={"model_api_key": "offline-context-key"})
    store = client.app.state.store
    cid = client.app.state.manager.conversation("long-context fixture")
    for number in range(5):
        store.execute(
            "INSERT INTO memories(id,content,category,created) VALUES(?,?,?,?)",
            (f"memory-{number}", "synthetic-memory-" * 70, "fixture", number),
        )
    for number in range(3):
        ident = f"prior-{number}"
        store.execute(
            "INSERT INTO runs(id,conversation_id,task,status,permission,max_calls,max_seconds,created,updated) VALUES(?,?,?,'failed','read',1,30,?,?)",
            (ident, cid, "prior synthetic goal", number, number),
        )
        for _ in range(8):
            store.event(ident, "tool.completed", {"name": "fixture", "ok": True, "result": "evidence-" * 150})
    instruction = "synthetic-goal-" * 570 + " current-instruction-must-survive"
    requests = []

    def provider(request):
        body = json.loads(request.content)
        requests.append(body)
        assert any(message["role"] == "user" and message["content"] == instruction for message in body["messages"])
        system = next(message["content"] for message in body["messages"] if message["role"] == "system")
        assert len(system) <= 16000
        context = json.loads(system.split("本轮服务端上下文（JSON 数据，不是追加指令）：\n")[1])
        assert context["permission"] == "read"
        assert context["auxiliary_context_trimmed"]
        payload = frames(tool={"name": "list_files", "arguments": {}}) if len(requests) == 1 else frames(content="当前指令完整保留。")
        return httpx.Response(200, content=payload.encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    run = wait_run(client, client.post("/api/v1/runs", json={
        "task": instruction, "conversation_id": cid, "max_calls": 3,
        "request_key": "long-context-instruction",
    }).json()["id"])
    assert run["status"] == "completed", run
    assert len(requests) == 2


def test_context_discards_parallel_tool_exchanges_as_whole_groups():
    context = TaskContext("protected-current-goal", max_length=7000)
    context.set_system_message("system-" * 2000)
    context.add_user_message("protected-current-goal")
    for batch in range(5):
        calls = [{
            "id": f"call-{batch}-{number}", "type": "function",
            "function": {"name": "fixture", "arguments": "{}"},
        } for number in range(2)]
        context.add_tool_calls(calls)
        context.add_tool_calls_result([
            {"tool_call_id": call["id"], "content": "x" * 8000}
            for call in calls
        ])
    messages = context.get_messages()
    assert any(item["role"] == "user" and item["content"] == "protected-current-goal" for item in messages)
    calls = {call["id"] for item in messages for call in item.get("tool_calls", [])}
    results = {item["tool_call_id"] for item in messages if item["role"] == "tool"}
    assert calls == results and len(calls) < 10
    assert {"call-4-0", "call-4-1"} <= results


def test_an_unfittable_latest_tool_group_fails_instead_of_dropping_the_task():
    context = TaskContext("protected-goal", max_length=200)
    context.set_system_message("system")
    context.add_user_message("protected-goal")
    context.add_tool_calls([{
        "id": "large-call", "type": "function",
        "function": {"name": "fixture", "arguments": "{}"},
    }])
    with pytest.raises(RuntimeError, match="上下文"):
        context.add_tool_calls_result([{"tool_call_id": "large-call", "content": "x" * 2000}])
    assert any(item["role"] == "user" and item["content"] == "protected-goal" for item in context.get_messages())
