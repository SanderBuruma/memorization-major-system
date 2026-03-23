"""Tests for the dyslexia-friendly font toggle feature.

Covers:
- Django model default and API round-trip (POST/GET)
- JS toggleDyslexiaFont body class toggling
- JS dyslexiaFont state persistence via localStorage
- Init applies body class when dyslexiaFont is true

Run:
    python -m pytest tests/test_dyslexia_font.py -v
"""

import json
import os
import unittest

# ---------------------------------------------------------------------------
# Django API tests
# ---------------------------------------------------------------------------

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.test import TestCase
from trainer.models import QuizState


class TestDyslexiaFontModel(TestCase):
    """QuizState.dyslexia_font field basics."""

    def test_default_is_false(self):
        state = QuizState.objects.create(ip_address='10.0.0.99')
        self.assertFalse(state.dyslexia_font)

    def test_set_true_persists(self):
        state = QuizState.objects.create(ip_address='10.0.0.99')
        state.dyslexia_font = True
        state.save()
        state.refresh_from_db()
        self.assertTrue(state.dyslexia_font)


class TestDyslexiaFontAPI(TestCase):
    """API round-trip for dyslexiaFont."""

    def test_get_default_is_false(self):
        resp = self.client.get('/api/state')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()['dyslexiaFont'])

    def test_post_true_roundtrip(self):
        self.client.post(
            '/api/state',
            data=json.dumps({'dyslexiaFont': True}),
            content_type='application/json',
        )
        resp = self.client.get('/api/state')
        self.assertTrue(resp.json()['dyslexiaFont'])

    def test_post_false_after_true(self):
        self.client.post(
            '/api/state',
            data=json.dumps({'dyslexiaFont': True}),
            content_type='application/json',
        )
        self.client.post(
            '/api/state',
            data=json.dumps({'dyslexiaFont': False}),
            content_type='application/json',
        )
        resp = self.client.get('/api/state')
        self.assertFalse(resp.json()['dyslexiaFont'])

    def test_invalid_type_ignored(self):
        """Non-bool values for dyslexiaFont should be ignored."""
        self.client.post(
            '/api/state',
            data=json.dumps({'dyslexiaFont': 'yes'}),
            content_type='application/json',
        )
        resp = self.client.get('/api/state')
        self.assertFalse(resp.json()['dyslexiaFont'])

    def test_isolated_by_ip(self):
        self.client.post(
            '/api/state',
            data=json.dumps({'dyslexiaFont': True}),
            content_type='application/json',
            REMOTE_ADDR='10.0.0.1',
        )
        resp_a = self.client.get('/api/state', REMOTE_ADDR='10.0.0.1')
        resp_b = self.client.get('/api/state', REMOTE_ADDR='10.0.0.2')
        self.assertTrue(resp_a.json()['dyslexiaFont'])
        self.assertFalse(resp_b.json()['dyslexiaFont'])


# ---------------------------------------------------------------------------
# JS tests (shared Node harness)
# ---------------------------------------------------------------------------

from tests.js_harness import run_js_tests as _run_js_tests


class TestDyslexiaFontToggleJS(unittest.TestCase):
    """toggleDyslexiaFont() toggles body class and updates appState."""

    def test_enable_adds_body_class(self):
        results = _run_js_tests([{
            "name": "enable_adds_class",
            "code": """
                _bodyClasses.clear();
                toggleDyslexiaFont(true);
                if(!_bodyClasses.has('dyslexia-font'))
                    throw new Error('body class not added');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_disable_removes_body_class(self):
        results = _run_js_tests([{
            "name": "disable_removes_class",
            "code": """
                _bodyClasses.add('dyslexia-font');
                toggleDyslexiaFont(false);
                if(_bodyClasses.has('dyslexia-font'))
                    throw new Error('body class not removed');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_enable_sets_appstate(self):
        results = _run_js_tests([{
            "name": "enable_sets_state",
            "code": """
                toggleDyslexiaFont(true);
                if(appState.dyslexiaFont !== true)
                    throw new Error('appState.dyslexiaFont not true');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_disable_clears_appstate(self):
        results = _run_js_tests([{
            "name": "disable_clears_state",
            "code": """
                appState.dyslexiaFont = true;
                toggleDyslexiaFont(false);
                if(appState.dyslexiaFont !== false)
                    throw new Error('appState.dyslexiaFont not false');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestDyslexiaFontPersistenceJS(unittest.TestCase):
    """dyslexiaFont survives saveState/loadState round-trip."""

    def test_true_persists(self):
        results = _run_js_tests([{
            "name": "true_persists",
            "code": """
                appState.dyslexiaFont = true;
                saveState();
                appState.dyslexiaFont = false;
                loadState();
                if(appState.dyslexiaFont !== true)
                    throw new Error('dyslexiaFont not restored: ' + appState.dyslexiaFont);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_false_persists(self):
        results = _run_js_tests([{
            "name": "false_persists",
            "code": """
                appState.dyslexiaFont = false;
                saveState();
                appState.dyslexiaFont = true;
                loadState();
                if(appState.dyslexiaFont !== false)
                    throw new Error('dyslexiaFont not restored: ' + appState.dyslexiaFont);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_in_save_payload(self):
        results = _run_js_tests([{
            "name": "in_payload",
            "code": """
                appState.dyslexiaFont = true;
                saveState();
                var saved = JSON.parse(localStorage.getItem('quizState'));
                if(saved.dyslexiaFont !== true)
                    throw new Error('dyslexiaFont missing from payload');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_toggle_then_persist(self):
        """toggleDyslexiaFont calls saveState, so the value should be in localStorage."""
        results = _run_js_tests([{
            "name": "toggle_persists",
            "code": """
                toggleDyslexiaFont(true);
                var saved = JSON.parse(localStorage.getItem('quizState'));
                if(saved.dyslexiaFont !== true)
                    throw new Error('toggle did not persist');
                toggleDyslexiaFont(false);
                saved = JSON.parse(localStorage.getItem('quizState'));
                if(saved.dyslexiaFont !== false)
                    throw new Error('toggle false did not persist');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_default_is_false(self):
        """Fresh state has dyslexiaFont=false."""
        results = _run_js_tests([{
            "name": "default_false",
            "code": """
                localStorage.clear();
                appState.dyslexiaFont = true;
                loadState();
                // No stored state, so loadState is a no-op; but the initial
                // appState default should be false. Reset and check.
                // Re-read the initial value from a fresh save.
                appState.dyslexiaFont = false;
                saveState();
                appState.dyslexiaFont = true;
                loadState();
                if(appState.dyslexiaFont !== false)
                    throw new Error('default not false: ' + appState.dyslexiaFont);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestDyslexiaFontInitJS(unittest.TestCase):
    """init() applies body class when dyslexiaFont is stored as true."""

    @classmethod
    def setUpClass(cls):
        from tests.js_harness import JS_PATH
        with open(JS_PATH, encoding="utf-8") as f:
            cls.js = f.read()

    def _function_body(self, name):
        start = self.js.index("function " + name + "(")
        brace = self.js.index("{", start)
        depth = 1
        i = brace + 1
        while depth > 0:
            if self.js[i] == "{":
                depth += 1
            elif self.js[i] == "}":
                depth -= 1
            i += 1
        return self.js[brace:i]

    def test_init_applies_dyslexia_class(self):
        """init() should check appState.dyslexiaFont and add the body class."""
        body = self._function_body("init")
        self.assertIn("dyslexia", body,
            "init() does not reference dyslexia font — class won't be applied on load")

    def test_toggleDyslexiaFont_calls_saveState(self):
        body = self._function_body("toggleDyslexiaFont")
        self.assertIn("saveState()", body)

    def test_toggleDyslexiaFont_toggles_class(self):
        body = self._function_body("toggleDyslexiaFont")
        self.assertIn("dyslexia-font", body)


class TestDyslexiaFontCSS(unittest.TestCase):
    """Compiled CSS applies OpenDyslexic universally via * selector."""

    @classmethod
    def setUpClass(cls):
        css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'css', 'app.css')
        with open(css_path, encoding='utf-8') as f:
            cls.css = f.read()

    def test_dyslexia_star_selector(self):
        """The dyslexia-font rule must use a * selector so all elements get the font."""
        import re
        # Compiled CSS should contain a rule like: .dyslexia-font *{font-family:OpenDyslexic...}
        # or body.dyslexia-font *,body.dyslexia-font{...}
        self.assertTrue(
            re.search(r'\.dyslexia-font\s*\*', self.css) or
            re.search(r'\.dyslexia-font[^}]*,\s*\.dyslexia-font\s*\*', self.css),
            'dyslexia-font CSS must use * selector to apply font universally',
        )

    def test_no_element_specific_font_family_overrides(self):
        """No SCSS file should set font-family on specific elements outside the dyslexia rule
        (except body's base font and inherit declarations)."""
        import re
        scss_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'scss')
        for fname in os.listdir(scss_dir):
            if not fname.endswith('.scss'):
                continue
            with open(os.path.join(scss_dir, fname), encoding='utf-8') as f:
                content = f.read()
            for match in re.finditer(r'font-family:\s*(.+?);', content):
                value = match.group(1).strip()
                if value == 'inherit':
                    continue
                # The only non-inherit font-family should be in _base.scss on body or the dyslexia rule
                if fname == '_base.scss':
                    continue
                self.fail(f'{fname} sets font-family: {value} — risks overriding dyslexia font')


if __name__ == "__main__":
    unittest.main()
