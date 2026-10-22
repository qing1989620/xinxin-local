"""Offline real OCR, extraction coverage, restart and cancellation contracts."""
import asyncio
import io
import time
import threading
import uuid
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, NumberObject, DecodedStreamObject

from app.document_text import extract_document
from app import learning_imports
from app.store import Store
from test_learning_studio import studio, source_list


def scanned_workbook():
    image = Image.new("RGB", (1500, 1800), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 40)
    lines = ["第一章 导数练习", "知识：函数 y = x^2 的导函数为 2x。"]
    for index in range(1, 9):
        lines.extend([f"{index}. 求函数 y = x^2 在 x = {index} 处的导数。", f"A. {2*index}     B. {2*index+1}     C. {2*index-1}     D. {2*index+2}"])
    for index, line in enumerate(lines):
        draw.text((80, 60 + index * 88), line, fill="black", font=font)
    jpeg = io.BytesIO()
    image.save(jpeg, "JPEG", quality=95)
    image.close()
    writer = PdfWriter()
    page = writer.add_blank_page(600, 720)
    bitmap = DecodedStreamObject()
    bitmap.set_data(jpeg.getvalue())
    bitmap.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Image"),
                   NameObject("/Width"): NumberObject(1500), NameObject("/Height"): NumberObject(1800),
                   NameObject("/ColorSpace"): NameObject("/DeviceRGB"), NameObject("/BitsPerComponent"): NumberObject(8), NameObject("/Filter"): NameObject("/DCTDecode")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/XObject"): DictionaryObject({NameObject("/Im0"): writer._add_object(bitmap)})})
    commands = DecodedStreamObject()
    commands.set_data(b"q 600 0 0 720 0 0 cm /Im0 Do Q")
    page[NameObject("/Contents")] = writer._add_object(commands)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def wait_import(client, job, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/learning/imports/{job['id']}")
        assert response.status_code == 200
        value = response.json()["job"]
        if value["status"] not in learning_imports.ACTIVE:
            return value
        time.sleep(.05)
    pytest.fail("import did not terminate")


def start(client, file_id, **options):
    return client.post("/api/v1/learning/imports", json={"file_id": file_id, "title": "合成扫描练习册", "subject": "数学", "request_key": uuid.uuid4().hex, **options})


def test_real_local_chinese_ocr_and_physical_page_source_labels(studio, monkeypatch):
    app, client, _ = studio
    uploaded = client.post("/api/v1/files", files={"file": ("synthetic-scanned-workbook.pdf", scanned_workbook())}).json()
    assert not uploaded["indexed"] and uploaded["extraction"]["missing_pages"] == [1]
    assert uploaded["parse_error"]
    job = start(client, uploaded["id"]).json()["job"]
    finished = wait_import(client, job, timeout=90)
    assert finished["status"] == "completed", finished
    row = app.state.store.one("SELECT text FROM files WHERE id=?", (uploaded["id"],))
    assert "导数" in row["text"] and "函数" in row["text"] and len(row["text"]) > 300
    assert "A." in row["text"] or "A．" in row["text"] or "A" in row["text"]
    book = client.get(f"/api/v1/learning/books/{finished['book_id']}").json()["book"]
    assert book["pages"] == 1 and book["extraction"]["ocr_pages"] == 1
    units = source_list(client, book)
    assert units and all(unit["page_from"] == unit["page_to"] == 1 for unit in units)
    progress = client.get(f"/api/v1/learning/imports/{job['id']}").json()["job"]["progress"]
    assert progress == {"page": 1, "total": 1, "method": "ocr"}
    def must_not_repeat_ocr(*_args):
        pytest.fail("completed OCR page should be reused")
    monkeypatch.setattr("app.document_text._recognize", must_not_repeat_ocr)
    repeated = wait_import(client, start(client, uploaded["id"]).json()["job"])
    assert repeated["status"] == "completed" and repeated["book_id"] != book["id"]
    repeated_book = client.get(f"/api/v1/learning/books/{repeated['book_id']}").json()["book"]
    assert repeated_book["extraction"]["resumed_ocr_pages"] == 1
    client.delete(f"/api/v1/files/{uploaded['id']}")
    assert client.get(f"/api/v1/learning/books/{book['id']}").json()["book"]["extraction"]["ocr_pages"] == 1


def test_large_pdf_is_no_longer_excluded_by_16_mib_threshold(studio, monkeypatch):
    from app import files
    monkeypatch.setattr(files, "MAX_EXTRACT", 10)
    _, client, _ = studio
    uploaded = client.post("/api/v1/files", files={"file": ("synthetic-scan.pdf", scanned_workbook())}).json()
    assert uploaded["extraction"]["pages"] == 1  # PDF path parser ran above old text threshold.
    assert "16 MB" not in uploaded["parse_error"]


def test_import_idempotency_authorization_and_cancellation_drain_worker(studio, monkeypatch):
    app, client, book = studio
    entered, exited = threading.Event(), threading.Event()
    def slow(_path, **options):
        entered.set()
        try:
            assert options["cancelled"].wait(10)
            raise asyncio.CancelledError()
        finally:
            exited.set()
    monkeypatch.setattr(learning_imports, "extract_document", slow)
    response = start(client, book["file_id"], request_key="import-idempotent-123")
    assert response.status_code == 200
    job = response.json()["job"]
    assert entered.wait(3)
    repeated = start(client, book["file_id"], request_key="import-idempotent-123").json()["job"]
    assert repeated["id"] == job["id"]
    assert start(client, book["file_id"]).status_code == 409
    assert client.delete(f"/api/v1/files/{book['file_id']}").status_code == 409
    assert client.get(f"/api/v1/learning/imports/{job['id']}", headers={"Authorization": "Bearer invalid"}).status_code == 401
    client.post(f"/api/v1/runs/{job['run_id']}/cancel")
    finished = wait_import(client, job)
    assert finished["status"] == "cancelled" and not finished["book_id"] and exited.is_set()
    assert client.delete(f"/api/v1/files/{book['file_id']}").status_code == 200


def test_restart_exposes_interrupted_import_without_replaying(studio, monkeypatch):
    app, client, book = studio
    monkeypatch.setattr(learning_imports, "extract_document", lambda *_args, **_kwargs: ("识别后的函数知识正文。" * 40, {"complete": True}))
    job = wait_import(client, start(client, book["file_id"]).json()["job"])
    assert job["status"] == "completed"
    app.state.store.execute("UPDATE runs SET status='running' WHERE id=?", (job["run_id"],))
    reopened = Store(app.state.store.directory)
    restored = learning_imports.snapshot(reopened, job["id"])
    assert restored["status"] == "interrupted" and restored["book_id"] == job["book_id"]


def test_huge_text_is_not_silently_truncated(tmp_path, monkeypatch):
    import app.document_text as module
    monkeypatch.setattr(module, "MAX_TEXT_CHARS", 50)
    target = tmp_path / "synthetic.txt"
    target.write_bytes(("需要完整识别的正文。" * 20).encode())
    with pytest.raises(ValueError, match="没有截断保存"):
        extract_document(target)


def test_word_preserves_equations_and_exercise_order_without_inflating_images(tmp_path):
    import zipfile
    target = tmp_path / "synthetic-formulas.docx"
    xml = b'''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body>
    <w:p><w:r><w:t>1. Find the derivative of </w:t></w:r><m:oMath><m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup></m:oMath></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>A. 2x</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
    <w:p><w:r><w:t>2. Simplify </w:t></w:r><m:oMath><m:f><m:num><m:r><m:t>1</m:t></m:r></m:num><m:den><m:r><m:t>x</m:t></m:r></m:den></m:f></m:oMath></w:p>
    </w:body></w:document>'''
    with zipfile.ZipFile(target, "w") as package:
        package.writestr("word/document.xml", xml)
        package.writestr("word/media/unused-image.bin", b"irrelevant-image")
    text, metadata = extract_document(target)
    assert "${x}^{2}$" in text and r"$\frac{1}{x}$" in text
    assert text.index("1. Find") < text.index("A. 2x") < text.index("2. Simplify")
    assert metadata["complete"]
