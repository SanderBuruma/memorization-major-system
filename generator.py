"""Word selection logic for Major System 00-99 noun associations.

Uses NLTK WordNet nouns filtered for concreteness (must trace to
physical_entity.n.01) and the CMU Pronouncing Dictionary for phoneme-based
encoding validation.
"""

import json
import logging
import random
from pathlib import Path

import nltk
from nltk.corpus import wordnet as wn

from validator import word_to_digits, number_to_digits

logger = logging.getLogger(__name__)

WORDLIST_PATH = Path(__file__).parent / 'wordlist.json'

# Manual overrides for numbers where the automatic search yields poor results.
# Each value must still pass all validation (noun, concrete, encoding).
MANUAL_OVERRIDES = {
    '03': 'seam',   '04': 'czar',   '07': 'sock',   '08': 'sofa',
    '09': 'soap',   '10': 'dice',   '14': 'door',   '15': 'doll',
    '17': 'dog',    '20': 'nose',   '22': 'noon',   '28': 'knife',
    '33': 'mom',    '34': 'mare',   '38': 'movie',  '40': 'rose',
    '49': 'rope',   '52': 'lion',   '54': 'lair',   '60': 'cheese',
    '66': 'judge',  '69': 'ship',   '92': 'bone',
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


_CONCRETE_ROOT_NAMES = (
    'physical_entity.n.01',
    'social_group.n.01',
    'person.n.01',
    'organism.n.01',
    'imaginary_being.n.01',
    'spiritual_being.n.01',
    'causal_agent.n.01',
    'clock_time.n.01',
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
    queue = [synset]
    while queue:
        current = queue.pop(0)
        if current in roots:
            return True
        if current in visited:
            continue
        visited.add(current)
        queue.extend(current.hypernyms())
    return False


def get_concrete_nouns():
    """Return a set of single-word concrete nouns from WordNet.

    A noun is *concrete* if at least one of its synsets is a hyponym of
    ``physical_entity.n.01``.
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
    """Map each two-digit string to its list of candidate nouns."""
    candidates = {}
    for noun in nouns:
        digits = word_to_digits(noun)
        if digits is not None and len(digits) == 2:
            candidates.setdefault(digits, []).append(noun)
    return candidates


def select_best_word(candidates):
    """Pick the shortest (then alphabetically first) candidate noun."""
    return sorted(candidates, key=lambda w: (len(w), w))[0]


def generate_wordlist(seed=42):
    """Generate the complete 00-99 Major System wordlist.

    Returns a dict mapping ``"00"``-``"99"`` to noun strings (or None).
    """
    random.seed(seed)

    logger.info("Loading concrete nouns from WordNet...")
    nouns = get_concrete_nouns()
    logger.info("Found %d concrete nouns", len(nouns))

    logger.info("Building candidate map from CMU pronunciations...")
    candidates = build_candidate_map(nouns)
    logger.info("Found candidates for %d / 100 digit pairs", len(candidates))

    wordlist = {}
    missing = []

    for num in range(100):
        digits = number_to_digits(num)

        if digits in MANUAL_OVERRIDES:
            wordlist[digits] = MANUAL_OVERRIDES[digits]
            logger.info("  %s -> %s (manual)", digits, MANUAL_OVERRIDES[digits])
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
    print(f"\nGenerated {filled}/100 associations")
    if issues:
        print(f"Issues fixed: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
    print(f"Saved to {WORDLIST_PATH}")
