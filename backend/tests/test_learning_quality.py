"""Adversarial materials, critic failures, quantity, OCR and real stream limits."""
import asyncio
import io
import json
import threading
import time

import httpx
import pytest

from app import learning, learning_quality as quality
from app.document_text import extract_document
from app.files import FileLibrary, FileTooLarge, MAX_UPLOAD
from app.learning_studio import sources
from app.store import Store
from test_learning_studio import studio, add_book, source_list, start, wait, question


def script(app, *, analyze=None, generate=None, review=None):
    calls = []
    async def respond(request):
        messages = json.loads(request.content)["messages"]
        payload = json.loads(messages[1]["content"])
        protocol = messages[0]["content"]
        if "学习材料分析协议" in protocol:
            stage = "analysis"
            value = analyze(payload) if analyze else {"type": "knowledge", "summary": "材料解释导数表示瞬时变化率，以及切线斜率的几何意义。", "knowledge_points": [{"name": "导数", "quote": payload["text"].strip()[:60]}], "exercises": []}
        elif "学习出题复核协议" in protocol:
            stage = "review"
            value = review(payload) if review else {"reviews": [{"index": index, "verdict": "accept", "relevant": True, "solvable": True, "correct": True, "reason": "合成核对：重新求解后答案与解析一致。"} for index in range(len(payload["questions"]))]}
        else:
            stage = "generation"
            value = generate(payload) if generate else [question(payload["text"])]
        calls.append((stage, payload))
        if asyncio.iscoroutine(value):
            value = await value
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(value, ensure_ascii=False)}}], "usage": {"total_tokens": 80}})
    app.state.manager.model_transport = httpx.MockTransport(respond)
    return calls


def test_numbered_exercises_and_table_of_contents_are_not_lost():
    toc = "目录\n" + "\n".join(f"第{number}章 微积分知识…………{number * 5}" for number in range(1, 18))
    content = "\n\n第一章 导数\n" + "导数的几何意义为切线斜率。" * 5 + "\n1. 已知 y=x^2，求 x=3 处的导数。\nA. 6 B. 9 C. 3 D. 2\n2. 说明导数与单调性的关系。\n3. 求函数 y=x^3 的导函数。"
    chapters = learning.split_chapters(toc + content)
    combined = "\n".join(row["content"] for row in chapters)
    for stem in ("1. 已知", "2. 说明", "3. 求函数", "第17章 微积分知识"):
        assert stem in combined
    assert quality.material_profile(chapters[0]["content"], "目录")["eligible"] is False
    assert len(chapters) == 2


def test_multilevel_exercise_instructions_remain_in_source_body():
    text = "第一章 导数\n" + "导数表示瞬时变化率，切线斜率是重要的几何意义。" * 10
    text += "\n1.1 求下列函数的导数\nf(x)=x^2\n" + "请写出计算过程并解释每一步依据。" * 10
    text += "\n1.2 下列说法中正确的是\nA. 导数表示变化率\nB. 导数一定为正\n" + "需要结合具体函数判断结论是否成立。" * 8
    combined = "\n".join(row["content"] for row in learning.split_chapters(text))
    assert "1.1 求下列函数的导数" in combined and "1.2 下列说法中正确的是" in combined


@pytest.mark.parametrize("first,second", [
    ("求 f(x)=x+1 在 x=2 处的值。", "求 f(x)=x-1 在 x=2 处的值。"),
    ("判断 x≤2 是否成立。", "判断 x≥2 是否成立。"),
    ("求 x*2 的值。", "求 x/2 的值。"),
    ("说明压力增大后的变化。", "说明压力减小后的变化。"),
    ("求 X 在此处的值。", "求 x 在此处的值。"),
    ('求表达式 "1" + "2" 的结果。', '求表达式 1 + 2 的结果。'),
    ('字符串 "1 2" 的长度是多少？', '字符串 "12" 的长度是多少？'),
])
def test_dedup_preserves_mathematical_and_logical_meaning(first, second):
    assert not quality.duplicate_stem(second, [first])
    assert quality.duplicate_stem(first + "？", [first])


@pytest.mark.parametrize("stem", ["第三章在第几页？", "哪个章节讲导数，在第几页开始？", "导数这一章位于第 ___ 页。", "What page does Chapter 2 begin on?", "如图所示，求三角形面积。"])
def test_metadata_or_missing_figure_questions_are_rejected(stem):
    assert quality.question_issue(stem)


def test_real_mathematics_and_reading_are_not_metadata_questions():
    for stem in ["求 f(x)=x^2 在 x=3 处的导数。", "比较两种算法的空间复杂度。", "请解释段落中作者的论证方法。",
                 "什么是字节？", "一个字节多少位？", "What is a page fault?", "Which page replacement algorithm minimizes faults?", "解释节拍与节奏的区别。"]:
        assert not quality.question_issue(stem)
    for stem in ["如图像分类任务中，为什么需要划分训练集和验证集？", "例如图书管理系统中如何建立索引？", "请比较以下图像处理方法：中值滤波和均值滤波。"]:
        assert not quality.question_issue(stem)


def test_contents_and_answer_key_cannot_start_generation(studio):
    app, client, _ = studio
    calls = script(app)
    for text in ["目录\n" + "\n".join(f"第{n}章 数学知识…………{n * 5}" for n in range(1, 30)),
                 "参考答案\n" + "\n".join(f"{n}. A" for n in range(1, 90))]:
        book = add_book(client, text)
        units = source_list(client, book)
        assert all(not unit["eligible"] for unit in units)
        response = start(client, book, units[:1])
        assert response.status_code == 409
    assert calls == []


def test_default_twelve_and_twenty_four_questions_are_batched_and_reviewed(studio):
    app, client, book = studio
    def generate(payload):
        offset = len(payload["avoid_stems"])
        return [question(payload["text"], f"求 f(x)=x^2 在 x={n} 处的导数。") | {
            "options": [{"key": key, "text": str(value)} for key, value in zip("ABCD", [2*n, 2*n+1, 2*n-1, 2*n+2])], "origin": "practice"
        } for n in range(offset + 1, offset + payload["count"] + 1)]
    calls = script(app, generate=generate)
    units = source_list(client, book)
    job = wait(client, start(client, book, units[:1], count=24).json()["job"])
    assert job["status"] == "completed" and job["created_count"] == 24
    assert [kind for kind, _ in calls].count("analysis") == 1
    assert [kind for kind, _ in calls].count("generation") == 8
    assert [kind for kind, _ in calls].count("review") == 8
    assert max(value["count"] for kind, value in calls if kind == "generation") == 3
    saved = client.get(f"/api/v1/learning/questions?book_id={book['id']}").json()["questions"]
    assert len(saved) == 24 and all(row["review"] == "model_checked" and row["origin"] == "practice" for row in saved)
    large = add_book(client, "第一章 导数\n" + "导数表示瞬时变化率，在几何上表示切线斜率。\n" * 5000)
    assert start(client, large, source_list(client, large)[:17], count=24).status_code == 409


@pytest.mark.parametrize("failure", ["incorrect", "missing", "duplicate", "malformed"])
def test_critic_rejection_or_invalid_response_never_enters_bank(studio, failure):
    app, client, book = studio
    def review(payload):
        row = {"index": 0, "verdict": "reject", "relevant": True, "solvable": True, "correct": False, "reason": "独立计算发现答案错误，应当拒绝入库。"}
        return {"reviews": [] if failure == "missing" else [row, row] if failure == "duplicate" else [row]} if failure != "malformed" else ["not an object"]
    script(app, review=review)
    job = wait(client, start(client, book, source_list(client, book)[:1]).json()["job"])
    assert job["status"] == "failed" and job["created_count"] == 0 and job["items"][0]["rejected"] >= 1
    assert not app.state.store.all("SELECT id FROM questions WHERE book_id=?", (book["id"],))


def test_analysis_requires_literal_evidence_and_can_be_requested_without_questions(studio):
    app, client, book = studio
    units = source_list(client, book)
    script(app, analyze=lambda _: {"type": "knowledge", "summary": "虚构的总结不能被采信，本测试应拒绝。", "knowledge_points": [{"name": "概率", "quote": "原文根本没有这段概率知识和文字。"}], "exercises": []})
    failed = wait(client, start(client, book, units[:1], analyze_only=True).json()["job"])
    assert failed["status"] == "failed" and failed["created_count"] == 0
    assert not app.state.store.all("SELECT * FROM learning_source_analysis")
    calls = script(app)
    done = wait(client, start(client, book, units[:1], analyze_only=True).json()["job"])
    assert done["status"] == "completed" and done["target"] == 0
    assert [kind for kind, _ in calls] == ["analysis"]
    listing = client.get(f"/api/v1/learning/books/{book['id']}/sources").json()
    assert listing["coverage"]["analyzed"] == 1 and listing["coverage"]["knowledge_points"] == 1
    assert listing["sources"][0]["analysis"]["summary"]
    wait(client, start(client, book, units[:1]).json()["job"])
    assert [kind for kind, _ in calls].count("analysis") == 1  # cached, versioned analysis


def test_analyze_only_does_not_require_exercises_in_original_mode(studio):
    app, client, book = studio
    script(app)
    done = wait(client, start(client, book, source_list(client, book)[:1], analyze_only=True, mode="original").json()["job"])
    assert done["status"] == "completed" and done["finished_sources"] == 1 and done["created_count"] == 0


def test_original_mode_does_not_mislabel_variations(studio):
    app, client, _ = studio
    text = "第一章 导数练习\n" + "1. 已知函数 y=x^2，求 x=3 处的导数，并解释几何意义。\n" * 8
    book = add_book(client, text)
    def analyze(payload):
        return {"type": "exercises", "summary": "材料包含导数计算原题，要求代入并解释切线斜率。", "knowledge_points": [], "exercises": [{"label": "第1题", "quote": payload["text"].splitlines()[0], "solvable": True}]}
    script(app, analyze=analyze, generate=lambda payload: [question(payload["text"]) | {"origin": "practice"}])
    job = wait(client, start(client, book, source_list(client, book)[:1], mode="original").json()["job"])
    assert job["created_count"] == 0 and "标识" in job["items"][0]["error"]


def test_source_correction_invalidates_summary_and_protects_existing_citations(studio):
    app, client, book = studio
    script(app)
    unit = source_list(client, book)[0]
    wait(client, start(client, book, [unit], analyze_only=True).json()["job"])
    text = "人工校对的原题：函数 y=x^2 的导函数为 2x，导数反映瞬时变化率。\n" * 5
    changed = client.put(f"/api/v1/learning/sources/{unit['id']}", json={"content": text})
    assert changed.status_code == 200
    assert changed.json()["source"]["edited_at"] and not changed.json()["source"]["analysis"]
    assert not app.state.store.one("SELECT data FROM learning_source_analysis WHERE source_id=?", (unit["id"],))
    assert "人工校对" in learning.chapter(app.state.store, unit["chapter_id"])["content"]
    wait(client, start(client, book, [unit]).json()["job"])
    assert client.put(f"/api/v1/learning/sources/{unit['id']}", json={"content": text + "不能覆盖已有依据"}).status_code == 409
    assert client.put(f"/api/v1/learning/sources/{unit['id']}", json={"content": "过短"}).status_code == 422


def test_cancelling_after_a_batch_preserves_committed_six_and_resumes_only_missing(studio):
    app, client, book = studio
    second_batch = threading.Event()
    async def generate(payload):
        offset = len(payload["avoid_stems"])
        if offset >= 6:
            second_batch.set()
            await asyncio.sleep(1)
        return [question(payload["text"], f"导数在 x={n} 处表示什么变化率？") for n in range(offset + 1, offset + payload["count"] + 1)]
    script(app, generate=generate)
    initial = start(client, book, source_list(client, book)[:1], count=12).json()["job"]
    assert second_batch.wait(5)
    client.post(f"/api/v1/runs/{initial['run_id']}/cancel")
    stopped = wait(client, initial)
    assert stopped["status"] == "cancelled" and stopped["created_count"] == 6
    resumed = wait(client, start(client, book, [], resume_job_id=initial["id"]).json()["job"])
    assert resumed["target"] == 6 and resumed["created_count"] == 6 and resumed["status"] == "completed"
    assert learning.get_book(app.state.store, book["id"])["question_count"] == 12


def test_obvious_legacy_metadata_is_quarantined_without_deleting_history(studio):
    app, client, book = studio
    unit = source_list(client, book)[0]
    app.state.store.execute("INSERT INTO questions(id,book_id,chapter_id,hash,kind,stem,created) VALUES('legacy-index',?,?,?,'short',?,1)", (book["id"], unit["chapter_id"], "legacy-index", "第二章在第几页？"))
    quality.quarantine_legacy(app.state.store)
    assert app.state.store.one("SELECT review FROM questions WHERE id='legacy-index'")["review"] == "excluded"
    assert learning.get_book(app.state.store, book["id"])["question_count"] == 0
    assert learning.list_questions(app.state.store, book["id"]) == []
    assert client.post("/api/v1/learning/quiz", json={"book_id": book["id"]}).status_code == 409


def test_deduplication_is_book_scoped_and_does_not_empty_a_reimport(studio):
    app, client, first = studio
    second = add_book(client)
    script(app)
    for book in (first, second):
        result = wait(client, start(client, book, source_list(client, book)[:1]).json()["job"])
        assert result["created_count"] == 1
    repeated = wait(client, start(client, first, source_list(client, first)[1:2]).json()["job"])
    assert repeated["created_count"] == 0 and repeated["items"][0]["duplicates"] > 0


def test_actual_256_mib_stream_accepts_boundary_and_cleans_one_byte_over(tmp_path):
    class RepeatingStream:
        def __init__(self, size): self.remaining = size
        def read(self, size):
            assert 0 < size <= 1024 * 1024
            amount = min(size, self.remaining)
            self.remaining -= amount
            return b"x" * amount
    assert MAX_UPLOAD == 256 * 1024 * 1024
    library = FileLibrary(Store(tmp_path))
    saved = library.save_stream("boundary.bin", RepeatingStream(MAX_UPLOAD), extract=False)
    assert saved["size"] == MAX_UPLOAD
    library.delete(saved["id"])
    with pytest.raises(FileTooLarge):
        library.save_stream("too-large.bin", RepeatingStream(MAX_UPLOAD + 1), extract=False)
    assert not list(library.root.iterdir())


def test_dedup_and_legacy_quarantine_cover_the_entire_book(studio):
    app, client, book = studio
    from app.store import uid
    rows = [(uid(), book["id"], book["chapters"][0]["id"], learning._hash(stem, "short"), "short", stem, "[]", "正确答案", "解释完整的知识含义。", "[]", 2, index)
            for index, stem in enumerate(["导数的几何意义是什么", "什么是字节？", "What is a page fault?"] + [f"第 {number} 组导数综合练习的答案是什么？" for number in range(600)])]
    with app.state.store.connect(write=True) as db:
        db.executemany("INSERT INTO questions(id,book_id,chapter_id,hash,kind,stem,options,answer,explanation,tags,difficulty,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    quality.quarantine_legacy(app.state.store)
    assert all(app.state.store.one("SELECT review FROM questions WHERE id=?", (row[0],))["review"] != "excluded" for row in rows[:3])
    app.state.store.execute("UPDATE questions SET review='excluded' WHERE id=?", (rows[1][0],))
    quality.quarantine_legacy(app.state.store)
    assert app.state.store.one("SELECT review FROM questions WHERE id=?", (rows[1][0],))["review"] == "legacy"
    script(app)
    result = wait(client, start(client, book, source_list(client, book)[:1]).json()["job"])
    assert result["created_count"] == 0 and result["items"][0]["duplicates"] >= 1


def test_legacy_chapter_generation_distributes_total_across_complete_chapter(studio):
    app, client, _ = studio
    book = add_book(client, "第一章 微积分\n" + "导数的概念是瞬时变化率，可用切线斜率说明。\n" * 250 + "积分可用于计算累积量，末尾知识不能被遗漏。\n" * 200)
    counter = 0
    def generate(payload):
        nonlocal counter
        result = []
        for _ in range(payload["count"]):
            counter += 1
            result.append(question(payload["text"], f"解释第 {counter} 个微积分练习的解题思路。"))
        return result
    calls = script(app, generate=generate)
    response = client.post(f"/api/v1/learning/books/{book['id']}/questions", json={"chapter_id": book["chapters"][0]["id"], "count": 7})
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["created"]) == result["job"]["target"] == 7
    payloads = [payload for stage, payload in calls if stage == "generation"]
    assert len(payloads) > 1 and sum(payload["count"] for payload in payloads) == 7
    assert any("末尾知识不能被遗漏" in payload["text"] for payload in payloads)
