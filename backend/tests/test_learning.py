"""书架、出题、练习与讲题。

模型全部打桩：这里验证的是"怎么问、怎么判、怎么存"，不是模型水平。
"""

import json

import httpx
from fastapi.testclient import TestClient

from app.config import Config
from app.learning import split_chapters
from app.main import create_app
from test_learning_studio import blind_response


def setup(tmp_path):
    app = create_app(Config(tmp_path, "synthetic-bootstrap"))
    client = TestClient(app)
    token = client.post(
        "/api/v1/auth/setup",
        json={
            "name": "LocalOwner",
            "password": "synthetic-password-123",
            "setup_code": "synthetic-bootstrap",
        },
    ).json()["token"]
    client.headers["Authorization"] = "Bearer " + token
    return app, client


def chapter_text(title: str, body: str) -> str:
    return f"{title}\n\n{body}\n\n" + ("这是用来撑够章节长度的说明性文字。" * 30)


BOOK = "\n\n".join(
    [
        chapter_text("第一章 函数与极限", "函数是数集之间的对应关系，极限描述无限逼近的过程。"),
        chapter_text("第二章 导数", "导数刻画瞬时变化率，几何意义是切线斜率。"),
    ]
)


def upload_book(client, name="微积分讲义.txt", text=BOOK):
    uploaded = client.post("/api/v1/files", files={"file": (name, text.encode())}).json()
    return uploaded["id"]


def add_book(client):
    file_id = upload_book(client)
    response = client.post(
        "/api/v1/learning/books",
        json={"file_id": file_id, "title": "微积分讲义", "subject": "数学"},
    )
    assert response.status_code == 200, response.text
    return response.json()["book"]


def mock_model(content, sink=None):
    def transport(request):
        if sink is not None:
            sink.append(json.loads(request.content))
        messages = json.loads(request.content)["messages"]
        response_content = content
        if "学习材料分析协议" in messages[0]["content"]:
            payload = json.loads(messages[1]["content"])
            response_content = json.dumps({"type": "knowledge", "summary": "本段说明导数刻画瞬时变化率，几何意义为切线斜率。", "knowledge_points": [{"name": "导数", "quote": payload["text"].strip()[:60]}], "exercises": []}, ensure_ascii=False)
        elif "学习独立求解协议" in messages[0]["content"]:
            response_content = json.dumps(blind_response(json.loads(messages[1]["content"])))
        elif "学习出题复核协议" in messages[0]["content"]:
            payload = json.loads(messages[1]["content"])
            response_content = json.dumps({"reviews": [{"index": index, "verdict": "accept", "relevant": True, "solvable": True, "correct": True, "independent_match": True, "reasoning_correct": True, "reasoning_check": "合成逐步核对：计算、前提及推理方向与解析一致。", "reason": "合成审题：题干完整，答案与解析一致。"} for index in range(len(payload["questions"]))]})
        elif "学习工作室协议" in messages[0]["content"]:
            payload = json.loads(messages[1]["content"])
            try:
                rows = json.loads(content)
                if isinstance(rows, list):
                    response_content = json.dumps([dict(row, source_quote=payload["text"].strip()[:60]) for row in rows])
            except ValueError:
                pass
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": response_content}}],
                "usage": {"total_tokens": 80},
            },
        )

    return httpx.MockTransport(transport)


QUESTIONS = json.dumps(
    [
        {
            "kind": "single",
            "stem": "导数的几何意义是什么？",
            "options": [
                {"key": "A", "text": "切线斜率"},
                {"key": "B", "text": "割线长度"},
                {"key": "C", "text": "面积"},
                {"key": "D", "text": "周长"},
            ],
            "answer": "A",
            "explanation": "导数就是切线斜率。",
            "tags": ["导数"],
            "difficulty": 1,
        },
        {
            "kind": "fill",
            "stem": "函数 y=x^2 在 x=2 处的导数是 ___ 。",
            "answer": ["4"],
            "explanation": "y'=2x，代入得 4。",
            "tags": ["导数"],
            "difficulty": 1,
        },
        {
            "kind": "single",
            "stem": "这是一道选项不够的题",
            "options": [{"key": "A", "text": "只有一项"}],
            "answer": "A",
            "explanation": "",
            "tags": [],
            "difficulty": 2,
        },
    ],
    ensure_ascii=False,
)


def test_split_chapters_uses_headings():
    chapters = split_chapters(BOOK)
    assert [item["title"] for item in chapters] == ["第一章 函数与极限", "第二章 导数"]
    assert all(len(item["content"]) > 300 for item in chapters)


def test_split_chapters_falls_back_to_blocks():
    chapters = split_chapters("没有任何标题的正文。" * 400)
    assert len(chapters) >= 1
    assert chapters[0]["content"]


def test_book_from_uploaded_text(tmp_path):
    app, client = setup(tmp_path)
    book = add_book(client)
    assert book["title"] == "微积分讲义"
    assert book["chapter_count"] == 2
    assert book["chapters"][0]["title"].startswith("第一章")
    detail = client.get(f"/api/v1/learning/books/{book['id']}").json()["book"]
    assert detail["question_count"] == 0
    chapter = client.get(f"/api/v1/learning/chapters/{book['chapters'][1]['id']}").json()["chapter"]
    assert "瞬时变化率" in chapter["content"]


def test_generate_questions_validates_and_dedups(tmp_path):
    app, client = setup(tmp_path)
    client.put("/api/v1/settings", json={"model_api_key": "offline-learning-key"})
    book = add_book(client)
    chapter_id = book["chapters"][1]["id"]
    calls = []
    app.state.manager.model_transport = mock_model(QUESTIONS, calls)

    first = client.post(
        f"/api/v1/learning/books/{book['id']}/questions",
        json={"chapter_id": chapter_id, "count": 4},
    ).json()
    assert len(first["created"]) == 2  # 第三道只有 1 个选项，被丢掉
    assert first["skipped"] >= 1
    assert first["created"][0]["kind"] == "single"
    assert json.loads(first["created"][1]["answer"]) == ["4"]
    assert "导数" in calls[0]["messages"][1]["content"]

    again = client.post(
        f"/api/v1/learning/books/{book['id']}/questions",
        json={"chapter_id": chapter_id, "count": 4},
    ).json()
    assert again["created"] == [] and again["skipped"] >= 3

    listed = client.get(
        "/api/v1/learning/questions", params={"chapter_id": chapter_id}
    ).json()["questions"]
    assert len(listed) == 2


def test_quiz_flow_grades_and_completes(tmp_path):
    app, client = setup(tmp_path)
    client.put("/api/v1/settings", json={"model_api_key": "offline-learning-key"})
    app.state.manager.model_transport = mock_model(QUESTIONS)
    book = add_book(client)
    chapter_id = book["chapters"][1]["id"]
    client.post(
        f"/api/v1/learning/books/{book['id']}/questions",
        json={"chapter_id": chapter_id, "count": 4},
    )

    session = client.post(
        "/api/v1/learning/quiz", json={"chapter_id": chapter_id, "count": 8}
    ).json()["session"]
    assert session["total"] == 2 and session["status"] == "active"

    single = next(item for item in session["questions"] if item["kind"] == "single")
    wrong = client.post(
        f"/api/v1/learning/quiz/{session['id']}/answer",
        json={"question_id": single["id"], "answer": "B"},
    ).json()
    assert wrong["status"] == "wrong"
    assert wrong["answer"] == "A"

    fill = next(item for item in session["questions"] if item["kind"] == "fill")
    ok = client.post(
        f"/api/v1/learning/quiz/{session['id']}/answer",
        json={"question_id": fill["id"], "answer": "4"},
    ).json()
    assert ok["status"] == "correct"
    assert ok["state"]["status"] == "completed"
    assert ok["state"]["correct"] == 1

    # 重复作答同一题会覆盖，不会重复计数
    again = client.post(
        f"/api/v1/learning/quiz/{session['id']}/answer",
        json={"question_id": single["id"], "answer": "A"},
    )
    assert again.status_code == 400  # 会话已结束


def test_short_answer_uses_model_grader(tmp_path):
    app, client = setup(tmp_path)
    client.put("/api/v1/settings", json={"model_api_key": "offline-learning-key"})
    payload = json.dumps(
        [
            {
                "kind": "short",
                "stem": "简述导数与单调性的关系。",
                "answer": "导数大于零则单调递增。",
                "explanation": "导数在区间恒正时，函数在该区间严格递增。",
                "tags": ["单调性"],
                "difficulty": 2,
            }
        ],
        ensure_ascii=False,
    )
    app.state.manager.model_transport = mock_model(payload)
    book = add_book(client)
    chapter_id = book["chapters"][1]["id"]
    client.post(
        f"/api/v1/learning/books/{book['id']}/questions",
        json={"chapter_id": chapter_id, "count": 2},
    )
    session = client.post("/api/v1/learning/quiz", json={"chapter_id": chapter_id}).json()["session"]
    question = session["questions"][0]

    app.state.manager.model_transport = mock_model(
        '{"verdict":"partial","reason":"只说了一半，缺少小于零的情况"}'
    )
    graded = client.post(
        f"/api/v1/learning/quiz/{session['id']}/answer",
        json={"question_id": question["id"], "answer": "导数正就递增"},
    ).json()
    assert graded["status"] == "partial"
    assert "缺少" in graded["reason"]


def test_explain_returns_reply_and_history(tmp_path):
    app, client = setup(tmp_path)
    client.put("/api/v1/settings", json={"model_api_key": "offline-learning-key"})
    app.state.manager.model_transport = mock_model(QUESTIONS)
    book = add_book(client)
    chapter_id = book["chapters"][1]["id"]
    created = client.post(
        f"/api/v1/learning/books/{book['id']}/questions",
        json={"chapter_id": chapter_id, "count": 4},
    ).json()["created"]
    question_id = created[0]["id"]

    app.state.manager.model_transport = mock_model(
        "先看切线：\n\n```plot\ny = 2*x - 4\n```"
    )
    reply = client.post(
        f"/api/v1/learning/questions/{question_id}/explain", json={"message": "为什么是 A"}
    ).json()
    assert "切线" in reply["reply"]
    assert len(reply["history"]) == 2
    assert reply["question"]["id"] == question_id


def test_stats_and_delete_cascade(tmp_path):
    app, client = setup(tmp_path)
    client.put("/api/v1/settings", json={"model_api_key": "offline-learning-key"})
    app.state.manager.model_transport = mock_model(QUESTIONS)
    book = add_book(client)
    chapter_id = book["chapters"][1]["id"]
    client.post(
        f"/api/v1/learning/books/{book['id']}/questions",
        json={"chapter_id": chapter_id, "count": 4},
    )
    session = client.post("/api/v1/learning/quiz", json={"chapter_id": chapter_id}).json()["session"]
    question = session["questions"][0]
    app.state.manager.model_transport = mock_model(QUESTIONS)
    client.post(
        f"/api/v1/learning/quiz/{session['id']}/answer",
        json={"question_id": question["id"], "answer": "A"},
    )

    stats = client.get("/api/v1/learning/stats").json()
    assert stats["books"] == 1
    assert stats["answered"] >= 1
    assert stats["accuracy"] > 0

    assert client.delete(f"/api/v1/learning/books/{book['id']}").status_code == 200
    assert client.get("/api/v1/learning/books").json()["books"] == []
    assert client.get("/api/v1/learning/stats").json()["questions"] == 0


def test_quiz_state_hides_answers_until_answered(tmp_path):
    app, client = setup(tmp_path)
    client.put("/api/v1/settings", json={"model_api_key": "offline-learning-key"})
    app.state.manager.model_transport = mock_model(QUESTIONS)
    book = add_book(client)
    chapter_id = book["chapters"][1]["id"]
    client.post(
        f"/api/v1/learning/books/{book['id']}/questions",
        json={"chapter_id": chapter_id, "count": 4},
    )
    session = client.post("/api/v1/learning/quiz", json={"chapter_id": chapter_id}).json()["session"]
    # 没作答之前，接口不能把答案和解析发出来
    for item in session["questions"]:
        assert "answer" not in item and "explanation" not in item

    target = session["questions"][0]
    answered = client.post(
        f"/api/v1/learning/quiz/{session['id']}/answer",
        json={"question_id": target["id"], "answer": "A"},
    ).json()
    state = answered["state"]
    first = next(item for item in state["questions"] if item["id"] == target["id"])
    assert first["answer"] and "explanation" in first
    rest = [item for item in state["questions"] if item["id"] != target["id"]]
    assert rest and all("answer" not in item for item in rest)


def test_delete_book_removes_its_sessions(tmp_path):
    app, client = setup(tmp_path)
    client.put("/api/v1/settings", json={"model_api_key": "offline-learning-key"})
    app.state.manager.model_transport = mock_model(QUESTIONS)
    book = add_book(client)
    chapter_id = book["chapters"][1]["id"]
    client.post(
        f"/api/v1/learning/books/{book['id']}/questions",
        json={"chapter_id": chapter_id, "count": 4},
    )
    client.post("/api/v1/learning/quiz", json={"chapter_id": chapter_id})
    assert client.get("/api/v1/learning/stats").json()["recent"]

    client.delete(f"/api/v1/learning/books/{book['id']}")
    stats = client.get("/api/v1/learning/stats").json()
    assert stats["recent"] == []
    assert stats["books"] == 0


def test_generate_reports_unparseable_model_output(tmp_path):
    app, client = setup(tmp_path)
    client.put("/api/v1/settings", json={"model_api_key": "offline-learning-key"})
    book = add_book(client)
    chapter_id = book["chapters"][1]["id"]
    app.state.manager.model_transport = mock_model("抱歉，我这次没有出题。")
    response = client.post(
        f"/api/v1/learning/books/{book['id']}/questions",
        json={"chapter_id": chapter_id, "count": 3},
    )
    assert response.status_code == 409
    assert "没返回可解析的题目" in response.json()["detail"]
