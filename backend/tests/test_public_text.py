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


@pytest.mark.parametrize("value", [
    "Bearer syntheticAlpha", "password: syntheticAlpha",
    'Bearer synthetic\\"Alpha', 'password: synthetic\\"Alpha',
])
def test_streaming_json_values_keep_their_structure_and_escapes(value):
    text = json.dumps({"output": value, "safe": "Done."})
    for first in range(len(text) + 1):
        for second in range(first, len(text) + 1):
            stream = PublicText(redact, [])
            public = (stream.feed(text[:first]) + stream.feed(text[first:second])
                      + stream.feed(text[second:]) + stream.finish())
            assert json.loads(public) == {"output": "[redacted]" if value.startswith("Bearer") else "password: [redacted]", "safe": "Done."}, (first, second, public)


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
