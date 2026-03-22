import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.test import TestCase
from trainer.validator import word_to_digits


class TestCandidatesAPI(TestCase):
    def test_returns_list(self):
        resp = self.client.get('/api/candidates/42')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_candidates_encode_to_correct_digits(self):
        for digits in ('00', '12', '42', '99'):
            with self.subTest(digits=digits):
                resp = self.client.get(f'/api/candidates/{digits}')
                data = resp.json()
                for word in data[:5]:  # check first 5 for speed
                    encoded = word_to_digits(word)
                    self.assertEqual(encoded, digits,
                        f"'{word}' encodes to '{encoded}', expected '{digits}'")

    def test_candidates_sorted_by_length_then_alpha(self):
        resp = self.client.get('/api/candidates/42')
        data = resp.json()
        if len(data) > 1:
            for i in range(len(data) - 1):
                a, b = data[i], data[i + 1]
                self.assertTrue(
                    (len(a), a) <= (len(b), b),
                    f"'{a}' should come before '{b}'")

    def test_single_digit_returns_list(self):
        resp = self.client.get('/api/candidates/0')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_single_digit_candidates_encode_correctly(self):
        for d in ('0', '5', '9'):
            with self.subTest(digit=d):
                resp = self.client.get(f'/api/candidates/{d}')
                data = resp.json()
                for word in data[:5]:
                    encoded = word_to_digits(word)
                    self.assertEqual(encoded, d,
                        f"'{word}' encodes to '{encoded}', expected '{d}'")

    def test_invalid_digits_returns_400(self):
        for bad in ('123', 'ab', 'x1'):
            with self.subTest(digits=bad):
                resp = self.client.get(f'/api/candidates/{bad}')
                self.assertEqual(resp.status_code, 400)

    def test_only_get_allowed(self):
        resp = self.client.post('/api/candidates/42')
        self.assertEqual(resp.status_code, 405)

    def test_returns_nonempty_for_common_digits(self):
        """Most 2-digit combos should have at least one candidate."""
        resp = self.client.get('/api/candidates/42')
        data = resp.json()
        self.assertGreater(len(data), 0)

    def test_uncommon_digits_returns_empty_list(self):
        """Some digit pairs may have no concrete noun candidates — should still return []."""
        resp = self.client.get('/api/candidates/77')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)
