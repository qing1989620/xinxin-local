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


def scanned_workbook(*, header=False, nested=False, inline=False):
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
    drawing = b"q 600 0 0 720 0 0 cm /Im0 Do Q"
    if inline:
        # Inline images are content-stream objects, not /XObject resources.
        drawing = b"q 600 0 0 720 0 0 cm BI /W 1500 /H 1800 /CS /RGB /BPC 8 /F /DCT ID " + jpeg.getvalue() + b"\nEI Q"
        page[NameObject("/Resources")] = DictionaryObject()
    if nested:
        from pypdf.generic import ArrayObject
        form = DecodedStreamObject()
        form.set_data(drawing)
        form.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Form"),
                     NameObject("/BBox"): ArrayObject([NumberObject(n) for n in (0, 0, 600, 720)]),
                     NameObject("/Resources"): page["/Resources"]})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/XObject"): DictionaryObject({NameObject("/Fm0"): writer._add_object(form)})})
        drawing = b"q /Fm0 Do Q"
    if header:
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
        page["/Resources"][NameObject("/Font")] = DictionaryObject({NameObject("/F1"): writer._add_object(font)})
        drawing += b" BT /F1 8 Tf 15 710 Td (Synthetic Workbook header: private teaching copy for document recognition tests only.) Tj ET"
    commands.set_data(drawing)
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
    response = client.get(f"/api/v1/learning/books/{repeated['book_id']}")
    assert response.status_code == 200, response.text
    repeated_book = response.json()["book"]
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


@pytest.mark.parametrize("nested,inline", [(False, False), (True, False), (False, True)])
def test_native_header_does_not_hide_scanned_body(tmp_path, monkeypatch, nested, inline):
    target = tmp_path / "hybrid.pdf"
    target.write_bytes(scanned_workbook(header=True, nested=nested, inline=inline))
    text, metadata = extract_document(target)
    assert len(text) > 40 and not metadata["complete"] and metadata["missing_pages"] == [1]
    recognized = "导数练习的文字条件：函数 y=x^2 的导函数为 2x。" * 5
    calls = []
    def recognize(image, _cancelled):
        calls.append(image.size)
        return recognized, False
    monkeypatch.setattr("app.document_text._recognize", recognize)
    text, metadata = extract_document(target, ocr=True)
    assert calls and recognized in text and "Synthetic Workbook header" in text
    assert metadata["complete"] and metadata["ocr_pages"] == 1
    monkeypatch.setattr("app.document_text._recognize", lambda *_args: ("", False))
    _, metadata = extract_document(target, ocr=True)
    assert not metadata["complete"]  # Native header cannot conceal failed OCR.


def test_pdfium_operations_are_serialized_across_document_workers(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import pypdfium2 as pdfium
    target = tmp_path / "scan.pdf"
    target.write_bytes(scanned_workbook())
    original = pdfium.PdfDocument
    def guarded(*args, **kwargs):
        from app.document_text import _pdfium_lock
        assert _pdfium_lock._is_owned()
        return original(*args, **kwargs)
    monkeypatch.setattr(pdfium, "PdfDocument", guarded)
    monkeypatch.setattr("app.document_text._recognize", lambda *_args: ("识别出的导数练习和完整数学条件。" * 8, False))
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda _: extract_document(target, ocr=True), range(4)))
    assert all(metadata["complete"] for _, metadata in results)


@pytest.mark.parametrize("properties,bases,expected", [
    ('<m:begChr m:val="|"/><m:endChr m:val="|"/>', ["x"], "$|x|$"),
    ('<m:begChr m:val="["/><m:endChr m:val="]"/>', ["a,b"], "$[a,b]$"),
    ('<m:sepChr m:val=";"/>', ["a", "b", "c"], "$(a;b;c)$"),
    ('<m:begChr m:val="{"/><m:endChr m:val="}"/>', ["a,b"], r"$\{a,b\}$"),
])
def test_word_delimiters_preserve_all_bases(tmp_path, properties, bases, expected):
    import zipfile
    from app.document_text import WORD, MATH
    target = tmp_path / "delimiters.docx"
    content = "".join(f"<m:e><m:r><m:t>{base}</m:t></m:r></m:e>" for base in bases)
    xml = f'<w:document xmlns:w="{WORD}" xmlns:m="{MATH}"><w:body><w:p><m:oMath><m:d><m:dPr>{properties}</m:dPr>{content}</m:d></m:oMath></w:p></w:body></w:document>'
    with zipfile.ZipFile(target, "w") as package:
        package.writestr("word/document.xml", xml)
    text, metadata = extract_document(target)
    assert text == expected and metadata["complete"]


def test_unsupported_word_operator_is_visible_and_blocks_generation(tmp_path):
    import zipfile
    from app.document_text import WORD, MATH, MATH_UNCERTAIN
    from app.learning_quality import material_profile
    target = tmp_path / "unsupported.docx"
    xml = f'<w:document xmlns:w="{WORD}" xmlns:m="{MATH}"><w:body><w:p><w:r><w:t>{"需要保留原始公式和条件的正文。" * 15}</w:t></w:r><m:oMath><m:acc><m:e><m:r><m:t>x</m:t></m:r></m:e></m:acc></m:oMath></w:p></w:body></w:document>'
    with zipfile.ZipFile(target, "w") as package:
        package.writestr("word/document.xml", xml)
    text, metadata = extract_document(target)
    assert MATH_UNCERTAIN in text and not metadata["complete"] and metadata["warning"]
    assert not material_profile(text)["eligible"]


def test_word_barless_fraction_preserves_stack_instead_of_division(tmp_path):
    import zipfile
    from app.document_text import WORD, MATH
    target = tmp_path / "combination.docx"
    xml = f'<w:document xmlns:w="{WORD}" xmlns:m="{MATH}"><w:body><w:p><m:oMath><m:f><m:fPr><m:type m:val="noBar"/></m:fPr><m:num><m:r><m:t>5</m:t></m:r></m:num><m:den><m:r><m:t>2</m:t></m:r></m:den></m:f></m:oMath></w:p></w:body></w:document>'
    with zipfile.ZipFile(target, "w") as package:
        package.writestr("word/document.xml", xml)
    text, metadata = extract_document(target)
    assert text == r"$\genfrac{}{}{0pt}{}{5}{2}$" and metadata["complete"]


def test_import_snapshot_cannot_publish_completed_before_book_link(studio, monkeypatch):
    app, client, book = studio
    store = app.state.store
    monkeypatch.setattr(learning_imports, "extract_document", lambda *_args, **_kwargs: ("合成知识正文，可完整用于学习分析。" * 30, {"complete": True}))
    finished = wait_import(client, start(client, book["file_id"]).json()["job"])
    imported = finished["book_id"]
    with store.connect(write=True) as db:
        db.execute("UPDATE learning_imports SET book_id=NULL WHERE id=?", (finished["id"],))
        db.execute("UPDATE runs SET status='running' WHERE id=?", (finished["run_id"],))
    original = store.one
    advanced = False
    def concurrent_read(sql, args=()):
        nonlocal advanced
        row = original(sql, args)
        if not advanced and "learning_imports" in sql:
            advanced = True
            with store.connect(write=True) as db:
                db.execute("UPDATE learning_imports SET book_id=? WHERE id=?", (imported, finished["id"]))
                db.execute("UPDATE runs SET status='completed' WHERE id=?", (finished["run_id"],))
        return row
    monkeypatch.setattr(store, "one", concurrent_read)
    snapshot = learning_imports.snapshot(store, finished["id"])
    assert snapshot["status"] != "completed" or snapshot["book_id"] == imported
    assert learning_imports.snapshot(store, finished["id"])["book_id"] == imported
