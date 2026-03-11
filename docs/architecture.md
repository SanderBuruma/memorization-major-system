# Architecture

The system follows a **generate-then-serve** pattern: Python modules produce a validated wordlist offline, a lightweight HTTP server serves it, and a vanilla JS frontend provides the training UI.

## Contents

- [System Overview](#system-overview)
- [Module Dependency Graph](#module-dependency-graph)
- [Data Flow](#data-flow)
- [Phoneme-to-Digit Mapping](#phoneme-to-digit-mapping)
- [Word Selection Pipeline](#word-selection-pipeline)
- [Validation Pipeline](#validation-pipeline)
- [HTTP Server](#http-server)
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
│  server.py                                           │
│  ├─ GET /api/wordlist → JSON                         │
│  ├─ GET /api/mapping  → JSON                         │
│  └─ GET /             → index.html                   │
└──────────────┬───────────────────────────────────────┘
               │ HTTP (localhost:8080)
               ▼
┌──────────────────────────────────────────────────────┐
│  static/index.html (SPA)                             │
│  ├─ Grid view (10×10)                                │
│  ├─ Quiz: number → word                              │
│  ├─ Quiz: word → number                              │
│  └─ Reference table                                  │
└──────────────────────────────────────────────────────┘
```

Three distinct layers with minimal coupling:

| Layer | File(s) | Responsibility |
|-------|---------|----------------|
| **Encoding** | `validator.py` | CMU phoneme lookup, digit conversion |
| **Generation** | `generator.py` | WordNet nouns, candidate selection, validation, persistence |
| **Serving** | `server.py`, `static/index.html` | HTTP endpoints + browser UI |

## Module Dependency Graph

```
cmudict (external)
  └─► validator.py
        └─► generator.py ◄── nltk/wordnet (external)
              └─► server.py ◄── http.server (stdlib)

test_associations.py ◄── validator, generator, nltk, unittest
```

- `validator.py` has no project-internal dependencies — pure encoding logic.
- `generator.py` depends on `validator` for encoding checks.
- `server.py` depends on both for startup loading.
- `test_associations.py` imports from all modules but is fully independent of the server.

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
Browser GET /  →  index.html (static)
Browser GET /api/wordlist  →  {"00":"sis","01":"set",...}  (from memory)
Browser GET /api/mapping   →  {"0":"S, Z","1":"T, D, TH",...}  (constant)
```

The wordlist is loaded into a module-level global at server startup. No database, no runtime generation.

### Startup Validation (fail-fast)

On every server start, `load_or_generate_wordlist()` (`generator.py:206`) runs:

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

### Step 4: Manual overrides (`generator.py:24`)

`MANUAL_OVERRIDES` dict (currently empty) is checked before automatic selection. Allows human curation of specific entries while still requiring them to pass validation.

## Validation Pipeline

Three levels of validation, in increasing depth:

### Quick check (server startup, `generator.py:213-222`)
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

**test_pool_quiz.py** — 25 tests verifying pool-based quiz logic (Python replica of JS):
- Pool init, replacement, pick, streak graduation, recycle-at-80, full simulation

## HTTP Server

`server.py` uses `http.server.SimpleHTTPRequestHandler` (stdlib) with custom routing:

| Route | Handler | Response |
|-------|---------|----------|
| `/api/wordlist` | `_json_response()` | Wordlist JSON (100 entries) |
| `/api/mapping` | `_json_response()` | Digit-to-sounds reference |
| `/` | Rewrite → `/index.html` | HTML frontend |
| `/*` | `SimpleHTTPRequestHandler` | Static files from `static/` |

No frameworks. No CORS (same-origin). No caching headers. Synchronous request handling.

## Frontend

`static/index.html` is a self-contained SPA (inline CSS + JS, no build step).

### State

```javascript
let wordlist = {};              // {"00":"sis",...} from /api/wordlist
let mapping  = {};              // {"0":"S, Z",...} from /api/mapping
let score    = {correct:0, total:0};  // session score
let currentQuiz    = null;      // {digits, word} for active quiz
let currentReverse = null;      // {digits, word} for active reverse quiz

// Pool-based quiz state (independent per quiz type)
let quizPool = [];              // 10 active keys for forward quiz
let quizStreaks = {};           // key → consecutive correct count
let quizMastered = {};          // key → true when graduated
let reversePool = [];           // same for reverse quiz
let reverseStreaks = {};
let reverseMastered = {};
```

Score is ephemeral — resets on page refresh. Pool state also resets on refresh (not persisted to localStorage).

### Pool-Based Quiz System (Spaced Repetition)

Both quiz modes use a **pool of 10 active words** instead of picking randomly from all 100. This ensures focused repetition for mastery.

**Pool lifecycle:**
1. On first quiz start, `initPool()` picks 10 random keys (Fisher-Yates shuffle)
2. `pickFromPool()` selects a random word from the pool, avoiding the last-shown word
3. On correct answer: increment streak counter for that word
4. **Graduation:** 3 consecutive correct answers → word is mastered, removed from pool, replaced by a new unmastered word via `replaceInPool()`
5. On incorrect or skip: streak resets to 0, word stays in pool
6. **Recycle at 80:** when 80 words are mastered, 1 random mastered word gets recycled back (unmastered, streak reset) — keeps the quiz cycling indefinitely
7. Pool persists across tab switches (module-level state)

**Helper functions:**
- `initPool(mastered)` — pick 10 random unmastered keys
- `replaceInPool(pool, masteredKey, mastered)` — swap graduated key for a fresh one
- `pickFromPool(pool, lastKey)` — random pick avoiding consecutive repeats

### Answer Checking

- Exact match, case-insensitive
- Reverse mode accepts "7" or "07" for "07"
- Feedback shows streak progress ("streak: 2/3") or mastery status ("Mastered (45/80)")
- Auto-advance to next question after 1800ms

### Sections

Four tabs: **Grid** (10×10 display), **Quiz →** (number→word), **← Reverse** (word→number), **Reference** (digit-to-sound table). Switching tabs via `showSection()` toggles CSS `display` and auto-starts quiz modes.

## Key Takeaways

1. **Phoneme-based, not letter-based.** The CMU Pronouncing Dictionary ensures "knife" encodes as 28 (N+F), not 728 (K+N+F). This is the core correctness guarantee.
2. **Concrete nouns only.** Every word must trace to `physical_entity.n.01` in WordNet's hypernym graph — no abstract concepts.
3. **Self-healing wordlist.** The server validates on startup and auto-repairs invalid entries. You can delete `wordlist.json` and it regenerates automatically.
4. **Deterministic generation.** Same WordNet + CMU dict → same wordlist every time. No randomness in the selection algorithm.
5. **Frontend is stateless.** All quiz logic runs client-side. The server is a static data provider with two JSON endpoints.
6. **Pool-based spaced repetition.** Each quiz type maintains an independent pool of 10 active words. Words graduate after 3 consecutive correct answers. At 80 mastered, 1 random word gets recycled back — the quiz never "finishes".
