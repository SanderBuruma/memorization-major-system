# Getting Started

## Prerequisites

- **Python 3.8+** (tested on 3.14)
- **Node.js 22+** (for TypeScript/SCSS build)
- **pip** for installing dependencies
- Internet connection for first run (downloads NLTK WordNet data)

## Setup

```bash
cd ~/Projects/memorization-major-system
pip install -r requirements.txt
npm ci
npm run build          # builds JS + CSS into static/
python manage.py migrate
```

This installs:
- `cmudict` — CMU Pronouncing Dictionary for phoneme lookups
- `nltk` — Natural Language Toolkit for WordNet access
- `setuptools` — required by some dependency internals
- `django` — web framework
- `gunicorn` — WSGI server (production)

On first run, NLTK will automatically download the `wordnet` and `omw-1.4` corpora (~30 MB).

## Running the App

```bash
python manage.py runserver 8080
```

Opens at **http://localhost:8080**. The app will:
1. Load `wordlist.json` (or generate it from scratch if missing)
2. Validate all 100 entries
3. Start serving via Django's development server

Press `Ctrl+C` to stop.

In production, the app runs with gunicorn behind nginx on port 8734. The `deploy.sh` script handles `migrate`, `collectstatic`, and service restart.

## Running Tests

```bash
python manage.py test             # run all tests
python manage.py test tests.test_associations   # wordlist validation only
python manage.py test tests.test_pool_quiz      # quiz logic only
python manage.py test tests.test_api            # API + auth integration
python manage.py test tests.test_persistence    # JS persistence logic (requires Node.js)
```

**test_associations.py** — validates all 100 number-noun pairs for:
- Coverage (no gaps)
- Noun status (exists in WordNet as a noun)
- Encoding correctness (CMU phonemes match expected digits)
- Concreteness (traces to `physical_entity.n.01`)

**test_pool_quiz.py** — verifies the score-based quiz system:
- Score-based selection, cooldown history, pick distribution
- Skip/incorrect score decrement
- All 100 words eventually seen

**test_api.py** — Django integration tests:
- Wordlist and mapping API endpoints
- State GET/POST with auth and anonymous access
- Login, register, logout flows
- IP-based state merging on registration

**test_persistence.py** — Node.js harness for JS persistence logic:
- saveState/loadState round-trips via localStorage mock

## Regenerating the Wordlist

To regenerate `wordlist.json` from scratch:

```bash
python trainer/generator.py
```

This takes 10–30 seconds (WordNet traversal + CMU lookups). The generator:
1. Extracts ~27k concrete nouns from WordNet
2. Encodes each via CMU Pronouncing Dictionary
3. Selects the best match for each number 00–99
4. Validates and saves to `wordlist.json`

## Customizing Words

To override specific associations, edit the `MANUAL_OVERRIDES` dict in `trainer/generator.py`:

```python
MANUAL_OVERRIDES = {
    "04": "star",   # S=0, T=1... wait, check encoding first!
}
```

Overrides still must pass validation (encoding, noun, concrete). Run `python trainer/generator.py` after editing to regenerate.

To block inappropriate words, add them to `BLOCKED_WORDS` in `trainer/generator.py`.

## CLI Lookup

To look up candidates for a number or check a word's encoding:

```bash
python scripts/lookup.py 47       # number -> show candidate words
python scripts/lookup.py roof     # word -> show its number + checks
```

## Project Structure

```
memorization-major-system/
├── config/
│   ├── settings.py         # Django settings (SQLite, static files, auth)
│   ├── urls.py             # Root URL config (includes trainer.urls)
│   └── wsgi.py             # WSGI entry point for gunicorn
├── trainer/
│   ├── generator.py        # Word selection + validation logic
│   ├── validator.py        # CMU phoneme → Major System digit encoding
│   ├── models.py           # QuizState model (per-user/IP quiz state)
│   ├── views.py            # API views, auth views, index
│   └── urls.py             # Route definitions
├── tests/
│   ├── test_associations.py  # Wordlist validation (4 tests × 100 subtests)
│   ├── test_api.py           # API + auth integration tests
│   ├── test_persistence.py   # JS persistence tests (Node.js harness)
│   ├── test_pool_quiz.py     # Quiz logic tests
│   └── test_theme.py         # Theme contrast/luminance tests
├── scripts/
│   └── lookup.py           # CLI tool for number/word lookups
├── src/
│   ├── ts/                  # TypeScript source (8 modules)
│   └── scss/                # SCSS source (10 partials)
├── templates/
│   └── login.html          # Login/register page
├── static/
│   ├── js/app.js           # Built JS bundle (gitignored)
│   └── css/app.css         # Built CSS (gitignored)
├── manage.py               # Django management command entry point
├── wordlist.json           # Generated 00–99 mappings
├── requirements.txt        # Python dependencies
├── deploy.sh               # VPS deployment (migrate, collectstatic, restart)
└── docs/                   # This documentation
```
