"""Verify that the digit strings in src/ts/constants.ts are correct."""

import re
from pathlib import Path

import pytest
from mpmath import mp, pi, e, phi, sqrt, euler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONSTANTS_TS = PROJECT_ROOT / "src" / "ts" / "constants.ts"


def _parse_constants():
    """Extract {key: digits} from constants.ts."""
    text = CONSTANTS_TS.read_text()
    entries = re.findall(
        r"symbol:\s*'([^']+)'.*?digits:\s*'(\d+)'", text, re.DOTALL
    )
    return {symbol: digits for symbol, digits in entries}


PARSED = _parse_constants()


def _to_digits(value, count):
    """Get the first `count` digits of a constant (no decimal point)."""
    s = mp.nstr(value, count + 1, strip_zeros=False)
    return s.replace(".", "")[:count]


@pytest.mark.parametrize(
    "symbol,compute",
    [
        ("π", lambda: pi),
        ("e", lambda: e),
        ("φ", lambda: phi),
        ("√2", lambda: sqrt(2)),
        ("τ", lambda: 2 * pi),
        ("√3", lambda: sqrt(3)),
        ("γ", lambda: euler),
    ],
)
def test_math_constant_digits(symbol, compute):
    assert symbol in PARSED, f"Missing constant {symbol}"
    stored = PARSED[symbol]
    mp.dps = len(stored) + 50
    expected = _to_digits(compute(), len(stored))
    assert stored == expected, (
        f"{symbol}: mismatch at position "
        f"{next(i for i, (a, b) in enumerate(zip(stored, expected)) if a != b)}"
    )


@pytest.mark.parametrize(
    "symbol,expected",
    [
        ("c", "299792458"),
        ("G", "66743"),
        ("Nₐ", "602214076"),
    ],
)
def test_physics_constants(symbol, expected):
    assert symbol in PARSED, f"Missing constant {symbol}"
    assert PARSED[symbol] == expected
