from __future__ import annotations

import hashlib
import io
import json
import mimetypes
import re
from pathlib import Path

from .skillnet.index import BM25Index
from .store import now, uid

MAX_UPLOAD = 64 * 1024 * 1024
MAX_EXTRACT = 16 * 1024 * 1024


class FileTooLarge(ValueError):
    pass


class UploadConflict(ValueError):
    pass


TEXT_EXT = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".yaml",
    ".yml",
    ".log",
}


class FileLibrary:
    def __init__(self, store):
        self.store = store
        self.root = store.directory / "files"
        self.root.mkdir(exist_ok=True)

    def save(self, name, content, mime=None, run_id=None, extract=True):
        return self.save_stream(name, io.BytesIO(content), mime, run_id, extract)

    def save_stream(
        self, name, source, mime=None, run_id=None, extract=True, request_id=None
    ):
        """Bounded disk copy; a retry key commits with the resource in one transaction."""
        name = Path(name.replace("\\", "/")).name[:180]
        if not name or name in {".", ".."}:
            raise ValueError("文件为空")
        mime = mime or mimetypes.guess_type(name)[0] or "application/octet-stream"
        ident = uid()
        suffix = Path(name).suffix.lower()
        suffix = suffix if re.fullmatch(r"\.[a-z0-9]{1,12}", suffix) else ""
        target = self.root / (ident + suffix)
        staging = self.root / (ident + ".incoming")
        total, digest = 0, hashlib.sha256()
        committed = False
        try:
            with staging.open("xb") as output:
                while chunk := source.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_UPLOAD:
                        raise FileTooLarge("文件超过 64 MB 上限")
                    output.write(chunk)
                    digest.update(chunk)
            if not total:
                raise ValueError("文件为空")
            checksum = digest.hexdigest()
            signature = json.dumps([name, mime, checksum], ensure_ascii=False)
            text, parse_error = "", ""
            if extract and total <= MAX_EXTRACT:
                try:
                    text = self.extract(name, staging.read_bytes())[:2_000_000]
                except Exception:  # noqa: BLE001 -- optional document parsers may raise format-specific errors; retain the original.
                    parse_error = "已保存原文件，暂时无法提取文本"
            elif extract:
                parse_error = "原文件已保存；超过 16 MB 的文件不自动提取正文，可交给 Agent 按需处理"
            with self.store.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                previous = (
                    db.execute(
                        "SELECT file_id,signature FROM uploads WHERE request_id=?",
                        (request_id,),
                    ).fetchone()
                    if request_id
                    else None
                )
                if previous:
                    if previous["signature"] != signature:
                        raise UploadConflict("上传重试标识与文件不匹配，请重新选择文件")
                    ident = previous["file_id"]
                else:
                    staging.replace(target)
                    db.execute(
                        "INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?)",
                        (
                            ident,
                            name,
                            mime,
                            total,
                            checksum,
                            str(target),
                            text,
                            run_id,
                            now(),
                        ),
                    )
                    if request_id:
                        db.execute(
                            "INSERT INTO uploads VALUES(?,?,?)",
                            (request_id, ident, signature),
                        )
            committed = True
            return {**self.get(ident), "parse_error": parse_error}
        finally:
            staging.unlink(missing_ok=True)
            if not committed:
                target.unlink(missing_ok=True)

    @staticmethod
    def extract(name, content):
        ext = Path(name).suffix.lower()
        if ext in TEXT_EXT:
            return content.decode("utf-8", errors="replace")
        if ext == ".pdf":
            from pypdf import PdfReader

            return "\n\n".join(
                page.extract_text() or ""
                for page in PdfReader(io.BytesIO(content)).pages
            )
        if ext == ".docx":
            from docx import Document

            document = Document(io.BytesIO(content))
            return "\n".join(
                [p.text for p in document.paragraphs]
                + [
                    " | ".join(cell.text for cell in row.cells)
                    for table in document.tables
                    for row in table.rows
                ]
            )
        return ""

    def get(self, ident):
        row = self.store.one("SELECT * FROM files WHERE id=?", (ident,))
        if not row:
            raise ValueError("文件不存在")
        return {
            key: value for key, value in row.items() if key not in {"path", "text"}
        } | {"indexed": bool(row["text"])}

    def path(self, ident):
        row = self.store.one("SELECT * FROM files WHERE id=?", (ident,))
        if not row:
            raise ValueError("文件不存在")
        path = Path(row["path"]).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():
            raise ValueError("文件不可用")
        return path

    def search(self, query, k=5):
        rows = self.store.all(
            "SELECT id,name,text FROM files WHERE text!='' ORDER BY created DESC"
        )
        chunks = []
        for row in rows:
            text = row["text"]
            for offset in range(0, len(text), 900):
                chunks.append(
                    {
                        "file_id": row["id"],
                        "filename": row["name"],
                        "offset": offset,
                        "text": text[offset : offset + 1100],
                    }
                )
        if not chunks:
            return []
        index = BM25Index()
        index.fit(
            [str(i) for i in range(len(chunks))], [chunk["text"] for chunk in chunks]
        )
        return [
            {**chunks[int(i)], "score": score}
            for i, score in index.search(query, top_k=k)
        ]

    def read(self, ident, offset=0, limit=12000):
        if offset < 0 or not 1 <= limit <= 16000:
            raise ValueError("读取范围无效")
        row = self.store.one("SELECT name,text FROM files WHERE id=?", (ident,))
        if not row:
            raise ValueError("文件不存在")
        end = min(offset + limit, len(row["text"]))
        return {
            "id": ident,
            "name": row["name"],
            "text": row["text"][offset:end],
            "offset": offset,
            "next_offset": end if end < len(row["text"]) else None,
            "total_chars": len(row["text"]),
        }

    def delete(self, ident):
        target = self.path(ident)
        with self.store.connect() as db:
            db.execute("DELETE FROM uploads WHERE file_id=?", (ident,))
            db.execute("DELETE FROM files WHERE id=?", (ident,))
        target.unlink(missing_ok=True)
