"""Playwright 专用本地服务：每次新建合成数据库，不读取主人账户或调用外部模型。"""

import asyncio
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

    async def respond(_request):
        body = json.loads(_request.content)
        messages = body.get("messages", [])
        latest_user = next((index for index in range(len(messages) - 1, -1, -1) if messages[index].get("role") == "user"), -1)
        if latest_user >= 0 and "合成 SkillNet 路线" in str(messages[latest_user].get("content")):
            await asyncio.sleep(1.2)  # Keep the real SSE route observable before tool completion.
            exchanges = messages[latest_user + 1:]
            names = [call["function"]["name"] for item in exchanges for call in item.get("tool_calls", [])]
            name = "load_skill" if not names else "write_file" if "write_file" not in names else ""
            if name:
                arguments = {"name": "coding-workspace"} if name == "load_skill" else {"path": "skillnet-demo.txt", "content": "合成 SkillNet 演示交付。"}
                delta = {"tool_calls": [{"index": 0, "id": "fixture-" + name, "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}]}
            else:
                denied = any('"ok":false' in str(item.get("content", "")).replace(" ", "") for item in exchanges if item.get("role") == "tool")
                delta = {"content": "已读取代码工作区方法；本轮只读权限阻止了写入。" if denied else "已读取代码工作区方法，说明文件已保存为本轮交付。"}
            chunks = [{"choices": [{"delta": delta, "finish_reason": None}]}, {"choices": [{"delta": {}, "finish_reason": "tool_calls" if name else "stop"}], "usage": {"total_tokens": 80}}]
            stream = "".join("data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n" for chunk in chunks) + "data: [DONE]\n\n"
            return httpx.Response(200, content=stream.encode(), headers={"Content-Type": "text/event-stream"})
        if body.get("stream"):
            stream = 'data: ' + json.dumps({"choices": [{"delta": {"content": "合成问候：你好。"}, "finish_reason": None}]}, ensure_ascii=False) + '\n\ndata: ' + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"total_tokens": 30}}) + '\n\ndata: [DONE]\n\n'
            return httpx.Response(200, content=stream.encode(), headers={"Content-Type": "text/event-stream"})
        return httpx.Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": "先求导，再把 x=1 代入。\n\n```plot\ny=x^2\n```"}}],
            "usage": {"total_tokens": 80},
        })

    app.state.manager.model_transport = httpx.MockTransport(respond)
    search = app.state.router.search

    def offline_selection(query, *args, **kwargs):
        result = search(query, *args, **kwargs)
        if "合成 SkillNet 路线" in query:
            return app.state.router.apply_rerank(result, {
                "skills": ["coding-workspace"],
                "decisions": [{"name": "coding-workspace", "reason": "需要在工作区写入说明文件，使用此方法指导文件操作和交付。"}],
            }, k=1)
        if query == "一句简短的合成问候":
            return app.state.router.apply_rerank(result, {"skills": [], "decisions": []})
        return result

    app.state.router.search = offline_selection
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
