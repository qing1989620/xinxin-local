"""Playwright 专用本地服务：每次新建合成数据库，不读取主人账户或调用外部模型。"""

import asyncio
import hashlib
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
from app.learning import GRADE_PROMPT


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

    grade_calls = {}
    async def respond(_request):
        body = json.loads(_request.content)
        messages = body.get("messages", [])
        if messages and messages[0].get("content") == GRADE_PROMPT:
            payload = json.loads(messages[1]["content"])
            key = payload["stem"]
            grade_calls[key] = grade_calls.get(key, 0) + 1
            if "合成待核对" in key and grade_calls[key] == 1:
                return httpx.Response(503, text="synthetic grading outage")
            return httpx.Response(200, json={"choices": [{"message": {"content": '{"verdict":"correct","reason":"合成核对：回答包含所需知识点，概念一致。"}'}}], "usage": {"total_tokens": 80}})
        if messages and "PDF 原页读取协议" in str(messages[0].get("content")):
            payload = json.loads(messages[1]["content"][0]["text"])
            value = {"pages": [{"page": page, "readable": True, "text": "1. 已知函数 f(x)=x^2，求 x=3 处的导数，并解释该点切线斜率。\nA. 6 B. 3 C. 9 D. 2", "reason": ""} for page in payload["physical_pages"]]}
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(value, ensure_ascii=False)}}], "usage": {"total_tokens": 80}})
        if messages and "学习材料分析协议" in str(messages[0].get("content")):
            payload = json.loads(messages[1]["content"])
            value = {"type": "knowledge", "summary": "本段材料说明导数刻画瞬时变化率，并以切线斜率解释其几何意义。", "knowledge_points": [{"name": "导数", "quote": payload["text"].strip()[:60]}], "exercises": []}
            if payload["text"].startswith("PDF 物理"):
                value = {"type": "exercises", "summary": "合成原页包含导数计算原题，代入自变量求导数，并解释切线斜率。", "knowledge_points": [{"name": "导数", "source_ref": "L2-L3"}, {"name": "无效条目", "source_ref": "L999"}], "exercises": [{"label": "原题 1", "source_ref": "L2-L3", "solvable": True}]}
            return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": json.dumps(value, ensure_ascii=False)}}], "usage": {"total_tokens": 80}})
        if messages and "学习独立求解协议" in str(messages[0].get("content")):
            content = messages[1]["content"]
            payload = json.loads(content[0]["text"] if isinstance(content, list) else content)
            value = {"solutions": [{"index": index, "solvable": True, "answer": "A" if row["kind"] == "single" else ["(0,1)", "A;B"] if "合成逐空" in row["stem"] else ["切线斜率"] if row["kind"] == "fill" else "切线斜率。",
                "solution": "合成盲解：核对定义与函数变化率，导数对应于该点的切线斜率。"} for index, row in enumerate(payload["questions"])]}
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(value, ensure_ascii=False)}}], "usage": {"total_tokens": 80}})
        if messages and "学习出题复核协议" in str(messages[0].get("content")):
            content = messages[1]["content"]
            payload = json.loads(content[0]["text"] if isinstance(content, list) else content)
            value = {"reviews": [{"index": index, "verdict": "reject" if row.get("answer") == "B" else "accept", "relevant": True, "solvable": True, "correct": row.get("answer") != "B", "independent_match": True, "reasoning_correct": True, "reasoning_check": "合成逐步核对：计算、前提及推理方向与解析一致。", "reason": "合成审题：答案错误，拒绝入库。" if row.get("answer") == "B" else "合成审题：核对题意与答案一致，条件完整可解。"} for index, row in enumerate(payload["questions"])]}
            if any("合成审题缺失" in row.get("stem", "") for row in payload["questions"]):
                value = {"reviews": []}
            return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": json.dumps(value, ensure_ascii=False)}}], "usage": {"total_tokens": 80}})
        if messages and "学习工作室协议" in str(messages[0].get("content")):
            payload = json.loads(messages[1]["content"])
            await asyncio.sleep(2 if "合成延迟" in payload["focus"] else .15)
            rows = []
            signature = hashlib.sha256(payload["text"].encode()).hexdigest()[:8]
            offset = len(payload["avoid_stems"])
            for index in range(offset, offset + payload["count"]):
                kind = payload["kinds"][index % len(payload["kinds"])]
                row = {"kind": kind, "stem": f"合成练习 {signature}-{index + 1}：导数的几何意义是什么？",
                       "answer": "A", "options": [{"key": key, "text": text} for key, text in zip("ABCD", ["切线斜率", "面积", "弧长", "周长"])],
                       "explanation": "导数刻画瞬时变化率，在几何上表示切线斜率。", "tags": ["导数"],
                       "difficulty": payload["difficulty"] or 2, "source_quote": payload["text"].strip()[:60]}
                if kind == "fill":
                    row.update(stem=f"合成练习 {signature}-{index + 1}：导数的几何意义为 ___ 。", answer=["切线斜率"])
                elif kind == "short":
                    row["answer"] = "导数的几何意义为切线斜率。"
                if "合成无效" in payload["focus"]:
                    row["source_quote"] = "这段话没有出现在原文，不能作为来源依据。"
                if "合成目录题" in payload["focus"]:
                    row["stem"] = "第三章在第几页？"
                if "合成审题拒绝" in payload["focus"]:
                    row["answer"] = "B"
                if "合成审题缺失" in payload["focus"]:
                    row["stem"] = "合成审题缺失：" + row["stem"]
                if payload["analysis"].get("source_method") == "pdf_images":
                    row["source_ref"] = "L2-L3"
                row["origin"] = "original" if payload["mode"] == "original" else "practice"
                if "合成逐空" in payload["focus"]:
                    row |= {"kind": "fill", "stem": f"合成逐空练习 {signature}-{index + 1}：区间 ___；代码字符串 ___。", "answer": ["(0,1)", "A;B"]}
                if "合成待核对" in payload["focus"]:
                    row |= {"kind": "short", "stem": "合成待核对 " + signature + "：解释导数的几何意义。", "answer": "切线斜率。"}
                rows.append(row)
            return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": json.dumps(rows, ensure_ascii=False)}}], "usage": {"total_tokens": 80}})
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
