# File Reference

Every source file with line counts, key sections, and function locations.

## validator.py (82 lines)

Pure encoding logic. No side effects, no file I/O.

| Line | Symbol | Description |
|------|--------|-------------|
| 6 | `_CMU_DICT` | Module-level CMU dictionary load (cached) |
| 15–26 | `PHONEME_TO_DIGIT` | Dict mapping 17 CMU consonant phonemes → digits 0–9 |
| 29–40 | `DIGIT_TO_SOUNDS` | Human-readable digit → consonant sounds reference |
| 43–57 | `phonemes_to_digits(phoneme_list)` | Convert list of CMU phonemes to digit string |
| 60–69 | `word_to_digits(word)` | Look up word in CMU dict, return digit encoding or None |
| 72–77 | `word_to_phonemes(word)` | Return first CMU pronunciation for a word, or None |
| 80–82 | `number_to_digits(number)` | Zero-pad integer to 2-digit string |

## generator.py (284 lines)

Word selection, validation, and persistence. Main workhorse module.

| Line | Symbol | Description |
|------|--------|-------------|
| 20 | `WORDLIST_PATH` | Path to `wordlist.json` (sibling to this file) |
| 23 | `BLOCKED_WORDS` | Set of excluded words (slurs, abbreviations) |
| 34–43 | `ensure_nltk_data()` | Download WordNet + OMW data if missing |
| 46–59 | `is_concrete_noun_synset(synset)` | BFS: does synset trace to `physical_entity.n.01`? |
| 62–83 | `get_concrete_nouns()` | Extract ~27k filtered concrete nouns from WordNet |
| 86–88 | `is_word_noun(word)` | Check if word has any NOUN synset |
| 91–93 | `is_word_concrete(word)` | Check if any noun synset is concrete |
| 96–103 | `build_candidate_map(nouns)` | Group nouns by their 2-digit encoding |
| 106–108 | `select_best_word(candidates)` | Pick shortest word, alphabetical tiebreak |
| 111–149 | `generate_wordlist(seed=42)` | Main generation: nouns → candidates → selection |
| 152–191 | `validate_and_fix(wordlist)` | Check all entries, auto-replace invalid ones |
| 194–203 | `_try_replace(wordlist, digits, candidates, bad_word)` | Replace one bad entry from candidate pool |
| 206–235 | `load_or_generate_wordlist()` | Load from disk or generate; quick-check + repair |
| 238–242 | `save_wordlist(wordlist)` | Write wordlist.json (sorted, indented) |
| 245+ | `__main__` block | CLI entry point: generate, validate, save, report |

## config/settings.py (65 lines)

Django settings. SQLite database, session auth, static file serving.

| Line | Symbol | Description |
|------|--------|-------------|
| 4 | `BASE_DIR` | Project root |
| 6 | `SECRET_KEY` | From env `DJANGO_SECRET_KEY` (fallback for dev) |
| 8 | `DEBUG` | From env `DJANGO_DEBUG` (default off) |
| 10 | `ALLOWED_HOSTS` | From env `DJANGO_ALLOWED_HOSTS` |
| 12–20 | `INSTALLED_APPS` | Includes `trainer` app |
| 50–55 | `DATABASES` | SQLite at `db.sqlite3` |
| 57–59 | Static file config | `STATIC_URL`, `STATICFILES_DIRS`, `STATIC_ROOT` |

## config/urls.py (10 lines)

Root URL config. Includes `trainer.urls` at `/`. Serves static files in DEBUG mode.

## config/wsgi.py (7 lines)

WSGI entry point for gunicorn.

## trainer/models.py (22 lines)

| Line | Symbol | Description |
|------|--------|-------------|
| 5–22 | `QuizState` | Per-user/IP quiz state model |
| 6 | `user` | OneToOneField to User (nullable) |
| 7 | `ip_address` | GenericIPAddressField (anonymous tracking) |
| 9–10 | `score_correct`, `score_total` | Overall score counters |
| 12–19 | Quiz JSONFields | `quiz_scores/history`, `reverse_scores/history`, `mixed_scores/history`, `con_scores/history` |
| 21 | `theme` | dark/light/oled/high-contrast preference |
| 22 | `updated_at` | Auto-updated timestamp |

## trainer/views.py (160 lines)

Django views for API endpoints and auth.

| Line | Symbol | Description |
|------|--------|-------------|
| 16–17 | `_wordlist`, `_mapping` | Module-level globals, populated at import |
| 20–24 | `get_client_ip(request)` | Extract client IP (X-Forwarded-For aware) |
| 27–33 | `get_quiz_state(request)` | Get or create QuizState for user or IP |
| 36–39 | `index_view(request)` | Render `templates/index.html` via Django template rendering with CSRF cookie |
| 42–44 | `wordlist_view(request)` | Return wordlist JSON |
| 47–49 | `mapping_view(request)` | Return digit-to-sounds JSON |
| 58–114 | `state_view(request)` | GET: return quiz state; POST: update quiz state |
| 117–127 | `login_view(request)` | Render login form or authenticate |
| 130–154 | `register_view(request)` | Create user, merge IP-based state |
| 157–160 | `logout_view(request)` | End session, redirect |

## trainer/urls.py (12 lines)

| Route | View | Description |
|-------|------|-------------|
| `/` | `index_view` | Frontend SPA |
| `/api/wordlist` | `wordlist_view` | Wordlist JSON |
| `/api/mapping` | `mapping_view` | Digit-to-sounds JSON |
| `/api/state` | `state_view` | Quiz state GET/POST |
| `/login/` | `login_view` | Login page |
| `/register/` | `register_view` | Registration |
| `/logout/` | `logout_view` | Logout |

## manage.py (20 lines)

Django management command entry point. Standard boilerplate.

## templates/login.html (148 lines)

Login and registration form page. Styled to match the SPA theme. Shows login form by default, registration form below.

## lookup.py (138 lines)

CLI tool for looking up Major System associations.

| Line | Symbol | Description |
|------|--------|-------------|
| 24–28 | `load_wordlist()` | Load wordlist.json |
| 31–79 | `lookup_number(digits)` | Show all candidate words for a 2-digit number |
| 82–119 | `lookup_word(word)` | Show number, phonemes, noun/concrete status for a word |
| 122–138 | `main()` | CLI entry point |

## test_associations.py (115 lines)

Unittest suite, runnable independently of the server.

| Line | Symbol | Description |
|------|--------|-------------|
| 22–111 | `TestMajorSystemAssociations` | Test class with 4 test methods |
| 25–33 | `setUpClass()` | Load NLTK data + wordlist (from file or generated) |
| 39–47 | `test_all_numbers_covered()` | All 100 entries exist and are non-null |
| 53–66 | `test_all_words_are_nouns()` | Every word is a noun in WordNet |
| 72–89 | `test_all_encodings_match()` | Every word's CMU encoding matches its number |
| 95–111 | `test_all_words_are_concrete()` | Every word traces to `physical_entity.n.01` |

## test_pool_quiz.py (235 lines)

Tests for the score-based quiz system. Replicates the JS quiz logic in Python and statistically verifies correctness.

## test_api.py (249 lines)

Django integration tests for API endpoints and auth flows.

| Symbol | Description |
|--------|-------------|
| `TestWordlistAPI` | Wordlist endpoint returns 100 two-digit keyed entries |
| `TestMappingAPI` | Mapping endpoint returns 10 single-digit keyed entries |
| `TestStateAPI` | State GET/POST for authenticated and anonymous users |
| `TestAuthViews` | Login, register, logout flows; IP state merging |

## test_persistence.py (423 lines)

Tests for JS localStorage persistence logic. Runs the esbuild bundle in Node.js with a localStorage mock (via shared `tests/js_harness.py`) and verifies saveState/loadState round-trips.

## templates/index.html

Django-served SPA. External JS bundle (`static/js/app.js`) and CSS bundle (`static/css/app.css`) compiled from `src/ts/` and `src/scss/` via esbuild and sass. Offline-first with localStorage caching and background server sync.

### CSS

| Section | Description |
|---------|-------------|
| Custom properties | Dark/light themes |
| Grid layout | 10-column, responsive to 5-column at 700px |
| Grid cell mastery colors | `.mastery-0` (red) through `.mastery-4` (green) |
| Quiz UI | Prompt, input, buttons, feedback colors |
| Score bar | Score display |
| Subnav | Quiz mode sub-navigation |
| Reference table | Digit-to-sound reference |
| Auth status | Login/logout link |
| Theme toggle | Sun/moon icon button |

### HTML

| Section | Description |
|---------|-------------|
| Theme toggle | Dark/light switch |
| Header | Title |
| Nav bar | 4 tabs: Grid, Quiz, Reference, Translate |
| Subnav | 4 quiz modes: # → Word, Word → #, Mixed, Sound → # |
| Grid section | 10×10 mastery grid |
| Quiz sections | Forward, reverse, mixed, consonant quiz UIs |
| Reference section | Digit-to-sound table |
| Score bar | Running correct/total display |
| Auth status | Username or login link |

### JavaScript

| Function | Description |
|----------|-------------|
| Theme toggle | `toggleTheme()`, `updateToggleIcon()` |
| State variables | wordlist, mapping, keys, score, quiz state per mode |
| `saveState()` | Write to localStorage + fire-and-forget POST to `/api/state` |
| `loadState()` | Read from localStorage |
| `applyState(s)` | Apply server state, re-render |
| `updateAuthUI(username)` | Show username/logout or login link |
| `init()` | Load cached data, render, background fetch + sync |
| `renderGrid()` | Build 100 grid cells |
| `updateMasteryColors()` | Color-code grid cells by combined scores |
| `renderRef()` | Build reference table rows |
| `showSection(name)` | Tab switching, auto-start quizzes |
| `pickNext(scores, history, allKeys)` | Score-based selection with cooldown |
| `startQuiz()` / `checkQuiz()` / `skipQuiz()` | Forward quiz |
| `startReverse()` / `checkReverse()` / `skipReverse()` | Reverse quiz |
| `startMixed()` / `checkMixed()` / `skipMixed()` | Mixed quiz |
| `startCon()` / `checkCon()` / `skipCon()` | Consonant quiz |
| `updateScore()` | Calculate percentage, update display |
| Event listeners | Enter key → submit for all quiz inputs |

## wordlist.json (102 lines)

Generated artifact. JSON object mapping `"00"`–`"99"` to noun strings. Regenerated by `python generator.py`.

## requirements.txt (5 lines)

```
cmudict>=1.0.0
nltk>=3.8
setuptools
django>=5.1
gunicorn
```

## deploy.sh

VPS deployment script. Pulls latest code, installs deps, runs `migrate` and `collectstatic`, restarts the systemd service.
