"""CLI lookup tool for Major System word/number associations.

Usage:
    python lookup.py 47       # number -> show candidate words
    python lookup.py roof     # word -> show its number + checks
"""

import json
import sys
from pathlib import Path

import cmudict

from validator import word_to_digits, word_to_phonemes, number_to_digits, phonemes_to_digits, PHONEME_TO_DIGIT
from generator import (
    ensure_nltk_data, is_word_concrete, is_word_noun,
    get_concrete_nouns, build_candidate_map, select_best_word,
    WORDLIST_PATH,
)

_CMU_DICT = cmudict.dict()


def load_wordlist():
    if WORDLIST_PATH.exists():
        with open(WORDLIST_PATH) as f:
            return json.load(f)
    return {}


def lookup_number(digits):
    """Show all candidate words for a 2-digit number."""
    wordlist = load_wordlist()
    current = wordlist.get(digits)

    print(f"\n=== {digits} ===")
    if current:
        print(f"  Current wordlist: {current}")
    else:
        print("  Current wordlist: (none)")

    # Concrete noun candidates
    ensure_nltk_data()
    nouns = get_concrete_nouns()
    candidates = build_candidate_map(nouns)
    concrete_list = sorted(candidates.get(digits, []), key=lambda w: (len(w), w))

    print(f"\n  Concrete noun candidates ({len(concrete_list)}):")
    for w in concrete_list:
        star = " *" if w == current else ""
        print(f"    {w}{star}")

    # All CMU dict words that encode to this number
    all_matches = []
    for word, pronunciations in _CMU_DICT.items():
        d = phonemes_to_digits(pronunciations[0])
        if d == digits:
            all_matches.append(word)
    all_matches.sort(key=lambda w: (len(w), w))

    # Non-concrete matches
    concrete_set = set(concrete_list)
    other = [w for w in all_matches if w not in concrete_set]
    print(f"\n  Other CMU dict matches ({len(other)}):")
    # Build display strings for each word
    entries = []
    for w in other:
        noun = is_word_noun(w)
        tag = " [noun]" if noun else ""
        star = " *" if w == current else ""
        entries.append(f"{w}{tag}{star}")
    # Print in columns
    if entries:
        col_width = max(len(e) for e in entries) + 2
        cols = max(1, 80 // col_width)
        for i in range(0, len(entries), cols):
            row = entries[i:i + cols]
            print("    " + "".join(e.ljust(col_width) for e in row).rstrip())
    print()


def lookup_word(word):
    """Show number, phonemes, and status for a word."""
    word = word.lower()
    digits = word_to_digits(word)
    phonemes = word_to_phonemes(word)

    print(f"\n=== {word} ===")
    if digits is None:
        print("  Not found in CMU dictionary.")
        return

    print(f"  Number:   {digits}")
    # Show phonemes with digit mapping
    phoneme_parts = []
    for p in phonemes:
        clean = p.rstrip('012')
        if clean in PHONEME_TO_DIGIT:
            phoneme_parts.append(f"{p}({PHONEME_TO_DIGIT[clean]})")
        else:
            phoneme_parts.append(p)
    print(f"  Phonemes: {' '.join(phoneme_parts)}")

    ensure_nltk_data()
    noun = is_word_noun(word)
    concrete = is_word_concrete(word)
    print(f"  Noun:     {'yes' if noun else 'no'}")
    print(f"  Concrete: {'yes' if concrete else 'no'}")

    wordlist = load_wordlist()
    current = wordlist.get(digits)
    if current:
        if current == word:
            print(f"  Wordlist: this IS the current word for {digits}")
        else:
            print(f"  Wordlist: {digits} -> {current}")
    else:
        print(f"  Wordlist: {digits} has no word assigned")
    print()


def main():
    if len(sys.argv) != 2:
        print("Usage: python lookup.py <number|word>")
        print("  python lookup.py 47    # number -> show candidates")
        print("  python lookup.py roof  # word -> show its number")
        sys.exit(1)

    arg = sys.argv[1]

    if arg.isdigit() and 0 <= int(arg) <= 99:
        lookup_number(number_to_digits(int(arg)))
    else:
        lookup_word(arg)


if __name__ == '__main__':
    main()
