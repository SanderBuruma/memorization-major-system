import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.test import TestCase, Client
from django.contrib.auth.models import User
from trainer.models import QuizState
import json


class TestWordlistAPI(TestCase):
    def test_wordlist_returns_110_entries(self):
        resp = self.client.get('/api/wordlist')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 110)

    def test_wordlist_keys_include_single_and_double_digits(self):
        resp = self.client.get('/api/wordlist')
        data = resp.json()
        expected_keys = {str(i) for i in range(10)} | {f"{i:02d}" for i in range(100)}
        self.assertEqual(set(data.keys()), expected_keys)

    def test_mapping_returns_10_entries(self):
        resp = self.client.get('/api/mapping')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 10)

    def test_mapping_keys_are_single_digits(self):
        resp = self.client.get('/api/mapping')
        data = resp.json()
        expected_keys = {str(i) for i in range(10)}
        self.assertEqual(set(data.keys()), expected_keys)


class TestStateAPI(TestCase):
    def test_get_empty_state(self):
        resp = self.client.get('/api/state')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['score']['correct'], 0)
        self.assertEqual(data['score']['total'], 0)
        self.assertEqual(data['quizScores'], {})
        self.assertEqual(data['quizHistory'], [])
        self.assertEqual(data['reverseScores'], {})
        self.assertEqual(data['reverseHistory'], [])
        self.assertEqual(data['mixedScores'], {})
        self.assertEqual(data['mixedHistory'], [])
        self.assertEqual(data['conScores'], {})
        self.assertEqual(data['conHistory'], [])
        self.assertEqual(data['theme'], 'dark')
        self.assertIsNone(data['user'])

    def test_post_and_get_roundtrip(self):
        payload = {
            'score': {'correct': 5, 'total': 10},
            'quizScores': {'42': 3},
            'quizHistory': [1, 0, 1],
            'reverseScores': {'07': 2},
            'reverseHistory': [1, 1],
            'mixedScores': {},
            'mixedHistory': [],
            'conScores': {'15': 1},
            'conHistory': [0],
            'theme': 'dark',
        }
        post_resp = self.client.post(
            '/api/state',
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(post_resp.status_code, 200)
        self.assertTrue(post_resp.json().get('ok'))

        get_resp = self.client.get('/api/state')
        data = get_resp.json()
        self.assertEqual(data['score']['correct'], 5)
        self.assertEqual(data['score']['total'], 10)
        self.assertEqual(data['quizScores'], {'42': 3})
        self.assertEqual(data['quizHistory'], [1, 0, 1])
        self.assertEqual(data['reverseScores'], {'07': 2})
        self.assertEqual(data['reverseHistory'], [1, 1])
        self.assertEqual(data['conScores'], {'15': 1})
        self.assertEqual(data['conHistory'], [0])

    def test_post_rejects_invalid_json(self):
        resp = self.client.post(
            '/api/state',
            data='not valid json{{{',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_post_rejects_non_json_content(self):
        resp = self.client.post(
            '/api/state',
            data='theme=light',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(resp.status_code, 400)

    def test_state_isolated_by_ip(self):
        payload_a = {
            'score': {'correct': 1, 'total': 1},
            'quizScores': {}, 'quizHistory': [],
            'reverseScores': {}, 'reverseHistory': [],
            'mixedScores': {}, 'mixedHistory': [],
            'conScores': {}, 'conHistory': [],
            'theme': 'dark',
        }
        payload_b = {
            'score': {'correct': 99, 'total': 100},
            'quizScores': {}, 'quizHistory': [],
            'reverseScores': {}, 'reverseHistory': [],
            'mixedScores': {}, 'mixedHistory': [],
            'conScores': {}, 'conHistory': [],
            'theme': 'light',
        }
        self.client.post(
            '/api/state',
            data=json.dumps(payload_a),
            content_type='application/json',
            REMOTE_ADDR='10.0.0.1',
        )
        self.client.post(
            '/api/state',
            data=json.dumps(payload_b),
            content_type='application/json',
            REMOTE_ADDR='10.0.0.2',
        )

        resp_a = self.client.get('/api/state', REMOTE_ADDR='10.0.0.1')
        resp_b = self.client.get('/api/state', REMOTE_ADDR='10.0.0.2')
        self.assertEqual(resp_a.json()['score']['correct'], 1)
        self.assertEqual(resp_b.json()['score']['correct'], 99)

    def test_theme_persists(self):
        payload = {
            'score': {'correct': 0, 'total': 0},
            'quizScores': {}, 'quizHistory': [],
            'reverseScores': {}, 'reverseHistory': [],
            'mixedScores': {}, 'mixedHistory': [],
            'conScores': {}, 'conHistory': [],
            'theme': 'light',
        }
        self.client.post(
            '/api/state',
            data=json.dumps(payload),
            content_type='application/json',
        )
        resp = self.client.get('/api/state')
        self.assertEqual(resp.json()['theme'], 'light')

    def test_all_theme_values_persist(self):
        """All 4 theme options (dark, light, oled, high-contrast) round-trip via API."""
        for theme in ('dark', 'light', 'oled', 'high-contrast'):
            with self.subTest(theme=theme):
                payload = {'theme': theme}
                self.client.post(
                    '/api/state',
                    data=json.dumps(payload),
                    content_type='application/json',
                )
                resp = self.client.get('/api/state')
                self.assertEqual(resp.json()['theme'], theme)


class TestCustomWords(TestCase):
    def test_custom_words_default_empty(self):
        resp = self.client.get('/api/state')
        self.assertEqual(resp.json()['customWords'], {})

    def test_post_and_get_custom_words_roundtrip(self):
        payload = {'customWords': {'03': 'myword', '42': 'hammer'}}
        self.client.post(
            '/api/state',
            data=json.dumps(payload),
            content_type='application/json',
        )
        resp = self.client.get('/api/state')
        self.assertEqual(resp.json()['customWords'], {'03': 'myword', '42': 'hammer'})

    def test_custom_words_persists_for_user(self):
        # Register
        self.client.post('/register/', {
            'username': 'cwuser', 'password': 'Str0ngP@ss!', 'password2': 'Str0ngP@ss!',
        })
        # Save custom words
        self.client.post(
            '/api/state',
            data=json.dumps({'customWords': {'10': 'dice'}}),
            content_type='application/json',
        )
        # Logout + login
        self.client.post('/logout/')
        self.client.post('/login/', {'username': 'cwuser', 'password': 'Str0ngP@ss!'})
        resp = self.client.get('/api/state')
        self.assertEqual(resp.json()['customWords'], {'10': 'dice'})

    def test_custom_words_isolated_by_ip(self):
        self.client.post(
            '/api/state',
            data=json.dumps({'customWords': {'01': 'alpha'}}),
            content_type='application/json',
            REMOTE_ADDR='10.0.0.1',
        )
        self.client.post(
            '/api/state',
            data=json.dumps({'customWords': {'01': 'beta'}}),
            content_type='application/json',
            REMOTE_ADDR='10.0.0.2',
        )
        resp_a = self.client.get('/api/state', REMOTE_ADDR='10.0.0.1')
        resp_b = self.client.get('/api/state', REMOTE_ADDR='10.0.0.2')
        self.assertEqual(resp_a.json()['customWords'], {'01': 'alpha'})
        self.assertEqual(resp_b.json()['customWords'], {'01': 'beta'})


class TestActivityLogAPI(TestCase):
    def test_activity_log_default_empty(self):
        resp = self.client.get('/api/state')
        self.assertEqual(resp.json()['activityLog'], {})

    def test_activity_log_round_trip(self):
        payload = {'activityLog': {'2026-03-21': 15, '2026-03-20': 3}}
        self.client.post(
            '/api/state',
            data=json.dumps(payload),
            content_type='application/json',
        )
        resp = self.client.get('/api/state')
        self.assertEqual(resp.json()['activityLog'], {'2026-03-21': 15, '2026-03-20': 3})

    def test_activity_log_merge_with_other_state(self):
        payload = {
            'score': {'correct': 5, 'total': 10},
            'activityLog': {'2026-03-21': 7},
        }
        self.client.post(
            '/api/state',
            data=json.dumps(payload),
            content_type='application/json',
        )
        resp = self.client.get('/api/state')
        data = resp.json()
        self.assertEqual(data['score']['correct'], 5)
        self.assertEqual(data['activityLog'], {'2026-03-21': 7})


class TestURLConfig(TestCase):
    def test_all_url_patterns_are_unique(self):
        from django.urls import get_resolver, URLPattern
        all_patterns = []
        def collect(resolver, prefix=''):
            for p in resolver.url_patterns:
                route = prefix + (p.pattern.regex.pattern if hasattr(p.pattern, 'regex') else p.pattern._route)
                if isinstance(p, URLPattern):
                    all_patterns.append(route)
                else:
                    collect(p, route)
        collect(get_resolver())
        self.assertEqual(len(all_patterns), len(set(all_patterns)), f'Duplicate URL patterns: {all_patterns}')

    def test_all_url_names_are_unique(self):
        from django.urls import get_resolver, URLPattern
        names = []
        def collect(resolver):
            for p in resolver.url_patterns:
                if isinstance(p, URLPattern) and p.name:
                    names.append(p.name)
                elif not isinstance(p, URLPattern):
                    collect(p)
        collect(get_resolver())
        self.assertEqual(len(names), len(set(names)), f'Duplicate URL names: {names}')


class TestAuth(TestCase):
    def _register(self, username='testuser', password='Str0ngP@ss!'):
        return self.client.post('/register/', {
            'username': username,
            'password': password,
            'password2': password,
        })

    def test_register_creates_user(self):
        self._register('newuser')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_merges_ip_state(self):
        # Save state as anonymous IP user
        payload = {
            'score': {'correct': 7, 'total': 12},
            'quizScores': {'55': 4},
            'quizHistory': [1, 1, 0],
            'reverseScores': {}, 'reverseHistory': [],
            'mixedScores': {}, 'mixedHistory': [],
            'conScores': {}, 'conHistory': [],
            'theme': 'light',
        }
        self.client.post(
            '/api/state',
            data=json.dumps(payload),
            content_type='application/json',
        )

        # Register — should merge the IP-based state to the new user
        self._register('merger')
        user = User.objects.get(username='merger')
        state = QuizState.objects.get(user=user)
        self.assertEqual(state.score_correct, 7)
        self.assertEqual(state.score_total, 12)
        self.assertEqual(state.quiz_scores, {'55': 4})
        self.assertEqual(state.theme, 'light')

    def test_login_switches_to_user_state(self):
        password = 'Str0ngP@ss!'
        # Register and save state
        self._register('logintest', password)
        payload = {
            'score': {'correct': 3, 'total': 5},
            'quizScores': {'10': 2},
            'quizHistory': [1, 0, 1],
            'reverseScores': {}, 'reverseHistory': [],
            'mixedScores': {}, 'mixedHistory': [],
            'conScores': {}, 'conHistory': [],
            'theme': 'dark',
        }
        self.client.post(
            '/api/state',
            data=json.dumps(payload),
            content_type='application/json',
        )

        # Logout
        self.client.post('/logout/')

        # Login again
        self.client.post('/login/', {
            'username': 'logintest',
            'password': password,
        })

        resp = self.client.get('/api/state')
        data = resp.json()
        self.assertEqual(data['score']['correct'], 3)
        self.assertEqual(data['user'], 'logintest')

    def test_login_invalid_credentials(self):
        self._register('badlogin')
        self.client.post('/logout/')
        resp = self.client.post('/login/', {
            'username': 'badlogin',
            'password': 'wrongpassword',
        })
        # Should not redirect to / on failure
        self.assertNotEqual(resp.status_code, 302)

    def test_logout(self):
        self._register('logouttest')
        self.client.post('/logout/')
        resp = self.client.get('/api/state')
        data = resp.json()
        self.assertIsNone(data['user'])

    def test_register_duplicate_username(self):
        self._register('dupeuser')
        self.client.post('/logout/')
        resp = self._register('dupeuser')
        # Should not redirect to / (registration failed)
        # User count should still be 1
        self.assertEqual(User.objects.filter(username='dupeuser').count(), 1)
