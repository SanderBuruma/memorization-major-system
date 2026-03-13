"""Major System consonant encoding logic using CMU Pronouncing Dictionary.

Uses the ``cmudict`` package directly for phoneme lookups.
"""

import cmudict

# Load once at module level
_CMU_DICT = cmudict.dict()

# CMU phoneme -> Major System digit
# Standard mapping per https://en.wikipedia.org/wiki/Mnemonic_major_system
# Vowels (AA, AE, AH, AO, AW, AY, EH, ER, EY, IH, IY, OW, OY, UH, UW)
# and HH, W, Y are ignored.
PHONEME_TO_DIGIT = {
    'S': '0', 'Z': '0',
    'T': '1', 'D': '1', 'TH': '1', 'DH': '1',
    'N': '2',
    'M': '3',
    'R': '4',
    'L': '5',
    'CH': '6', 'JH': '6', 'SH': '6', 'ZH': '6',
    'K': '7', 'G': '7', 'NG': '7',
    'F': '8', 'V': '8',
    'P': '9', 'B': '9',
}

# Human-readable digit-to-sounds reference
DIGIT_TO_SOUNDS = {
    '0': 'S, Z',
    '1': 'T, D, TH',
    '2': 'N',
    '3': 'M',
    '4': 'R',
    '5': 'L',
    '6': 'CH, J, SH',
    '7': 'C, K, G, NG',
    '8': 'F, V',
    '9': 'P, B',
}


def phonemes_to_digits(phoneme_list):
    """Convert a list of CMU phonemes to a Major System digit string.

    Args:
        phoneme_list: List of CMU phoneme strings, e.g. ['K', 'EY1', 'K']

    Returns:
        Digit string, e.g. '77' for 'cake'.
    """
    digits = []
    for phoneme in phoneme_list:
        clean = phoneme.rstrip('012')  # strip stress markers
        if clean in PHONEME_TO_DIGIT:
            digits.append(PHONEME_TO_DIGIT[clean])
    return ''.join(digits)


def word_to_digits(word):
    """Convert a word to its Major System digit encoding via CMU dictionary.

    Returns:
        Digit string, or None if the word is not in the CMU dictionary.
    """
    pronunciations = _CMU_DICT.get(word.lower())
    if not pronunciations:
        return None
    return phonemes_to_digits(pronunciations[0])


def word_to_phonemes(word):
    """Return the first CMU pronunciation for *word*, or None."""
    pronunciations = _CMU_DICT.get(word.lower())
    if not pronunciations:
        return None
    return pronunciations[0]


def number_to_digits(number):
    """Convert a number 0-99 to its zero-padded two-digit string."""
    return f"{number:02d}"
