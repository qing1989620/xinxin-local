"""Durable book preparation: local OCR can take minutes and must be cancellable."""
from __future__ import annotations

import asyncio
import hashlib
import json

from . import learning
from .document_text import extract_document
from .store import encode, now, uid
from .uploads import finish_upload

ACTIVE = {"queued", "running", "cancelling"}


def snapshot(store, ident):
    # One SQLite statement keeps the linked book and run state in the same
    # read snapshot. Otherwise a fast cached import can return completed with
    # the previous NULL book_id and send the client to a nonexistent book.
    row = store.one("SELECT i.*,r.status AS run_status,r.error AS run_error,"
                    "(SELECT data FROM events WHERE run_id=i.run_id AND kind='learning.import.page' ORDER BY seq DESC LIMIT 1) AS progress_data "
                    "FROM learning_imports i LEFT JOIN runs r ON r.id=i.run_id WHERE i.id=?", (ident,))
    if not row:
        raise ValueError("资料识别任务不存在")
    return {"id": row["id"], "run_id": row["run_id"], "file_id": row["file_id"],
            "book_id": row["book_id"], "status": row["run_status"] or "interrupted",
            "error": row["run_error"] or "", "progress": json.loads(row["progress_data"]) if row["progress_data"] else None}


async def start(store, library, manager, body):
    signature = hashlib.sha256(encode({key: body[key] for key in ("file_id", "title", "subject")}).encode()).hexdigest()
    prior = store.one("SELECT id,signature FROM learning_imports WHERE request_key=?", (body["request_key"],))
    if prior:
        if prior["signature"] != signature:
            raise ValueError("相同请求标识不能用于不同资料")
        return snapshot(store, prior["id"])
    if store.one("SELECT i.id FROM learning_imports i JOIN runs r ON r.id=i.run_id WHERE r.status IN ('queued','running','cancelling')"):
        raise ValueError("已有资料正在识别，请等待或在任务页停止后重试")
    file = store.one("SELECT * FROM files WHERE id=?", (body["file_id"],))
    if not file:
        raise ValueError("先上传这份资料")
    path = library.path(file["id"])
    if path.suffix.lower() not in {".pdf", ".docx", ".txt", ".md", ".markdown"}:
        raise ValueError("请选择 PDF、Word 或文本学习资料")
    ident = uid()
    store.execute("INSERT INTO learning_imports VALUES(?,?,?,NULL,?,?,?)", (ident, None, file["id"], body["request_key"], signature, now()))

    async def operation(run_id, flag):
        def progress(value):
            if not flag.is_set():
                store.event(run_id, "learning.import.page", value)
        cached = {row["page"]: row for row in store.all("SELECT * FROM file_ocr_pages WHERE file_id=? AND version=1", (file["id"],))}
        def save_page(number, text, uncertain):
            if not flag.is_set():
                store.execute("INSERT INTO file_ocr_pages VALUES(?,?,?,?,1) ON CONFLICT(file_id,page) DO UPDATE SET text=excluded.text,uncertain=excluded.uncertain,version=1", (file["id"], number, text, int(uncertain)))
        worker = asyncio.create_task(asyncio.to_thread(extract_document, path, ocr=True, cancelled=flag, progress=progress, cached_pages=cached, page_sink=save_page))
        text, extraction = await finish_upload(worker)
        if flag.is_set():
            raise asyncio.CancelledError()
        # Never replace saved text with a failed/empty OCR result.
        if len(text.strip()) < 200:
            raise ValueError("未识别出足够正文；可能是空白或图像质量过低，请核对原文件")
        with store.connect(write=True) as db:
            if not db.execute("SELECT id FROM files WHERE id=?", (file["id"],)).fetchone():
                raise ValueError("原资料已移除，停止识别")
            old = db.execute("SELECT data FROM file_extractions WHERE file_id=?", (file["id"],)).fetchone()
            old_metadata = json.loads(old["data"]) if old else {"complete": False, "warning": "旧版资料未记录识别覆盖，请使用重新识别后的新副本"}
            old_metadata.pop("page_spans", None)
            db.execute("INSERT OR IGNORE INTO learning_book_extractions SELECT id,? FROM books WHERE file_id=?", (encode(old_metadata), file["id"]))
            db.execute("UPDATE files SET text=? WHERE id=?", (text, file["id"]))
            db.execute("INSERT INTO file_extractions VALUES(?,?) ON CONFLICT(file_id) DO UPDATE SET data=excluded.data", (file["id"], encode(extraction)))
        book = learning.create_book(store, library, file | {"text": text, "pages": extraction.get("pages", 0)}, body["title"], body["subject"])
        store.execute("UPDATE learning_imports SET book_id=? WHERE id=?", (book["id"], ident))
        return {"import_id": ident, "book_id": book["id"], "warning": extraction.get("warning", "")}

    try:
        run = await manager.submit("识别学习资料 · " + file["name"], permission="read", max_calls=0, max_seconds=7200,
                                   max_total_tokens=0, request_key="learning-import:" + body["request_key"],
                                   operation=operation, operation_input={"import_id": ident})
    except BaseException:
        store.execute("DELETE FROM learning_imports WHERE id=?", (ident,))
        raise
    store.execute("UPDATE learning_imports SET run_id=? WHERE id=?", (run["id"], ident))
    return snapshot(store, ident)
