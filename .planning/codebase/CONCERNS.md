# Codebase Concerns

**Analysis Date:** 2025-03-25

## Tech Debt

**Silent API Failure in State Sync:**
- Issue: `saveState()` in `src/ts/persistence.ts` catches all errors silently with `.catch(() => {})`, hiding network or server errors
- Files: `src/ts/persistence.ts` (line 28)
- Impact: Quiz scores and settings may fail to sync to server without user awareness. If localStorage quota is exceeded, data loss occurs
- Fix approach: Log failed syncs to console in development; implement retry logic with exponential backoff; display user notification for critical failures

**localStorage Quota Risk:**
- Issue: Multiple large objects stored in localStorage without quota checking:
  - `quizState` (all quiz mode scores, history, guesses for 4 modes)
  - `wordlist` (100+ items)
  - `mapping` (phoneme data)
  - `theme` preference
- Files: `src/ts/persistence.ts` (lines 21, 72, 77, 88), `src/ts/init.ts` (lines 72, 77, 88)
- Impact: localStorage is typically 5-10MB per origin. Heavy usage could hit quota and silently fail. No checks for `QuotaExceededError`
- Fix approach: Add quota checking before localStorage writes; implement cache eviction (drop old quiz history beyond MAX_RECENT_GUESSES); measure actual storage footprint

**CSRF Cookie HTTPOnly Disabled:**
- Issue: `CSRF_COOKIE_HTTPONLY = False` in `config/settings.py` (line 68)
- Files: `config/settings.py`
- Impact: CSRF token can be read by JavaScript, increasing XSS attack surface (attacker can exfiltrate token)
- Fix approach: Set to `True` and use standard Django CSRF middleware (passes token in POST body automatically). Verify CSRF token extraction in `src/ts/persistence.ts` still works

**Unbounded Forward Text Input:**
- Issue: Mixed quiz mode sets `maxLength = 524288` (browser default) for forward word guesses in `src/ts/state.ts` (line 72)
- Files: `src/ts/state.ts` (line 72)
- Impact: Users can paste gigabytes of text; may cause UI lag, memory spikes, or database bloat if persisted
- Fix approach: Cap at reasonable length (e.g., 256 characters) matching longest dictionary word

**Default Django Secret Key:**
- Issue: `SECRET_KEY` defaults to `'dev-insecure-key-change-in-production'` if env var not set in `config/settings.py` (line 6)
- Files: `config/settings.py`
- Impact: If deployed without setting `DJANGO_SECRET_KEY`, sessions are forgeable
- Fix approach: Raise error on startup if deploying with DEBUG=False and SECRET_KEY is default

**Deprecated NLTK Paths in Tests:**
- Issue: Tests check for 'testserver' in ALLOWED_HOSTS and modify it at import time in `tests/test_api.py` (line 8-9), `tests/test_tutorial.py`, etc.
- Files: `tests/test_api.py`, `tests/test_tutorial.py`, `tests/test_candidates.py`, `tests/test_encode.py`, `tests/test_dyslexia_font.py`
- Impact: Modifying settings at import time is fragile; test isolation breaks if tests run in different order; Django test runner already handles ALLOWED_HOSTS
- Fix approach: Remove manual ALLOWED_HOSTS modification; use Django's `override_settings` decorator if needed

## Known Bugs

**Quiz Timeout Penalty Scaling Loss:**
- Symptoms: When timeout occurs, penalty is `floor(score/4) + 1`. A score of 0 incurs penalty -1, making future scores negative without lower bound
- Files: `src/ts/quiz.ts` (line 17-18), `src/ts/quiz.ts` (line 82)
- Trigger: Time out on first attempt (score 0) for a quiz item repeatedly
- Workaround: Score can go negative but mastery threshold checks may not handle it correctly (threshold at -3)
- Fix approach: Clamp minimum score to 0 or apply ceiling to negative penalties

**History Array Rotation Issue:**
- Symptoms: `mode.history` is limited to 10 items. When rotating (shift), the order of dequeuing happens *after* checking, not before
- Files: `src/ts/quiz.ts` (lines 91-92, 194, 204)
- Trigger: Answer > 10 questions in a row
- Workaround: None (history is only used for recent-question avoidance in `pickNext`)
- Fix approach: Ensure history management happens atomically; consider using a circular buffer for clarity

**Server-Side Score Comparison Logic:**
- Symptoms: `init.ts` line 82 applies server state only if `serverState.score.total > appState.score.total`, but doesn't check individual quiz mode scores
- Files: `src/ts/init.ts` (lines 82-84)
- Trigger: User with high total score but low mode-specific scores syncs; server quiz_scores is discarded
- Workaround: Manual state export/import
- Fix approach: Implement three-way merge for quiz mode scores (take server version if newer based on timestamp)

## Security Considerations

**XSS via innerHTML in User-Controlled Data:**
- Risk: Most innerHTML calls are properly escaped, but theme toggle uses unescaped SVG: `btn.innerHTML = THEME_ICONS[theme]`
- Files: `src/ts/theme.ts` (line 37)
- Current mitigation: THEME_ICONS are hardcoded, not user input, so safe
- Recommendations: Comment as "safe because hardcoded"; future refactorings should use `textContent` for non-HTML data

**Candidate Word Autocomplete Injection:**
- Risk: Autocomplete shows candidates from `build_candidate_map()` which sources from NLTK. API returns array of strings which are escaped in `src/ts/ui.ts` (lines 266, 291)
- Files: `src/ts/ui.ts` (line 46, 29-31), `trainer/views.py` (line 169)
- Current mitigation: Properly escaped with `escapeHTML()`
- Recommendations: Validate candidate length server-side (currently no max length on returned suggestions)

**Auth Token in innerHTML:**
- Risk: `src/ts/init.ts` line 18 includes CSRF token in button onclick
- Files: `src/ts/init.ts` (line 18)
- Current mitigation: Token is escaped, but inline event handlers are legacy. If token is sensitive, this is still a surface
- Recommendations: Use `addEventListener` instead of inline onclick; store token in data attribute, not HTML attribute

**IP-Based Session Isolation:**
- Risk: Anonymous users are tracked by IP in `trainer/models.py` (`ip_address` field). Shared/office IPs will conflate users
- Files: `trainer/models.py` (line 7), `trainer/views.py` (line 47)
- Current mitigation: None
- Recommendations: Warn users that shared networks = shared progress; add browser fingerprinting or device-local storage as fallback for authenticated users

## Performance Bottlenecks

**Synchronous NLTK Loading:**
- Problem: `get_concrete_nouns()` in `trainer/generator.py` and `ensure_nltk_data()` block on first request
- Files: `trainer/generator.py` (line 99), `trainer/generator.py` (line 37-46)
- Cause: NLTK data fetch happens at request time if not cached
- Improvement path: Pre-download NLTK data in CI/deployment setup; cache in process with module-level singleton (already done for `_get_wordlist`)

**Autocomplete Dropdown DOM Thrashing:**
- Problem: `filterDropdown()` recreates all dropdown options on every keystroke, removing and re-adding elements
- Files: `src/ts/ui.ts` (line 81-85)
- Cause: `showDropdown()` recreates DOM, `filterDropdown()` calls it on each `input` event
- Improvement path: Use classList toggling on existing options instead of removing/re-adding

**Profile Statistics Recalculation:**
- Problem: `renderProfile()` iterates through all quiz modes and keys on each section switch
- Files: `src/ts/profile.ts` (lines 95-120)
- Cause: No caching; O(modes × keys) = O(4 × 100) = 400 DOM reads per render
- Improvement path: Memoize stats calculation; only recalculate on score change (in `saveState()`)

**Candidate Map Generation:**
- Problem: `_get_candidate_map()` is built once per process but generation is O(n²) in `build_candidate_map()` function
- Files: `trainer/views.py` (line 29-33)
- Cause: WordNet concrete noun filtering is expensive; lazy initialization happens on first API call
- Improvement path: Acceptable as singleton, but document that first candidate request may be slow (200-500ms)

## Fragile Areas

**State Field Synchronization:**
- Files: `src/ts/state.ts` (lines 95-110), `src/ts/persistence.ts` (lines 15-17)
- Why fragile: `STATE_FIELDS` manifest must stay in sync with `_FIELD_MAP` in `trainer/views.py`. Adding a new field requires changes in 3 places (state.ts, views.py, types.ts) with no validation
- Safe modification: When adding persisted state:
  1. Add field to `AppState` interface in `src/ts/types.ts`
  2. Initialize in `appState` object in `src/ts/state.ts`
  3. Add entry to `STATE_FIELDS` array in `src/ts/state.ts` with get/set
  4. Add Django model field in `trainer/models.py`
  5. Add to `_FIELD_MAP` and `_STATE_KEYS` in `trainer/views.py`
  6. Test roundtrip: save locally, POST to API, GET and verify
- Test coverage: No tests for STATE_FIELDS synchronization; only API tests

**Quiz Mode Configuration:**
- Files: `src/ts/state.ts` (lines 24-93)
- Why fragile: MODES is a massive object with callbacks; `allKeys()`, `pickItem()`, `normalize()`, `formatCorrect()` must match between client and validation expectations. Any callback returning wrong type breaks `checkMode`
- Safe modification: When modifying mode behavior:
  1. Update callbacks in MODES object
  2. Add corresponding test in `tests/test_pool_quiz.py` or add new test file
  3. Test with timed and untimed quiz
  4. Verify score calculation matches penalty logic
- Test coverage: `test_pool_quiz.py` tests some mode behavior but not all callbacks

**Quiz History / Recent Guesses Rotation:**
- Files: `src/ts/quiz.ts` (lines 11-14), `src/ts/state.ts` (line 108)
- Why fragile: Manual array rotation with `shift()` and length checks. No invariant validation (e.g., ensuring length never exceeds 10)
- Safe modification: Consider wrapping in a `CircularBuffer` class or adding assertions
- Test coverage: No tests for rotation behavior; relies on manual verification

**Wordlist Merging Logic:**
- Files: `src/ts/state.ts` (line 118), `src/ts/ui.ts` (line 75)
- Why fragile: `rebuildWordlist()` merges defaultWordlist and customWords with `...` spread. If a digit exists in both, customWords wins. No conflict detection or undo
- Safe modification: Make merge explicit; document precedence; add test for merge behavior
- Test coverage: No tests for merge behavior

## Scaling Limits

**Single IP per Anonymous User:**
- Current capacity: Shared IP = shared user (could mean 50+ people on office network share state)
- Limit: Office/school networks collapse all users into one
- Scaling path: Use browser fingerprinting (user-agent + screen resolution hash) as fallback; offer optional login for persistent storage

**Quiz History Limited to 10 Items:**
- Current capacity: Only remembers last 10 answered items
- Limit: With 100 items, 90% of pool is always re-selectable on next session
- Scaling path: Increase to 20-50; benchmark localStorage impact

**localStorage Size ~5-10MB:**
- Current capacity: Estimated payload with full state ~2-3MB (100 wordlist entries + 4 × 100 quiz scores + history)
- Limit: Hitting quota silently breaks persistence
- Scaling path: Implement client-side compression; archive old activity logs; migrate heavy state to IndexedDB

## Dependencies at Risk

**NLTK WordNet Dependency:**
- Risk: NLTK data downloads on first request; network-dependent; large corpus (100+ MB decompressed)
- Impact: Startup slow on new deployments; CI may timeout if repo doesn't include wordnet data
- Migration plan: Pre-download and commit NLTK data to repo; use `nltk.data.path` to pin location

**Django ORM with SQLite:**
- Risk: SQLite locks on concurrent writes; no connection pooling
- Impact: Multiple simultaneous quiz state updates may fail with "database is locked"
- Migration plan: Use PostgreSQL for production; add connection retry logic in views.py

## Missing Critical Features

**Data Export/Import Completeness:**
- Problem: Export works (CSV/JSON), but import only supports custom words, not quiz scores/history
- Blocks: User cannot backup and restore full quiz progress across devices
- Files: `src/ts/ui.ts` (lines 428-486, 538-544)
- Fix: Add import for quiz mode scores; validate format; test roundtrip export → import

**Offline Capability:**
- Problem: App requires server for wordlist and mapping on first load
- Blocks: Cannot use on flight/no-internet; requires initial API call
- Files: `src/ts/init.ts` (lines 65-95)
- Fix: Bundle default wordlist and mapping in HTML; serve from localStorage fallback

**Undo for Quiz State:**
- Problem: No way to undo a quiz answer or reset a mode's scores
- Blocks: Accidental wrong answers or fat-finger clicks irreversible
- Files: `src/ts/quiz.ts`, `src/ts/state.ts`
- Fix: Add "Undo Last" button; persist undo stack per mode

## Test Coverage Gaps

**Quiz Penalty Logic Edge Cases:**
- What's not tested: Negative scores, penalty application on timeout vs. wrong answer, score clamping
- Files: `src/ts/quiz.ts` (lines 17-18, 82, 188)
- Risk: Penalty formula changes silently break; no regression tests
- Priority: High

**State Persistence Roundtrip:**
- What's not tested: Save to localStorage → load → modify → POST to server → GET from server → verify all fields match
- Files: `src/ts/persistence.ts`, `trainer/views.py`
- Risk: State loss on sync failure; mismatched data types between client/server
- Priority: High

**Autocomplete Filtering:**
- What's not tested: Dropdown updates on each keystroke; candidate caching; cache invalidation
- Files: `src/ts/ui.ts` (lines 24-85)
- Risk: Stale cache; XSS from malformed candidates
- Priority: Medium

**Import CSV/JSON Validation:**
- What's not tested: Edge cases in `parseCSV()` and `parseJSON()` (empty file, malformed numbers, invalid words)
- Files: `src/ts/ui.ts` (lines 430-487)
- Risk: Silent parsing failure; corrupted import
- Priority: Medium

**Theme Switching Persistence:**
- What's not tested: Theme syncs to server; theme applied on reload from localStorage + server state merge
- Files: `src/ts/theme.ts`, `src/ts/persistence.ts`, `src/ts/init.ts`
- Risk: Theme preference lost on sync failure
- Priority: Low

---

*Concerns audit: 2025-03-25*
