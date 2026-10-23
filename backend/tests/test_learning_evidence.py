"""Representative model formats and image provenance; all materials synthetic."""
import asyncio
import base64
import io
import json
import threading

import httpx
import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from app import learning_evidence as evidence, learning_quality as quality, learning_visual as visual
from app.learning_studio import validate
from app.model import ModelGateway
from test_learning_studio import studio, add_book, source_list, start, wait, question
from test_learning_quality import script
from test_learning_imports import start as import_start, wait_import


TEXT = "推导与练习\n1. 已知 f(x)=x^2，求 x=3 处的导数。\nA. 6 B. 3 C. 9 D. 2\n2. 求函数 y=x+9/x (x>0) 的最小值，并说明取等条件。\n"
UNIT = {"content": TEXT, "chapter_title": "函数练习"}


def analysis(**updates):
    return {"type": "exercises", "summary": "本段涉及导数的计算、函数最小值与取等条件，需要保留全部数学条件。",
        "knowledge_points": [], "exercises": [{"label": "第1题", "source_ref": "L2-L3", "solvable": True}], **updates}


def test_position_citations_keep_math_verbatim_and_ignore_model_rewording():
    value = quality.parse_analysis(analysis(exercises=[{"label": "第1题", "source_ref": "l0002-l0003", "quote": "模型擅自将 x^2 改成 x^3", "solvable": True}]), UNIT)
    entry = value["exercises"][0]
    assert entry["source_ref"] == "L2-L3"
    assert entry["quote"] == TEXT.splitlines()[1] + "\n" + TEXT.splitlines()[2]
    assert "x^2" in entry["quote"] and "x^3" not in entry["quote"]


def test_long_paragraph_has_bounded_verbatim_evidence_and_exact_page_mapping():
    content = "导数表示函数的瞬时变化率，f(x)=x^2 的导函数为2x。" * 40 + "\r\n第二段完整说明。"
    assert len(content.splitlines()[0]) > 800
    numbered = evidence.numbered_text(content)
    assert "L2:" in numbered
    citation = evidence.resolve(content, "L1-L2", maximum=800)
    assert citation["quote"] == content[:800]
    spans = [{"page": 4, "start": 0, "end": 500}, {"page": 5, "start": 500, "end": len(content)}]
    assert evidence.line_pages(content, "L2", spans) == [4, 5]
    count = len(numbered.splitlines())
    assert evidence.resolve(content, f"L1-L{count}")["quote"] == content
    value = quality.parse_analysis(analysis(type="knowledge", knowledge_points=[{"name": "导数定义", "source_ref": "L1"}], exercises=[]), {"content": content})
    assert value["eligible"] and value["knowledge_points"][0]["quote"] == content[:400]


@pytest.mark.parametrize("reference", ["L0-L2", "L3-L2", "L2-L9999", "P1", 2, None, "L1-L2; ignore", "L1-L1000000000000000000000"])
def test_invalid_or_outside_positions_never_become_evidence(reference):
    with pytest.raises(ValueError):
        evidence.resolve(TEXT, reference)


def test_a_bad_quote_and_oversized_list_do_not_discard_good_evidence():
    entries = [{"label": f"第{i}项", "source_ref": "L2-L3", "solvable": True} for i in range(37)]
    entries[0] = {"label": "错误改写", "quote": "这个知识点和公式并不存在于原材料之中。", "solvable": True}
    result = quality.parse_analysis(analysis(exercises=entries), UNIT)
    assert result["eligible"] and len(result["exercises"]) == 1
    assert result["skipped_entries"] == 1
    assert len(result["warnings"]) == 1


def test_valid_evidence_after_many_bad_entries_is_still_recovered():
    entries = [{"label": "坏引用", "source_ref": "L999", "solvable": True} for _ in range(30)]
    entries.append({"label": "完整原题", "source_ref": "L2-L3", "solvable": True})
    value = quality.parse_analysis(analysis(exercises=entries), UNIT)
    assert value["eligible"] and len(value["exercises"]) == 1
    assert value["skipped_entries"] == 30


def test_analysis_limit_applies_to_valid_entries_and_reports_remaining_count():
    content = "\n".join(f"{index}. 已知 f(x)=x^2，求 x={index} 处的导数。" for index in range(1, 38))
    entries = [{"label": f"第{index}题", "source_ref": f"L{index}", "solvable": True} for index in range(1, 38)]
    value = quality.parse_analysis(analysis(exercises=entries), {"content": content})
    assert value["eligible"] and len(value["exercises"]) == 30
    assert value["skipped_entries"] == 7 and "7 条未纳入" in value["warnings"][0]


def test_unsolvable_formula_is_not_an_approved_question_source():
    value = quality.parse_analysis(analysis(exercises=[{"label": "完整题", "source_ref": "L2-L3", "solvable": True},
        {"label": "待核对题", "source_ref": "L4", "solvable": False}]), UNIT)
    options = {"kinds": ["single"], "difficulty": 0}
    valid, error = validate(question(TEXT) | {"source_ref": "L4"}, UNIT, options, value)
    assert valid is None and "完整原题" in error
    valid, _ = validate(question(TEXT) | {"source_ref": "L2-L3", "source_quote": "不存在的文字"}, UNIT, options, value)
    assert valid and valid["source_quote"].startswith("1. 已知")
    valid, error = validate(question(TEXT) | {"origin": "original", "source_ref": "L2-L3"}, UNIT, options | {"mode": "practice"}, value)
    assert valid is None and "标识" in error


def test_empty_evidence_still_fails_instead_of_fabricating_questions():
    with pytest.raises(ValueError, match="可核对"):
        quality.parse_analysis(analysis(exercises=[{"label": "虚构原题", "quote": "完全没有在材料中出现的原题内容。", "solvable": True}]), UNIT)


def test_analysis_repair_is_bounded_and_receives_actionable_feedback(studio):
    app, client, book = studio
    attempts = []
    def respond(payload):
        attempts.append(payload)
        if len(attempts) == 1:
            return analysis(exercises=[{"label": "错误引用", "source_ref": "L999", "solvable": True}])
        return analysis(type="knowledge", knowledge_points=[{"name": "导数", "source_ref": "L1"}], exercises=[])
    calls = script(app, analyze=respond)
    done = wait(client, start(client, book, source_list(client, book)[:1], analyze_only=True).json()["job"])
    assert done["status"] == "completed" and len(attempts) == 2
    assert "来源编号超出" in attempts[1]["repair_notes"]
    assert attempts[0]["numbered_text"].startswith("L1:")
    assert [stage for stage, _ in calls] == ["analysis", "analysis"]


def test_failed_analysis_repair_stops_after_two_calls(studio):
    app, client, book = studio
    calls = script(app, analyze=lambda _: analysis(exercises=[{"label": "错误引用", "source_ref": "L999", "solvable": True}]))
    done = wait(client, start(client, book, source_list(client, book)[:1]).json()["job"])
    assert done["status"] == "failed" and done["created_count"] == 0
    assert len(calls) == 2 and all(stage == "analysis" for stage, _ in calls)


def test_short_but_complete_math_exercises_are_not_blocked_by_word_count(studio):
    app, client, _ = studio
    book = add_book(client, TEXT)
    calls = script(app, analyze=lambda _: analysis())
    unit = source_list(client, book)[0]
    assert unit["eligible"] and unit["chars"] < 200
    done = wait(client, start(client, book, [unit], analyze_only=True).json()["job"])
    assert done["status"] == "completed" and len(calls) == 1


@pytest.mark.parametrize("number", ["(1)", "（1）"])
def test_parenthesized_short_exercise_reaches_generation_and_review(studio, number):
    app, client, _ = studio
    content = number + " 设函数 f(x)=x^2+3x，求 f'(2) 的值。"
    assert 24 <= len(quality.compact(content)) < 80
    file = client.post("/api/v1/files", files={"file": ("synthetic-short-exercise.txt", content.encode())}).json()
    imported = wait_import(client, import_start(client, file["id"]).json()["job"])
    assert imported["status"] == "completed", imported
    book = client.get(f"/api/v1/learning/books/{imported['book_id']}").json()["book"]
    calls = script(app, analyze=lambda _: analysis(exercises=[{"label": "第1题", "source_ref": "L1", "solvable": True}]),
        generate=lambda _: [question(content, "求函数 f(x)=x^2+3x 在 x=2 处的导数：___。", kind="fill") |
            {"source_ref": "L1", "options": [], "answer": ["7"], "explanation": "先求导得到 f'(x)=2x+3，代入 x=2 得到7。"}])
    done = wait(client, start(client, book, source_list(client, book)[:1], kinds=["fill"]).json()["job"])
    assert done["status"] == "completed" and done["created_count"] == 1
    assert [stage for stage, _ in calls] == ["analysis", "generation", "review"]


def add_pdf(client, pages=2):
    output = io.BytesIO()
    document = PdfWriter()
    font = document._add_object(DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")}))
    for number in range(1, pages + 1):
        page = document.add_blank_page(600, 800)
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
        stream = DecodedStreamObject()
        text = f"Learning page {number}: derivative of x squared is twice x. Compute f prime at x=3 and explain the tangent slope. "
        stream.set_data(f"BT /F1 12 Tf 30 740 Td ({text}) Tj ET".encode())
        page[NameObject("/Contents")] = document._add_object(stream)
    document.write(output)
    file = client.post("/api/v1/files", files={"file": ("synthetic-math.pdf", output.getvalue())}).json()
    book = client.post("/api/v1/learning/books", json={"file_id": file["id"]}).json()["book"]
    return book, source_list(client, book)[0]


def visual_transport(app, *, reading=None, reviewing=None):
    captured = []
    async def respond(request):
        messages = json.loads(request.content)["messages"]
        content = messages[1]["content"]
        blocks = content if isinstance(content, list) else []
        payload = json.loads(blocks[0]["text"] if blocks else content)
        protocol = messages[0]["content"]
        if "PDF 原页读取协议" in protocol:
            value = reading(payload) if reading else {"pages": [{"page": page, "readable": True,
                "text": "1. 已知函数 f(x)=x^2，求 x=3 处的导数。\nA. 6 B. 3 C. 9 D. 2", "reason": ""} for page in payload["physical_pages"]]}
            stage = "reading"
        elif "学习材料分析协议" in protocol:
            value, stage = analysis(), "analysis"
        elif "学习出题复核协议" in protocol:
            value = reviewing(payload) if reviewing else {"reviews": [{"index": i, "verdict": "accept", "relevant": True, "solvable": True, "correct": True, "reason": "合成审题：导函数为2x，代入3得到6，原图条件一致。"} for i in range(len(payload["questions"]))]}
            stage = "review"
        else:
            value, stage = {"questions": [question(payload["text"], "求函数 f(x)=x^2 在 x=3 处的导数。") | {"source_ref": "L2-L3", "origin": "original"}]}, "generation"
        captured.append((stage, payload, blocks))
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(value, ensure_ascii=False)}, "finish_reason": "stop"}], "usage": {"total_tokens": 80}})
    app.state.store.set_setting("model_url", "https://api.deepseek.com/chat/completions")
    app.state.manager.model_transport = httpx.MockTransport(respond)
    return captured


def test_visual_questions_keep_original_ocr_and_are_reviewed_against_images(studio):
    app, client, _ = studio
    book, unit = add_pdf(client)
    damaged = "OCR 原文缺失了关键公式，不能据此补猜原题条件。" * 8
    app.state.store.execute("UPDATE learning_sources SET content=? WHERE id=?", (damaged, unit["id"]))
    calls = visual_transport(app)
    done = wait(client, start(client, book, [unit], read_mode="pdf").json()["job"])
    assert done["status"] == "completed" and done["created_count"] == 1
    assert [stage for stage, *_ in calls] == ["reading", "analysis", "generation", "review"]
    for stage, _, blocks in calls:
        images = [block for block in blocks if block["type"] == "image_url"]
        if stage in {"reading", "review"}:
            assert images
            assert base64.b64decode(images[0]["image_url"]["url"].split(",", 1)[1]).startswith(b"\xff\xd8")
    row = app.state.store.one("SELECT * FROM questions WHERE book_id=?", (book["id"],))
    assert row["source_method"] == "pdf_images" and json.loads(row["source_pages"]) == [1]
    assert "x^2" in row["source_quote"]
    assert app.state.store.one("SELECT content FROM learning_sources WHERE id=?", (unit["id"],))["content"] == damaged
    assert app.state.store.one("SELECT count(*) n FROM learning_visual_pages")["n"] == 2
    count = len(calls)
    again = wait(client, start(client, book, [unit], analyze_only=True, read_mode="pdf").json()["job"])
    assert again["status"] == "completed" and len(calls) == count
    hidden = client.post("/api/v1/learning/quiz", json={"book_id": book["id"], "count": 1}).json()
    assert "source_quote" not in json.dumps(hidden) or row["source_quote"] not in json.dumps(hidden, ensure_ascii=False)


def test_raw_pdf_preview_is_authenticated_bounded_and_does_not_call_model(studio):
    app, client, _ = studio
    book, unit = add_pdf(client)
    calls = visual_transport(app)
    endpoint = f"/api/v1/learning/sources/{unit['id']}/pages/1"
    assert client.get(endpoint, headers={"Authorization": ""}).status_code == 401
    result = client.get(endpoint)
    assert result.status_code == 200 and result.content.startswith(b"\xff\xd8")
    assert result.headers["cache-control"] == "no-store"
    assert client.get(endpoint[:-1] + "3").status_code == 404
    assert calls == []


def test_unsupported_model_cannot_silently_send_pdf_images(studio):
    app, client, _ = studio
    book, unit = add_pdf(client)
    calls = visual_transport(app)
    app.state.store.set_setting("model_url", "https://unsupported.example/chat/completions")
    response = start(client, book, [unit], read_mode="pdf")
    assert response.status_code == 409 and "尚未接入" in response.json()["detail"]
    assert calls == []


def test_visual_reading_cancellation_keeps_completed_pages_and_reuses_them(studio):
    app, client, _ = studio
    book, listing = add_pdf(client, pages=5)
    calls = visual_transport(app)
    from app.learning_studio import source
    unit = source(app.state.store, listing["id"])
    flag = threading.Event()
    gateway = ModelGateway("https://api.deepseek.com/chat/completions", "deepseek-flash", "synthetic-key", lambda _: None,
        flag, transport=app.state.manager.model_transport)
    def progress(value):
        if value["page"] > 1:
            flag.set()
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(visual.read_source(app.state.store, app.state.library, gateway, unit, flag, progress))
    assert app.state.store.one("SELECT count(*) n FROM learning_visual_pages")["n"] == 3
    flag.clear()
    material = asyncio.run(visual.read_source(app.state.store, app.state.library, gateway, unit, flag))
    assert material["read_pages"] == [1, 2, 3, 4, 5]
    assert [payload["physical_pages"] for stage, payload, _ in calls if stage == "reading"] == [[1, 2, 3], [4, 5]]


def test_partial_visual_analysis_retries_only_unread_pages_then_reuses_complete_result(studio):
    app, client, _ = studio
    book, unit = add_pdf(client)
    batches = []
    def reading(payload):
        batches.append(payload["physical_pages"])
        return {"pages": [{"page": page, "readable": len(batches) > 1 or page == 1,
            "text": "1. 已知函数 f(x)=x^2，求 x=3 处的导数。\nA. 6 B. 3 C. 9 D. 2" if len(batches) > 1 or page == 1 else "",
            "reason": "本次未能辨认" if len(batches) == 1 and page == 2 else ""} for page in payload["physical_pages"]]}
    calls = visual_transport(app, reading=reading)
    first = wait(client, start(client, book, [unit], analyze_only=True, read_mode="pdf").json()["job"])
    assert first["status"] == "completed"
    value = json.loads(app.state.store.one("SELECT data FROM learning_source_analysis WHERE source_id=?", (unit["id"],))["data"])
    assert value["reading_warnings"] and value["read_pages"] == [1]
    second = wait(client, start(client, book, [unit], analyze_only=True, read_mode="pdf").json()["job"])
    assert second["status"] == "completed" and batches == [[1, 2], [2]]
    assert app.state.store.one("SELECT count(*) n FROM learning_visual_pages")["n"] == 2
    count = len(calls)
    third = wait(client, start(client, book, [unit], analyze_only=True, read_mode="pdf").json()["job"])
    assert third["status"] == "completed" and len(calls) == count


def test_visual_critic_rejection_never_enters_question_bank(studio):
    app, client, _ = studio
    book, unit = add_pdf(client)
    calls = visual_transport(app, reviewing=lambda _: {"reviews": [{"index": 0, "verdict": "reject", "relevant": True,
        "solvable": True, "correct": False, "reason": "合成审题：对照原图发现题干公式不一致，拒绝入库。"}]})
    done = wait(client, start(client, book, [unit], read_mode="pdf").json()["job"])
    assert done["status"] == "failed" and done["created_count"] == 0
    assert not app.state.store.one("SELECT id FROM questions WHERE book_id=?", (book["id"],))
    assert all(any(block["type"] == "image_url" for block in blocks) for stage, _, blocks in calls if stage == "review")


def test_old_failed_text_job_can_be_repaired_with_explicit_pdf_reading(studio):
    app, client, _ = studio
    book, unit = add_pdf(client)
    script(app, analyze=lambda _: analysis(exercises=[{"label": "坏引用", "source_ref": "L999", "solvable": True}]))
    old = wait(client, start(client, book, [unit]).json()["job"])
    assert old["status"] == "failed" and old["created_count"] == 0
    calls = visual_transport(app)
    repaired = wait(client, start(client, book, [], resume_job_id=old["id"], read_mode="pdf").json()["job"])
    assert repaired["status"] == "completed" and repaired["created_count"] == 1
    assert repaired["options"]["read_mode"] == "pdf"
    assert calls[0][0] == "reading"


def test_resume_without_new_read_mode_keeps_previously_approved_pdf_mode(studio):
    app, client, _ = studio
    book, unit = add_pdf(client)
    calls = visual_transport(app, reviewing=lambda _: {"reviews": []})
    old = wait(client, start(client, book, [unit], read_mode="pdf").json()["job"])
    assert old["status"] == "failed"
    visual_transport(app)
    repaired = wait(client, start(client, book, [], resume_job_id=old["id"]).json()["job"])
    assert repaired["options"]["read_mode"] == "pdf" and repaired["created_count"] == 1


@pytest.mark.parametrize("rows", [[], [{"page": 1, "text": "完整文字内容已经足够读取", "readable": True}] * 2,
    [{"page": 3, "text": "完整文字内容已经足够读取", "readable": True}],
    [{"page": 1, "text": "", "readable": True}], [{"page": True, "text": "完整文字内容已经足够读取", "readable": True}]])
def test_visual_reader_rejects_missing_duplicate_or_empty_page_results(rows):
    with pytest.raises(ValueError):
        visual.parse_pages({"pages": rows}, [1])


def test_image_transport_counts_image_tokens_instead_of_base64_text():
    async def run():
        seen = []
        async def response(request):
            seen.append(json.loads(request.content))
            return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]})
        gateway = ModelGateway("https://api.deepseek.com/chat/completions", "deepseek-flash", "synthetic-key", lambda _: None,
            threading.Event(), max_tokens=8000, context_window_tokens=80000, transport=httpx.MockTransport(response))
        data = "data:image/jpeg;base64," + "a" * 300000
        await gateway.apredict([{"role": "user", "content": [{"type": "text", "text": "Read the formula"}, {"type": "image_url", "image_url": {"url": data}}]}])
        assert gateway.context_tokens < 10000
        assert seen[0]["messages"][0]["content"][1]["image_url"]["url"] == data
    asyncio.run(run())


def test_truncated_model_output_is_detected_before_question_parsing():
    async def run():
        gateway = ModelGateway("https://api.deepseek.com/chat/completions", "deepseek-flash", "synthetic-key", lambda _: None,
            threading.Event(), transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"choices": [{"message": {"content": '{"questions":['}, "finish_reason": "length"}]})))
        with pytest.raises(RuntimeError, match="截断"):
            await gateway.apredict([{"role": "user", "content": "synthetic input"}])
    asyncio.run(run())
