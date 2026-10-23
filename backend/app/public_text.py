"""Publish response text without exposing credentials split across model deltas."""
import json
import re


_ASSIGNMENT = r"(?i)(api[_-]?key|password|secret|authorization|token)([\s:=]+)"
_BEARER = r"(?i)\bBearer\s+"
_SECRET_FIELDS = {"apikey", "password", "secret", "authorization", "token",
                  "privatekey", "modelapikey", "smtppassword"}


def _secret_field(label):
    try:
        name = json.loads(label)
    except ValueError:
        return False
    return name.lower().replace("_", "").replace("-", "") in _SECRET_FIELDS


def credential_fields(text):
    """Locate complete or unfinished JSON credential values, including escapes."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r'"(?:\\.|[^"\\])*"\s*:\s*', text):
        if not _secret_field(match.group().rsplit(":", 1)[0].strip()):
            continue
        try:
            _, size = decoder.raw_decode(text[match.end():])
            end = match.end() + size
        except ValueError:
            end = len(text)
        yield match.start(), match.end(), end


def redact_text(text, forms=(), limit=None):
    """Merge sensitive spans in the original text before replacing any bytes.

    Replacing a label can hide another credential; replacing part of a known
    multi-word value can expose its suffix. Neither rule may change the input
    seen by the other rules. The outermost span keeps its output representation.
    """
    spans = [(start, end, '"[redacted]"')
             for _, start, end in credential_fields(text)]
    for match in re.finditer(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)",
        text, flags=re.S,
    ):
        spans.append((match.start(), match.end(), "[redacted private key]"))
    for match in re.finditer(_BEARER + r"[^\s,;]+", text):
        spans.append((match.start(), match.end(), "[redacted]"))
    for match in re.finditer(_ASSIGNMENT + r"([^\s,;]+)", text):
        spans.append((match.start(3), match.end(3), "[redacted]"))
    for form in forms:
        if form:
            spans.extend((match.start(), match.end(), "[redacted]")
                         for match in re.finditer(re.escape(form), text))
    spans.extend((match.start(), match.end(), "[redacted]")
                 for match in re.finditer(r"sk-[A-Za-z0-9_-]{12,}", text))
    merged = []
    for start, end, replacement in sorted(spans, key=lambda span: (span[0], -span[1])):
        if merged and start < merged[-1][1]:
            previous = merged[-1]
            merged[-1] = (previous[0], max(end, previous[1]), previous[2])
        else:
            merged.append((start, end, replacement))
    parts, cursor = [], 0
    for start, end, replacement in merged:
        parts.extend((text[cursor:start], replacement))
        cursor = end
    result = "".join((*parts, text[cursor:]))
    return result if limit is None else result[:limit]


class PublicText:
    def __init__(self, redact, forms):
        self.redact = redact
        # Keep the original credentials even if settings rotate during a request.
        self.forms = sorted(set(forms), key=len, reverse=True)
        self.pending = ""

    def sanitize(self, value, limit=None):
        # Preserve the original field names until semantic redaction finishes.
        return self.redact(value, limit=limit, known_forms=self.forms)

    def feed(self, delta):
        self.pending += delta
        # ASCII tokens remain pending until a delimiter arrives. CJK text can
        # stream immediately; known Unicode credentials are held below too.
        token = re.search(r"[\x21-\x7e]+$", self.pending)
        cut = token.start() if token else len(self.pending)
        for form in self.forms:
            start = self.pending.find(form)
            while start >= 0:
                if start < cut < start + len(form):
                    cut = start
                start = self.pending.find(form, start + 1)
            # Do not publish a prefix of a known multi-word/escaped credential.
            for start in range(max(0, len(self.pending) - len(form) + 1), cut):
                if form.startswith(self.pending[start:]):
                    cut = start
                    break
        for pattern in (_ASSIGNMENT + r"[^\s,;]+", _ASSIGNMENT + r"$",
                        _BEARER + r"[^\s,;]+", _BEARER + r"$"):
            for match in re.finditer(pattern, self.pending):
                if match.start() < cut <= match.end():
                    cut = match.start()
        for start, _, end in credential_fields(self.pending):
            if start < cut <= end:
                cut = start
        for match in re.finditer(r'("(?:\\.|[^"\\])*")\s*$', self.pending):
            if _secret_field(match.group(1)):
                cut = min(cut, match.start())
        # A PEM block can contain arbitrary whitespace. Keep it as a unit so
        # that the existing redactor sees its header and body together.
        for match in re.finditer("-----BEGIN", self.pending):
            start = match.start()
            end = re.search(r"-----END [A-Z ]+-----", self.pending[start:])
            if end is None or cut < start + end.end():
                cut = min(cut, start)
        if not cut:
            return ""
        value, self.pending = self.pending[:cut], self.pending[cut:]
        return self.sanitize(value)

    def finish(self):
        value, self.pending = self.pending, ""
        return self.sanitize(value)
