"""Seed a throw-away UI database with product-demo content for screenshots.

Only runs against a data directory under .qa-data/ so the live state is never
touched. Files, memories, schedules and records go through the real API; runs,
conversations and their events are inserted directly because they normally
require a model call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--data", required=True)
    args = parser.parse_args()

    data = Path(args.data).resolve()
    if ".qa-data" not in str(data):
        raise SystemExit("refusing to seed a non-demo directory")

    client = httpx.Client(
        base_url=args.url,
        headers={"Authorization": "Bearer " + args.token},
        timeout=30,
        trust_env=False,
    )
    now = int(time.time() * 1000)
    day = 86_400_000

    files = [
        (
            "实验数据.csv",
            b"group,value\ncontrol,12.4\ntreatment,15.8\ncontrol,11.9\ntreatment,16.3\n",
            "text/csv",
        ),
        (
            "研究笔记.md",
            "# 本周实验\n\n- 样本量 48，随机分组\n- 主要终点：第 7 天读数\n- 下一步：补做剂量梯度\n".encode(),
            "text/markdown",
        ),
        (
            "绘图参数.json",
            b'{"dpi": 300, "format": "pdf", "palette": "muted"}',
            "application/json",
        ),
    ]
    for name, content, mime in files:
        client.post(
            "/api/v1/files",
            files={"file": (name, content, mime)},
            headers={"X-Upload-ID": "demo-" + uuid.uuid4().hex[:12]},
        ).raise_for_status()

    memories = [
        ("我偏好先给结论，再展开证据。", "preference"),
        ("重要实验的原始数据放在工作区 data/raw 下。", "habit"),
        ("当前项目：产业政策评估，主要用省级面板数据。", "project"),
        ("回复使用简体中文，专业术语保留英文原文。", "preference"),
    ]
    for content, category in memories:
        client.post(
            "/api/v1/memories", json={"content": content, "category": category}
        ).raise_for_status()

    schedules = [
        ("每周整理研究笔记", "把本周新增的研究笔记整理成要点，列出待验证的假设。", 10080),
        ("每日检查数据目录", "检查工作区 data/raw 是否有新增文件，列出异常与缺失。", 1440),
    ]
    for title, task, minutes in schedules:
        client.post(
            "/api/v1/schedules",
            json={
                "title": title,
                "task": task,
                "interval_minutes": minutes,
                "enabled": True,
                "permission": "read",
            },
        ).raise_for_status()

    records = [
        {
            "kind": "article",
            "payload": {
                "title": "技能路由笔记",
                "summary": "为什么先检索再让模型决定，而不是把一千多个技能全塞进提示。",
                "content": "检索负责缩小空间，模型负责判断必要性。两者分开，提示才不会失控。",
                "category": "方法",
                "published": True,
            },
        },
        {
            "kind": "article",
            "payload": {
                "title": "本地优先的三个边界",
                "summary": "数据、密钥、执行都不离开这台机器。",
                "content": "数据落在本地 SQLite；密钥加密存本地；执行只经回环与网关。",
                "category": "原则",
                "published": False,
            },
        },
    ]
    for record in records:
        client.post("/api/v1/records", json=record).raise_for_status()
    client.close()

    db = sqlite3.connect(data / "xinxin.sqlite3")
    conversations = [
        ("d" * 32, "把实验数据整理成可复现报告", now - 2 * day),
        ("e" * 32, "技能路由是怎么选技能的", now - 1 * day),
        ("f" * 32, "整理本周的研究笔记", now - 3 * 3_600_000),
    ]
    for ident, title, created in conversations:
        db.execute(
            "INSERT OR REPLACE INTO conversations(id,title,created,updated,archived) VALUES(?,?,?,?,0)",
            (ident, title, created, created),
        )
    messages = [
        ("d" * 32, "user", "把工作区里的实验数据画成散点图，并附上可复现脚本。", now - 2 * day),
        ("d" * 32, "assistant", "已生成散点图与脚本，数据清洗步骤记录在报告中。", now - 2 * day + 600_000),
        ("e" * 32, "user", "技能是怎么被选中的？", now - day),
        ("e" * 32, "assistant", "先检索再判断必要性，最后只把需要的技能交给模型。", now - day + 120_000),
    ]
    for cid, role, content, created in messages:
        db.execute(
            "INSERT OR REPLACE INTO messages(id,conversation_id,role,content,created) VALUES(?,?,?,?,?)",
            (uuid.uuid4().hex, cid, role, content, created),
        )

    usage = {
        "calls": 4,
        "total_tokens": 18342,
        "max_calls": 8,
        "max_total_tokens": 200000,
        "context_window_tokens": 1048576,
    }
    runs = [
        (
            "a" * 32,
            "d" * 32,
            "把实验数据画成散点图并导出可复现脚本",
            "completed",
            "已生成散点图与可复现脚本，数据清洗步骤记录在报告里。",
            "",
            now - 2 * day,
            usage,
        ),
        (
            "b" * 32,
            "e" * 32,
            "梳理技能路由的决策链，输出一页说明",
            "completed",
            "检索 → 关系扩展 → 必要性重排 → 依赖排序，四步都保留痕迹。",
            "",
            now - day,
            {**usage, "calls": 6, "total_tokens": 25106},
        ),
        (
            "c" * 32,
            "f" * 32,
            "整理本周研究笔记并列出待验证假设",
            "completed",
            "整理出 12 条要点，其中 3 条需要补实验验证。",
            "",
            now - 5 * 3_600_000,
            {**usage, "calls": 3, "total_tokens": 12877},
        ),
        (
            "9" * 32,
            "f" * 32,
            "导出报告 PDF 并检查排版",
            "failed",
            "",
            "本轮模型调用次数达到预算（8/8），尚未形成最终答复；已执行的工具记录会保留。",
            now - 4 * 3_600_000,
            {**usage, "calls": 8},
        ),
    ]
    for ident, cid, task, status, result, error, created, used in runs:
        db.execute(
            "INSERT OR REPLACE INTO runs(id,conversation_id,task,status,permission,server_id,max_calls,max_seconds,created,updated,result,error,usage,request_key,request_signature,allow_memory,max_total_tokens,context_window_tokens,resume_of) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                ident, cid, task, status, "workspace", None, 8, 300,
                created, created + 300_000, result, error,
                json.dumps(used), None,
                hashlib.sha256(ident.encode()).hexdigest(), 1, 200000, 1048576, None,
            ),
        )
        events = [
            ("queued", {"permission": "workspace"}),
            ("started", {}),
            (
                "skills",
                {
                    "mode": "fabric",
                    "selected": ["scientific-plotting", "data-cleaning"],
                    "decision": "auto",
                    "components": {"llm_rerank": True},
                },
            ),
            ("delta", {"text": result or "正在准备最终答复…"}),
            (
                "finished",
                {"status": status, **({"error": error} if error else {})},
            ),
        ]
        for seq, (kind, payload) in enumerate(events, 1):
            db.execute(
                "INSERT OR REPLACE INTO events(run_id,seq,kind,data,created) VALUES(?,?,?,?,?)",
                (ident, seq, kind, json.dumps(payload, ensure_ascii=False), created + seq * 1000),
            )
    db.commit()
    db.close()
    print(f"seeded demo data under {data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
