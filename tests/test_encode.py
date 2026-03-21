import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.test import TestCase
import json


class TestEncodeAPI(TestCase):
    def _post(self, text):
        return self.client.post(
            '/api/encode',
            data=json.dumps({'text': text}),
            content_type='application/json',
        )

    def test_known_word_returns_digits(self):
        resp = self._post('moon')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['word'], 'moon')
        self.assertEqual(data[0]['digits'], '32')

    def test_multi_word_input(self):
        resp = self._post('tie moon')
        data = resp.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['word'], 'tie')
        self.assertEqual(data[0]['digits'], '1')
        self.assertEqual(data[1]['word'], 'moon')
        self.assertEqual(data[1]['digits'], '32')

    def test_unknown_word_returns_null_digits(self):
        resp = self._post('xyzzyplugh')
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['word'], 'xyzzyplugh')
        self.assertIsNone(data[0]['digits'])

    def test_empty_text_returns_empty_list(self):
        resp = self._post('')
        data = resp.json()
        self.assertEqual(data, [])

    def test_only_numbers_returns_empty_list(self):
        resp = self._post('123 456')
        data = resp.json()
        self.assertEqual(data, [])

    def test_mixed_known_unknown(self):
        resp = self._post('nail xyzzyplugh bear')
        data = resp.json()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['digits'], '25')
        self.assertIsNone(data[1]['digits'])
        self.assertEqual(data[2]['digits'], '94')

    def test_invalid_json_returns_400(self):
        resp = self.client.post(
            '/api/encode',
            data='not json',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_non_string_text_returns_400(self):
        resp = self.client.post(
            '/api/encode',
            data=json.dumps({'text': 123}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_only_post_allowed(self):
        resp = self.client.get('/api/encode')
        self.assertEqual(resp.status_code, 405)

    def test_case_insensitive(self):
        resp = self._post('Moon NAIL')
        data = resp.json()
        self.assertEqual(data[0]['word'], 'moon')
        self.assertEqual(data[0]['digits'], '32')
        self.assertEqual(data[1]['word'], 'nail')
        self.assertEqual(data[1]['digits'], '25')

    def test_sentence_with_punctuation(self):
        resp = self._post("the cat's hat!")
        data = resp.json()
        words = [d['word'] for d in data]
        self.assertEqual(words, ['the', 'cat', 's', 'hat'])
