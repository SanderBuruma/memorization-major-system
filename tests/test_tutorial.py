import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

import json
import unittest

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


# --- JS persistence tests (shared Node.js harness) ---

from tests.js_harness import run_js_tests as _run_js_tests


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
    def test_tutorial_picks_words_from_wordlist(self):
        results = _run_js_tests([{
            "name": "tutorial_dynamic_words",
            "code": """
                // Populate wordlist so pickRandomWords has data
                appState.defaultWordlist = {"00":"sis","01":"seat","02":"son","03":"seam","04":"seer","05":"sail"};
                rebuildWordlist();
                startTutorial();
                if (!tutorialQuizWords || tutorialQuizWords.length !== 3)
                    throw new Error('Expected 3 quiz words, got ' +
                        (tutorialQuizWords ? tutorialQuizWords.length : 'undefined'));
                for (var i = 0; i < tutorialQuizWords.length; i++) {
                    var q = tutorialQuizWords[i];
                    if (!q.word || !q.digits)
                        throw new Error('Question ' + i + ' missing word or digits');
                    if (q.digits.length !== 2)
                        throw new Error('Digits should be 2 chars: ' + q.digits);
                    if (appState.wordlist[q.digits] !== q.word)
                        throw new Error('Word "' + q.word + '" not in wordlist for digits ' + q.digits);
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
