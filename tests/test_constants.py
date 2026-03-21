"""Verify that the digit strings in src/ts/constants.ts are correct."""

import re
import unittest
from pathlib import Path

from mpmath import mp, pi, e, phi, sqrt, euler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONSTANTS_TS = PROJECT_ROOT / "src" / "ts" / "constants.ts"


def _parse_constants():
    """Extract {symbol: digits} from constants.ts."""
    text = CONSTANTS_TS.read_text()
    entries = re.findall(
        r"symbol:\s*'([^']+)'.*?digits:\s*'(\d+)'", text, re.DOTALL
    )
    return {symbol: digits for symbol, digits in entries}


def _to_digits(value, count):
    """Get the first `count` digits of a constant (no decimal point)."""
    s = mp.nstr(value, count + 1, strip_zeros=False)
    return s.replace(".", "")[:count]


PARSED = _parse_constants()

MATH_CONSTANTS = [
    ("π", lambda: pi),
    ("e", lambda: e),
    ("φ", lambda: phi),
    ("√2", lambda: sqrt(2)),
    ("τ", lambda: 2 * pi),
    ("√3", lambda: sqrt(3)),
    ("γ", lambda: euler),
]

PHYSICS_CONSTANTS = [
    ("c", "299792458"),
    ("G", "66743"),
    ("Nₐ", "602214076"),
]


class ConstantDigitsTest(unittest.TestCase):
    def test_math_constants(self):
        for symbol, compute in MATH_CONSTANTS:
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, PARSED, f"Missing constant {symbol}")
                stored = PARSED[symbol]
                mp.dps = len(stored) + 50
                expected = _to_digits(compute(), len(stored))
                self.assertEqual(stored, expected, f"{symbol}: digit mismatch")

    def test_physics_constants(self):
        for symbol, expected in PHYSICS_CONSTANTS:
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, PARSED, f"Missing constant {symbol}")
                self.assertEqual(PARSED[symbol], expected)
