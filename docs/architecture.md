# Architecture

The system follows a **generate-then-serve** pattern: Python modules produce a validated wordlist offline, a Django app serves it via gunicorn behind nginx, and a vanilla JS frontend provides the training UI with offline-first state management.

## Contents

- [System Overview](#system-overview)
- [Module Dependency Graph](#module-dependency-graph)
- [Data Flow](#data-flow)
- [Phoneme-to-Digit Mapping](#phoneme-to-digit-mapping)
- [Word Selection Pipeline](#word-selection-pipeline)
- [Validation Pipeline](#validation-pipeline)
- [Django App](#django-app)
- [Frontend](#frontend)
- [Key Takeaways](#key-takeaways)

## System Overview

```
┌──────────────────────────────────────────────────────┐
│                   WORDNET (NLTK)                     │
└──────────────┬───────────────────────────────────────┘
               │ get_concrete_nouns()
               ▼
┌──────────────────────────────────────────────────────┐
│  generator.py                                        │
│  ├─ build_candidate_map() ← word_to_digits() [CMU]  │
│  ├─ select_best_word()                               │
│  └─ validate_and_fix()                               │
└──────────────┬───────────────────────────────────────┘
               │ wordlist.json
               ▼
┌──────────────────────────────────────────────────────┐
│  Django (config/ + trainer/)                         │
│  ├─ GET /api/wordlist → JSON                         │
│  ├─ GET /api/mapping  → JSON                         │
│  ├─ GET/POST /api/state → quiz state per user/IP     │
│  ├─ GET /             → index.html                   │
│  └─ /login/ /register/ /logout/ → user auth          │
└──────────────┬───────────────────────────────────────┘
               │ gunicorn + nginx (port 8734)
               ▼
┌──────────────────────────────────────────────────────┐
│  templates/index.html (SPA, offline-first)            │
│  ├─ Grid view (10×10, color-coded mastery)           │
│  ├─ Quiz: number → word                              │
│  ├─ Quiz: word → number                              │
│  ├─ Quiz: mixed (random direction)                   │
│  ├─ Quiz: sound → digit (consonant quiz)             │
│  ├─ Translate section                                │
│  └─ Reference table                                  │
└──────────────────────────────────────────────────────┘
```

Three distinct layers with minimal coupling:

| Layer | File(s) | Responsibility |
|-------|---------|----------------|
| **Encoding** | `validator.py` | CMU phoneme lookup, digit conversion |
| **Generation** | `generator.py` | WordNet nouns, candidate selection, validation, persistence |
| **Serving** | `config/`, `trainer/`, `templates/index.html`, `src/ts/`, `src/scss/` | Django app, API endpoints, auth, browser UI |

## Module Dependency Graph

```
cmudict (external)
  └─► validator.py
        └─► generator.py ◄── nltk/wordnet (external)
              └─► trainer/views.py ◄── django

config/settings.py ◄── django config
config/urls.py     ◄── includes trainer/urls.py
trainer/models.py  ◄── QuizState (SQLite)
trainer/views.py   ◄── generator, validator, models

test_associations.py ◄── validator, generator, nltk, unittest
test_pool_quiz.py    ◄── standalone JS logic replica
test_api.py          ◄── django.test (API + auth integration)
test_persistence.py  ◄── node.js harness (JS persistence logic)
```

- `validator.py` has no project-internal dependencies — pure encoding logic.
- `generator.py` depends on `validator` for encoding checks.
- `trainer/views.py` imports from both for startup loading.
- Test files are independent of the running server.

## Data Flow

### Generation (offline, one-time)

```
WordNet corpus
  → physical_entity.n.01 hyponym closure (~27k nouns)
  → filter: single-word, alphabetic, has vowel, not blocked
  → CMU pronunciation lookup → encode to digits
  → keep only 2-digit encodings
  → group by digit pair → {"00": ["sis","sea",...], "01": ["set","sat",...], ...}
  → select shortest word per group
  → validate each: encoding ✓, noun ✓, concrete ✓
  → persist to wordlist.json
```

### Serving (runtime)

```
Browser GET /             →  index.html (served by Django view)
Browser GET /api/wordlist →  {"00":"sis","01":"set",...}  (from memory)
Browser GET /api/mapping  →  {"0":"S, Z","1":"T, D, TH",...}  (constant)
Browser GET /api/state    →  quiz state (per user or IP)
Browser POST /api/state   →  save quiz state to server
```

The wordlist is loaded into a module-level global at app startup. Quiz state is stored in SQLite via the `QuizState` model.

### Startup Validation (fail-fast)

On every app start, `load_or_generate_wordlist()` (`generator.py`) runs:

1. If `wordlist.json` exists: load it and do a **quick encoding check** (CMU dict only, fast)
2. If any entry is missing or mis-encoded: run **full validation** (WordNet noun + concreteness check), auto-replace broken entries, save repaired file
3. If `wordlist.json` is missing: generate from scratch, validate, save

This ensures the served data is always valid without requiring manual intervention.

## Phoneme-to-Digit Mapping

The core encoding in `validator.py:15-26`:

| Digit | CMU Phonemes | Sounds |
|-------|-------------|--------|
| 0 | S, Z | S as in "sun", Z as in "zoo" |
| 1 | T, D, TH, DH | T as in "top", D as in "dog", TH as in "math" |
| 2 | N | N as in "net" |
| 3 | M | M as in "map" |
| 4 | R | R as in "run" |
| 5 | L | L as in "lid" |
| 6 | CH, JH, SH, ZH | CH as in "chin", J as in "jet", SH as in "ship" |
| 7 | K, G, NG | K as in "key", G as in "go", NG as in "ring" |
| 8 | F, V | F as in "fan", V as in "van" |
| 9 | P, B | P as in "pen", B as in "bat" |

**Ignored:** All vowels (AA, AE, AH, AO, AW, AY, EH, ER, EY, IH, IY, OW, OY, UH, UW), plus HH, W, Y.

**Example:** "cage" → CMU `K EY1 JH` → K=7, EY1=ignored, JH=6 → **"76"**

Stress markers (0/1/2 suffixes on vowels) are stripped before lookup (`validator.py:54`).

## Word Selection Pipeline

### Step 1: Collect concrete nouns (`generator.py:62-83`)

```python
physical_entity = wn.synset('physical_entity.n.01')
concrete_synsets = set(physical_entity.closure(lambda s: s.hyponyms()))
```

Uses WordNet's hyponym closure — traverses downward from `physical_entity.n.01` to collect all concrete noun synsets. Then extracts lemma names with filters:

- No underscores (no multi-word phrases)
- Alphabetic only
- Length > 1
- Must contain a vowel (filters abbreviations like "FBI")
- Not in `BLOCKED_WORDS` (slurs, abbreviations like "atm", "rna")

Yields ~27k candidate nouns.

### Step 2: Build candidate map (`generator.py:96-103`)

Each noun is encoded via `word_to_digits()`. Only nouns with exactly 2-digit encodings are kept, grouped by their digit pair.

### Step 3: Select best word (`generator.py:106-108`)

```python
def select_best_word(candidates):
    return sorted(candidates, key=lambda w: (len(w), w))[0]
```

Deterministic: shortest word wins, alphabetical tiebreaker. No randomness in final selection.

### Step 4: Blocked words (`generator.py:23`)

`BLOCKED_WORDS` set excludes offensive, abbreviated, or unsuitable words. Custom associations are set per-user via the grid UI, not in the generator.

## Validation Pipeline

Three levels of validation, in increasing depth:

### Quick check (app startup)
- For each 00–99: is the word non-null and does `word_to_digits(word)` match?
- Only uses CMU dict — fast (~1 second for all 100)

### Full validation (`generator.py:152-191`)
Triggered only when quick check finds issues. For each entry, checks in order:
1. **Not null** — entry exists
2. **Encoding match** — `word_to_digits(word) == digits`
3. **Noun status** — word has at least one NOUN synset in WordNet
4. **Concreteness** — at least one noun synset traces to `physical_entity.n.01`

Each failure triggers `_try_replace()` which picks the next-best candidate from the pool.

### Test suites

**test_associations.py** — independent validation with 4 test methods, each iterating all 100 entries via `subTest()`:
- `test_all_numbers_covered` — no nulls
- `test_all_words_are_nouns` — WordNet noun check
- `test_all_encodings_match` — CMU encoding check
- `test_all_words_are_concrete` — hypernym chain to `physical_entity.n.01`

**test_pool_quiz.py** — tests verifying score-based quiz logic (Python replica of JS):
- Score-based selection, cooldown history, pick distribution

**test_api.py** — Django integration tests for API endpoints and auth:
- Wordlist/mapping endpoints, state GET/POST, login/register/logout

**test_persistence.py** — Node.js harness testing JS persistence logic:
- saveState/loadState round-trips, localStorage format

## Django App

The server uses Django with gunicorn behind nginx (port 8734 in production).

### Routes (`trainer/urls.py`)

| Route | View | Response |
|-------|------|----------|
| `/` | `index_view` | Renders `templates/index.html` via Django template rendering with CSRF cookie |
| `/api/wordlist` | `wordlist_view` | Wordlist JSON (100 entries) |
| `/api/mapping` | `mapping_view` | Digit-to-sounds reference |
| `/api/state` | `state_view` | GET: load quiz state; POST: save quiz state |
| `/login/` | `login_view` | Login form (GET) or authenticate (POST) |
| `/register/` | `register_view` | Create account + merge IP state |
| `/logout/` | `logout_view` | End session |

### QuizState Model (`trainer/models.py`)

Stores quiz state per user (authenticated) or per IP (anonymous):

- `user` — OneToOneField to User (nullable for anonymous)
- `ip_address` — GenericIPAddressField (for anonymous tracking)
- `score_correct`, `score_total` — overall score counters
- `quiz_scores`, `quiz_history` — forward quiz state (JSONField)
- `reverse_scores`, `reverse_history` — reverse quiz state
- `mixed_scores`, `mixed_history` — mixed quiz state
- `con_scores`, `con_history` — consonant quiz state
- `theme` — dark/light/oled/high-contrast preference
- `updated_at` — auto-updated timestamp

On registration, IP-based state is merged into the new user account.

## Frontend

`templates/index.html` is a Django-served SPA. TypeScript source in `src/ts/` is compiled via esbuild into `static/js/app.js`; SCSS in `src/scss/` is compiled via sass into `static/css/app.css`. Build step: `npm run build`. Offline-first: loads from localStorage immediately, syncs to server in background.

### State

All state is consolidated into two TypeScript objects in `src/ts/state.ts`:

```typescript
// Shared app state (src/ts/state.ts)
export const appState: AppState = {
  wordlist: {},              // {"00":"sis",...} merged default + custom
  defaultWordlist: {},       // from /api/wordlist
  customWords: {},           // user overrides per digit pair
  mapping: {},               // {"0":"S, Z",...} from /api/mapping
  keys: [],                  // sorted digit pair keys
  score: { correct: 0, total: 0 },
  timedQuiz: false,
  tutorialSeen: false,
  conKeys: [],
  conMap: {},
  dyslexiaFont: false,
};

// Per-quiz-mode config and state (src/ts/state.ts)
export const MODES: AllModes = {
  quiz:      { scores: {}, history: [], current: null, ... },
  reverse:   { scores: {}, history: [], current: null, ... },
  mixed:     { scores: {}, history: [], current: null, ... },
  consonant: { scores: {}, history: [], current: null, ... },
};
```

Persistence uses a `STATE_FIELDS` manifest -- add new persisted fields there, not in saveState/loadState individually.

State persists across page refreshes via localStorage. On each state change, `saveState()` writes to localStorage and fire-and-forget POSTs to `/api/state`.

### Score-Based Quiz System

All quiz modes use **score-based selection with cooldown** instead of random picks. This focuses practice on weaker items.

**Selection algorithm (`pickNext()`):**
1. Exclude keys in the history array (last 10 shown — cooldown)
2. Find the minimum score among eligible keys
3. Collect all keys with that minimum score
4. Pick one randomly from that group

**Scoring:**
- Correct answer: score increments (+1)
- Incorrect: score decrements (-1); Skip: no score change, but added to history cooldown
- Scores start at 0 for all keys

**Feedback:** Shows correct/incorrect status. Does not display individual scores.

### Mastery Grid

Grid cells are color-coded based on combined scores across all quiz modes:

| Combined Score | Class | Color |
|----------------|-------|-------|
| <= -3 | `mastery-0` | Red |
| < 0 | `mastery-1` | Orange |
| <= 3 | `mastery-2` | Neutral (default) |
| <= 8 | `mastery-3` | Yellow-green |
| > 8 | `mastery-4` | Green |

### Offline-First Init

```
1. Load wordlist/mapping from localStorage (cached from last fetch)
2. Load quiz state from localStorage
3. Render immediately with cached data
4. Background fetch: /api/wordlist, /api/mapping, /api/state
5. If server state has higher score.total → apply server state
6. Re-render with fresh data
```

### Sections

Five tabs: **Grid** (10x10 color-coded display), **Quiz** (subnav with four modes: # -> Word, Word -> #, Mixed, Sound -> #), **Reference** (digit-to-sound table), **Translate**. Switching tabs via `showSection()` toggles CSS `display` and auto-starts quiz modes.

### Answer Checking

- Exact match, case-insensitive
- Reverse mode accepts "7" or "07" for "07"
- Auto-advance to next question after 1800ms

## Key Takeaways

1. **Phoneme-based, not letter-based.** The CMU Pronouncing Dictionary ensures "knife" encodes as 28 (N+F), not 728 (K+N+F). This is the core correctness guarantee.
2. **Concrete nouns only.** Every word must trace to `physical_entity.n.01` in WordNet's hypernym graph — no abstract concepts.
3. **Self-healing wordlist.** The server validates on startup and auto-repairs invalid entries. You can delete `wordlist.json` and it regenerates automatically.
4. **Deterministic generation.** Same WordNet + CMU dict → same wordlist every time. No randomness in the selection algorithm.
5. **Offline-first frontend.** Loads cached data from localStorage immediately, then syncs with the server in the background. Works even when the server is unreachable.
6. **Server-side state persistence.** Quiz state is stored in SQLite via Django's `QuizState` model — per user (authenticated) or per IP (anonymous). State merges on registration.
7. **Score-based quiz selection.** Each quiz type tracks per-key scores. The next question targets the lowest-scoring eligible key, with a 10-key cooldown to prevent consecutive repeats.
