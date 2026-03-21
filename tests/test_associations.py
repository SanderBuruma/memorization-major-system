"""Unit-test suite for Major System 00-99 noun associations.

Run independently:
    python -m unittest test_associations
    python test_associations.py
"""

import json
import unittest
from pathlib import Path

from nltk.corpus import wordnet as wn

from trainer.generator import ensure_nltk_data, is_concrete_noun_synset, load_or_generate_wordlist
from trainer.validator import number_to_digits, word_to_digits, word_to_phonemes


class TestMajorSystemAssociations(unittest.TestCase):
    """Validate every 00-99 association for correctness."""

    @classmethod
    def setUpClass(cls):
        ensure_nltk_data()
        wordlist_path = Path(__file__).resolve().parent.parent / 'wordlist.json'
        if wordlist_path.exists():
            with open(wordlist_path) as f:
                cls.wordlist = json.load(f)
        else:
            cls.wordlist = load_or_generate_wordlist()

    # ------------------------------------------------------------------
    # Coverage
    # ------------------------------------------------------------------

    def test_all_numbers_covered(self):
        """Every number 00-99 must have a non-null association."""
        for num in range(100):
            digits = number_to_digits(num)
            with self.subTest(number=digits):
                self.assertIn(digits, self.wordlist,
                              f"Number {digits} missing from wordlist")
                self.assertIsNotNone(self.wordlist[digits],
                                     f"Number {digits} has a null association")

    # ------------------------------------------------------------------
    # Noun check
    # ------------------------------------------------------------------

    def test_all_words_are_nouns(self):
        """Every word must be a noun in WordNet."""
        for num in range(100):
            digits = number_to_digits(num)
            word = self.wordlist.get(digits)
            if word is None:
                continue
            with self.subTest(number=digits, word=word):
                noun_synsets = wn.synsets(word, pos=wn.NOUN)
                self.assertTrue(
                    len(noun_synsets) > 0,
                    f"'{word}' (for {digits}) is not a noun in WordNet. "
                    f"Synsets: {[s.name() for s in wn.synsets(word)]}",
                )

    # ------------------------------------------------------------------
    # Encoding check
    # ------------------------------------------------------------------

    def test_all_encodings_match(self):
        """Every word's Major System encoding must equal its assigned number."""
        for num in range(100):
            digits = number_to_digits(num)
            word = self.wordlist.get(digits)
            if word is None:
                continue
            with self.subTest(number=digits, word=word):
                actual = word_to_digits(word)
                self.assertIsNotNone(
                    actual,
                    f"'{word}' (for {digits}) not found in CMU dictionary",
                )
                self.assertEqual(
                    actual, digits,
                    f"'{word}' encodes as '{actual}', expected '{digits}'. "
                    f"Phonemes: {word_to_phonemes(word)}",
                )

    # ------------------------------------------------------------------
    # Concreteness check
    # ------------------------------------------------------------------

    def test_all_words_are_concrete(self):
        """Every word must trace to an accepted concrete root via hypernyms."""
        for num in range(100):
            digits = number_to_digits(num)
            word = self.wordlist.get(digits)
            if word is None:
                continue
            with self.subTest(number=digits, word=word):
                concrete = any(
                    is_concrete_noun_synset(s)
                    for s in wn.synsets(word, pos=wn.NOUN)
                )
                self.assertTrue(
                    concrete,
                    f"'{word}' (for {digits}) is not a concrete noun. "
                    f"Noun synsets: {[s.name() for s in wn.synsets(word, pos=wn.NOUN)]}",
                )


if __name__ == '__main__':
    unittest.main(verbosity=2)
