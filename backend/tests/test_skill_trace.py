import json

import httpx

from app.skill_trace import route_preview, run_skill_traces, skill_evidence
from app.store import Store
from test_platform import client, frames, wait_run


def routing():
    return {
        "skills": [{"id": "coding-workspace", "name": "代码工作区", "description": "读写并验证代码", "tools": ["read_file", "write_file"]}],
        "dependencies": [{"id": "private-documents", "name": "资料", "tools": ["read_document"]}],
        "candidates": [{"id": "not-selected", "tools": ["write_file"]}],
        "selection": {"method": "task_utility"},
    }


def test_selection_is_not_execution_or_candidate_evidence():
    selected = routing()
    assert route_preview(selected, 2)["evidence"] == []
    assert skill_evidence("write_file", {}, selected, True) == [
        {"id": "coding-workspace", "kind": "tool", "ok": True},
    ]
    assert skill_evidence("read_document", {}, selected, False) == [
        {"id": "private-documents", "kind": "tool", "ok": False},
    ]
    assert skill_evidence("execute_unknown", {}, selected, True) == []


def test_reference_reads_are_distinct_and_validated():
    selected = routing()
    assert skill_evidence("load_skill", {"name": "coding-workspace"}, selected, True)[0]["kind"] == "reference"
    assert skill_evidence("read_skill_resource", {"name": "extra-reference"}, selected, True)[0]["id"] == "extra-reference"
    assert skill_evidence("load_skill", {"name": "not-a-skill"}, selected, False) == []
    assert skill_evidence("load_skill", {"name": "coding-workspace"}, selected, False)[0]["ok"] is False


def test_historical_trace_is_batched_compact_and_replayable(tmp_path):
    store = Store(tmp_path)
    store.event("one", "skills", routing())
    evidence = skill_evidence("write_file", {}, routing(), True)
    store.event("one", "tool.completed", {"name": "write_file", "skill_evidence": evidence, "result": "PRIVATE-LARGE-TOOL-OUTPUT", "arguments": "PRIVATE-ARGS"})
    store.event("one", "delta", {"text": "PRIVATE-TOKEN-STREAM"})
    store.event("two", "skills", {"skills": [], "dependencies": []})
    traces = run_skill_traces(store, ["one", "two", "missing"])
    assert len(traces["one"]["evidence"]) == 1
    assert traces["one"]["evidence"][0]["seq"] == 2
    assert traces["two"]["skills"] == []
    assert "missing" not in traces
    assert "PRIVATE-" not in json.dumps(traces)
    assert "candidates" not in json.dumps(traces)
    # Persisted events survive process restart; no separate summary table.
    reopened = Store(tmp_path)
    assert run_skill_traces(reopened, ["one", "two"]) == traces


def test_latest_route_does_not_inherit_older_evidence(tmp_path):
    store = Store(tmp_path)
    store.event("one", "skills", routing())
    store.event("one", "tool.completed", {"skill_evidence": skill_evidence("write_file", {}, routing(), True)})
    store.event("one", "skills", {"skills": [], "dependencies": []})
    assert run_skill_traces(store, ["one"])["one"]["evidence"] == []


def test_legacy_tool_output_cannot_imply_skill_execution(tmp_path):
    store = Store(tmp_path)
    store.event("legacy", "skills", routing())
    store.event("legacy", "tool.completed", {"name": "write_file", "ok": True, "result": "worked"})
    assert run_skill_traces(store, ["legacy"])["legacy"]["evidence"] == []
    assert run_skill_traces(store, []) == {}


def test_real_agent_returns_reference_and_failed_tool_evidence(client, monkeypatch):
    manager = client.app.state.manager
    monkeypatch.setattr(manager.router, "search", lambda *args, **kwargs: routing())
    client.put("/api/v1/settings", json={"model_api_key": "synthetic-skill-trace-key"})
    responses = iter([
        frames(tool={"name": "load_skill", "arguments": {"name": "coding-workspace"}}),
        frames(tool={"name": "write_file", "arguments": {"path": "trace.txt", "content": "should be denied"}}),
        frames(content="本轮只读取了方法，写文件被只读权限阻止。"),
    ])
    manager.model_transport = httpx.MockTransport(lambda _: httpx.Response(200, content=next(responses).encode()))
    ident = client.post("/api/v1/runs", json={"task": "synthetic skill route", "request_key": "skill-trace", "permission": "read"}).json()["id"]
    run = wait_run(client, ident)
    assert run["status"] == "failed"  # Unresolved denied write is never successful completion.
    trace = run["skillnet"]
    assert trace["evidence"] == [
        {"id": "coding-workspace", "kind": "reference", "ok": True, "seq": trace["evidence"][0]["seq"]},
        {"id": "coding-workspace", "kind": "tool", "ok": False, "seq": trace["evidence"][1]["seq"]},
    ]
    detail = client.get(f'/api/v1/conversations/{run["conversation_id"]}').json()
    assert detail["runs"][0]["skillnet"] == trace
    saved = client.app.state.store.events(ident)
    assert any(event["kind"] == "tool.completed" and event["data"]["skill_evidence"] for event in saved)
