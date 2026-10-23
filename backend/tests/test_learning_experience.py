"""Learning journeys and adversarial answers; synthetic inputs and model transports."""
import json
import asyncio

import httpx
import pytest

from app import learning
from app import learning_quality as quality
from app.learning_studio import validate
from app.learning_studio import generate_batch, review_batch
from app.learning_answers import check_choice, check_fill
from app.store import uid
from test_learning_studio import studio, source_list, start, wait, question
from test_learning_evidence import add_pdf, analysis, visual_transport
from test_learning_quality import script


@pytest.mark.parametrize("expected,given", [
    ("1.2", "12"), ("(a+b)*c", "a+b*c"), ("X", "x"), ('"1 2"', '"12"'),
    ("1,2", "12"), ("-2", "2"), ("x^2", "x^3"), ("(0,1)", "[0,1]"),
    ("1/0", "0"), ("0.333", "1/3"), ("1e1000", "1e999"), ("a(b+c)", "ab+c"),
])
def test_grading_never_erases_mathematical_or_code_meaning(expected, given):
    assert not check_fill(json.dumps([expected]), given)


@pytest.mark.parametrize("expected,given", [
    ("4", "$4$"), ("1/2", "0.5"), (r"\frac{1}{2}", "0.500"),
    (r"$-\dfrac{3}{4}$", "−0.75"), ("1.2", "1.20"), ("50%", ".5"),
    ("1e-3", "0.001"), ("(-2)", "-2"), (r"\(x^{2}\)", "x^{2}"),
])
def test_exact_numbers_and_math_presentation_can_be_equivalent(expected, given):
    assert check_fill(json.dumps([expected]), given)


def test_legacy_blanks_keep_empty_positions_and_single_value_punctuation():
    assert not check_fill('["a","b"]', 'a;;b')
    assert not check_fill('["a","b","c"]', 'a;;c')
    assert check_fill('["(0,1)"]', '(0,1)')
    assert check_fill('["a;b"]', 'a;b')
    assert check_fill('["a","b"]', 'a；b')
    assert check_choice('A', ' a ') and not check_choice('A', 'A or B')


def test_math_format_guard_rejects_double_escaped_commands_but_keeps_multiline_tex():
    assert quality.math_issue(r'$\\frac{1}{2}$')
    assert quality.math_issue(r'\(\\lambda+1\)')
    assert not quality.math_issue(r'$\frac{1}{2}$')
    assert not quality.math_issue(r'$\begin{matrix}a\\b\end{matrix}$')
    assert not quality.math_issue(r'$\substack{a\\b}$')
    assert not quality.math_issue(r'代码字符串 "\\frac" 在正文原样保留')


def test_answer_correct_never_overrides_failed_or_missing_reasoning_review():
    row = {"index": 0, "verdict": "accept", "relevant": True, "solvable": True, "correct": True,
           "reason": "独立求解得到的数值与答案一致。", "independent_match": True, "reasoning_correct": False,
           "reasoning_check": "解析把递增数列写成递减，单调方向与趋于零的结论矛盾。"}
    decisions = quality.parse_reviews({"reviews": [row]}, 1)
    assert decisions == [(False, row["reasoning_check"])]
    with pytest.raises(ValueError, match="解析步骤"):
        quality.parse_reviews({"reviews": [{key: value for key, value in row.items() if key != "reasoning_check"}]}, 1)
    with pytest.raises(ValueError, match="解析步骤"):
        quality.parse_reviews({"reviews": [row | {"independent_match": True, "reasoning_correct": "true"}]}, 1)


def test_new_original_batches_do_not_offer_previously_saved_exercises_again():
    old = "第一题：已知导数为瞬时变化率，解释它在几何上的含义。"
    fresh = "第二题：已知切线斜率为导数，说明它如何反映函数局部的变化。"
    material = {"content": old + "\n" + fresh}
    entries = [{"label": str(index), "source_ref": f"L{index}-L{index}", "quote": text, "solvable": True} for index, text in enumerate((old, fresh), 1)]
    analyzed = {"exercises": entries, "knowledge_points": []}
    class Gateway:
        async def apredict(self, messages, **kwargs):
            payload = json.loads(messages[1]["content"])
            assert payload["analysis"]["exercises"] == entries[1:]
            assert payload["available_original_refs"] == ["L2-L2"]
            assert payload["used_original_refs"] == ["L1-L1"]
            row = question(fresh, "导数表示的局部变化有什么几何含义？") | {"origin": "original", "source_ref": "L2"}
            return {"content": json.dumps({"questions": [row]})}
    rows, invalid, repeated = asyncio.run(generate_batch(Gateway(), material, analyzed,
        {"kinds": ["single"], "difficulty": 0, "mode": "original"}, 1, [], [], [], {old}))
    assert len(rows) == 1 and not invalid and not repeated and rows[0]["source_quote"] == fresh


@pytest.mark.parametrize("independent_answer,independent_match,expected", [("A", True, True), ("B", True, False), ("A", False, False)])
def test_blind_solution_hides_candidate_answers_and_disagreement_never_passes(independent_answer, independent_match, expected):
    candidate = question("合成导数正文")
    candidate["explanation"] = "待核对解析，不得泄露到盲解请求。"
    calls = []
    class Gateway:
        async def apredict(self, messages, **kwargs):
            payload = json.loads(messages[1]["content"])
            calls.append(payload)
            if len(calls) == 1:
                assert set(payload["questions"][0]) == {"index", "kind", "stem", "options"}
                assert candidate["explanation"] not in messages[1]["content"]
                value = {"solutions": [{"index": 0, "solvable": True, "answer": independent_answer, "solution": "合成盲解：先独立计算切线斜率，再比对选项。"}]}
            else:
                assert payload["independent_solutions"][0]["answer"] == independent_answer
                value = {"reviews": [{"index": 0, "verdict": "accept", "relevant": True, "solvable": True, "correct": True,
                    "reason": "合成对照：核对导数与切线斜率。", "reasoning_correct": True,
                    "reasoning_check": "合成逐步核对：定义与计算成立。", "independent_match": independent_match}]}
            return {"content": json.dumps(value)}
    result = asyncio.run(review_batch(Gateway(), {"content": "合成导数正文"}, {}, [candidate], []))
    assert len(calls) == 2 and result[0][0] is expected


@pytest.mark.parametrize("value", [{}, {"solutions": []}, {"solutions": [{"index": 0, "solvable": "true", "answer": "A", "solution": "无可靠独立求解的错误布尔类型。"}]}])
def test_missing_or_malformed_blind_solutions_cannot_bypass_review(value):
    with pytest.raises(ValueError, match="独立求解"):
        quality.parse_solutions(value, 1)


def test_legacy_source_evidence_does_not_erase_spaces_inside_code_strings():
    text = '知识正文：print("1 2") 会输出含有空格的字符串。' * 4
    material = {"content": text}
    good = {"type": "knowledge", "summary": "本段讲解字符串中的空格属于内容，不能删除。", "exercises": [],
            "knowledge_points": [{"name": "字符串", "quote": text[:40]}]}
    accepted = quality.parse_analysis(good, material)
    bad = {**good, "knowledge_points": [{"name": "字符串", "quote": text[:40].replace('1 2', '12')}]}
    with pytest.raises(ValueError, match="可核对"):
        quality.parse_analysis(bad, material)
    row, reason = validate(question(text) | {"source_quote": text[:40].replace('1 2', '12')}, material, {"kinds": ["single"], "difficulty": 0}, accepted)
    assert row is None and "原文依据" in reason


def add_question(app, book, *, kind="fill", answer='["1.2"]', stem="填入计算结果 ___。"):
    ident = uid()
    app.state.store.execute("INSERT INTO questions(id,book_id,chapter_id,hash,kind,stem,answer,explanation,tags,created,source_quote) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (ident, book["id"], book["chapters"][0]["id"], ident, kind, stem, answer, "先核对题干条件，再按定义计算。", '["合成知识"]', 1, "合成原文含参考答案，用于检查未作答时隐藏摘录。"))
    return ident


def quiz(client, book, count=8):
    return client.post('/api/v1/learning/quiz', json={"book_id": book["id"], "count": count}).json()["session"]


def test_structured_multi_blank_values_survive_commas_and_semicolons(studio):
    app, client, book = studio
    ident = add_question(app, book, answer='["(0,1)","A;B"]', stem="第一空 ___，第二空 ___。")
    session = quiz(client, book)
    assert session["questions"][0]["blank_count"] == 2
    assert "answer" not in session["questions"][0]
    endpoint = f"/api/v1/learning/quiz/{session['id']}/answer"
    missing = client.post(endpoint, json={"question_id": ident, "answers": ["(0,1)", ""]})
    assert missing.status_code == 400
    assert not app.state.store.one("SELECT id FROM quiz_answers")
    result = client.post(endpoint, json={"question_id": ident, "answers": ["(0,1)", "A;B"]}).json()
    assert result["status"] == "correct" and result["state"]["answered"] == 1
    assert json.loads(result["state"]["questions"][0]["answered"]) == ["(0,1)", "A;B"]


def test_failed_subjective_grading_is_saved_and_can_be_retried_after_session_finishes(studio):
    app, client, book = studio
    ident = add_question(app, book, kind="short", answer="导数为瞬时变化率", stem="解释导数的意义。")
    app.state.manager.model_transport = httpx.MockTransport(lambda _: httpx.Response(503, text="synthetic failure"))
    session = quiz(client, book)
    endpoint = f"/api/v1/learning/quiz/{session['id']}/answer"
    first = client.post(endpoint, json={"question_id": ident, "answer": "描述瞬时变化率。"})
    assert first.status_code == 200, first.text
    first = first.json()
    assert first["status"] == "unknown" and first["state"]["status"] == "completed"
    stats = client.get('/api/v1/learning/stats').json()
    assert stats["pending"] == 1 and stats["graded"] == 0
    captured = []
    def respond(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"verdict":"correct","reason":"作答明确说明瞬时变化率，概念一致。"}'}}]})
    app.state.manager.model_transport = httpx.MockTransport(respond)
    result = client.post(endpoint, json={"question_id": ident, "answer": "不能替换原作答", "retry_grading": True})
    assert result.status_code == 200, result.text
    result = result.json()
    assert result["status"] == "correct" and result["state"]["answered"] == 1
    student = json.loads(captured[0]["messages"][1]["content"])["student"]
    assert student == "描述瞬时变化率。"
    assert app.state.store.one("SELECT count(*) n FROM quiz_answers")["n"] == 1
    assert client.post(endpoint, json={"question_id": ident, "retry_grading": True}).status_code == 400


def test_tutoring_is_scoped_to_current_session_and_earlier_history_is_read_only(studio):
    app, client, book = studio
    ident = add_question(app, book)
    path = f'/api/v1/learning/questions/{ident}'
    payloads = []
    def respond(request):
        payloads.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "先看变化率定义，再检查计算步骤。"}}]})
    app.state.manager.model_transport = httpx.MockTransport(respond)
    first = quiz(client, book)
    client.post(f"/api/v1/learning/quiz/{first['id']}/answer", json={"question_id": ident, "answers": ["12"]})
    assert client.post(path + '/explain', json={"session_id": first["id"]}).status_code == 200
    second = quiz(client, book)
    history = client.get(path + '/tutor', params={"session_id": second["id"], "previous": True}).json()
    assert history["history"] == [] and history["previous_count"] == 2 and history["previous_history"] == []
    reply = client.post(path + '/explain', json={"session_id": second["id"]}).json()
    assert "answer" not in reply["question"] and reply["question"]["source_quote"] == ""
    context = json.loads(payloads[-1]["messages"][1]["content"].split('\n', 1)[1])
    assert context["student_attempt"] is None and "尚未作答" in payloads[-1]["messages"][0]["content"]
    assert len(reply["history"]) == 2
    assert client.post(path + '/explain', json={"session_id": "unrelated-session"}).status_code == 409
    client.post(f"/api/v1/learning/quiz/{second['id']}/answer", json={"question_id": ident, "answers": ["1.2"]})
    previous = client.get(path + '/tutor', params={"session_id": second["id"], "previous": True}).json()
    assert len(previous["previous_history"]) == 2


def test_pdf_page_scope_matches_actual_images_cache_and_question_provenance(studio):
    app, client, _ = studio
    book, unit = add_pdf(client, pages=4)
    calls = visual_transport(app)
    done = wait(client, start(client, book, [unit], read_mode="pdf", page_ranges={unit["id"]: [2, 3]}).json()["job"])
    assert done["status"] == "completed"
    assert [payload["physical_pages"] for stage, payload, _ in calls if stage == "reading"] == [[2, 3]]
    row = app.state.store.one("SELECT source_pages FROM questions WHERE book_id=?", (book["id"],))
    assert json.loads(row["source_pages"]) == [2]
    listing = client.get(f"/api/v1/learning/books/{book['id']}/sources").json()
    assert listing["coverage"]["partial_sources"] == 1
    assert listing["sources"][0]["analysis"]["page_scope"] == [2, 3]
    previous_calls = len(calls)
    again = wait(client, start(client, book, [unit], analyze_only=True, read_mode="pdf", page_ranges={unit["id"]: [3, 4]}).json()["job"])
    assert again["status"] == "completed"
    assert [payload["physical_pages"] for stage, payload, _ in calls[previous_calls:] if stage == "reading"] == [[4]]


@pytest.mark.parametrize('pages', [[0, 2], [3, 2], [1, 5], [True, 2]])
def test_bad_pdf_ranges_are_rejected_before_model_calls(studio, pages):
    app, client, _ = studio
    book, unit = add_pdf(client, pages=4)
    calls = visual_transport(app)
    response = start(client, book, [unit], read_mode="pdf", page_ranges={unit["id"]: pages})
    assert response.status_code in {409, 422} and not calls


def test_failed_material_summary_can_resume_only_its_unfinished_sources(studio):
    app, client, book = studio
    units = source_list(client, book)[:1]
    script(app, analyze=lambda _: analysis(exercises=[{"label": "坏证据", "source_ref": "L999", "solvable": True}]))
    first = wait(client, start(client, book, units, analyze_only=True).json()["job"])
    assert first["status"] == "failed" and first["target"] == 0
    calls = script(app)
    repaired = wait(client, start(client, book, [], resume_job_id=first["id"], analyze_only=True).json()["job"])
    assert repaired["status"] == "completed" and repaired["finished_sources"] == 1
    assert [stage for stage, _ in calls] == ["analysis"]


def test_temporary_batch_failure_can_recover_to_full_requested_count(studio):
    app, client, book = studio
    sizes, serial = [], 0
    def generate(payload):
        nonlocal serial
        sizes.append(payload["count"])
        if len(sizes) == 1:
            raise RuntimeError("synthetic output truncation")
        rows = []
        for _ in range(payload["count"]):
            serial += 1
            rows.append(question(payload["text"], f"合成导数应用第 {serial} 题，解释几何意义。"))
        return rows
    script(app, generate=generate)
    done = wait(client, start(client, book, source_list(client, book)[:1], count=12).json()["job"])
    assert done["status"] == "completed" and done["created_count"] == 12
    assert sizes[:4] == [3, 1, 2, 3]


def test_original_mode_uses_available_exercises_and_cannot_reword_same_original_again(studio):
    app, client, _ = studio
    book, unit = add_pdf(client)
    calls = visual_transport(app)
    first = wait(client, start(client, book, [unit], read_mode="pdf", mode="original", count=12).json()["job"])
    assert first["status"] == "completed" and first["target"] == first["created_count"] == 1
    count = len(calls)
    second = wait(client, start(client, book, [unit], read_mode="pdf", mode="original", count=12).json()["job"])
    assert second["status"] == "completed" and second["target"] == second["created_count"] == 0
    assert len(calls) == count
