"""Unit tests verifying ARIA attributes are present in templates/index.html.

Parses the HTML template and checks that accessibility attributes exist
on navigation, feedback, input, and status elements.

Run:
    python -m pytest tests/test_aria.py
"""

import unittest
from html.parser import HTMLParser
from pathlib import Path

HTML_PATH = Path(__file__).resolve().parent.parent / "templates" / "index.html"


class AttrCollector(HTMLParser):
    """Collect elements matching specific criteria from HTML."""

    def __init__(self):
        super().__init__()
        self.elements_by_id: dict[str, dict] = {}
        self.elements_by_class: dict[str, list[dict]] = {}

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        el = {"tag": tag, "attrs": attr_dict}
        if "id" in attr_dict:
            self.elements_by_id[attr_dict["id"]] = el
        for cls in attr_dict.get("class", "").split():
            self.elements_by_class.setdefault(cls, []).append(el)


def parse_html():
    html = HTML_PATH.read_text()
    parser = AttrCollector()
    parser.feed(html)
    return parser


class TestNavigationARIA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = parse_html()

    def test_topbar_nav_has_role(self):
        navs = [el for el in self.p.elements_by_class.get("topbar-nav", [])
                if el["attrs"].get("role") == "navigation"]
        self.assertTrue(navs, "topbar-nav missing role='navigation'")

    def test_topbar_nav_has_aria_label(self):
        navs = self.p.elements_by_class.get("topbar-nav", [])
        self.assertTrue(navs)
        self.assertIn("aria-label", navs[0]["attrs"])

    def test_subnav_has_role(self):
        el = self.p.elements_by_id.get("subnav")
        self.assertIsNotNone(el, "#subnav not found")
        self.assertEqual(el["attrs"].get("role"), "navigation")

    def test_subnav_has_aria_label(self):
        el = self.p.elements_by_id.get("subnav")
        self.assertIsNotNone(el)
        self.assertIn("aria-label", el["attrs"])


class TestContainerRole(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = parse_html()

    def test_container_has_main_role(self):
        containers = [el for el in self.p.elements_by_class.get("container", [])
                      if el["attrs"].get("role") == "main"]
        self.assertTrue(containers, ".container missing role='main'")


class TestFeedbackARIA(unittest.TestCase):
    FEEDBACK_IDS = ["quiz-feedback", "rev-feedback", "mix-feedback", "con-feedback"]

    @classmethod
    def setUpClass(cls):
        cls.p = parse_html()

    def test_feedback_elements_have_aria_live(self):
        for fid in self.FEEDBACK_IDS:
            with self.subTest(id=fid):
                el = self.p.elements_by_id.get(fid)
                self.assertIsNotNone(el, f"#{fid} not found")
                self.assertEqual(el["attrs"].get("aria-live"), "polite",
                    f"#{fid} missing aria-live='polite'")

    def test_score_text_has_aria_live(self):
        el = self.p.elements_by_id.get("score-text")
        self.assertIsNotNone(el, "#score-text not found")
        self.assertEqual(el["attrs"].get("aria-live"), "polite")


class TestInputARIA(unittest.TestCase):
    INPUT_IDS = ["quiz-input", "rev-input", "mix-input", "con-input", "translate-input"]

    @classmethod
    def setUpClass(cls):
        cls.p = parse_html()

    def test_inputs_have_aria_labels(self):
        for iid in self.INPUT_IDS:
            with self.subTest(id=iid):
                el = self.p.elements_by_id.get(iid)
                self.assertIsNotNone(el, f"#{iid} not found")
                label = el["attrs"].get("aria-label", "")
                self.assertTrue(len(label) > 0, f"#{iid} missing aria-label")


class TestButtonARIA(unittest.TestCase):
    SUBMIT_IDS = ["quiz-submit", "rev-submit", "mix-submit", "con-submit"]
    SKIP_CLASSES = "skip"

    @classmethod
    def setUpClass(cls):
        cls.p = parse_html()

    def test_submit_buttons_have_aria_label(self):
        for bid in self.SUBMIT_IDS:
            with self.subTest(id=bid):
                el = self.p.elements_by_id.get(bid)
                self.assertIsNotNone(el, f"#{bid} not found")
                self.assertIn("aria-label", el["attrs"],
                    f"#{bid} missing aria-label")

    def test_skip_buttons_have_aria_label(self):
        """Check skip buttons inside quiz sections (not gridquiz reset or tutorial nav)."""
        skips = [el for el in self.p.elements_by_class.get("skip", [])
                 if el["tag"] == "button"
                 and "onclick" in el["attrs"]
                 and el["attrs"]["onclick"].startswith("skip")]
        self.assertTrue(skips, "No quiz skip buttons found")
        for i, el in enumerate(skips):
            with self.subTest(onclick=el["attrs"].get("onclick")):
                self.assertIn("aria-label", el["attrs"],
                    f"Skip button missing aria-label")


class TestStatusARIA(unittest.TestCase):
    STATUS_IDS = ["gridquiz-timer", "gridquiz-result"]

    @classmethod
    def setUpClass(cls):
        cls.p = parse_html()

    def test_status_elements_have_role(self):
        for sid in self.STATUS_IDS:
            with self.subTest(id=sid):
                el = self.p.elements_by_id.get(sid)
                self.assertIsNotNone(el, f"#{sid} not found")
                self.assertEqual(el["attrs"].get("role"), "status",
                    f"#{sid} missing role='status'")


class TestExistingARIA(unittest.TestCase):
    """Verify pre-existing aria-labels on settings and theme toggle."""

    @classmethod
    def setUpClass(cls):
        cls.p = parse_html()

    def test_settings_button_has_aria_label(self):
        settings = [el for el in self.p.elements_by_class.get("settings-btn", [])
                    if "aria-label" in el["attrs"]]
        self.assertTrue(settings, "Settings button missing aria-label")

    def test_theme_toggle_has_aria_label(self):
        el = self.p.elements_by_id.get("theme-toggle")
        self.assertIsNotNone(el)
        self.assertIn("aria-label", el["attrs"])


if __name__ == "__main__":
    unittest.main()
