"""Streaming boundaries use synthetic credentials and no external services."""
import json

import pytest

from app.public_text import PublicText, redact_text


def redact(value, limit=None, *, known_forms=()):
    return redact_text(value, known_forms, limit)


@pytest.mark.parametrize("label", ["password", "token", "Bearer", '"password"'])
def test_overlapping_hold_ranges_never_split_a_known_credential(label):
    known = "syntheticAlpha " + label
    text = known + (" syntheticBeta" if label == "Bearer" else ": syntheticBeta")
    if label.startswith('"'):
        text = known + ': "syntheticBeta"'
    for first in range(len(text) + 1):
        for second in range(first, len(text) + 1):
            stream = PublicText(redact, [known])
            public = (stream.feed(text[:first]) + stream.feed(text[first:second])
                      + stream.feed(text[second:]) + stream.finish())
            assert "syntheticAlpha" not in public, (first, second, public)
            assert "syntheticBeta" not in public, (first, second, public)


@pytest.mark.parametrize("ascii_json", [False, True])
@pytest.mark.parametrize("value, expected", [
    ("Bearer syntheticAlpha", "[redacted]"),
    ("password: syntheticAlpha", "password: [redacted]"),
    ('Bearer synthetic\\"Alpha', "[redacted]"),
    ('password: synthetic\\"Alpha', "password: [redacted]"),
    ("中文 Bearer syntheticAlpha", "中文 [redacted]"),
    ("前缀\nBearer syntheticAlpha", "前缀\n[redacted]"),
    ("前缀\tpassword: syntheticAlpha", "前缀\tpassword: [redacted]"),
])
def test_streaming_json_values_keep_their_structure_and_escapes(value, expected, ascii_json):
    text = json.dumps({"output": value, "safe": "Done."}, ensure_ascii=ascii_json)
    for first in range(len(text) + 1):
        for second in range(first, len(text) + 1):
            stream = PublicText(redact, [])
            public = (stream.feed(text[:first]) + stream.feed(text[first:second])
                      + stream.feed(text[second:]) + stream.finish())
            assert json.loads(public) == {"output": expected, "safe": "Done."}, (first, second, public)


def test_current_credentials_join_the_snapshot_before_any_delta_is_published():
    current = ["syntheticOld credential"]
    stream = PublicText(redact, lambda: current)
    current[:] = ["syntheticAlpha syntheticBeta"]
    public = stream.feed("syntheticAlpha ")
    assert public == ""
    public += stream.feed("syntheticBeta ")
    current[:] = ["syntheticNew credential"]
    public += stream.feed("syntheticOld credential; syntheticAlpha syntheticBeta.")
    public += stream.finish()
    assert not any(word in public for word in ("syntheticOld", "syntheticAlpha", "syntheticBeta"))


@pytest.mark.parametrize("text", [
    '{"output":"prefix\\nBearer syntheticAlpha',
    '{"output":"Bearer\\u0020syntheticAlpha',
    '{"output":"中文\\tpassword: syntheticAlpha',
    '{"output":"Bearer syntheticAlpha\\',
])
def test_unfinished_quoted_tails_are_not_released_at_completion(text):
    assert "syntheticAlpha" not in redact(text)
    for split in range(len(text) + 1):
        stream = PublicText(redact, [])
        public = stream.feed(text[:split]) + stream.feed(text[split:]) + stream.finish()
        assert "syntheticAlpha" not in public, (split, public)


@pytest.mark.parametrize("shape", ["valid", "invalid", "unfinished"])
@pytest.mark.parametrize("value, private", [
    ("prefix\nBearer syntheticAlpha", "syntheticAlpha"),
    ("prefix\tpassword: syntheticAlpha", "syntheticAlpha"),
    ("prefix\nsk-syntheticPrivateValue123", "sk-syntheticPrivateValue123"),
    ("prefix\n-----BEGIN PRIVATE KEY-----\nSYNTHETIC_PRIVATE_BODY\n-----END PRIVATE KEY-----", "SYNTHETIC_PRIVATE_BODY"),
])
def test_each_quoted_state_still_applies_credential_rules(shape, value, private):
    text = '"' + value + '"' if shape == "invalid" else json.dumps(value)
    if shape == "unfinished":
        text = text[:-1]
    assert private not in redact(text)
    for first in range(len(text) + 1):
        for second in range(first, len(text) + 1):
            stream = PublicText(redact, [])
            public = (stream.feed(text[:first]) + stream.feed(text[first:second])
                      + stream.feed(text[second:]) + stream.finish())
            assert private not in public, (shape, first, second, public)


def test_plain_quoted_windows_paths_do_not_require_json_escaping():
    text = r'Open "C:\Users\synthetic\book.pdf" next.'
    for split in range(len(text) + 1):
        stream = PublicText(redact, [])
        assert stream.feed(text[:split]) + stream.feed(text[split:]) + stream.finish() == text
