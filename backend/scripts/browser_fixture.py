"""Playwright 专用本地服务：每次新建合成数据库，不读取主人账户或调用外部模型。"""

import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["XINXIN_DATA_DIR"] = str(ROOT / ".qa-data" / ("browser-" + uuid.uuid4().hex))
os.environ["DEEPSEEK_API_KEY"] = ""
os.environ["XINXIN_SKILLNET_RERANK"] = "0"

import httpx
import uvicorn
from fastapi.testclient import TestClient

from app.config import Config
from app.main import create_app


def create_fixture():
    app = create_app(Config(Path(os.environ["XINXIN_DATA_DIR"]), "synthetic-browser-bootstrap"))
    client = TestClient(app)
    response = client.post("/api/v1/auth/setup", json={
        "name": "BrowserOwner", "password": "synthetic-browser-password-123",
        "setup_code": "synthetic-browser-bootstrap",
    })
    response.raise_for_status()
    client.headers["Authorization"] = "Bearer " + response.json()["token"]
    client.put("/api/v1/settings", json={"model_api_key": "synthetic-offline-key"}).raise_for_status()

    def respond(_request):
        return httpx.Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": "先求导，再把 x=1 代入。\n\n```plot\ny=x^2\n```"}}],
            "usage": {"total_tokens": 80},
        })

    app.state.manager.model_transport = httpx.MockTransport(respond)
    text = "第一章 导数\n\n" + "导数刻画变化率，几何意义为切线斜率。" * 40
    uploaded = client.post("/api/v1/files", files={"file": ("合成浏览器讲义.txt", text.encode())})
    uploaded.raise_for_status()
    book = client.post("/api/v1/learning/books", json={"file_id": uploaded.json()["id"], "title": "合成浏览器讲义"}).json()["book"]
    chapter = book["chapters"][0]
    app.state.store.execute(
        "INSERT INTO questions(id,book_id,chapter_id,hash,kind,stem,options,answer,explanation,tags,difficulty,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        ("browser-question", book["id"], chapter["id"], "browser-question", "single", "y=x^2 在 x=1 的导数？",
         json.dumps([{"key": "A", "text": "2"}, {"key": "B", "text": "1"}, {"key": "C", "text": "0"}, {"key": "D", "text": "4"}]),
         "A", "先求导，再代入。", '["导数"]', 1, 1),
    )
    return app


if __name__ == "__main__":
    uvicorn.run(create_fixture(), host="127.0.0.1", port=8017, access_log=False)
