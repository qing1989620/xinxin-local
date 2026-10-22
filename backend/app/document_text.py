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
# PDFium is process-wide and not thread safe, even for separate documents.
# Keep every handle operation (including close) under this mutex; OCR uses a
# copied PIL image so expensive recognition does not hold the renderer lock.
_pdfium_lock = threading.RLock()
_ocr_engine = None
MATH_UNCERTAIN = "〔公式待校对〕"
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
    if kind == "d":
        def delimiter(name, default):
            value = node.find(f"{{{MATH}}}dPr/{{{MATH}}}{name}")
            return value.get(f"{{{MATH}}}val", default) if value is not None else default
        # A delimiter can have several bases, e.g. (a|b), not just the first e.
        return delimiter("begChr", "(") + delimiter("sepChr", "|").join(
            _math_text(child) for child in node.findall(f"{{{MATH}}}e")
        ) + delimiter("endChr", ")")
    if kind == "func": return argument("fName") + "{" + argument("e") + "}"
    if kind in {"limLow", "limUpp"}:
        return "{" + argument("e") + "}" + ("_" if kind == "limLow" else "^") + "{" + argument("lim") + "}"
    if kind.endswith("Pr"):
        return ""
    children = "".join(_math_text(child) for child in node)
    if kind in {"oMath", "r", "e", "num", "den", "deg", "sub", "sup", "fName", "lim"}:
        return children
    # Unknown constructs may encode essential operators (integral, matrix,
    # accent, cases...). Do not silently flatten them into a different formula.
    return MATH_UNCERTAIN + children


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


def _large_raster(page):
    """Measure placed images, including Form XObjects, rather than file bytes.

    Called only while holding _pdfium_lock. A large illustration may also
    trigger OCR; that is preferable to treating a scan's header as its body.
    """
    import pypdfium2 as pdfium
    left, bottom, right, top = page.get_bbox()
    area = max(1, (right - left) * (top - bottom))
    image_area = 0
    for image in page.get_objects(filter=[pdfium.raw.FPDF_PAGEOBJ_IMAGE], max_depth=15):
        bounds = image.get_bounds()
        container = image.container
        while container is not None:
            bounds = container.get_matrix().on_rect(*bounds)
            container = container.container
        x0, y0, x1, y1 = bounds
        image_area += max(0, min(right, x1) - max(left, x0)) * max(0, min(top, y1) - max(bottom, y0))
    return image_area / area >= .45


def _merge_ocr(native, recognized):
    recognized = clean_text(recognized)
    compact = "".join(recognized.split())
    retained = [line for line in native.splitlines() if line.strip() and "".join(line.split()) not in compact]
    return "\n".join([recognized, *retained]).strip()


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
        text = clean_text("\n".join(parts))
        uncertain = MATH_UNCERTAIN in text
        return text, {"complete": not uncertain, "method": "native",
                      "warning": "包含尚不支持的 Word 公式，请校对标记处；这些片段已暂停出题" if uncertain else ""}
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
                needs_ocr = len("".join(text.split())) < 40
                # Some workbooks have a native header/watermark over a scanned
                # body. Native character count alone cannot establish coverage.
                resources = page.get("/Resources")
                has_objects = bool(resources and resources.get_object().get("/XObject"))
                image = None
                if needs_ocr or has_objects:
                    with _pdfium_lock:
                        import pypdfium2 as pdfium
                        if renderer is None:
                            renderer = pdfium.PdfDocument(path)
                        rendered_page = renderer[index]
                        bitmap = None
                        try:
                            needs_ocr = needs_ocr or _large_raster(rendered_page)
                            cached = (cached_pages or {}).get(index + 1) if ocr else None
                            if needs_ocr and ocr and not cached:
                                width, height = rendered_page.get_size()
                                bitmap = rendered_page.render(scale=min(2.5, 2600 / max(width, height)))
                                image = bitmap.to_pil().copy()
                        finally:
                            if bitmap is not None:
                                bitmap.close()
                            rendered_page.close()
                if needs_ocr:
                    cached = (cached_pages or {}).get(index + 1) if ocr else None
                    recognized = ""
                    if cached:
                        recognized, method = cached["text"], "ocr"
                        text = _merge_ocr(text, recognized)
                        resumed_pages += 1
                        if cached["uncertain"]:
                            uncertain.append(index + 1)
                    elif ocr:
                        try:
                            recognized, low_confidence = _recognize(image, cancelled)
                            if recognized.strip():
                                text, method = _merge_ocr(text, recognized), "ocr"
                            if low_confidence:
                                uncertain.append(index + 1)
                            _check_cancel(cancelled)
                            if method == "ocr" and page_sink:
                                page_sink(index + 1, clean_text(recognized), low_confidence)
                        finally:
                            if image is not None:
                                image.close()
                    if not ocr or len("".join(recognized.split())) < 40:
                        missing.append(index + 1)
                size += len(text)
                if size > MAX_TEXT_CHARS:
                    raise ValueError("正文超过 600 万字识别上限，请拆分资料；没有截断保存")
                parts.append(text)
                methods.append(method)
                if progress:
                    progress({"page": index + 1, "total": total, "method": method})
        warning = f"{len(missing)} / {total} 页正文未完整识别（可能为空白、封面或含扫描图片）" if missing else ""
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
            with _pdfium_lock:
                renderer.close()
