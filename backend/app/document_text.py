"""Local, bounded extraction. Page coverage survives beyond the upload response."""
from __future__ import annotations

import asyncio
import threading
import zipfile
from pathlib import Path

from .store import clean_text

MAX_TEXT_CHARS = 6_000_000
MAX_PDF_PAGES = 1600
_ocr_lock = threading.Lock()
_ocr_engine = None
WORD = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MATH = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _math_text(node):
    """Keep common Word equations instead of silently dropping OMML objects."""
    from lxml import etree
    kind = etree.QName(node).localname
    def argument(name):
        child = node.find(f"{{{MATH}}}{name}")
        return _math_text(child) if child is not None else ""
    if kind == "t":
        return node.text or ""
    if kind in {"sSup", "sSub", "sSubSup"}:
        result = "{" + argument("e") + "}"
        if kind in {"sSub", "sSubSup"}: result += "_{" + argument("sub") + "}"
        if kind in {"sSup", "sSubSup"}: result += "^{" + argument("sup") + "}"
        return result
    if kind == "f": return r"\frac{" + argument("num") + "}{" + argument("den") + "}"
    if kind == "rad":
        degree = argument("deg")
        return r"\sqrt" + ("[" + degree + "]" if degree else "") + "{" + argument("e") + "}"
    if kind == "d": return "(" + argument("e") + ")"
    if kind.endswith("Pr"):
        return ""
    return "".join(_math_text(child) for child in node)


def _word_text(node):
    if node.tag == f"{{{MATH}}}oMath":
        return "$" + _math_text(node) + "$"
    if node.tag == f"{{{WORD}}}t": return node.text or ""
    if node.tag == f"{{{WORD}}}tab": return "\t"
    if node.tag in {f"{{{WORD}}}br", f"{{{WORD}}}cr"}: return "\n"
    return "".join(_word_text(child) for child in node)


def _check_cancel(cancelled):
    if cancelled and cancelled.is_set():
        raise asyncio.CancelledError()


def _recognize(image, cancelled):
    """One CPU OCR engine, bundled models; never download models at runtime."""
    global _ocr_engine
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    while not _ocr_lock.acquire(timeout=.1):
        _check_cancel(cancelled)
    try:
        _check_cancel(cancelled)
        if _ocr_engine is None:
            _ocr_engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
        result, _ = _ocr_engine(np.array(image.convert("RGB"))[:, :, ::-1])
        lines = result or []
        return "\n".join(line[1] for line in lines if line[2] >= .55), any(line[2] < .8 for line in lines)
    finally:
        _ocr_lock.release()


def extract_document(path: Path, *, suffix=None, ocr=False, cancelled=None, progress=None, cached_pages=None, page_sink=None):
    extension = suffix or path.suffix.lower()
    if extension == ".docx":
        from lxml import etree
        # Read document XML only; hundreds of MiB of embedded pictures need not
        # be inflated merely to identify exercises and equations.
        with zipfile.ZipFile(path) as package:
            info = package.getinfo("word/document.xml")
            if info.file_size > MAX_TEXT_CHARS * 6:
                raise ValueError("Word 正文过大，请分册导入；没有截断保存")
            document = etree.fromstring(package.read(info), parser=etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False))
        parts = []
        size = 0
        for block in document.iter(f"{{{WORD}}}p"):
            _check_cancel(cancelled)
            text = _word_text(block)
            size += len(text)
            if size > MAX_TEXT_CHARS:
                raise ValueError("正文超过 600 万字识别上限，请拆分资料；没有截断保存")
            parts.append(text)
        return clean_text("\n".join(parts)), {"complete": True, "method": "native", "warning": ""}
    if extension != ".pdf":
        # Read a bounded amount even for a 256 MiB plain-text file.
        with path.open("r", encoding="utf-8-sig", errors="replace") as stream:
            text = stream.read(MAX_TEXT_CHARS + 1)
        if len(text) > MAX_TEXT_CHARS:
            raise ValueError("正文超过 600 万字识别上限，请拆分资料；没有截断保存")
        return clean_text(text), {"complete": True, "method": "text", "warning": ""}

    from pypdf import PdfReader
    parts, missing, uncertain, methods = [], [], [], []
    resumed_pages = 0
    renderer = None
    try:
        # A seekable stream keeps the complete 256 MiB original off the heap.
        with path.open("rb") as stream:
            reader = PdfReader(stream)
            if reader.is_encrypted and not reader.decrypt(""):
                raise ValueError("PDF 已加密，请先使用自己的密码解锁后上传")
            total = len(reader.pages)
            if total > MAX_PDF_PAGES:
                raise ValueError(f"PDF 超过 {MAX_PDF_PAGES} 页，请分册导入；没有只读取前几页")
            size = 0
            for index, page in enumerate(reader.pages):
                _check_cancel(cancelled)
                text = clean_text(page.extract_text() or "")
                method = "native"
                if len("".join(text.split())) < 40:
                    cached = (cached_pages or {}).get(index + 1) if ocr else None
                    if cached:
                        text, method = cached["text"], "ocr"
                        resumed_pages += 1
                        if cached["uncertain"]:
                            uncertain.append(index + 1)
                    elif ocr:
                        if renderer is None:
                            import pypdfium2 as pdfium
                            renderer = pdfium.PdfDocument(path)
                        rendered_page = renderer[index]
                        bitmap = None
                        image = None
                        try:
                            width, height = rendered_page.get_size()
                            bitmap = rendered_page.render(scale=min(2.5, 2600 / max(width, height)))
                            image = bitmap.to_pil()
                            recognized, low_confidence = _recognize(image, cancelled)
                            if len(recognized.strip()) > len(text.strip()):
                                text, method = clean_text(recognized), "ocr"
                            if low_confidence:
                                uncertain.append(index + 1)
                            _check_cancel(cancelled)
                            if method == "ocr" and page_sink:
                                page_sink(index + 1, text, low_confidence)
                        finally:
                            if image is not None:
                                image.close()
                            if bitmap is not None:
                                bitmap.close()
                            rendered_page.close()
                    if len("".join(text.split())) < 40:
                        missing.append(index + 1)
                size += len(text)
                if size > MAX_TEXT_CHARS:
                    raise ValueError("正文超过 600 万字识别上限，请拆分资料；没有截断保存")
                parts.append(text)
                methods.append(method)
                if progress:
                    progress({"page": index + 1, "total": total, "method": method})
        warning = f"{len(missing)} / {total} 页文字不足（可能为空白、封面或扫描页）" if missing else ""
        if missing and not ocr:
            warning += "；加入学习时将进行本地 OCR 识别"
        if uncertain:
            warning += ("；" if warning else "") + f"{len(uncertain)} 页含低置信度 OCR 文字，请核对公式与图示"
        elif "ocr" in methods:
            warning += ("；" if warning else "") + "扫描文字已本地识别，请在出题前核对公式、单位与图示条件"
        spans, offset = [], 0
        for text in parts:
            spans.append([offset, offset + len(text)])
            offset += len(text) + 2
        return "\n\n".join(parts), {
            "complete": not missing, "pages": total, "native_pages": methods.count("native"),
            "ocr_pages": methods.count("ocr"), "missing_pages": missing, "uncertain_pages": uncertain,
            "warning": warning, "method": "ocr" if "ocr" in methods else "native",
            "page_spans": spans,
            "resumed_ocr_pages": resumed_pages,
        }
    finally:
        if renderer is not None:
            renderer.close()
