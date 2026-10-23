"""Synthetic documents and scripted models: contracts, not real-model quality."""
import asyncio
import io
import json
import time
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.learning import MAX_CHAPTER_CHARS, split_chapters
from app.learning_studio import chunks, validate
from app.main import create_app

TEXT = "第一章 导数\n\n" + "导数刻画瞬时变化率，几何意义是函数图像在该点的切线斜率。\n" * 200


@pytest.fixture
def studio(tmp_path):
    app = create_app(Config(tmp_path, "synthetic-bootstrap"))
    with TestClient(app) as client:
        token = client.post("/api/v1/auth/setup", json={"name": "Student", "password": "synthetic-password-123", "setup_code": "synthetic-bootstrap"}).json()["token"]
        client.headers["Authorization"] = "Bearer " + token
        client.put("/api/v1/settings", json={"model_api_key": "synthetic-key"})
        book = add_book(client)
        yield app, client, book


def add_book(client, text=TEXT, name="合成学习资料.txt"):
    file = client.post("/api/v1/files", files={"file": (name, text.encode())}).json()
    return client.post("/api/v1/learning/books", json={"file_id": file["id"]}).json()["book"]


def source_list(client, book):
    response = client.get(f"/api/v1/learning/books/{book['id']}/sources")
    assert response.status_code == 200, response.text
    return response.json()["sources"]


def question(text, stem="导数的几何意义是什么？", kind="single"):
    return {"kind": kind, "stem": stem, "options": [{"key": key, "text": value} for key, value in zip("ABCD", ["切线斜率", "面积", "弧长", "周长"])],
            "answer": "A", "explanation": "导数描述瞬时变化率，在几何上对应切线斜率。", "tags": ["导数"], "difficulty": 2, "source_quote": text.strip()[:40]}


def blind_response(payload):
    return {"solutions": [{"index": index, "solvable": True, "answer": "A" if row["kind"] == "single" else ["切线斜率"] if row["kind"] == "fill" else "切线斜率。",
                           "solution": "合成盲解：由导数定义与几何意义，核对切线的斜率和瞬时变化率。"} for index, row in enumerate(payload["questions"])]}


def step_checks(question):
    return [{"index": step["index"], "valid": True, "reason": "合成逐步核对：该步骤的前提及计算成立。"}
            for step in question["reasoning_steps"]]


def model(app, responder):
    async def transport(request):
        messages = json.loads(request.content)["messages"]
        payload = json.loads(messages[1]["content"])
        if "学习材料分析协议" in messages[0]["content"]:
            result = {"type": "knowledge", "summary": "本段解释导数表示瞬时变化率，几何意义为切线斜率。", "knowledge_points": [{"name": "导数", "quote": payload["text"].strip()[:60]}], "exercises": []}
        elif "学习独立求解协议" in messages[0]["content"]:
            result = blind_response(payload)
        elif "学习出题复核协议" in messages[0]["content"]:
            result = {"reviews": [{"index": index, "steps": step_checks(payload["questions"][index]), "verdict": "accept", "relevant": True, "solvable": True, "correct": True, "independent_match": True, "reasoning_correct": True, "reasoning_check": "合成逐步核对：计算、前提及推理方向与解析一致。", "reason": "合成审题：题目条件完整，答案与材料知识一致。"} for index in range(len(payload["questions"]))]}
        else:
            result = responder(payload)
        if asyncio.iscoroutine(result):
            result = await result
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": json.dumps(result, ensure_ascii=True)}}], "usage": {"total_tokens": 80}})
    app.state.manager.model_transport = httpx.MockTransport(transport)


def start(client, book, sources, **options):
    payload = {"source_ids": [unit["id"] for unit in sources], "count": 1, "request_key": uuid.uuid4().hex, **options}
    return client.post(f"/api/v1/learning/books/{book['id']}/generations", json=payload)


def wait(client, job):
    for _ in range(300):
        response = client.get(f"/api/v1/learning/generations/{job['id']}")
        assert response.status_code == 200, response.text
        value = response.json()["job"]
        if value["status"] not in {"queued", "running", "cancelling"}:
            return value
        time.sleep(.01)
    pytest.fail("generation did not terminate")


def test_long_chapters_and_source_chunks_preserve_all_text(monkeypatch):
    body = "甲乙丙丁。" * (MAX_CHAPTER_CHARS // 2)
    chapters = split_chapters("第一章 测试\n" + body)
    assert len(chapters) > 1
    assert "".join(chapter["content"] for chapter in chapters) == body
    assert "".join(chunks(body)) == body
    monkeypatch.setattr("app.learning.MAX_CHAPTERS", 2)
    with pytest.raises(ValueError, match="2 个章节"):
        split_chapters("纯正文" * MAX_CHAPTER_CHARS)


def test_sources_are_stable_and_neighbors_bounded(studio):
    _, client, book = studio
    units = source_list(client, book)
    assert len(units) >= 2 and all(unit["page_from"] is None for unit in units)
    assert units == source_list(client, book)
    assert client.get(f"/api/v1/learning/sources/{units[0]['id']}?offset=-1").status_code == 404
    assert client.get(f"/api/v1/learning/sources/{units[0]['id']}?offset=2").status_code == 422
    next_unit = client.get(f"/api/v1/learning/sources/{units[0]['id']}?offset=1").json()["source"]
    assert next_unit["id"] == units[1]["id"]
    assert "path" not in next_unit


def test_pdf_page_labels_require_real_exact_extraction(studio):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    _, client, book = studio
    writer = PdfWriter()
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    for number in (1, 2):
        page = writer.add_blank_page(600, 800)
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
        stream = DecodedStreamObject()
        text = f"Chapter {number} Calculus\\n" + (f"Derivatives on physical page {number} measure the instantaneous rate of change. " * 12)
        stream.set_data(f"BT /F1 12 Tf 20 700 Td ({text}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
    buffer = io.BytesIO()
    writer.write(buffer)
    uploaded = client.post("/api/v1/files", files={"file": ("synthetic.pdf", buffer.getvalue())}).json()
    pdf_book = client.post("/api/v1/learning/books", json={"file_id": uploaded["id"]}).json()["book"]
    pdf_units = source_list(client, pdf_book)
    assert pdf_units[0]["page_from"] == 1 and pdf_units[-1]["page_to"] == 2
    assert all(unit["page_from"] is not None for unit in pdf_units)
    assert all(unit["page_from"] is None for unit in source_list(client, book))


def test_durable_generation_citations_idempotency_and_replay(studio):
    app, client, book = studio
    units = source_list(client, book)
    calls = []
    def respond(payload):
        calls.append(payload)
        return [question(payload["text"])]
    model(app, respond)
    response = start(client, book, units[:1], request_key="same-request-123", focus="几何理解", kinds=["single"], difficulty=2)
    assert response.status_code == 200, response.text
    job = wait(client, response.json()["job"])
    assert job["status"] == "completed" and job["created_count"] == 1
    retry = start(client, book, units[:1], request_key="same-request-123", focus="几何理解", kinds=["single"], difficulty=2).json()["job"]
    assert retry["id"] == job["id"] and len(calls) == 1
    conflict = start(client, book, units[:1], request_key="same-request-123", count=2)
    assert conflict.status_code == 409
    events = app.state.store.all("SELECT seq,kind FROM events WHERE run_id=? ORDER BY seq", (job["run_id"],))
    assert [event["seq"] for event in events] == sorted({event["seq"] for event in events})
    assert "learning.source.finished" in {event["kind"] for event in events}
    replay = client.get(f"/api/v1/runs/{job['run_id']}/events?after={events[-2]['seq']}")
    assert '"finished"' in replay.text
    listed = client.get(f"/api/v1/learning/questions?book_id={book['id']}").json()["questions"]
    assert listed[0]["source_id"] == units[0]["id"] and listed[0]["source_quote"]
    quiz = client.post("/api/v1/learning/quiz", json={"book_id": book["id"]}).json()["session"]
    assert "answer" not in quiz["questions"][0] and not quiz["questions"][0]["source_quote"]
    usage = json.loads(app.state.store.one("SELECT usage FROM runs WHERE id=?", (job["run_id"],))["usage"])
    assert usage["calls"] == 4 and usage["total_tokens"] == 320


@pytest.mark.parametrize("patch", [
    {"source_quote": "完全不在教材里的引用，不能假装有依据。"},
    {"options": [None] * 4},
    {"options": [{"key": key, "text": "重复"} for key in "ABCD"]},
    {"answer": "A or B"}, {"difficulty": True}, {"explanation": ""},
    {"kind": "fill", "stem": "有 ___ 和 ___ 两个空。", "answer": ["只填一个"]},
])
def test_question_quality_rejects_malformed_and_ungrounded_rows(patch):
    text = TEXT[12:1000]
    row = question(text) | patch
    valid, reason = validate(row, {"content": text}, {"kinds": ["single", "fill", "short"], "difficulty": 0})
    assert valid is None and reason


def test_partial_repair_and_resume_only_missing_count(studio):
    app, client, book = studio
    units = source_list(client, book)
    model(app, lambda payload: [question(payload["text"])])
    job = wait(client, start(client, book, units[:1], count=2).json()["job"])
    assert job["status"] == "partial" and job["created_count"] == 1 and job["items"][0]["duplicates"] == 2
    calls = []
    def respond(payload):
        calls.append(payload)
        return [question(payload["text"], "导数如何刻画瞬时变化？")]
    model(app, respond)
    resumed = wait(client, start(client, book, [], resume_job_id=job["id"]).json()["job"])
    assert resumed["status"] == "completed" and resumed["target"] == 1
    assert calls[0]["count"] == 1
    assert start(client, book, [], resume_job_id=job["id"]).status_code == 409
    assert client.get(f"/api/v1/learning/books/{book['id']}").json()["book"]["question_count"] == 2


def test_restart_marks_generation_interrupted_without_replaying(studio):
    from app.store import Store
    from app.learning_studio import snapshot
    app, client, book = studio
    unit = source_list(client, book)[0]
    model(app, lambda payload: [])
    job = wait(client, start(client, book, [unit]).json()["job"])
    app.state.store.execute("UPDATE runs SET status='running' WHERE id=?", (job["run_id"],))
    reopened = Store(app.state.store.directory)
    assert snapshot(reopened, job["id"])["status"] == "interrupted"
    assert snapshot(reopened, job["id"])["created_count"] == 0
    model(app, lambda payload: [question(payload["text"])])
    resumed = wait(client, start(client, book, [], resume_job_id=job["id"]).json()["job"])
    assert resumed["status"] == "completed"


def test_cancel_stops_late_commit_and_allows_resume(studio):
    app, client, book = studio
    units = source_list(client, book)
    async def delayed(payload):
        await asyncio.sleep(.6)
        return [question(payload["text"])]
    model(app, delayed)
    first = start(client, book, units[:2]).json()["job"]
    assert start(client, book, units[:1]).status_code == 409
    assert client.delete(f"/api/v1/learning/books/{book['id']}").status_code >= 400
    client.post(f"/api/v1/runs/{first['run_id']}/cancel")
    stopped = wait(client, first)
    assert stopped["status"] == "cancelled" and stopped["created_count"] == 0
    assert not app.state.store.all("SELECT id FROM questions WHERE book_id=?", (book["id"],))
    model(app, lambda payload: [question(payload["text"], "第" + str(len(payload["text"])) + "段：导数的几何意义？")])
    resumed = wait(client, start(client, book, [], resume_job_id=first["id"]).json()["job"])
    assert resumed["target"] == 2


def test_limits_authorization_cross_book_and_delete_cleanup(studio):
    app, client, book = studio
    units = source_list(client, book)
    other = add_book(client, "第二章 概率\n" + "概率是衡量随机事件发生可能性的数值。" * 50)
    assert start(client, other, units[:1]).status_code == 409
    assert start(client, book, units[:1] * 41).status_code == 422
    assert start(client, book, []).status_code == 409
    assert start(client, book, units[:1], count=25).status_code == 422
    assert client.get(f"/api/v1/learning/books/{book['id']}/sources", headers={"Authorization": "Bearer invalid"}).status_code == 401
    model(app, lambda payload: [question(payload["text"])])
    job = wait(client, start(client, book, units[:1]).json()["job"])
    assert client.delete(f"/api/v1/learning/books/{book['id']}").status_code == 200
    assert not app.state.store.one("SELECT id FROM learning_sources WHERE book_id=?", (book["id"],))
    assert client.get(f"/api/v1/learning/generations/{job['id']}").status_code == 404


def test_mistakes_use_latest_answer_and_quiz_scope_is_consistent(studio):
    app, client, book = studio
    unit = source_list(client, book)[0]
    model(app, lambda payload: [question(payload["text"])])
    wait(client, start(client, book, [unit]).json()["job"])
    first = client.post("/api/v1/learning/quiz", json={"book_id": book["id"]}).json()["session"]
    qid = first["questions"][0]["id"]
    client.post(f"/api/v1/learning/quiz/{first['id']}/answer", json={"question_id": qid, "answer": "B"})
    review = client.post("/api/v1/learning/quiz", json={"book_id": book["id"], "mode": "mistakes"}).json()["session"]
    assert review["total"] == 1
    client.post(f"/api/v1/learning/quiz/{review['id']}/answer", json={"question_id": qid, "answer": "A"})
    assert client.post("/api/v1/learning/quiz", json={"book_id": book["id"], "mode": "mistakes"}).status_code == 409
    detail = client.get(f"/api/v1/learning/books/{book['id']}").json()["book"]
    assert detail["unique_answered"] == 1 and detail["answered"] == 2
    other = add_book(client)
    assert client.post("/api/v1/learning/quiz", json={"book_id": other["id"], "chapter_id": unit["chapter_id"]}).status_code == 409


def test_revising_older_answer_becomes_latest_even_with_same_timestamp(studio, monkeypatch):
    app, client, book = studio
    unit = source_list(client, book)[0]
    model(app, lambda payload: [question(payload["text"], "导数几何意义第" + str(index) + "问？") for index in (1,2)])
    wait(client, start(client, book, [unit], count=2).json()["job"])
    sessions = [client.post("/api/v1/learning/quiz", json={"book_id": book["id"], "count": 2}).json()["session"] for _ in (1,2)]
    qid = sessions[0]["questions"][0]["id"]
    from app import learning
    monkeypatch.setattr(learning, "time", SimpleNamespace(time=lambda: 1_700_000_000))
    for session, answer in [(sessions[0], "B"), (sessions[1], "A"), (sessions[0], "B")]:
        assert client.post(f"/api/v1/learning/quiz/{session['id']}/answer", json={"question_id": qid, "answer": answer}).status_code == 200
    review = client.post("/api/v1/learning/quiz", json={"book_id": book["id"], "mode": "mistakes"}).json()["session"]
    assert review["questions"][0]["id"] == qid and review["mode"] == "mistakes"
    assert len(app.state.store.all("SELECT id FROM quiz_answers WHERE session_id=? AND question_id=?", (sessions[0]["id"], qid))) == 1


def test_markdown_extension_is_a_usable_book(studio):
    _, client, _ = studio
    book = add_book(client, name="synthetic.markdown")
    assert book["chapter_count"] > 0


def test_subjective_grading_cannot_write_after_book_deleted(studio):
    app, client, book = studio
    unit = source_list(client, book)[0]
    model(app, lambda payload: [question(payload["text"], kind="short") | {"answer": "导数的几何意义是切线斜率。"}])
    wait(client, start(client, book, [unit], kinds=["short"]).json()["job"])
    session = client.post("/api/v1/learning/quiz", json={"book_id": book["id"]}).json()["session"]
    entered = threading.Event()
    async def grade(payload):
        entered.set()
        await asyncio.sleep(.4)
        return {"verdict": "correct", "reason": "合成判分"}
    model(app, grade)
    with ThreadPoolExecutor(max_workers=1) as pool:
        response = pool.submit(client.post, f"/api/v1/learning/quiz/{session['id']}/answer", json={"question_id": session["questions"][0]["id"], "answer": "切线斜率"})
        assert entered.wait(2)
        assert client.delete(f"/api/v1/learning/books/{book['id']}").status_code == 200
        assert response.result(timeout=5).status_code == 400
    assert not app.state.store.all("SELECT id FROM quiz_answers WHERE session_id=?", (session["id"],))


def test_surrogate_model_and_user_strings_are_safe_in_transactions(studio):
    from app import learning
    app, client, book = studio
    added = client.post("/api/v1/learning/books", content=json.dumps({"file_id": book["file_id"], "title": "合成标题\ud800", "subject": "数学\ud800"}), headers={"Content-Type": "application/json"})
    assert added.status_code == 422  # Pydantic rejects lone surrogates at the HTTP boundary.
    file_row = app.state.store.one("SELECT * FROM files WHERE id=?", (book["file_id"],))
    direct_book = learning.create_book(app.state.store, None, file_row, "合成标题\ud800", "数学\ud800")
    assert "\ufffd" in direct_book["title"]
    unit = source_list(client, book)[0]
    row = question(TEXT, "合成题干\ud800：解释导数几何意义", kind="short") | {"answer": "切线斜率\ud800", "explanation": "导数在几何上的意义是切线斜率。\ud800", "source_quote": TEXT.split("\n\n")[1][:40]}
    model(app, lambda payload: [row])
    job = wait(client, start(client, book, [unit], kinds=["short"]).json()["job"])
    assert job["created_count"] == 1
    quiz = client.post("/api/v1/learning/quiz", json={"book_id": book["id"]}).json()["session"]
    model(app, lambda payload: {"verdict": "correct", "reason": "回答准确\ud800"})
    result = client.post(f"/api/v1/learning/quiz/{quiz['id']}/answer", content=json.dumps({"question_id": quiz["questions"][0]["id"], "answer": "切线斜率\ud800"}), headers={"Content-Type": "application/json"})
    assert result.status_code == 422
    result = client.post(f"/api/v1/learning/quiz/{quiz['id']}/answer", json={"question_id": quiz["questions"][0]["id"], "answer": "切线斜率"})
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "correct" and "\ufffd" in result.json()["reason"]
    next_session = learning.start_quiz(app.state.store, book_id=book["id"])
    direct = asyncio.run(learning.submit_answer(app.state.store, None, next_session["id"], quiz["questions"][0]["id"], "切线斜率\ud800"))
    assert "\ufffd" in direct["state"]["questions"][0]["answered"]


def test_nested_fill_answers_with_surrogates_are_cleaned(studio):
    app, client, book = studio
    unit = source_list(client, book)[0]
    row = question(TEXT, "导数的几何意义为 ___ 。", kind="fill") | {"answer": ["切线斜率\ud800"], "source_quote": TEXT.split("\n\n")[1][:40]}
    model(app, lambda payload: [row])
    job = wait(client, start(client, book, [unit], kinds=["fill"]).json()["job"])
    assert job["status"] == "completed" and job["created_count"] == 1
    saved = client.get(f"/api/v1/learning/questions?book_id={book['id']}").json()["questions"][0]
    assert json.loads(saved["answer"]) == ["切线斜率\ufffd"]
