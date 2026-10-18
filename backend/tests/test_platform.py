import asyncio
import json
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.execution import Policy, execute_process
from app.main import create_app
from app.model import ModelGateway


@pytest.fixture
def client(tmp_path):
    application = create_app(Config(tmp_path, "local-bootstrap"))
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/auth/setup",
            json={
                "name": "主人",
                "password": "private-test-password",
                "setup_code": "local-bootstrap",
            },
        )
        client.headers["Authorization"] = "Bearer " + response.json()["token"]
        yield client


def test_initialization_is_private_and_single_owner(tmp_path):
    with TestClient(create_app(Config(tmp_path, "private-code"))) as client:
        assert client.get("/api/v1/auth/status").json() == {
            "configured": False,
            "registration": "disabled",
            "email_enabled": False,
        }
        assert client.get("/api/v1/files").status_code == 401
        assert (
            client.post(
                "/api/v1/auth/setup",
                json={
                    "name": "me",
                    "password": "long-password-123",
                    "setup_code": "wrong",
                },
            ).status_code
            == 403
        )
        good = {
            "name": "me",
            "password": "long-password-123",
            "setup_code": "private-code",
        }
        assert client.post("/api/v1/auth/setup", json=good).status_code == 200
        assert client.post("/api/v1/auth/setup", json=good).status_code == 409
        assert client.post("/api/v1/auth/register", json=good).status_code == 404


def test_unicode_owner_login_and_password_revocation(client):
    first = client.headers["Authorization"]
    response = client.post(
        "/api/v1/auth/login", json={"name": "主人", "password": "private-test-password"}
    )
    assert response.status_code == 200
    response = client.put(
        "/api/v1/auth/password",
        json={"current": "private-test-password", "password": "new-private-password"},
    )
    assert response.status_code == 200
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": first}).status_code
        == 401
    )
    assert (
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer " + response.json()["token"]},
        ).status_code
        == 200
    )


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/dashboard",
        "/api/v1/skills",
        "/api/v1/skills/status",
        "/api/v1/records?kind=article",
        "/api/v1/servers",
        "/api/v1/memories",
        "/api/v1/settings",
        "/api/v1/runs",
        "/api/v1/schedules",
        "/api/v1/audit",
    ],
)
def test_private_routes_require_auth(client, path):
    assert (
        client.get(path, headers={"Authorization": "Bearer invalid"}).status_code == 401
    )


@pytest.mark.parametrize(
    "kind,payload",
    [
        ("article", {"title": "私人文章", "content": "内容", "published": False}),
        ("collection", {"title": "我的项目", "description": "合集"}),
        ("photo", {"title": "日常", "category": "生活"}),
        ("poem", {"content": "山有木兮木有枝", "author": "佚名"}),
        (
            "resume",
            {
                "name": "主人",
                "experiences": [{"title": "项目", "image_file_id": "legacy-reference"}],
            },
        ),
    ],
)
def test_content_crud_preserves_payload(client, kind, payload):
    created = client.post("/api/v1/records", json={"kind": kind, "payload": payload})
    assert created.status_code == 200
    ident = created.json()["id"]
    assert (
        client.get("/api/v1/records", params={"kind": kind}).json()[0]["payload"]
        == payload
    )
    updated = {**payload, "note": "更新"}
    assert (
        client.put(
            "/api/v1/records/" + ident, json={"kind": kind, "payload": updated}
        ).json()["payload"]
        == updated
    )
    assert client.delete("/api/v1/records/" + ident).status_code == 200
    assert client.get("/api/v1/records", params={"kind": kind}).json() == []


def test_file_search_download_and_active_content(client):
    response = client.post(
        "/api/v1/files",
        files={"file": ("资料.md", "私人苹果项目的部署记录".encode(), "text/markdown")},
    )
    assert response.status_code == 200
    ident = response.json()["id"]
    assert client.get("/api/v1/files/search?q=苹果").json()[0]["file_id"] == ident
    assert (
        client.get(f"/api/v1/files/{ident}/download").content
        == "私人苹果项目的部署记录".encode()
    )
    assert (
        client.get(
            f"/api/v1/files/{ident}/download", headers={"Authorization": "Bearer bad"}
        ).status_code
        == 401
    )
    script = client.post(
        "/api/v1/files",
        files={"file": ("untrusted.html", b"<script>alert(1)</script>", "text/html")},
    ).json()
    download = client.get(f"/api/v1/files/{script['id']}/download?inline=true")
    assert "attachment" in download.headers["content-disposition"]
    assert download.headers["content-type"] == "application/octet-stream"
    assert "sandbox" in download.headers["content-security-policy"]
    assert client.delete(f"/api/v1/files/{ident}").status_code == 200
    assert client.get(f"/api/v1/files/{ident}/download").status_code == 400


def test_secrets_never_return_to_frontend(client):
    response = client.put(
        "/api/v1/settings",
        json={"model_api_key": "test-secret-do-not-return", "model": "deepseek-flash"},
    )
    assert response.status_code == 200
    assert "test-secret" not in response.text
    assert response.json()["model_configured"] is True
    stored = client.app.state.store.setting("secret:model_api_key")
    assert "test-secret" not in stored
    server = client.post(
        "/api/v1/servers",
        json={
            "name": "测试机",
            "host": "example.org",
            "private_key": "SECRET-PRIVATE-KEY",
        },
    ).json()
    assert server["key_configured"] and "SECRET-PRIVATE-KEY" not in json.dumps(server)
    assert "SECRET-PRIVATE-KEY" not in client.get("/api/v1/servers").text


@pytest.mark.parametrize(
    "url",
    [
        "http://remote.example/v1",
        "https://user:password@example.com/api",
        "file:///tmp/key",
        "https://example.com/?key=secret",
    ],
)
def test_model_urls_reject_credential_leak_routes(client, url):
    assert client.put("/api/v1/settings", json={"model_url": url}).status_code == 400


def test_task_permission_rejects_write_and_traversal(client, tmp_path):
    manager = client.app.state.manager
    run = {
        "id": "local-test",
        "conversation_id": "workspace",
        "permission": "read",
        "server_id": None,
    }
    tools = manager._tools(run, threading.Event())
    with pytest.raises(PermissionError):
        tools.get_tool("write_file")("notes.txt", "content")
    with pytest.raises(PermissionError):
        tools.get_tool("execute_command")("echo no")
    with pytest.raises(PermissionError):
        Policy("workspace", tmp_path).path("../outside.txt")
    run["permission"] = "workspace"
    tools = manager._tools(run, threading.Event())
    assert (
        tools.get_tool("write_file")("nested/notes.txt", "内容")["written"]
        == "nested/notes.txt"
    )
    with pytest.raises(PermissionError):
        tools.get_tool("execute_command")("echo no")
    with pytest.raises(PermissionError):
        tools.get_tool("run_remote_command")("echo no")


def frames(content=None, tool=None):
    chunks = []
    if content:
        chunks.append(
            {"choices": [{"delta": {"content": content}, "finish_reason": None}]}
        )
    if tool:
        args = json.dumps(tool["arguments"], ensure_ascii=False)
        chunks.extend(
            [
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {
                                        "index": 0,
                                        "id": "call-1",
                                        "type": "function",
                                        "function": {
                                            "name": tool["name"],
                                            "arguments": args[:5],
                                        },
                                    }
                                ]
                            },
                            "finish_reason": None,
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {"index": 0, "function": {"arguments": args[5:]}}
                                ]
                            },
                            "finish_reason": None,
                        }
                    ]
                },
            ]
        )
    chunks.append(
        {
            "choices": [
                {"delta": {}, "finish_reason": "tool_calls" if tool else "stop"}
            ],
            "usage": {"total_tokens": 12, "prompt_tokens": 8, "completion_tokens": 4},
        }
    )
    return (
        "\n\n".join(
            "data: " + json.dumps(chunk, ensure_ascii=False) for chunk in chunks
        )
        + "\n\ndata: [DONE]\n\n"
    )


def wait_run(client, ident):
    for _ in range(1500):
        run = client.get("/api/v1/runs/" + ident).json()
        if run["status"] not in {"queued", "running", "cancelling"}:
            return run
        time.sleep(0.02)
    pytest.fail("local mock run did not complete")


def test_paginated_skill_reference_reaches_the_next_model_call_intact(client):
    client.put("/api/v1/settings", json={"model_api_key": "offline-page-key"})
    router = client.app.state.router
    ident, path = next(
        (card["id"], item["path"])
        for card in router.packages.cards.values()
        for item in card["files"]
        if item["path"].endswith("implementation-playbook.md")
    )
    received = {}

    def provider(request):
        body = json.loads(request.content)
        results = [message for message in body["messages"] if message["role"] == "tool"]
        offset = 0
        if results:
            page = json.loads(results[-1]["content"])
            assert page["license"] and page["source_url"]
            received[page["offset"]] = page["text"]
            offset = page["next_offset"]
        output = (
            frames(content="已读完所有参考页。")
            if offset is None
            else frames(
                tool={
                    "name": "read_skill_resource",
                    "arguments": {"name": ident, "path": path, "offset": offset},
                }
            )
        )
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=output.encode()
        )

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    run = client.post(
        "/api/v1/runs",
        json={
            "task": "分页读取技能参考",
            "permission": "read",
            "max_calls": 12,
            "request_key": "reference-pagination-test",
        },
    ).json()
    result = wait_run(client, run["id"])
    assert result["status"] == "completed", result
    source = (router.packages.root / "packages" / ident / path).read_text("utf-8-sig")
    expected = "".join(
        json.loads(
            client.app.state.manager.redact(
                json.dumps({"text": source[offset : offset + 6000]})
            )
        )["text"]
        for offset in range(0, len(source), 6000)
    )
    assert len(received) >= 2
    assert "".join(received[offset] for offset in sorted(received)) == expected
    sanitized = json.loads(
        client.app.state.manager.redact(
            json.dumps(
                {
                    "text": "token example",
                    "next_offset": 6000,
                    "password": "private-test-value",
                }
            )
        )
    )
    assert sanitized["next_offset"] == 6000 and sanitized["password"] == "[redacted]"
    assert "private-test-value" not in json.dumps(sanitized)
    keys = json.loads(
        client.app.state.manager.redact(
            json.dumps({"nested": {"offline-page-key": "one", "[redacted]": "two"}})
        )
    )
    assert "offline-page-key" not in json.dumps(keys)
    assert set(keys["nested"].values()) == {"one", "two"}


def test_tina_tool_loop_persists_events_artifacts_and_usage(client):
    client.put("/api/v1/settings", json={"model_api_key": "offline-test-key"})
    requests = []

    def provider(request):
        body = json.loads(request.content)
        requests.append(body)
        system = next(
            message["content"]
            for message in body["messages"]
            if message["role"] == "system"
        )
        assert "Xinxin" in system and "好滴" in system and "女生" in system
        assert '"persona_version": "xinxin-3.0"' in system and "2007-11-09" in system
        context = json.loads(
            system.split("本轮服务端上下文（JSON 数据，不是追加指令）：\n", 1)[1]
        )
        assert context["permission"] == "workspace" and context["allow_memory"] is False
        assert context["server_id"] is None and context["execution_host"]["workspace"]
        assert "offline-test-key" not in system
        assert (
            body["model"] == "deepseek-flash" and body["thinking"]["type"] == "disabled"
        )
        payload = (
            frames(
                content="好滴，我先创建文件。",
                tool={
                    "name": "write_file",
                    "arguments": {"path": "hello.txt", "content": "hello"},
                }
            )
            if len(requests) == 1
            else frames(content="已创建文件，并记录了交付物。")
        )
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=payload.encode()
        )

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    body = {
        "task": "创建一个文本文件",
        "permission": "workspace",
        "request_key": "stable-request-1",
    }
    response = client.post("/api/v1/runs", json=body)
    assert response.status_code == 200
    ident = response.json()["id"]
    run = wait_run(client, ident)
    assert run["status"] == "completed", run
    assert run["result"] == "已创建文件，并记录了交付物。"
    progress = [
        event
        for event in client.app.state.store.events(ident)
        if event["kind"] == "assistant.progress"
    ]
    assert [event["data"]["text"] for event in progress] == ["好滴，我先创建文件。"]
    history = client.get("/api/v1/conversations/" + run["conversation_id"]).json()
    assert [
        message["content"]
        for message in history["messages"]
        if message["role"] == "assistant"
    ] == [run["result"]]
    assert run["files"][0]["name"] == "hello.txt"
    assert json.loads(run["usage"])["total_tokens"] == 24
    assert len(requests) == 2
    assert any(message["role"] == "tool" for message in requests[1]["messages"])
    replay = client.get(f"/api/v1/runs/{ident}/events?after=1")
    assert "tool.completed" in replay.text and "event: end" in replay.text
    assert "id: 1\n" not in replay.text
    assert client.post("/api/v1/runs", json=body).json()["id"] == ident
    assert (
        client.post(
            "/api/v1/skills/coding-workspace/feedback",
            json={"run_id": ident, "reward": 1},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/skills/coding-workspace/feedback",
            json={"run_id": ident, "reward": 1},
        ).status_code
        == 400
    )
    from app.skills import SkillRouter

    restored = SkillRouter(client.app.state.store)
    assert restored.bandit.n_updates == 1


@pytest.mark.parametrize("max_calls,completed", [(2, False), (3, True)])
def test_progress_survives_replay_but_is_not_saved_as_the_final_answer(
    client, max_calls, completed
):
    client.put("/api/v1/settings", json={"model_api_key": "offline-progress-key"})
    calls = 0

    def provider(request):
        nonlocal calls
        calls += 1
        payload = (
            frames(
                content=f"进度{calls}：我再确认一下。",
                tool={"name": "list_files", "arguments": {}},
            )
            if calls <= 2
            else frames(content="检查完成。\n\n```text\n/demo\n```\n\n- 已核对")
        )
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=payload.encode()
        )

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    response = client.post(
        "/api/v1/runs",
        json={
            "task": "检查合成工作区",
            "permission": "read",
            "max_calls": max_calls,
            "request_key": "progress-budget-case",
        },
    )
    run = wait_run(client, response.json()["id"])
    assert run["status"] == ("completed" if completed else "failed")
    events = client.app.state.store.events(run["id"])
    progress = [event for event in events if event["kind"] == "assistant.progress"]
    assert [event["data"]["text"] for event in progress] == [
        "进度1：我再确认一下。",
        "进度2：我再确认一下。",
    ]
    draft = ""
    for event in events:
        if event["kind"] == "delta":
            draft += event["data"]["text"]
        elif event["kind"] == "assistant.progress":
            draft = ""
    assert draft == run["result"]
    history = client.get("/api/v1/conversations/" + run["conversation_id"]).json()
    answers = [
        message["content"]
        for message in history["messages"]
        if message["role"] == "assistant"
    ]
    if completed:
        assert answers == ["检查完成。\n\n```text\n/demo\n```\n\n- 已核对"]
    else:
        assert answers == [] and run["result"] == ""
        assert "最终答复" in run["error"]


@pytest.mark.parametrize("stage", ["tool-fragment", "direct-answer", "after-tool"])
def test_disconnected_model_drafts_remain_progress_not_final_history(client, stage):
    client.put("/api/v1/settings", json={"model_api_key": "offline-disconnect-key"})
    calls = 0
    partial = "我先查看工作区。" if stage == "tool-fragment" else "还未完整的答复"

    def provider(request):
        nonlocal calls
        calls += 1
        if stage == "after-tool" and calls == 1:
            payload = frames(
                content="我先检查一下。",
                tool={"name": "list_files", "arguments": {}},
            )
        else:
            deltas = [{"content": partial}]
            if stage == "tool-fragment":
                deltas.append(
                    {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "incomplete-call",
                                "function": {"name": "list_files", "arguments": "{"},
                            }
                        ]
                    }
                )
            payload = "".join(
                "data: "
                + json.dumps({"choices": [{"delta": delta, "finish_reason": None}]})
                + "\n\n"
                for delta in deltas
            )
        return httpx.Response(200, content=payload.encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    response = client.post(
        "/api/v1/runs",
        json={
            "task": "合成断流验收",
            "permission": "read",
            "max_calls": 3,
            "request_key": "disconnect-" + stage,
        },
    )
    run = wait_run(client, response.json()["id"])
    assert run["status"] == "failed" and "模型输出未完整结束" in run["error"]
    assert run["result"] == ""
    events = client.app.state.store.events(run["id"])
    progress = [event for event in events if event["kind"] == "assistant.progress"]
    assert progress[-1]["data"]["text"] == partial
    tools = [event for event in events if event["kind"] == "tool.started"]
    assert len(tools) == (1 if stage == "after-tool" else 0)
    history = client.get("/api/v1/conversations/" + run["conversation_id"]).json()
    assert not any(message["role"] == "assistant" for message in history["messages"])


def test_cancelled_model_draft_remains_available_as_progress_only(client):
    client.put("/api/v1/settings", json={"model_api_key": "offline-cancel-key"})

    class WaitingStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            payload = {
                "choices": [
                    {"delta": {"content": "尚未完成"}, "finish_reason": None}
                ]
            }
            yield ("data: " + json.dumps(payload) + "\n\n").encode()
            while True:
                await asyncio.sleep(1)

    client.app.state.manager.model_transport = httpx.MockTransport(
        lambda request: httpx.Response(200, stream=WaitingStream())
    )
    response = client.post(
        "/api/v1/runs",
        json={"task": "合成取消验收", "request_key": "cancel-progress"},
    )
    ident = response.json()["id"]
    deadline = time.monotonic() + 5
    while not any(
        event["kind"] == "delta" for event in client.app.state.store.events(ident)
    ):
        assert time.monotonic() < deadline, "Model did not yield its draft"
        time.sleep(0.01)
    client.post("/api/v1/runs/" + ident + "/cancel")
    run = wait_run(client, ident)
    assert run["status"] == "cancelled" and run["result"] == ""
    events = client.app.state.store.events(ident)
    progress = [event for event in events if event["kind"] == "assistant.progress"]
    assert [event["data"]["text"] for event in progress] == ["尚未完成"]
    assert sum(event["kind"] == "finished" for event in events) == 1
    history = client.get("/api/v1/conversations/" + run["conversation_id"]).json()
    assert not any(message["role"] == "assistant" for message in history["messages"])


def test_missing_model_key_is_actionable_not_fake_success(client):
    response = client.post(
        "/api/v1/runs", json={"task": "部署网站", "request_key": "no-key-request"}
    )
    assert response.status_code == 400 and "密钥" in response.json()["detail"]
    assert client.get("/api/v1/runs").json() == []


def test_managed_process_cancel_prevents_late_side_effect(tmp_path):
    flag = threading.Event()
    target = tmp_path / "late.txt"
    command = [
        sys.executable,
        "-c",
        "import time;from pathlib import Path;time.sleep(3);Path('late.txt').write_text('bad')",
    ]
    result = []
    worker = threading.Thread(
        target=lambda: result.append(execute_process(command, tmp_path, flag, 10))
    )
    worker.start()
    time.sleep(0.15)
    flag.set()
    worker.join(timeout=8)
    assert not worker.is_alive()
    assert result[0]["stopped"] == "cancelled" and not result[0]["ok"]
    assert not target.exists()


def test_restart_preserves_history_and_marks_inflight_interrupted(client):
    store = client.app.state.store
    store.execute(
        "INSERT INTO conversations(id,title,created,updated) VALUES('c','test',1,1)"
    )
    store.execute(
        "INSERT INTO runs(id,conversation_id,task,status,permission,max_calls,max_seconds,created,updated) VALUES('r','c','task','running','read',2,30,1,1)"
    )
    from app.store import Store

    restarted = Store(store.directory)
    assert (
        restarted.one("SELECT status FROM runs WHERE id='r'")["status"] == "interrupted"
    )
    assert (
        restarted.one("SELECT title FROM conversations WHERE id='c'")["title"] == "test"
    )


def test_model_stream_disconnect_cannot_be_success():
    async def exercise():
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=b'data: {"choices":[{"delta":{"content":"partial"},"finish_reason":null}]}\n\n',
            )
        )
        gateway = ModelGateway(
            "https://example.com/chat",
            "test",
            "test",
            lambda value: None,
            threading.Event(),
            transport=transport,
        )
        stream = await gateway.apredict(
            messages=[{"role": "user", "content": "hello"}], stream=True
        )
        with pytest.raises(RuntimeError):
            async for _ in stream:
                pass

    asyncio.run(exercise())


def test_plot_job_produces_three_real_artifacts(client):
    file = client.post(
        "/api/v1/files",
        files={"file": ("series.csv", b"x,y\n1,2\n2,5\n3,4", "text/csv")},
    ).json()
    assert client.get(f"/api/v1/files/{file['id']}/columns").json()["columns"] == [
        "x",
        "y",
    ]
    response = client.post(
        "/api/v1/tools/plot",
        json={
            "file_id": file["id"],
            "x": "x",
            "y": "y",
            "title": "Local verification",
            "request_key": "plot-verification",
        },
    )
    run = wait_run(client, response.json()["id"])
    assert run["status"] == "completed", run
    names = {file["name"] for file in run["files"]}
    assert names == {"xinxin-figure.png", "xinxin-figure.pdf", "xinxin-figure.py"}
    png = next(file for file in run["files"] if file["name"].endswith(".png"))
    assert client.get(f"/api/v1/files/{png['id']}/download").content.startswith(
        b"\x89PNG"
    )


def test_unresolved_tool_denial_cannot_be_completed(client):
    client.put("/api/v1/settings", json={"model_api_key": "offline-test"})
    calls = []

    def provider(request):
        calls.append(request)
        data = (
            frames(
                tool={
                    "name": "write_file",
                    "arguments": {"path": "denied.txt", "content": "no"},
                }
            )
            if len(calls) == 1
            else frames(content="已完成写入。")
        )
        return httpx.Response(200, content=data.encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    result = client.post(
        "/api/v1/runs",
        json={"task": "写文件", "permission": "read", "request_key": "denial-request"},
    ).json()
    run = wait_run(client, result["id"])
    assert run["status"] == "failed" and "工具" in run["error"]
    assert run["files"] == []


def test_conflicting_idempotency_key_rejects_different_operation(client):
    file = client.post(
        "/api/v1/files", files={"file": ("a.csv", b"x,y\n1,2\n2,3", "text/csv")}
    ).json()
    payload = {
        "file_id": file["id"],
        "x": "x",
        "y": "y",
        "title": "Same title",
        "request_key": "plot-stable-id",
    }
    original = client.post("/api/v1/tools/plot", json=payload).json()
    wait_run(client, original["id"])
    assert (
        client.post("/api/v1/tools/plot", json=payload).json()["id"] == original["id"]
    )
    assert (
        client.post("/api/v1/tools/plot", json={**payload, "kind": "bar"}).status_code
        == 400
    )


def test_server_edit_preserves_encrypted_key_and_schedule_scope(client):
    server = client.post(
        "/api/v1/servers",
        json={"name": "node", "host": "example.org", "private_key": "PRIVATE"},
    ).json()
    body = {"name": "renamed", "host": "new.example.org", "private_key": ""}
    assert client.put("/api/v1/servers/" + server["id"], json=body).json()[
        "key_configured"
    ]
    assert client.app.state.auth.secret("ssh:" + server["id"]) == "PRIVATE"
    task = {
        "title": "Review server",
        "task": "检查状态",
        "interval_minutes": 60,
        "permission": "full",
        "server_id": server["id"],
    }
    schedule = client.post("/api/v1/schedules", json=task).json()
    assert client.get("/api/v1/schedules").json()[0]["permission"] == "full"
    assert (
        client.put(
            "/api/v1/schedules/" + schedule["id"], json={**task, "enabled": False}
        ).status_code
        == 200
    )
    assert not client.get("/api/v1/schedules").json()[0]["enabled"]


def test_password_whitespace_is_not_silently_changed(tmp_path):
    with TestClient(create_app(Config(tmp_path, "code"))) as client:
        body = {"name": "owner", "password": " long password ", "setup_code": "code"}
        assert client.post("/api/v1/auth/setup", json=body).status_code == 200
        assert (
            client.post(
                "/api/v1/auth/login",
                json={"name": "owner", "password": "long password"},
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/auth/login",
                json={"name": "owner", "password": " long password "},
            ).status_code
            == 200
        )


def test_myself_migration_is_readonly_idempotent_and_skips_credentials(tmp_path):
    import hashlib
    import sqlite3
    from scripts.migrate_myself import migrate
    from app.store import Store

    source = tmp_path / "source"
    source.mkdir()
    (source / "public").mkdir()
    original = source / "dev.db"
    with sqlite3.connect(original) as db:
        db.executescript(
            "CREATE TABLE Article(id INTEGER,title TEXT,content TEXT,collectionId INTEGER,coverImage TEXT); CREATE TABLE User(id INTEGER,password TEXT); INSERT INTO User VALUES(1,'must-not-import');"
        )
        db.execute(
            "INSERT INTO Article VALUES(1,?,?,NULL,NULL)", ("Imported", "plain content")
        )
    before = hashlib.sha256(original.read_bytes()).hexdigest()
    store = Store(tmp_path / "destination")
    assert migrate(source, store)["source_counts"]["Article"] == 1
    assert migrate(source, store, apply=True)["records_added"] == 1
    assert migrate(source, store, apply=True)["records_added"] == 0
    assert store.all("SELECT * FROM owner") == []
    assert "must-not-import" not in encode_for_test(store.all("SELECT * FROM records"))
    assert before == hashlib.sha256(original.read_bytes()).hexdigest()


def encode_for_test(value):
    return json.dumps(value, ensure_ascii=False)


@pytest.mark.parametrize("inherit_output", [True, False])
def test_short_parent_cannot_release_child_outside_command_budget(
    tmp_path, inherit_output
):
    import subprocess
    import psutil

    late = tmp_path / "escaped.txt"
    # The child would escape after 4s; the budget is 1s so a healthy run must
    # return well before that. A tighter 0.3s budget made this test depend on
    # interpreter start-up speed: on a busy machine the parent was killed
    # before it could print the child pid.
    child = "import time;from pathlib import Path;time.sleep(4);Path('escaped.txt').write_text('bad')"
    parent = (
        "import subprocess,sys; p=subprocess.Popen([sys.executable,'-c',"
        + repr(child)
        + "]"
        + (
            ""
            if inherit_output
            else ",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL"
        )
        + ");print(p.pid,flush=True)"
    )
    started = time.monotonic()
    result = execute_process(
        [sys.executable, "-c", parent], tmp_path, threading.Event(), 1.0
    )
    assert time.monotonic() - started < 3, result
    assert result["stopped"] == "timeout" and not result["ok"], result
    assert not late.exists()
    text = result["output"].strip()
    if text:
        pid = int(text)
        try:
            assert psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            pass


def test_validation_errors_never_echo_credentials(client):
    for path, payload, secret in [
        ("/settings", {"model_api_key": "LOCAL-SECRET-" * 100}, "LOCAL-SECRET"),
        ("/settings", {"image_api_key": "not-ascii\nsecret-value"}, "secret-value"),
        (
            "/servers",
            {"name": "node", "host": "example.org", "private_key": "PRIVATE-" * 3000},
            "PRIVATE-",
        ),
    ]:
        result = (
            client.put("/api/v1" + path, json=payload)
            if path == "/settings"
            else client.post("/api/v1" + path, json=payload)
        )
        assert result.status_code == 422
        assert secret not in result.text and "input" not in result.text


def test_provider_exception_redacts_known_nonstandard_key(client):
    key = "compatible-provider-credential"
    client.put("/api/v1/settings", json={"model_api_key": key})

    def provider(request):
        raise RuntimeError("invalid header " + key)

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    run = client.post(
        "/api/v1/runs", json={"task": "分析", "request_key": "error-redaction"}
    ).json()
    detail = wait_run(client, run["id"])
    assert detail["status"] == "failed" and key not in json.dumps(detail)
    assert key not in client.get(f"/api/v1/runs/{run['id']}/events").text


def test_restart_skips_expired_automation(client):
    from app.store import Store, now

    store = client.app.state.store
    store.execute(
        "INSERT INTO schedules(id,title,task,interval_minutes,next_at,enabled,permission) VALUES('expired','test','task',60,1,1,'full')"
    )
    Store(store.directory)
    assert (
        store.one("SELECT next_at FROM schedules WHERE id='expired'")["next_at"] > now()
    )


def test_memory_requires_explicit_task_grant(client):
    manager = client.app.state.manager
    run = {
        "id": "memory-test",
        "conversation_id": "memory-test",
        "permission": "workspace",
        "server_id": None,
    }
    tool = manager._tools(run, threading.Event()).get_tool("remember")
    with pytest.raises(PermissionError):
        tool("unsolicited fact")
    run["allow_memory"] = True
    manager._tools(run, threading.Event()).get_tool("remember")(
        "explicitly requested fact"
    )
    assert len(client.get("/api/v1/memories").json()) == 1


def test_document_tail_is_searchable_and_readable(client):
    text = "a" * 70000 + " unique_document_tail_marker"
    file = client.post(
        "/api/v1/files", files={"file": ("long.txt", text.encode(), "text/plain")}
    ).json()
    assert (
        client.get("/api/v1/files/search?q=unique_document_tail_marker").json()[0][
            "file_id"
        ]
        == file["id"]
    )
    first = client.get(f"/api/v1/files/{file['id']}/text").json()
    assert first["next_offset"] and first["total_chars"] == len(text)
    assert (
        "unique_document_tail_marker"
        in client.get(f"/api/v1/files/{file['id']}/text?offset=70000").json()["text"]
    )


def test_skill_routing_includes_ucb_exploration(client, monkeypatch):
    router = client.app.state.router
    router.bandit.n_updates = 1
    monkeypatch.setattr(
        router.bandit,
        "score",
        lambda task, name: (10000, 0, 10000) if name == "owner-memory" else (0, 0, 0),
    )
    assert router.search("写代码并记住主人的偏好")["skills"][0]["id"] == "owner-memory"


def test_archiving_keeps_conversation_history_and_can_restore(client):
    cid = client.post("/api/v1/conversations", json={"title": "history"}).json()["id"]
    client.app.state.store.message(cid, "user", "Preserve this history")
    assert (
        client.put(
            "/api/v1/conversations/" + cid, json={"title": "renamed"}
        ).status_code
        == 200
    )
    assert client.delete("/api/v1/conversations/" + cid).status_code == 200
    assert not client.get("/api/v1/conversations").json()
    assert client.get("/api/v1/conversations?archived=true").json()[0]["id"] == cid
    assert (
        client.get("/api/v1/conversations/" + cid).json()["messages"][0]["content"]
        == "Preserve this history"
    )
    assert client.post("/api/v1/conversations/" + cid + "/restore").status_code == 200
    assert client.get("/api/v1/conversations").json()[0]["title"] == "renamed"
    assert len(client.get("/api/v1/dashboard").json()["daily_activity"]) == 7


@pytest.mark.parametrize("wake_before_cancel", [False, True])
def test_queued_cancellation_is_single_terminal_event_and_cleans_maps(
    tmp_path, wake_before_cancel
):
    async def scenario():
        manager = create_app(Config(tmp_path, "local-code")).state.manager

        async def hold(*_):
            await asyncio.Event().wait()

        first = await manager.submit("hold", operation=hold)
        await asyncio.sleep(0.02)
        queued = await manager.submit("queued", operation=hold)
        if wake_before_cancel:
            await asyncio.sleep(0.02)
        manager.cancel(queued["id"])
        await asyncio.sleep(0.02)
        assert (
            manager.store.one("SELECT status FROM runs WHERE id=?", (queued["id"],))[
                "status"
            ]
            == "cancelled"
        )
        assert (
            len(
                [
                    e
                    for e in manager.store.events(queued["id"])
                    if e["kind"] == "finished"
                ]
            )
            == 1
        )
        assert (
            queued["id"] not in manager.tasks
            and queued["id"] not in manager.cancellations
        )
        await manager.close()

    asyncio.run(scenario())


def test_fast_output_over_limit_is_not_success(tmp_path):
    result = execute_process(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('x'*70000);sys.stdout.flush()",
        ],
        tmp_path,
        threading.Event(),
        timeout=3,
    )
    assert (
        not result["ok"]
        and result["stopped"] == "output_limit"
        and len(result["output"]) == 65536
    )


def test_gallery_reference_matches_allowlisted_assets(client):
    cards = client.get("/api/v1/tools/gallery").json()
    assert len(cards) == 95
    card = next(row for row in cards if row["has_code"])
    detail = client.get("/api/v1/tools/gallery/" + card["id"] + "/reference").json()
    assert detail["code"] and detail["markdown"] and detail["id"] == card["id"]
    assert client.get("/api/v1/tools/gallery/unknown/reference").status_code == 404


def test_secret_redaction_handles_serialized_multiline_keys_and_vault(client):
    manager = client.app.state.manager
    private_key = "-----BEGIN OPENSSH PRIVATE KEY-----\nsynthetic-private-material\n-----END OPENSSH PRIVATE KEY-----"
    client.app.state.auth.set_secret("ssh:synthetic", private_key)
    encoded = json.dumps({"output": private_key})
    assert private_key not in json.loads(manager.redact(encoded))["output"]
    client.app.state.store.event(
        "synthetic-log", "tool.started", {"arguments": manager.redact(encoded)}
    )
    assert "synthetic-private-material" not in json.dumps(
        client.app.state.store.events("synthetic-log")
    )
    vault = (client.app.state.store.directory / "vault.key").read_text().strip()
    assert manager.redact(vault) == "[redacted]"


def test_exported_plot_script_reproduces_the_actual_png(client, tmp_path):
    import subprocess
    from app.creative import plot_csv

    csv = b"x,y\nA,12\nB,17\nC,9\n"
    original = client.post(
        "/api/v1/files", files={"file": ("original.csv", csv, "text/csv")}
    ).json()
    library = client.app.state.library
    result = plot_csv(
        library, original["id"], "x", "y", kind="bar", title="Reproducible figure"
    )
    code = next(row for row in result["files"] if row["name"].endswith(".py"))
    png = next(row for row in result["files"] if row["name"].endswith(".png"))
    script = tmp_path / "reproduce.py"
    script.write_bytes(library.path(code["id"]).read_bytes())
    (tmp_path / "original.csv").write_bytes(csv)
    completed = subprocess.run(
        [sys.executable, str(script), "original.csv"],
        cwd=tmp_path,
        capture_output=True,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert (tmp_path / "figure.png").read_bytes() == library.path(
        png["id"]
    ).read_bytes()
