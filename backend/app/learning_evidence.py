"""Resolve model-selected positions to verbatim server-owned evidence."""
from __future__ import annotations

import re

from .store import clean_text

REFERENCE = re.compile(r"L0*([1-9]\d*)(?:\s*[-–:]\s*L?0*([1-9]\d*))?", re.I)


def _lines(content):
    # Long PDF/text paragraphs must still offer selectable evidence below the
    # knowledge-point limit. Keep every character, including original line ends,
    # so adjacent references join verbatim and page offsets stay exact.
    return [line[offset:offset + 400] for line in content.splitlines(keepends=True)
            for offset in range(0, len(line), 400)]


def numbered_text(content):
    return "\n".join(f"L{index}: " + line.rstrip("\r\n") for index, line in enumerate(_lines(content), 1))


def resolve(content, reference, *, maximum=4000):
    if not isinstance(reference, str) or not (match := REFERENCE.fullmatch(reference.strip())):
        raise ValueError("来源编号格式无效，需使用 L起始行-L结束行")
    start, end = int(match[1]), int(match[2] or match[1])
    lines = _lines(content)
    if not 1 <= start <= end <= len(lines) or end - start >= 100:
        raise ValueError("来源编号超出当前材料范围")
    quote = clean_text("".join(lines[start - 1:end])).strip()
    if not 8 <= len(quote) <= maximum:
        raise ValueError("来源证据过短或过长，请缩小到完整知识点或原题")
    return {"source_ref": f"L{start}-L{end}", "quote": quote}


def line_pages(content, reference, spans):
    """Page spans describe the exact effective text, never guessed printed pages."""
    resolved = resolve(content, reference)
    match = REFERENCE.fullmatch(resolved["source_ref"])
    lines = _lines(content)
    start = sum(map(len, lines[:int(match[1]) - 1]))
    end = sum(map(len, lines[:int(match[2])]))
    return [span["page"] for span in spans if span["start"] < end and span["end"] > start]
