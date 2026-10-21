"""音乐档位、双辅导与失败恢复；仅使用合成题目和模拟模型。"""

import json
import sqlite3
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.learning import tutor_history
from app.main import create_app
from app.music import atmosphere, current_mood, record_play, remember_emotion, set_influence_level
from app.store import Store


@pytest.fixture
def workspace(tmp_path):
    app = create_app(Config(tmp_path, "synthetic-bootstrap"))
    client = TestClient(app)
    token = client.post("/api/v1/auth/setup", json={
        "name": "LocalOwner", "password": "synthetic-password-123", "setup_code": "synthetic-bootstrap",
    }).json()["token"]
    client.headers["Authorization"] = "Bearer " + token
    client.put("/api/v1/settings", json={"model_api_key": "offline-learning-key"})
    app.state.store.execute(
        "INSERT INTO questions(id,hash,kind,stem,options,answer,explanation,tags,difficulty,created) VALUES(?,?,?,?,?,?,?,?,?,?)",
        ("q1", "synthetic-q1", "single", "y=x^2 在 x=1 的导数？", json.dumps([
            {"key": "A", "text": "2"}, {"key": "B", "text": "1"},
            {"key": "C", "text": "0"}, {"key": "D", "text": "4"},
        ]), "A", "先求导，再代入。", '["导数"]', 1, int(time.time())),
    )
    return app, client


def model(app, content="先求导，再代入。", status=200):
    calls = []

    def respond(request):
        calls.append(json.loads(request.content))
        return httpx.Response(status, json={"choices": [{"message": {"content": content}}]})

    app.state.manager.model_transport = httpx.MockTransport(respond)
    return calls


def calibrated_play(store, ident="t1", moods=None):
    track = {"id": ident, "source": "netease", "name": "合成测试曲"}
    remember_emotion(store, track, {"valence": 0.7, "energy": 0.8, "label": "乐", "moods": moods or ["热血"]})
    record_play(store, track)


def test_influence_defaults_and_preserves_level_when_toggled(workspace):
    app, client = workspace
    assert client.get("/api/v1/music/mood").json()["mood"]["influence_level"] == 2
    selected = client.put("/api/v1/music/settings", json={"influence_level": 4}).json()["mood"]
    assert selected["influence_level"] == 4 and selected["influence"] is True
    calibrated_play(app.state.store)
    client.put("/api/v1/music/settings", json={"influence": False})
    assert atmosphere(app.state.store) == ("", None)
    client.put("/api/v1/music/settings", json={"influence": True})
    assert client.get("/api/v1/music/mood").json()["mood"]["influence_level"] == 4
    assert Store(app.state.store.directory).setting("music_influence_level") == 4
    cleared = client.delete("/api/v1/music/mood").json()["mood"]
    assert cleared["influence_level"] == 4 and cleared["intensity"] == 0


@pytest.mark.parametrize("level", [0, 5, -1, "4", True, 1.5])
def test_invalid_influence_levels_do_not_mutate_settings(workspace, level):
    app, client = workspace
    assert client.put("/api/v1/music/settings", json={"influence_level": level}).status_code == 422
    assert current_mood(app.state.store)["influence_level"] == 2


def test_each_level_changes_prompt_and_includes_calibrated_moods(workspace):
    app, _ = workspace
    calibrated_play(app.state.store, moods=["温柔", "治愈"])
    notes = []
    for level, name in enumerate(["轻微", "自然", "明显", "沉浸"], 1):
        set_influence_level(app.state.store, level)
        note, ambient = atmosphere(app.state.store)
        assert name in note and f"{level}/4" in note
        assert "温柔" in note and "治愈" in note
        assert "解题准确性" in note
        assert ambient["influence_level"] == level
        notes.append(note)
    assert len(set(notes)) == 4


def test_mood_words_decay_along_with_coordinates(workspace):
    app, _ = workspace
    store = app.state.store
    for _ in range(5):
        calibrated_play(store, "old", ["怀旧"])
    store.execute("UPDATE music_plays SET created=?", (time.time() - 90 * 60 * 10,))
    calibrated_play(store, "new", ["热血"])
    words = {item["mood"]: item["share"] for item in current_mood(store)["moods"]}
    assert words["热血"] > 0.99 and words["怀旧"] < 0.01


def test_legacy_tutor_history_migrates_once_and_stays_in_teacher_mode(tmp_path):
    with sqlite3.connect(tmp_path / "xinxin.sqlite3") as db:
        db.execute("CREATE TABLE tutor_messages(id TEXT PRIMARY KEY,question_id TEXT NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,created INTEGER NOT NULL)")
        db.execute("INSERT INTO tutor_messages VALUES('old','q1','assistant','旧讲解',1)")
    for _ in range(2):
        store = Store(tmp_path)
        assert [item["content"] for item in tutor_history(store, "q1")] == ["旧讲解"]
        assert tutor_history(store, "q1", "xinxin") == []


def test_tutor_modes_have_separate_prompts_and_persistent_histories(workspace):
    app, client = workspace
    calibrated_play(app.state.store)
    set_influence_level(app.state.store, 4)
    calls = model(app)
    path = "/api/v1/learning/questions/q1"
    normal = client.post(path + "/explain", json={"message": "普通老师追问"}).json()
    assert normal["mode"] == "teacher" and len(normal["history"]) == 2
    assert "你叫 Xinxin" not in calls[0]["messages"][0]["content"]
    assert "此刻的氛围" not in calls[0]["messages"][0]["content"]
    special = client.post(path + "/explain", json={"mode": "xinxin", "message": "一起想想"}).json()
    assert special["mode"] == "xinxin" and len(special["history"]) == 2
    prompt = calls[1]["messages"][0]["content"]
    assert "你叫 Xinxin" in prompt and "沉浸" in prompt
    assert "普通老师追问" not in json.dumps(calls[1], ensure_ascii=False)
    materials = json.loads(calls[1]["messages"][1]["content"].split("\n", 1)[1])
    assert materials["question"]["options"][0] == {"key": "A", "text": "2"}
    assert client.get(path + "/tutor").json()["history"] == normal["history"]
    assert client.get(path + "/tutor?mode=xinxin").json()["history"] == special["history"]
    assert "answer" not in special["question"] and "explanation" not in special["question"]
    client.put("/api/v1/music/settings", json={"influence": False})
    client.post(path + "/explain", json={"mode": "xinxin", "message": "继续"})
    assert "此刻的氛围" not in calls[2]["messages"][0]["content"]
    assert "ambient_music" not in calls[2]["messages"][1]["content"]
    assert [item["role"] for item in client.get(path + "/tutor?mode=xinxin").json()["history"]] == ["user", "assistant", "user", "assistant"]


@pytest.mark.parametrize("mode", ["teacher", "xinxin"])
def test_empty_model_reply_keeps_history_unchanged(workspace, mode):
    app, client = workspace
    model(app, "已有讲解")
    path = "/api/v1/learning/questions/q1"
    previous = client.post(path + "/explain", json={"mode": mode}).json()["history"]
    model(app, "  ")
    response = client.post(path + "/explain", json={"message": "别丢掉这句", "mode": mode})
    assert response.status_code == 409 and "没有收到讲解" in response.json()["detail"]
    assert client.get(path + "/tutor", params={"mode": mode}).json()["history"] == previous


def test_model_failure_does_not_save_half_a_tutor_turn(workspace):
    app, client = workspace
    model(app, status=503)
    with pytest.raises(RuntimeError):
        client.post("/api/v1/learning/questions/q1/explain", json={"mode": "xinxin"})
    assert tutor_history(app.state.store, "q1", "xinxin") == []


def test_unknown_tutor_modes_rejected_before_calling_model(workspace):
    app, client = workspace
    calls = model(app)
    path = "/api/v1/learning/questions/q1"
    assert client.get(path + "/tutor?mode=unknown").status_code == 422
    assert client.post(path + "/explain", json={"mode": "unknown"}).status_code == 422
    assert not calls and not tutor_history(app.state.store, "q1")


def test_tutor_uses_actual_student_answer(workspace):
    app, client = workspace
    session = client.post("/api/v1/learning/quiz", json={"count": 1}).json()["session"]
    client.post(f"/api/v1/learning/quiz/{session['id']}/answer", json={"question_id": "q1", "answer": "B"})
    calls = model(app)
    reply = client.post("/api/v1/learning/questions/q1/explain", json={}).json()
    materials = json.loads(calls[0]["messages"][1]["content"].split("\n", 1)[1])
    assert materials["student_attempt"]["answer"] == "B"
    assert materials["student_attempt"]["status"] == "wrong"
    assert reply["question"]["answer"] == "A"
