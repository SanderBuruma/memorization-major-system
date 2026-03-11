# Getting Started

## Prerequisites

- **Python 3.8+** (tested on 3.14)
- **pip** for installing dependencies
- Internet connection for first run (downloads NLTK WordNet data)

## Setup

```bash
cd C:\Projects\memorization-major-system
pip install -r requirements.txt
```

This installs:
- `cmudict` — CMU Pronouncing Dictionary for phoneme lookups
- `nltk` — Natural Language Toolkit for WordNet access
- `setuptools` — required by some dependency internals

On first run, NLTK will automatically download the `wordnet` and `omw-1.4` corpora (~30 MB).

## Running the App

```bash
python server.py
```

Opens at **http://localhost:8080**. The server will:
1. Load `wordlist.json` (or generate it from scratch if missing)
2. Validate all 100 entries
3. Start serving on port 8080

Press `Ctrl+C` to stop.

## Running Tests

```bash
python -m unittest test_associations
# or
python test_associations.py
```

Validates all 100 number-noun pairs for:
- Coverage (no gaps)
- Noun status (exists in WordNet as a noun)
- Encoding correctness (CMU phonemes match expected digits)
- Concreteness (traces to `physical_entity.n.01`)

## Regenerating the Wordlist

To regenerate `wordlist.json` from scratch:

```bash
python generator.py
```

This takes 10–30 seconds (WordNet traversal + CMU lookups). The generator:
1. Extracts ~27k concrete nouns from WordNet
2. Encodes each via CMU Pronouncing Dictionary
3. Selects the best match for each number 00–99
4. Validates and saves to `wordlist.json`

## Customizing Words

To override specific associations, edit the `MANUAL_OVERRIDES` dict in `generator.py`:

```python
MANUAL_OVERRIDES = {
    "04": "star",   # S=0, T=1... wait, check encoding first!
}
```

Overrides still must pass validation (encoding, noun, concrete). Run `python generator.py` after editing to regenerate.

To block inappropriate words, add them to `BLOCKED_WORDS` in `generator.py`.

## Project Structure

```
major_system/
├── generator.py         # Word selection + validation logic
├── validator.py         # CMU phoneme → Major System digit encoding
├── server.py            # HTTP server (localhost:8080)
├── test_associations.py # Unittest suite (4 tests × 100 subtests)
├── static/
│   └── index.html       # Single-page frontend
├── wordlist.json        # Generated 00–99 mappings
├── requirements.txt     # Python dependencies
└── docs/                # This documentation
```
