"""Conservative local grading: typography may vary, mathematical meaning may not."""
from __future__ import annotations

import json
import re
from fractions import Fraction

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?"
DECIMAL = re.compile(NUMBER)
FRACTION = re.compile(rf"({NUMBER})\s*/\s*({NUMBER})")
LATEX_FRACTION = re.compile(
    rf"([+-]?)\s*\\(?:d|t)?frac\s*(?:\{{\s*({NUMBER})\s*\}}|([0-9]))"
    rf"\s*(?:\{{\s*({NUMBER})\s*\}}|([0-9]))"
)


def unwrapped(value):
    text = str(value).strip()
    for left, right in (("$$", "$$"), (r"\(", r"\)"), (r"\[", r"\]"), ("$", "$")):
        if text.startswith(left) and text.endswith(right) and len(text) > len(left) + len(right):
            return text[len(left):-len(right)].strip()
    return text


def number(value):
    text = unwrapped(value).replace("−", "-")
    if len(text) > 200:
        return None
    percent = text.endswith("%")
    if percent:
        text = text[:-1].strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()
    # Bound exponent and literal size before Fraction allocates powers of ten.
    if any(abs(int(exponent)) > 100 for exponent in re.findall(r"[eE]([+-]?\d+)", text)):
        return None
    try:
        if DECIMAL.fullmatch(text):
            result = Fraction(text)
        elif match := FRACTION.fullmatch(text):
            result = Fraction(match[1]) / Fraction(match[2])
        elif match := LATEX_FRACTION.fullmatch(text):
            # TeX consumes one digit per unbraced argument: \frac12 is 1/2,
            # while \frac123 has an extra token and must not become 12/3.
            result = Fraction(match[2] or match[3]) / Fraction(match[4] or match[5])
            if match[1] == "-":
                result = -result
        else:
            return None
        return result / 100 if percent else result
    except (ValueError, ZeroDivisionError, OverflowError):
        return None


def equivalent(expected, given):
    left, right = unwrapped(expected), unwrapped(given)
    if left == right:
        return True
    first, second = number(left), number(right)
    return first is not None and second is not None and first == second


def expected_blanks(value):
    try:
        result = json.loads(value)
    except (ValueError, TypeError):
        return [str(value)]
    return result if isinstance(result, list) and all(isinstance(item, str) for item in result) else [str(value)]


def given_blanks(value, count):
    # New clients submit arrays separately. This is only legacy text support.
    # A single interval, tuple or code string can contain commas and semicolons.
    if count == 1:
        return [value]
    separator = r"[;；|]" if re.search(r"[;；|]", value) else r"[,，、]"
    return re.split(separator, value)


def check_fill(expected, given, answers=None):
    blanks = expected_blanks(expected)
    parts = answers if answers is not None else given_blanks(given, len(blanks))
    return bool(blanks) and len(parts) == len(blanks) and all(
        isinstance(right, str) and right.strip() and equivalent(left, right)
        for left, right in zip(blanks, parts)
    )


def check_choice(expected, given):
    answer = given.strip().upper()
    return answer in {"A", "B", "C", "D"} and expected.strip().upper() == answer
