"""Unit tests verifying dark theme is dark and light theme is light.

Parses CSS custom properties from src/scss/_variables.scss and checks
luminance to ensure backgrounds and text colors match their theme.

Run:
    python -m pytest test_theme.py
    python -m unittest test_theme
"""

import re
import unittest
from pathlib import Path

CSS_PATH = Path(__file__).resolve().parent.parent / "src" / "scss" / "_variables.scss"

# Variable classifications
BG_VARS = {"--bg-page", "--bg-surface", "--bg-nav-hover", "--bg-success", "--bg-error", "--bg-stripe",
           "--bg-mastery-0", "--bg-mastery-1", "--bg-mastery-3", "--bg-mastery-4"}
TEXT_VARS = {"--text-primary", "--text-secondary", "--text-muted"}
FG_ACCENT_VARS = {"--color-primary", "--color-primary-hover", "--color-success", "--color-error",
                  "--color-mastery-0", "--color-mastery-1", "--color-mastery-3", "--color-mastery-4"}
# Colors used on top of --color-primary backgrounds (not page backgrounds)
ON_PRIMARY_VARS = {"--color-on-primary"}
NON_COLOR_VARS = {"--shadow-hover", "--border-color", "--border-input",
                  "--color-skip", "--color-skip-hover"}
ALL_CLASSIFIED = BG_VARS | TEXT_VARS | FG_ACCENT_VARS | ON_PRIMARY_VARS | NON_COLOR_VARS

DARK_BG_MAX_LUM = 0.15
DARK_TEXT_MIN_LUM = 0.18
LIGHT_BG_MIN_LUM = 0.55
LIGHT_TEXT_MAX_LUM = 0.25


def parse_hex(color: str) -> tuple[int, int, int] | None:
    color = color.strip().lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    if len(color) in (6, 8):
        return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    return None


def parse_rgba(color: str) -> tuple[int, int, int] | None:
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", color)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None


def relative_luminance(r: int, g: int, b: int) -> float:
    def linearize(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def extract_css_vars(css: str, selector: str) -> dict[str, str]:
    """Find a CSS block whose selector list contains `selector`."""
    # Match any rule block, then check if selector appears in its selector list
    for m in re.finditer(r"([^{}]+)\{([^}]+)\}", css):
        selectors = m.group(1)
        if selector in selectors:
            variables = {}
            for line in m.group(2).split(";"):
                line = line.strip()
                if line.startswith("--"):
                    name, _, value = line.partition(":")
                    variables[name.strip()] = value.strip()
            if variables:
                return variables
    return {}


def get_rgb(variables: dict, var: str) -> tuple[int, int, int]:
    value = variables[var]
    rgb = parse_hex(value) or parse_rgba(value)
    assert rgb is not None, f"Cannot parse {var}: {value}"
    return rgb


class TestDarkTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        css = CSS_PATH.read_text()
        cls.vars = extract_css_vars(css, ":root")
        assert cls.vars, ":root block has no variables"

    def test_backgrounds_are_dark(self):
        for var in BG_VARS:
            with self.subTest(var=var):
                r, g, b = get_rgb(self.vars, var)
                lum = relative_luminance(r, g, b)
                self.assertLess(lum, DARK_BG_MAX_LUM,
                    f"{var}={self.vars[var]} luminance {lum:.3f} too bright for dark theme")

    def test_text_is_light(self):
        for var in TEXT_VARS:
            with self.subTest(var=var):
                r, g, b = get_rgb(self.vars, var)
                lum = relative_luminance(r, g, b)
                self.assertGreater(lum, DARK_TEXT_MIN_LUM,
                    f"{var}={self.vars[var]} luminance {lum:.3f} too dim for dark theme text")

    def test_accents_readable_on_dark(self):
        for var in FG_ACCENT_VARS:
            with self.subTest(var=var):
                r, g, b = get_rgb(self.vars, var)
                lum = relative_luminance(r, g, b)
                self.assertGreater(lum, DARK_TEXT_MIN_LUM,
                    f"{var}={self.vars[var]} luminance {lum:.3f} not readable on dark backgrounds")

    def test_on_primary_contrasts_primary(self):
        """--color-on-primary must contrast well against --color-primary."""
        fg = get_rgb(self.vars, "--color-on-primary")
        bg = get_rgb(self.vars, "--color-primary")
        fg_lum = relative_luminance(*fg)
        bg_lum = relative_luminance(*bg)
        ratio = (max(fg_lum, bg_lum) + 0.05) / (min(fg_lum, bg_lum) + 0.05)
        self.assertGreater(ratio, 3.0,
            f"--color-on-primary vs --color-primary contrast ratio {ratio:.1f} < 3.0")


class TestLightTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        css = CSS_PATH.read_text()
        cls.vars = extract_css_vars(css, '[data-theme="light"]')
        assert cls.vars, '[data-theme="light"] block has no variables'

    def test_backgrounds_are_light(self):
        for var in BG_VARS:
            with self.subTest(var=var):
                r, g, b = get_rgb(self.vars, var)
                lum = relative_luminance(r, g, b)
                self.assertGreater(lum, LIGHT_BG_MIN_LUM,
                    f"{var}={self.vars[var]} luminance {lum:.3f} too dark for light theme")

    def test_text_is_dark(self):
        for var in TEXT_VARS:
            with self.subTest(var=var):
                r, g, b = get_rgb(self.vars, var)
                lum = relative_luminance(r, g, b)
                self.assertLess(lum, LIGHT_TEXT_MAX_LUM,
                    f"{var}={self.vars[var]} luminance {lum:.3f} too bright for light theme text")

    def test_accents_readable_on_light(self):
        for var in FG_ACCENT_VARS:
            with self.subTest(var=var):
                r, g, b = get_rgb(self.vars, var)
                lum = relative_luminance(r, g, b)
                self.assertLess(lum, 0.35,
                    f"{var}={self.vars[var]} luminance {lum:.3f} not readable on light backgrounds")

    def test_on_primary_contrasts_primary(self):
        fg = get_rgb(self.vars, "--color-on-primary")
        bg = get_rgb(self.vars, "--color-primary")
        fg_lum = relative_luminance(*fg)
        bg_lum = relative_luminance(*bg)
        ratio = (max(fg_lum, bg_lum) + 0.05) / (min(fg_lum, bg_lum) + 0.05)
        self.assertGreater(ratio, 3.0,
            f"--color-on-primary vs --color-primary contrast ratio {ratio:.1f} < 3.0")


class TestThemeCompleteness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        css = CSS_PATH.read_text()
        cls.dark_vars = extract_css_vars(css, ":root")
        cls.light_vars = extract_css_vars(css, '[data-theme="light"]')

    def test_light_theme_covers_all_dark_vars(self):
        """Every variable in dark theme must have a light theme override."""
        for var in self.dark_vars:
            with self.subTest(var=var):
                self.assertIn(var, self.light_vars,
                    f"{var} defined in dark theme but missing from light theme")

    def test_all_vars_classified(self):
        """Every CSS variable should belong to a test category."""
        for var in self.dark_vars:
            with self.subTest(var=var):
                self.assertIn(var, ALL_CLASSIFIED,
                    f"{var} is unclassified — add it to a test category")


if __name__ == "__main__":
    unittest.main()
