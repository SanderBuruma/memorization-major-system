import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from django.test import TestCase, override_settings
from trainer.models import QuizState


# --- Django API tests ---

class TestTutorialSeenAPI(TestCase):
    def test_tutorial_seen_defaults_false(self):
        resp = self.client.get('/api/state')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()['tutorialSeen'])

    def test_tutorial_seen_roundtrip(self):
        self.client.post(
            '/api/state',
            data=json.dumps({'tutorialSeen': True}),
            content_type='application/json',
        )
        resp = self.client.get('/api/state')
        self.assertTrue(resp.json()['tutorialSeen'])

    def test_tutorial_seen_rejects_non_bool(self):
        self.client.post(
            '/api/state',
            data=json.dumps({'tutorialSeen': 'yes'}),
            content_type='application/json',
        )
        resp = self.client.get('/api/state')
        self.assertFalse(resp.json()['tutorialSeen'])

    def test_tutorial_seen_persists_for_user(self):
        self.client.post('/register/', {
            'username': 'tutuser', 'password': 'Str0ngP@ss!', 'password2': 'Str0ngP@ss!',
        })
        self.client.post(
            '/api/state',
            data=json.dumps({'tutorialSeen': True}),
            content_type='application/json',
        )
        self.client.post('/logout/')
        self.client.post('/login/', {'username': 'tutuser', 'password': 'Str0ngP@ss!'})
        resp = self.client.get('/api/state')
        self.assertTrue(resp.json()['tutorialSeen'])

    def test_tutorial_seen_isolated_by_ip(self):
        self.client.post(
            '/api/state',
            data=json.dumps({'tutorialSeen': True}),
            content_type='application/json',
            REMOTE_ADDR='10.0.0.1',
        )
        resp_a = self.client.get('/api/state', REMOTE_ADDR='10.0.0.1')
        resp_b = self.client.get('/api/state', REMOTE_ADDR='10.0.0.2')
        self.assertTrue(resp_a.json()['tutorialSeen'])
        self.assertFalse(resp_b.json()['tutorialSeen'])


class TestTutorialSeenModel(TestCase):
    def test_model_field_default(self):
        state = QuizState.objects.create(ip_address='127.0.0.1')
        self.assertFalse(state.tutorial_seen)

    def test_model_field_set_true(self):
        state = QuizState.objects.create(ip_address='127.0.0.1')
        state.tutorial_seen = True
        state.save()
        state.refresh_from_db()
        self.assertTrue(state.tutorial_seen)


@override_settings(STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class TestTutorialHTML(TestCase):
    def test_tutorial_section_present(self):
        resp = self.client.get('/')
        content = resp.content.decode()
        self.assertIn('id="section-tutorial"', content)

    def test_tutorial_has_five_steps(self):
        resp = self.client.get('/')
        content = resp.content.decode()
        for i in range(5):
            self.assertIn(f'data-step="{i}"', content)

    def test_tutorial_nav_buttons_present(self):
        resp = self.client.get('/')
        content = resp.content.decode()
        self.assertIn('id="tutorial-prev"', content)
        self.assertIn('id="tutorial-next"', content)

    def test_tutorial_quiz_container_present(self):
        resp = self.client.get('/')
        content = resp.content.decode()
        self.assertIn('id="tutorial-quiz"', content)

    def test_replay_button_in_settings(self):
        resp = self.client.get('/')
        content = resp.content.decode()
        self.assertIn('Replay Tutorial', content)

    def test_tutorial_progress_dots_present(self):
        resp = self.client.get('/')
        content = resp.content.decode()
        self.assertIn('id="tutorial-dots"', content)


# --- JS persistence tests (Node.js harness) ---

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_JS_PATH = str(_PROJECT_ROOT / "static" / "js" / "app.js")

_NODE_HARNESS = r"""
var _store = {};
var localStorage = {
  getItem: function(k){ return _store[k] || null; },
  setItem: function(k,v){ _store[k] = v; },
  removeItem: function(k){ delete _store[k]; },
  clear: function(){ _store = {}; }
};
var _stubEl = {textContent:'',value:'',innerHTML:'',disabled:false,className:'',
  style:{},
  focus:function(){},appendChild:function(){},addEventListener:function(){},
  classList:{add:function(){},remove:function(){},toggle:function(){},contains:function(){return false;}},
  setAttribute:function(){},getAttribute:function(){return 'dark';},
  removeAttribute:function(){},
  querySelector:function(){ return _stubEl; },
  querySelectorAll:function(){ return {forEach:function(){}}; },
  insertAdjacentHTML:function(){},
  parentNode:{querySelector:function(){return _stubEl;}},
  remove:function(){}};
var document = {
  getElementById: function(){ return _stubEl; },
  querySelectorAll: function(){ return {forEach:function(){}}; },
  querySelector: function(){ return _stubEl; },
  createElement: function(){ return Object.create(_stubEl); },
  documentElement: {getAttribute:function(){return 'dark';},setAttribute:function(){}},
  cookie: '',
  body: {classList:{add:function(){},remove:function(){},toggle:function(){}}}
};
var window = {};
var performance = {now: function(){return 0;}};
var fetch = function(){ return Promise.resolve({ok:true,json:function(){return Promise.resolve({})}}); };
function clearTimeout(){}
function setTimeout(){ return 0; }
function setInterval(){ return 0; }
function clearInterval(){}

%JSCODE%

var fs = require('fs');
var _tests = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
var results = [];
for(var _ti = 0; _ti < _tests.length; _ti++){
  try {
    eval(_tests[_ti].code);
    results.push({name: _tests[_ti].name, pass: true});
  } catch(e) {
    results.push({name: _tests[_ti].name, pass: false, error: e.message});
  }
}
process.stdout.write(JSON.stringify(results));
"""


def _run_js_tests(tests):
    with open(_JS_PATH, encoding="utf-8") as f:
        js_code = f.read()
    js_code = js_code.replace('"use strict";\n(() => {\n', "")
    js_code = js_code.replace("\n})();\n", "\n")
    js_code = re.sub(r"Object\.assign\(window,\s*\{[^}]*\}\);", "", js_code)
    js_code = re.sub(r"\n\s*init\(\);\n", "\n", js_code)
    js_code = js_code.replace("\nlet ", "\nvar ").replace("\nconst ", "\nvar ")

    harness = _NODE_HARNESS.replace("%JSCODE%", js_code)

    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as hf:
        hf.write(harness)
        harness_path = hf.name
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump(tests, tf)
        tests_path = tf.name
    try:
        result = subprocess.run(
            ["node", harness_path, tests_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Node failed:\n{result.stderr}")
        return json.loads(result.stdout)
    finally:
        os.unlink(harness_path)
        os.unlink(tests_path)


class TestTutorialSeenPersistence(unittest.TestCase):
    def test_tutorial_seen_in_state_fields(self):
        results = _run_js_tests([{
            "name": "tutorialSeen_in_state",
            "code": """
                saveState();
                var saved = JSON.parse(localStorage.getItem('quizState'));
                if (saved.tutorialSeen !== false)
                    throw new Error('default tutorialSeen: ' + saved.tutorialSeen);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_tutorial_seen_roundtrip(self):
        results = _run_js_tests([{
            "name": "tutorialSeen_roundtrip",
            "code": """
                appState.tutorialSeen = true;
                saveState();
                appState.tutorialSeen = false;
                loadState();
                if (appState.tutorialSeen !== true)
                    throw new Error('tutorialSeen not restored: ' + appState.tutorialSeen);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_tutorial_seen_default_false(self):
        results = _run_js_tests([{
            "name": "tutorialSeen_default",
            "code": """
                if (appState.tutorialSeen !== false)
                    throw new Error('default is not false: ' + appState.tutorialSeen);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestTutorialStepNavigation(unittest.TestCase):
    def test_tutorial_questions_defined(self):
        results = _run_js_tests([{
            "name": "tutorial_questions",
            "code": """
                if (!TUTORIAL_QUESTIONS || TUTORIAL_QUESTIONS.length !== 3)
                    throw new Error('Expected 3 tutorial questions, got ' +
                        (TUTORIAL_QUESTIONS ? TUTORIAL_QUESTIONS.length : 'undefined'));
                for (var i = 0; i < TUTORIAL_QUESTIONS.length; i++) {
                    var q = TUTORIAL_QUESTIONS[i];
                    if (!q.word || !q.answer)
                        throw new Error('Question ' + i + ' missing word or answer');
                    if (q.answer.length !== 2)
                        throw new Error('Answer should be 2 digits: ' + q.answer);
                }
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_tutorial_total_is_five(self):
        results = _run_js_tests([{
            "name": "tutorial_total",
            "code": """
                if (TUTORIAL_TOTAL !== 5)
                    throw new Error('Expected 5, got ' + TUTORIAL_TOTAL);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


if __name__ == "__main__":
    unittest.main()
