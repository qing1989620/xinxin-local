"""Actual-route companion to the explicitly authorized private live check.

No secrets, original pages or generated exercise text belong in public reports.
This transport forwards real requests, counts before sending, and discards the
provider's internal reasoning. Run sequentially with the authorization ledger.
"""
from __future__ import annotations

import json
import os
import shutil
import threading
import time

import httpx
from fastapi.testclient import TestClient

from app.store import encode, now, uid


class BoundedTransport(httpx.AsyncBaseTransport):
    def __init__(self, args, directory):
        self.args, self.directory = args, directory
        self.calls, self.trace, self.lock = 0, [], threading.Lock()

    async def handle_async_request(self, request):
        if request.url.scheme != "https" or request.url.host != self.args.allow_host:
            raise RuntimeError("真实检查禁止访问未授权的模型目的地")
        ledger_path = self.args.ledger.resolve()
        with self.lock:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"calls": 0, "tokens": 0}
            if ledger["calls"] >= self.args.ledger_limit or self.calls >= self.args.max_calls:
                raise RuntimeError("真实检查达到明确授权的调用上限")
            self.calls += 1
            ledger["calls"] += 1
            ledger_path.write_text(encode(ledger), encoding="utf-8")
        payload = json.loads(request.content)
        record = {"call": ledger["calls"], "thinking": payload.get("thinking"), "messages": [
            {"role": item["role"], "content": [block for block in item["content"] if block.get("type") == "text"]
             if isinstance(item.get("content"), list) else item.get("content")} for item in payload["messages"]]}
        try:
            async with httpx.AsyncHTTPTransport() as network:
                response = await network.handle_async_request(request)
                await response.aread()
            data = response.json()
            record["status"] = response.status_code
            record["content"] = data.get("choices", [{}])[0].get("message", {}).get("content")
            with self.lock:
                ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
                ledger["tokens"] += int(data.get("usage", {}).get("total_tokens", 0))
                ledger_path.write_text(encode(ledger), encoding="utf-8")
            return response
        finally:
            self.trace.append(record)
            self.directory.joinpath("http-trace-" + str(now()) + ".private.json").write_text(
                json.dumps(self.trace, ensure_ascii=False, indent=2), encoding="utf-8")


def checked(response):
    if response.status_code != 200:
        raise RuntimeError("隔离 HTTP 检查失败，状态码 " + str(response.status_code))
    return response.json()


def generate(client, args, unit):
    body = {"source_ids": [unit["id"]], "count": args.count, "kinds": args.kinds,
            "mode": args.mode, "read_mode": args.read_mode, "request_key": uid()}
    if args.resume_latest:
        previous = checked(client.get(f"/api/v1/learning/books/{unit['book_id']}/generation"))["job"]
        if not previous:
            raise RuntimeError("没有可补出的隔离任务")
        body = {"resume_job_id": previous["id"], "request_key": uid()}
    job = checked(client.post(f"/api/v1/learning/books/{unit['book_id']}/generations", json=body))["job"]
    deadline, state = time.monotonic() + 900, None
    while time.monotonic() < deadline:
        job = checked(client.get(f"/api/v1/learning/generations/{job['id']}"))["job"]
        current = (job["status"], job["created_count"], tuple(item["status"] for item in job["items"]))
        if current != state:
            print("http stage: " + encode(current), flush=True)
            state = current
        if job["status"] not in {"queued", "running", "cancelling"}:
            return {"job": job, "book": checked(client.get(f"/api/v1/learning/books/{unit['book_id']}"))}
        time.sleep(.25)
    raise RuntimeError("隔离真实任务未在 15 分钟内结束")


def quiz(client, store, unit):
    session = checked(client.post("/api/v1/learning/quiz", json={"book_id": unit["book_id"], "count": 1}))["session"]
    question = session["questions"][0]
    assert "answer" not in question and "explanation" not in question
    ident, session_id = question["id"], session["id"]
    prefix = f"/api/v1/learning/questions/{ident}"
    hint = checked(client.post(prefix + "/explain", json={"mode": "teacher", "session_id": session_id,
        "message": "先给我一个切入提示，不要公布最后的答案。"}))
    saved = store.one("SELECT kind,answer FROM questions WHERE id=?", (ident,))
    body = {"question_id": ident, "answer": saved["answer"]}
    if saved["kind"] == "fill":
        body = {"question_id": ident, "answers": json.loads(saved["answer"])}
    result = checked(client.post(f"/api/v1/learning/quiz/{session_id}/answer", json=body))
    assert result["status"] == "correct", "真实判分没有认可已核对的参考作答"
    explanation = checked(client.post(prefix + "/explain", json={"mode": "xinxin", "session_id": session_id,
        "message": "请结合我的作答，认真核对关键步骤，再帮我总结一个易错点。"}))
    assert len(hint["history"]) == len(explanation["history"]) == 2
    completed = checked(client.get(f"/api/v1/learning/quiz/{session_id}"))["session"]
    assert completed["status"] == "completed"
    fresh = checked(client.post("/api/v1/learning/quiz", json={"book_id": unit["book_id"], "count": 30}))["session"]
    fresh_history = checked(client.get(prefix + "/tutor", params={"session_id": fresh["id"], "mode": "teacher"}))
    assert fresh_history["history"] == [] and fresh_history["previous_history"] == []
    return {"session": completed, "teacher": hint, "grading": result, "xinxin": explanation, "fresh_history": fresh_history}


def verify_quiz(client, store, unit):
    saved = store.one("SELECT id FROM quiz_sessions WHERE book_id=? AND status='completed' ORDER BY rowid DESC LIMIT 1", (unit["book_id"],))
    if not saved:
        raise RuntimeError("没有已完成的真实隔离练习可核对")
    session = checked(client.get(f"/api/v1/learning/quiz/{saved['id']}"))["session"]
    assert session["questions"][0]["status"] == "correct"
    ident = session["questions"][0]["id"]
    history = {mode: checked(client.get(f"/api/v1/learning/questions/{ident}/tutor", params={"session_id": saved["id"], "mode": mode}))
               for mode in ("teacher", "xinxin")}
    assert all(len(value["history"]) == 2 for value in history.values())
    fresh = checked(client.post("/api/v1/learning/quiz", json={"book_id": unit["book_id"], "count": 30}))["session"]
    assert ident in {question["id"] for question in fresh["questions"]}
    empty = checked(client.get(f"/api/v1/learning/questions/{ident}/tutor", params={"session_id": fresh["id"], "mode": "teacher"}))
    assert not empty["history"] and not empty["previous_history"]
    return {"session": session, "history": history, "fresh_history": empty}


def hints(client, unit):
    session = checked(client.post("/api/v1/learning/quiz", json={"book_id": unit["book_id"], "count": 1}))["session"]
    question = session["questions"][0]
    results = {mode: checked(client.post(f"/api/v1/learning/questions/{question['id']}/explain", json={
        "mode": mode, "session_id": session["id"], "message": "只给我一个切入提示和一个问题，不要提前告诉我答案。"}))
        for mode in ("teacher", "xinxin")}
    assert all("answer" not in value["question"] and "explanation" not in value["question"] for value in results.values())
    return {"session": session, "hints": results}


def http_flow(args, config, unit, original):
    # main also constructs a module-level ASGI app. Redirect that initialization
    # before importing it, not merely the explicit create_app(config) below.
    os.environ["XINXIN_DATA_DIR"] = str(config.data_dir.resolve())
    os.environ["DEEPSEEK_API_KEY"] = ""
    from app.main import create_app
    app = create_app(config)
    store = app.state.store
    target = store.directory / "files" / (unit["file_id"] + original.suffix)
    if not target.exists():
        shutil.copyfile(original, target)
    store.execute("INSERT OR IGNORE INTO files VALUES(?,?,?,?,?,?,?,?,?)", (
        unit["file_id"], "私有诊断副本.pdf", "application/pdf", target.stat().st_size, "private-check",
        str(target.resolve()), "", None, now()))
    transport = BoundedTransport(args, store.directory)
    app.state.manager.model_transport = transport
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + app.state.auth.issue()
        if args.http_flow == "generate":
            result = generate(client, args, unit)
        elif args.http_flow == "quiz":
            result = quiz(client, store, unit)
        elif args.http_flow == "verify-quiz":
            result = verify_quiz(client, store, unit)
        else:
            result = hints(client, unit)
    store.directory.joinpath("http-result-" + str(now()) + ".private.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"http_flow": args.http_flow, "calls": transport.calls, "owner_database_written": False}
    if "job" in result:
        summary |= {key: result["job"][key] for key in ("status", "target", "created_count")}
    print(encode(summary), flush=True)
    return 0
