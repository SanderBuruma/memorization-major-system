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

## static/index.html (306 lines)

Self-contained SPA: inline CSS (lines 7–64) + inline JavaScript (lines 129–304).

### CSS (lines 7–64)

| Line | Section |
|------|---------|
| 8–18 | Global resets, body, container, header, nav buttons |
| 22–28 | Grid layout (10-column, responsive to 5-column at 700px) |
| 30–45 | Quiz UI: prompt, input, buttons, feedback colors |
| 47–50 | Score bar |
| 52–57 | Reference table |
| 59–63 | Media query for mobile |

### HTML (lines 66–127)

| Line | Section |
|------|---------|
| 68–71 | Header with title |
| 73–78 | Nav bar (4 tab buttons) |
| 81–83 | Grid section |
| 86–97 | Quiz section (number → word) |
| 100–111 | Reverse quiz section (word → number) |
| 114–121 | Reference section |
| 124–126 | Score bar |

### JavaScript (lines 129–304)

| Line | Function | Description |
|------|----------|-------------|
| 133–140 | State variables | `wordlist`, `mapping`, `keys`, `score`, quiz state |
| 145–155 | `init()` | Parallel fetch of `/api/wordlist` + `/api/mapping`, render |
| 160–171 | `renderGrid()` | Build 100 grid cells |
| 176–184 | `renderRef()` | Build reference table rows |
| 189–196 | `showSection(name)` | Tab switching, auto-start quizzes |
| 201–212 | `startQuiz()` | Pick random number, set up quiz UI |
| 215–236 | `checkQuiz()` | Validate answer, show feedback, auto-advance (1800ms) |
| 241–252 | `startReverse()` | Pick random word, set up reverse quiz UI |
| 255–278 | `checkReverse()` | Validate answer (accepts "7" or "07"), auto-advance |
| 283–287 | `updateScore()` | Calculate percentage, update display |
| 292–297 | Event listeners | Enter key → submit for both quiz inputs |
| 302 | `init()` call | Boots the application |

## wordlist.json (102 lines)

Generated artifact. JSON object mapping `"00"`–`"99"` to noun strings. Regenerated by `python generator.py`.

## requirements.txt (3 lines)

```
cmudict>=1.0.0
nltk>=3.8
setuptools
```
