# File Reference

Every source file with line counts, key sections, and function locations.

## validator.py (83 lines)

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

## generator.py (257 lines)

Word selection, validation, and persistence. Main workhorse module.

| Line | Symbol | Description |
|------|--------|-------------|
| 20 | `WORDLIST_PATH` | Path to `wordlist.json` (sibling to this file) |
| 24 | `MANUAL_OVERRIDES` | Dict for human-curated overrides (empty by default) |
| 27–31 | `BLOCKED_WORDS` | Set of excluded words (slurs, abbreviations) |
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
| 245–256 | `__main__` block | CLI entry point: generate, validate, save, report |

## server.py (89 lines)

HTTP server with JSON API endpoints.

| Line | Symbol | Description |
|------|--------|-------------|
| 19–20 | `HOST`, `PORT` | `localhost`, `8080` |
| 23 | `wordlist` | Module-level global, populated at startup |
| 26–55 | `MajorSystemHandler` | Custom request handler (extends `SimpleHTTPRequestHandler`) |
| 28–33 | `__init__()` | Sets static file directory to `static/` |
| 35–44 | `do_GET()` | Routes: `/api/wordlist`, `/api/mapping`, `/`, fallback |
| 46–52 | `_json_response(data)` | Send JSON with Content-Type and Content-Length |
| 54–55 | `log_message()` | Redirect HTTP logs to `logger.debug` |
| 58–84 | `main()` | Startup: load wordlist → create server → serve forever |

## test_associations.py (116 lines)

Unittest suite, runnable independently of the server.

| Line | Symbol | Description |
|------|--------|-------------|
| 22–111 | `TestMajorSystemAssociations` | Test class with 4 test methods |
| 25–33 | `setUpClass()` | Load NLTK data + wordlist (from file or generated) |
| 39–47 | `test_all_numbers_covered()` | All 100 entries exist and are non-null |
| 53–66 | `test_all_words_are_nouns()` | Every word is a noun in WordNet |
| 72–89 | `test_all_encodings_match()` | Every word's CMU encoding matches its number |
| 95–111 | `test_all_words_are_concrete()` | Every word traces to `physical_entity.n.01` |

## test_pool_quiz.py (232 lines)

Tests for the pool-based quiz system. Replicates the JS pool logic in Python and statistically verifies correctness.

| Line | Class | Tests | Description |
|------|-------|-------|-------------|
| 14–20 | Helper functions | — | `init_pool()`, `replace_in_pool()`, `pick_from_pool()` (Python replicas of JS) |
| 40–57 | `TestInitPool` | 5 | Pool size, mastered exclusion, validity, no duplicates, randomness |
| 60–87 | `TestReplaceInPool` | 4 | Replacement, mastered exclusion, pool shrinking, no duplicates |
| 90–104 | `TestPickFromPool` | 4 | Empty pool, single element, avoids last key, all members reachable |
| 107–125 | `TestStreakGraduation` | 3 | 3-correct graduation, incorrect reset, skip reset |
| 128–170 | `TestRecycleAt80` | 4 | Drops to 79, streak reset, never exceeds 80, random distribution |
| 173–184 | `TestPoolPersistence` | 2 | Pool survives across rounds, reinits when empty |
| 187–230 | `TestFullSimulation` | 3 | Only pool words quizzed, no consecutive repeats, all 100 eventually seen |

## static/index.html (481 lines)

Self-contained SPA: inline CSS + inline JavaScript (no build step).

### CSS (lines 14–119)

| Line | Section |
|------|---------|
| 15–54 | CSS custom properties (dark/light themes, 18 vars each) |
| 55–56 | Global resets, body |
| 57–65 | Container, header, nav buttons |
| 69–75 | Grid layout (10-column, responsive to 5-column at 700px) |
| 77–93 | Quiz UI: prompt, input, buttons, feedback colors |
| 95–98 | Score bar |
| 100–105 | Reference table |
| 107–112 | Theme toggle button |
| 114–118 | Media query for mobile |

### HTML (lines 121–183)

| Line | Section |
|------|---------|
| 122 | Theme toggle button |
| 124–127 | Header with title |
| 129–134 | Nav bar (4 tab buttons) |
| 137–139 | Grid section |
| 142–153 | Quiz section (number → word), skip calls `skipQuiz()` |
| 155–167 | Reverse quiz section (word → number), skip calls `skipReverse()` |
| 169–177 | Reference section |
| 179–182 | Score bar |

### JavaScript (lines 185–480)

| Line | Function | Description |
|------|----------|-------------|
| 189–206 | Theme toggle | `toggleTheme()`, `updateToggleIcon()`, SVG icons |
| 211–227 | State variables | `wordlist`, `mapping`, `keys`, `score`, quiz state + pool state |
| 232–241 | `init()` | Parallel fetch of `/api/wordlist` + `/api/mapping`, render |
| 246–257 | `renderGrid()` | Build 100 grid cells |
| 262–270 | `renderRef()` | Build reference table rows |
| 275–282 | `showSection(name)` | Tab switching, auto-start quizzes |
| 288–296 | `initPool(mastered)` | Pick 10 random unmastered keys (Fisher-Yates shuffle) |
| 298–305 | `replaceInPool(pool, masteredKey, mastered)` | Remove graduated key, add random replacement |
| 307–313 | `pickFromPool(pool, lastKey)` | Random pick from pool, avoids consecutive repeats |
| 318–338 | `startQuiz()` | Lazy-init pool, pick from pool, set up quiz UI |
| 340–378 | `checkQuiz()` | Validate answer, track streaks, graduate at 3, recycle at 80 |
| 380–383 | `skipQuiz()` | Reset streak, advance to next |
| 388–408 | `startReverse()` | Lazy-init pool, pick from pool, set up reverse quiz UI |
| 410–448 | `checkReverse()` | Validate answer, track streaks, graduate at 3, recycle at 80 |
| 450–453 | `skipReverse()` | Reset streak, advance to next |
| 458–462 | `updateScore()` | Calculate percentage, update display |
| 467–472 | Event listeners | Enter key → submit for both quiz inputs |
| 478 | `init()` call | Boots the application |

## wordlist.json (102 lines)

Generated artifact. JSON object mapping `"00"`–`"99"` to noun strings. Regenerated by `python generator.py`.

## requirements.txt (3 lines)

```
cmudict>=1.0.0
nltk>=3.8
setuptools
```
