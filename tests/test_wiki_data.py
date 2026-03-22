"""Tests verifying data contracts that the wiki's dynamic content depends on.

The wiki renders examples from appState.wordlist and appState.mapping.
These tests ensure the backend always provides the keys the wiki expects.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.test import TestCase
from trainer.generator import load_or_generate_wordlist
from trainer.validator import word_to_digits


class TestSingleDigitWords(TestCase):
    """The wiki's SINGLE_DIGIT_WORDS must encode to the correct single digit."""

    # Must match SINGLE_DIGIT_WORDS in src/ts/wiki.ts
    SINGLE_DIGIT_WORDS = {
        '0': 'sea', '1': 'tie', '2': 'knee', '3': 'maw', '4': 'aura',
        '5': 'oil', '6': 'shoe', '7': 'cow', '8': 'fur', '9': 'pie',
    }

    def test_each_word_encodes_to_its_digit(self):
        for digit, word in self.SINGLE_DIGIT_WORDS.items():
            encoded = word_to_digits(word)
            self.assertEqual(encoded, digit,
                             f"'{word}' encodes to '{encoded}', expected '{digit}'")

    def test_all_10_digits_covered(self):
        self.assertEqual(set(self.SINGLE_DIGIT_WORDS.keys()),
                         {str(d) for d in range(10)})


class TestWordlistCoversWikiKeys(TestCase):
    """wordExamples() reads keys 00, 14, 27, 53, 91.
    inlineExample() reads key 14.
    All must exist and encode correctly."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wordlist = load_or_generate_wordlist()

    def test_wordlist_has_110_entries(self):
        self.assertEqual(len(self.wordlist), 110)

    def test_all_word_example_keys_present(self):
        """Keys used by wordExamples in the wiki."""
        for key in ('00', '14', '27', '53', '91'):
            self.assertIn(key, self.wordlist, f"Missing wordlist key {key}")
            self.assertIsNotNone(self.wordlist[key], f"Wordlist key {key} is None")

    def test_all_wordlist_entries_encode_correctly(self):
        """Every word in the wordlist must encode back to its key."""
        for num in range(100):
            key = f"{num:02d}"
            word = self.wordlist.get(key)
            if word is None:
                continue
            encoded = word_to_digits(word)
            self.assertEqual(encoded, key,
                             f"'{word}' encodes to '{encoded}', expected '{key}'")


class TestMappingCoversAllDigits(TestCase):
    """The wiki's mappingTable() and singleDigitExamples() read mapping[0..9]."""

    def test_mapping_api_has_all_10_digits(self):
        resp = self.client.get('/api/mapping')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for d in range(10):
            key = str(d)
            self.assertIn(key, data, f"Missing mapping key {key}")
            self.assertTrue(len(data[key]) > 0, f"Empty mapping for digit {key}")

    def test_mapping_values_are_comma_separated(self):
        """singleDigitExamples splits on ', ' to get the first sound."""
        resp = self.client.get('/api/mapping')
        data = resp.json()
        for d in range(10):
            val = data[str(d)]
            parts = val.split(', ')
            self.assertGreater(len(parts), 0,
                               f"Digit {d} mapping has no parts after split")
            for part in parts:
                self.assertTrue(len(part.strip()) > 0,
                                f"Digit {d} has empty part in '{val}'")


class TestCandidatesForWikiKeys(TestCase):
    """The wiki shows example words — candidates API should work for those keys."""

    def test_candidates_available_for_word_example_keys(self):
        for key in ('00', '14', '27', '53', '91'):
            with self.subTest(key=key):
                resp = self.client.get(f'/api/candidates/{key}')
                self.assertEqual(resp.status_code, 200)
                self.assertIsInstance(resp.json(), list)
