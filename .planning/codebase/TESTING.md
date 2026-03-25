# Testing Patterns

**Analysis Date:** 2026-03-25

## Test Framework

**Runner:**
- **Python:** Django TestCase via `python manage.py test --no-input`
- **JavaScript/TypeScript:** Custom Node.js harness (`tests/js_harness.py`)
  - Runs esbuild-compiled bundle in Node.js
  - Provides localStorage mock and minimal DOM stubs
  - Invoked from Python test classes via `run_js_tests()`

**Assertion Library:**
- Python: Django TestCase assertions (`assertEqual`, `assertTrue`, `assertIsNone`, etc.)
- JavaScript: Manual throw-based assertions in test code

**Run Commands:**
```bash
npm run check              # Typecheck and build (test prerequisite)
python manage.py test --no-input  # Run all Django + JS tests
pytest tests/ -v          # Alternative: run via pytest (delegates to manage.py test)
```

**CI/CD:**
GitHub Actions (`.github/workflows/deploy.yml`):
- Node 22: `npm ci` → `npm run check` (typecheck + build)
- Python 3.13: `pip install -r requirements.txt` → `python manage.py test --no-input`
- Fails if any test fails; deploy only on success

## Test File Organization

**Location:**
- Python: `tests/` directory, separate from source
- JavaScript: Embedded in Python test files (test code as string literals)
- Shared infrastructure: `tests/js_harness.py` (Node harness + localStorage mock)

**Naming:**
- `test_<module>.py` (e.g., `test_api.py`, `test_persistence.py`)
- No file naming pattern for JS tests (inline as JSON test specs)

**Structure:**
```
tests/
├── __init__.py
├── js_harness.py           # Shared Node.js harness + DOM stubs
├── test_api.py             # Django API endpoints (wordlist, mapping, state)
├── test_encode.py          # /api/encode endpoint
├── test_persistence.py     # saveState/loadState (JS tests via harness)
├── test_theme.py           # Theme switching (JS tests via harness)
├── test_tutorial.py        # Onboarding flow (JS tests via harness)
├── test_dyslexia_font.py   # Font loading (JS tests via harness)
├── test_aria.py            # ARIA attributes (JS tests via harness)
├── test_pool_quiz.py       # Quiz mode selection logic
├── test_associations.py    # Word-to-digit encoding
├── test_candidates.py      # Candidate suggestion API
├── test_constants.py       # Math constants
└── test_wiki_data.py       # Reference wiki content
```

## Test Structure

**Python Django Test Suite:**
```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.test import TestCase
import json

class TestWordlistAPI(TestCase):
    def test_wordlist_returns_110_entries(self):
        resp = self.client.get('/api/wordlist')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 110)

    def test_wordlist_keys_include_single_and_double_digits(self):
        resp = self.client.get('/api/wordlist')
        data = resp.json()
        expected_keys = {str(i) for i in range(10)} | {f"{i:02d}" for i in range(100)}
        self.assertEqual(set(data.keys()), expected_keys)
```

**JavaScript Test Suite (via harness):**
```python
class TestSaveLoadRoundTrip(unittest.TestCase):
    """saveState() writes to localStorage, loadState() restores from it."""

    def test_empty_state_round_trips(self):
        """Default empty state survives save/load cycle."""
        results = _run_js_tests([{
            "name": "empty_round_trip",
            "code": """
                saveState();
                var saved = JSON.parse(localStorage.getItem('quizState'));
                if(!saved) throw new Error('nothing saved');
                if(saved.score.correct !== 0) throw new Error('score.correct not 0');
                if(saved.score.total !== 0) throw new Error('score.total not 0');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))
```

**Patterns:**

1. **Setup:** No explicit setUp() in most tests; Django creates fresh database per test class
2. **Assertions:** One assertion per test method (clear intent)
3. **Test naming:** `test_<what_is_being_tested>` or `test_<action>_<expected_result>`
4. **Teardown:** Implicit (Django cleans up database after each test)

## Mocking

**Framework:** No explicit mocking library used

**DOM Stubs (JavaScript):**
Located in `tests/js_harness.py`, provided to Node.js test environment:

```javascript
var _store = {};
var localStorage = {
  getItem: function(k){ return _store[k] || null; },
  setItem: function(k,v){ _store[k] = v; },
  removeItem: function(k){ delete _store[k]; },
  clear: function(){ _store = {}; }
};

var _stubEl = {
  textContent: '',
  value: '',
  innerHTML: '',
  disabled: false,
  className: '',
  style: {},
  focus: function(){},
  appendChild: function(){},
  addEventListener: function(){},
  classList: {
    add: function(c){...},
    remove: function(c){...},
    toggle: function(c, force){...},
    contains: function(c){...}
  },
  ...
};

var document = {
  getElementById: function(){ return _stubEl; },
  querySelectorAll: function(){ return {forEach: function(){}}; },
  querySelector: function(){ return _stubEl; },
  createElement: function(){ return Object.create(_stubEl); },
  documentElement: {getAttribute: function(){return 'dark';}, setAttribute: function(){}},
  cookie: '',
  body: _stubEl
};

var window = {};
var performance = {now: function(){return 0;}};
```

**HTTP Requests (Python):**
Django TestCase provides `self.client` (test HTTP client):
```python
resp = self.client.post('/api/encode', data=json.dumps({'text': text}), content_type='application/json')
```

**HTTP Mocking (JavaScript):**
Window `fetch` mocked in harness:
```javascript
var fetch = function(){ return Promise.resolve({ok:true, json:function(){return Promise.resolve({})}}); };
```

**What to Mock:**
- localStorage ✓ (provides persistence isolation)
- DOM elements ✓ (avoid real DOM operations in headless tests)
- fetch ✓ (avoid real API calls during unit tests)
- setTimeout/clearTimeout ✓ (avoid timing issues)

**What NOT to Mock:**
- appState object ✗ (test state directly)
- Quiz mode functions ✗ (test real quiz logic)
- Core business logic (encoding, validation) ✗

## Fixtures and Factories

**Test Data:**
No dedicated fixture files. Data created inline:

**Python API tests:**
```python
payload = {
    'score': {'correct': 5, 'total': 10},
    'quizScores': {'42': 3},
    'quizHistory': [1, 0, 1],
    'reverseScores': {'07': 2},
    'reverseHistory': [1, 1],
}
```

**JavaScript tests:**
```javascript
MODES.quiz.scores = {'03': 5, '17': -2, '42': 0};
MODES.quiz.history = ['03','17','42'];
MODES.reverse.scores = {'02': -1};
```

**Location:**
- Inline in test methods (no factory pattern)
- Constants reused across tests when stable (e.g., wordlist from API)

## Coverage

**Requirements:** Not enforced

**View Coverage:**
```bash
# No coverage command configured; coverage data not tracked
```

## Test Types

**Unit Tests:**
- **Scope:** Individual functions/modules in isolation
- **Approach:** Direct function calls with known inputs; verify outputs and side effects
- Examples: `test_associations.py` (word_to_digits), `test_encode.py` (API endpoint)

**Integration Tests:**
- **Scope:** APIs + database interactions
- **Approach:** Full HTTP request → database state → response verification
- Examples: `test_api.py` (state roundtrip), `test_persistence.py` (localStorage ↔ appState)

**E2E Tests:**
- **Framework:** Not used
- **Alternative:** CI/CD deploys to VPS; manual testing on production

## Common Patterns

**Async Testing (JavaScript):**
Test code runs synchronously in Node harness; async operations (fetch, setTimeout) are mocked:
```javascript
// Timers are stubbed — no actual waiting
setTimeout(function() { ... }, 1000);  // Executes immediately in test

// fetch is stubbed to return resolved Promise
fetch('/api/state').then(...).catch(...);  // Returns immediately with mock data
```

**Error Testing:**
```python
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
```

**State Roundtrip Testing (JS + Python):**
```python
def test_score_persists(self):
    """Verify appState.score survives localStorage cycle."""
    results = _run_js_tests([{
        "name": "score_persists",
        "code": """
            appState.score = {correct: 7, total: 12};
            saveState();
            appState.score = {correct: 0, total: 0};
            loadState();
            if(appState.score.correct !== 7) throw new Error('...');
        """,
    }])
    self.assertTrue(results[0]["pass"], results[0].get("error"))
```

**Database State Verification:**
```python
def test_post_and_get_roundtrip(self):
    payload = {...}
    post_resp = self.client.post('/api/state', data=json.dumps(payload), ...)
    self.assertEqual(post_resp.status_code, 200)
    self.assertTrue(post_resp.json().get('ok'))

    get_resp = self.client.get('/api/state')
    data = get_resp.json()
    self.assertEqual(data['score']['correct'], 5)
    self.assertEqual(data['quizScores'], {'42': 3})
```

## Test Execution Flow

**Local Development:**
```bash
npm run check              # Builds TypeScript/CSS; errors block tests
python manage.py test     # Runs Django tests (includes JS tests via harness)
```

**CI/CD:**
```yaml
# .github/workflows/deploy.yml
- run: npm ci
- run: npm run check       # Typecheck failure = stop here
- run: pip install -r requirements.txt
- run: python manage.py test --no-input  # pytest/Django failure = stop here
# If all pass: deploy to VPS
```

---

*Testing analysis: 2026-03-25*
