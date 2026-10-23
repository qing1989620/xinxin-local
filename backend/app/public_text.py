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


def quoted_strings(text):
    """Yield quoted units, including an unfinished string or escape at the end."""
    cursor = 0
    while (start := text.find('"', cursor)) >= 0:
        end = start + 1
        complete = False
        while end < len(text):
            if text[end] == "\\":
                end += 2
            elif text[end] == '"':
                end += 1
                complete = True
                break
            else:
                end += 1
        end = min(end, len(text))
        yield start, end, complete
        cursor = end


def redact_text(text, forms=(), limit=None):
    """Merge sensitive spans in the original text before replacing any bytes.

    Replacing a label can hide another credential; replacing part of a known
    multi-word value can expose its suffix. Neither rule may change the input
    seen by the other rules. The outermost span keeps its output representation.
    """
    spans = [(start, end, '"[redacted]"')
             for _, start, end in credential_fields(text)]
    units = list(quoted_strings(text))
    # A cancelled/truncated response cannot supply enough JSON context to
    # decode its final value. Never release that undecodable private tail.
    spans.extend((start, end, '"[redacted]"')
                 for start, end, complete in units if not complete)
    quotes = [(start, end) for start, end, complete in units if complete]
    for start, end in quotes:
        try:
            decoded = json.loads(text[start:end])
        except ValueError:
            continue
        # JSON escaping can hide whitespace and word boundaries from a regex.
        # Decode a complete string first, then encode its cleaned value once.
        cleaned = redact_text(decoded, forms)
        if cleaned != decoded:
            spans.append((start, end, json.dumps(cleaned, ensure_ascii=False)))

    def in_string(position):
        return any(start < position < end for start, end in quotes)

    for match in re.finditer(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)",
        text, flags=re.S,
    ):
        if not in_string(match.start()):
            spans.append((match.start(), match.end(), "[redacted private key]"))
    for pattern, group in ((_BEARER + r"[^\s,;]+", 0),
                           (_ASSIGNMENT + r"([^\s,;]+)", 3)):
        for match in re.finditer(pattern, text):
            if not in_string(match.start()):
                spans.append((match.start(group), match.end(group), "[redacted]"))
    for form in forms:
        if form:
            spans.extend((match.start(), match.end(), "[redacted]")
                         for match in re.finditer(re.escape(form), text))
    spans.extend((match.start(), match.end(), "[redacted]")
                 for match in re.finditer(r"sk-[A-Za-z0-9_-]{12,}", text)
                 if not in_string(match.start()))
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
        self.current_forms = forms if callable(forms) else None
        self.forms = [] if self.current_forms else list(forms)
        self._refresh_forms()
        self.pending = ""

    def _refresh_forms(self):
        # Accumulate both initial and later credentials during a long task.
        current = self.current_forms() if self.current_forms else ()
        self.forms = sorted(set(self.forms) | set(current), key=len, reverse=True)

    def sanitize(self, value, limit=None):
        self._refresh_forms()
        # Preserve the original field names until semantic redaction finishes.
        return self.redact(value, limit=limit, known_forms=self.forms)

    def feed(self, delta):
        self._refresh_forms()
        self.pending += delta
        # ASCII tokens remain pending until a delimiter arrives. CJK text can
        # stream immediately; known Unicode credentials are held below too.
        token = re.search(r"[\x21-\x7e]+$", self.pending)
        cut = token.start() if token else len(self.pending)
        holds = []
        for form in self.forms:
            start = self.pending.find(form)
            while start >= 0:
                holds.append((start, start + len(form)))
                start = self.pending.find(form, start + 1)
            # Do not publish a prefix of a known multi-word/escaped credential.
            for start in range(max(0, len(self.pending) - len(form) + 1), len(self.pending)):
                if form.startswith(self.pending[start:]):
                    holds.append((start, len(self.pending) + 1))
                    break
        for pattern in (_ASSIGNMENT + r"[^\s,;]+", _ASSIGNMENT + r"$",
                        _BEARER + r"[^\s,;]+", _BEARER + r"$"):
            for match in re.finditer(pattern, self.pending):
                holds.append((match.start(), match.end() + 1))
        for start, _, end in credential_fields(self.pending):
            holds.append((start, end + 1))
        # Keep every quoted value intact, including non-secret JSON envelopes.
        # Otherwise the next fragment loses the context of escaped characters.
        holds.extend((start, end if complete else end + 1)
                     for start, end, complete in quoted_strings(self.pending))
        for match in re.finditer(r'("(?:\\.|[^"\\])*")\s*$', self.pending):
            if _secret_field(match.group(1)):
                holds.append((match.start(), len(self.pending) + 1))
        # A PEM block can contain arbitrary whitespace. Keep it as a unit so
        # that the existing redactor sees its header and body together.
        for match in re.finditer("-----BEGIN", self.pending):
            start = match.start()
            end = re.search(r"-----END [A-Z ]+-----", self.pending[start:])
            holds.append((start, len(self.pending) + 1 if end is None else start + end.end()))
        # All rules observe the same original buffer. A later rule can move the
        # boundary into an earlier interval, so converge rather than use order.
        while True:
            earlier = min((start for start, end in holds if start < cut < end), default=cut)
            if earlier == cut:
                break
            cut = earlier
        if not cut:
            return ""
        value, self.pending = self.pending[:cut], self.pending[cut:]
        return self.sanitize(value)

    def finish(self):
        value, self.pending = self.pending, ""
        return self.sanitize(value)
