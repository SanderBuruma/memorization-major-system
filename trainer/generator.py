"""Word selection logic for Major System 0-99 noun associations.

Uses NLTK WordNet nouns filtered for concreteness (must trace to
physical_entity.n.01) and the CMU Pronouncing Dictionary for phoneme-based
encoding validation.
"""

import json
import logging
import random
from collections import deque
from pathlib import Path

import nltk
from nltk.corpus import wordnet as wn

from trainer.validator import word_to_digits, number_to_digits

logger = logging.getLogger(__name__)

WORDLIST_PATH = Path(__file__).resolve().parent.parent / 'wordlist.json'

# Curated single-digit nouns: vivid, concrete, easy to visualize.
SINGLE_DIGIT_WORDS = {
    '0': 'sea', '1': 'tie', '2': 'knee', '3': 'maw', '4': 'aura',
    '5': 'oil', '6': 'shoe', '7': 'cow', '8': 'fur', '9': 'pie',
}

# Words to exclude (offensive, abbreviations, or poor for memorization)
BLOCKED_WORDS = {
    'jap', 'fag', 'coon', 'spic', 'kike',          # slurs
    'cfo', 'atm', 'atp', 'amd', 'rna', 'hiv',      # abbreviations
    'anus', 'cul',                                    # not great for learning
}


def ensure_nltk_data():
    """Download required NLTK data if not already present."""
    for path, name in [
        ('corpora/wordnet', 'wordnet'),
        ('corpora/omw-1.4', 'omw-1.4'),
    ]:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)


# Two-tier concreteness system:
#   Narrow (get_concrete_nouns): only physical_entity hyponyms — used to generate
#     candidate suggestions, where we want strictly tangible objects.
#   Broad (_CONCRETE_ROOT_NAMES / is_concrete_noun_synset): adds social groups,
#     imaginary beings, etc. — used to validate user-chosen words, where we accept
#     anything vivid enough to form a mental image.
_CONCRETE_ROOT_NAMES = (
    'physical_entity.n.01',      # core: objects, substances, locations
    'social_group.n.01',         # teams, families, nations — visualisable groups
    'person.n.01',               # people (already under physical, but explicit for clarity)
    'organism.n.01',             # animals and plants
    'imaginary_being.n.01',      # dragon, unicorn — vivid mental images
    'spiritual_being.n.01',      # angel, demon — culturally concrete
    'causal_agent.n.01',         # broader than person: includes natural forces
    'clock_time.n.01',           # noon, midnight — concrete points in time
    'sound.n.04',               # bang, hiss — auditory but sensory-concrete
    'written_symbol.n.01',       # letter, digit — visually concrete symbols
)
_concrete_roots = None


def _get_concrete_roots():
    global _concrete_roots
    if _concrete_roots is None:
        _concrete_roots = {wn.synset(name) for name in _CONCRETE_ROOT_NAMES}
    return _concrete_roots


def is_concrete_noun_synset(synset):
    """Check whether *synset* traces to an accepted concrete root via hypernyms."""
    roots = _get_concrete_roots()
    visited = set()
    queue = deque([synset])
    while queue:
        current = queue.popleft()
        if current in roots:
            return True
        if current in visited:
            continue
        visited.add(current)
        queue.extend(current.hypernyms())
    return False


def get_concrete_nouns():
    """Return a set of single-word concrete nouns from WordNet.

    Uses the *narrow* tier (``physical_entity.n.01`` only) — see the
    two-tier concreteness comment above ``_CONCRETE_ROOT_NAMES``.
    """
    ensure_nltk_data()
    physical_entity = wn.synset('physical_entity.n.01')
    concrete_synsets = set(physical_entity.closure(lambda s: s.hyponyms()))
    concrete_synsets.add(physical_entity)

    nouns = set()
    for synset in concrete_synsets:
        for lemma in synset.lemmas():
            name = lemma.name().lower()
            # Single words, alphabetic, must contain a vowel (filters abbreviations),
            # and not in the blocklist.
            if ('_' not in name and name.isalpha() and len(name) > 1
                    and any(c in 'aeiouy' for c in name)
                    and name not in BLOCKED_WORDS):
                nouns.add(name)
    return nouns


def is_word_noun(word):
    """Return True if *word* has at least one noun synset in WordNet."""
    return len(wn.synsets(word, pos=wn.NOUN)) > 0


def is_word_concrete(word):
    """Return True if *word* has at least one concrete noun synset."""
    return any(is_concrete_noun_synset(s) for s in wn.synsets(word, pos=wn.NOUN))


def build_candidate_map(nouns):
    """Map each one- or two-digit string to its list of candidate nouns."""
    candidates = {}
    for noun in nouns:
        digits = word_to_digits(noun)
        if digits is not None and len(digits) in (1, 2):
            candidates.setdefault(digits, []).append(noun)
    return candidates


def select_best_word(candidates):
    """Pick the shortest (then alphabetically first) candidate noun."""
    return sorted(candidates, key=lambda w: (len(w), w))[0]


def generate_wordlist(seed=42):
    """Generate the complete 0-99 Major System wordlist.

    Preserves existing valid entries from wordlist.json (the single source of
    truth) and only auto-fills missing or invalid slots.

    Returns a dict mapping ``"0"``-``"9"`` and ``"00"``-``"99"`` to noun strings (or None).
    """
    random.seed(seed)

    # Load existing wordlist to preserve manual picks
    existing = {}
    if WORDLIST_PATH.exists():
        with open(WORDLIST_PATH) as f:
            existing = json.load(f)

    logger.info("Loading concrete nouns from WordNet...")
    nouns = get_concrete_nouns()
    logger.info("Found %d concrete nouns", len(nouns))

    logger.info("Building candidate map from CMU pronunciations...")
    candidates = build_candidate_map(nouns)
    logger.info("Found candidates for %d digit strings", len(candidates))

    wordlist = {}
    missing = []

    # Single-digit entries (0-9): use curated defaults, allow existing overrides
    for digit in range(10):
        d = str(digit)
        if d in existing and existing[d] and word_to_digits(existing[d]) == d:
            wordlist[d] = existing[d]
            logger.info("  %s -> %s (existing)", d, existing[d])
        else:
            wordlist[d] = SINGLE_DIGIT_WORDS[d]
            logger.info("  %s -> %s (curated default)", d, SINGLE_DIGIT_WORDS[d])

    # Two-digit entries (00-99)
    for num in range(100):
        digits = number_to_digits(num)

        # Keep existing entry if it has a valid encoding
        if digits in existing and existing[digits] and word_to_digits(existing[digits]) == digits:
            wordlist[digits] = existing[digits]
            logger.info("  %s -> %s (existing)", digits, existing[digits])
            continue

        if digits in candidates and candidates[digits]:
            word = select_best_word(candidates[digits])
            wordlist[digits] = word
            logger.info("  %s -> %s", digits, word)
        else:
            missing.append(digits)
            wordlist[digits] = None
            logger.warning("  %s -> NO CANDIDATE FOUND", digits)

    if missing:
        logger.warning("Missing words for: %s", ', '.join(missing))

    return wordlist


def validate_and_fix(wordlist):
    """Validate every entry; replace invalid ones from the candidate pool.

    Returns ``(wordlist, issues)`` where *issues* is a list of strings
    describing what was wrong and fixed.
    """
    ensure_nltk_data()
    issues = []

    # Build candidates once for replacements
    nouns = get_concrete_nouns()
    candidates = build_candidate_map(nouns)

    # Ensure single-digit entries exist
    for digit in range(10):
        d = str(digit)
        word = wordlist.get(d)
        if word is None or word_to_digits(word) != d:
            wordlist[d] = SINGLE_DIGIT_WORDS[d]
            if word is not None:
                issues.append(f"{d}: '{word}' encodes incorrectly, reset to '{SINGLE_DIGIT_WORDS[d]}'")

    for num in range(100):
        digits = number_to_digits(num)
        word = wordlist.get(digits)

        if word is None:
            issues.append(f"{digits}: no word assigned")
            _try_replace(wordlist, digits, candidates, None)
            continue

        actual_digits = word_to_digits(word)
        if actual_digits != digits:
            issues.append(
                f"{digits}: '{word}' encodes as '{actual_digits}', expected '{digits}'"
            )
            _try_replace(wordlist, digits, candidates, word)
            continue

        if not is_word_noun(word):
            issues.append(f"{digits}: '{word}' is not a noun in WordNet")
            _try_replace(wordlist, digits, candidates, word)
            continue

        if not is_word_concrete(word):
            issues.append(f"{digits}: '{word}' is not a concrete noun")
            _try_replace(wordlist, digits, candidates, word)

    return wordlist, issues


def _try_replace(wordlist, digits, candidates, bad_word):
    """Attempt to replace an invalid entry from the candidate pool."""
    pool = candidates.get(digits, [])
    pool = [w for w in pool if w != bad_word]
    if pool:
        replacement = select_best_word(pool)
        wordlist[digits] = replacement
        logger.info("  Replaced %s: %s -> %s", digits, bad_word, replacement)
    else:
        logger.error("  No replacement available for %s", digits)


def load_or_generate_wordlist():
    """Load wordlist from disk, generating or fixing as needed."""
    if WORDLIST_PATH.exists():
        with open(WORDLIST_PATH) as f:
            wordlist = json.load(f)

        # Quick encoding check (fast, only needs CMU dict)
        needs_fix = False

        # Check single-digit entries
        for digit in range(10):
            d = str(digit)
            word = wordlist.get(d)
            if word is None or word_to_digits(word) != d:
                logger.warning("Invalid/missing single-digit entry for %s: %s", d, word)
                needs_fix = True

        # Check two-digit entries
        for num in range(100):
            digits = number_to_digits(num)
            word = wordlist.get(digits)
            if word is None or word_to_digits(word) != digits:
                logger.warning("Invalid entry for %s: %s", digits, word)
                needs_fix = True

        if not needs_fix:
            return wordlist

        logger.info("Fixing invalid entries in existing wordlist...")
        wordlist, issues = validate_and_fix(wordlist)
        if issues:
            logger.warning("Fixed %d issues", len(issues))
        save_wordlist(wordlist)
        return wordlist

    logger.info("No wordlist.json found — generating from scratch...")
    wordlist = generate_wordlist()
    wordlist, issues = validate_and_fix(wordlist)
    save_wordlist(wordlist)
    return wordlist


def save_wordlist(wordlist):
    """Persist wordlist to wordlist.json."""
    with open(WORDLIST_PATH, 'w') as f:
        json.dump(wordlist, f, indent=2, sort_keys=True)
    logger.info("Saved wordlist to %s", WORDLIST_PATH)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    wl = generate_wordlist()
    wl, issues = validate_and_fix(wl)
    save_wordlist(wl)
    filled = sum(1 for v in wl.values() if v is not None)
    print(f"\nGenerated {filled}/110 associations")
    if issues:
        print(f"Issues fixed: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
    print(f"Saved to {WORDLIST_PATH}")
