# Architecture

**Analysis Date:** 2026-03-25

## Pattern Overview

**Overall:** Django SPA with TypeScript frontend + Python backend. Single-page application serving quiz modes as section-based views rendered in JavaScript.

**Key Characteristics:**
- Frontend: Monolithic IIFE bundle (esbuild-compiled from 10 TypeScript modules)
- Backend: Django REST API (mostly GET/POST endpoints returning JSON)
- State: Dual-storage (localStorage for speed, QuizState model for persistence)
- UI: Section-based SPA (Grid, Quiz modes, Reference, Profile, Settings, etc.) rendered via `showSection()`
- Quiz: Generic engine supporting 4 modes (quiz/reverse/mixed/consonant) via pluggable `MODES` config

## Layers

**Presentation (Frontend):**
- Location: `src/ts/ui.ts`, `src/ts/tutorial.ts`, `src/ts/wiki.ts`, `src/ts/theme.ts`, `src/ts/profile.ts`
- Purpose: Render sections, handle user interactions, manage DOM state
- Contains: Section renderers (grid, quiz, reference, translate, settings), event handlers, DOM manipulation
- Depends on: State layer, persistence layer, theme utilities
- Used by: `init.ts` (entry point), quiz engine, user interactions

**State Management:**
- Location: `src/ts/state.ts`
- Purpose: Centralize `appState` object and quiz mode configurations
- Contains: `appState` (wordlist, scores, settings), `MODES` (quiz mode definitions), `STATE_FIELDS` (persistence manifest)
- Depends on: Types, none (no external dependencies)
- Used by: UI layer, persistence layer, quiz engine, profile analytics

**Quiz Engine:**
- Location: `src/ts/quiz.ts`
- Purpose: Generic question picking, answer checking, scoring, timer management
- Contains: `startMode()`, `checkMode()`, `skipMode()`, countdown logic, score calculation
- Depends on: State, persistence, UI (for feedback rendering)
- Used by: UI via onclick handlers (checkQuiz, skipQuiz, etc.)

**Persistence (Client):**
- Location: `src/ts/persistence.ts`
- Purpose: Sync state between localStorage and QuizState API
- Contains: `loadState()` (localStorage → appState), `saveState()` (appState → localStorage + debounced POST to `/api/state`)
- Depends on: State, UI (for re-renders after server sync)
- Used by: All layers when state changes

**Backend API:**
- Location: `trainer/views.py`
- Purpose: Serve frontend data (wordlist, mapping, state) and handle authentication
- Contains: Views for wordlist, mapping, encoding, state sync, candidate suggestions, auth
- Depends on: Generator, validator, QuizState model
- Used by: Frontend fetch() calls

**Data Generation & Validation:**
- Location: `trainer/generator.py`, `trainer/validator.py`
- Purpose: Generate candidate nouns (via WordNet), validate words (via CMU phonemes)
- Contains: Word filtering (concreteness), phoneme→digit mapping, candidate caching
- Depends on: NLTK WordNet, CMU Pronouncing Dictionary
- Used by: Views (lazy-initialized singletons `_get_wordlist()`, `_get_candidate_map()`)

**Types & Constants:**
- Location: `src/ts/types.ts`, `src/ts/constants.ts`
- Purpose: Shared type definitions and magic numbers
- Contains: `AppState`, `QuizMode`, `ServerState` interfaces; `MATH_CONSTANTS`
- Depends on: None
- Used by: All TypeScript modules

## Data Flow

**Quiz Session:**

1. User clicks "Quiz" → `showQuizNav()` switches to quiz subnav
2. User clicks "# → Word" → `showSection('quiz')` renders quiz section
3. Page calls `startMode(MODES.quiz)` auto-running `startQuiz()`
4. Quiz engine:
   - Picks next question via `pickNext()` (weighted by mastery score)
   - Renders prompt + input field via `showQuizArea()`
   - User types answer + submits
5. `checkQuiz()` called → `checkMode(MODES.quiz)` validates answer
6. If correct: score += 1, if wrong: score -= penalty(current_score)
7. Updates `MODES.quiz.scores`, `MODES.quiz.recentGuesses`, `appState.score.total`
8. Feedback rendered, auto-advances to next question after 1.8s
9. Every answer updates `updateAccuracy()` (UI shows 100-question rolling average)
10. `saveState()` debounces POST to `/api/state` (1s delay to batch updates)

**State Synchronization:**

1. On page load: `init()` → `loadState()` restores from localStorage
2. Fetch `/api/state` → if server has newer/better score, `applyState()` overwrites local
3. On user action: `saveState()` writes to localStorage immediately
4. Debounced POST (1s) syncs to server via `/api/state` endpoint
5. Server identifies user by auth session or IP address, updates QuizState model
6. Next session loads state from server (not just localStorage)

**Grid Customization:**

1. User clicks grid cell → input focuses → fetch candidates from `/api/candidates/{digits}`
2. Candidates cached in memory
3. User types → dropdown filters candidates
4. User selects → word stored in `appState.customWords`
5. `rebuildWordlist()` merges `defaultWordlist + customWords`
6. Changes persist via `saveState()`

**State Management:**

- `appState` is single source of truth for all application state
- `STATE_FIELDS` manifest drives persistence (add field → add to manifest, not saveState/loadState directly)
- Quiz modes store per-question scores in `MODES[name].scores` (keyed by digit/word key)
- Activity log tracks quiz attempts per day (ISO date string)
- Theme, tutorial, dyslexia font are server-persisted boolean flags

## Key Abstractions

**QuizMode<T>:**
- Purpose: Pluggable quiz mode definition; all quiz types share same engine
- Examples: `MODES.quiz` (digit→word), `MODES.reverse` (word→digit), `MODES.consonant` (sound→digit)
- Pattern: Mode object defines prompt/answer/normalization functions; engine uses them polymorphically

**AppState:**
- Purpose: Central mutable state object
- Contains: wordlist, scoring data (per-question), user preferences, activity log
- Boundary: Passed to functions that need global access; never reconstructed

**MODES Configuration:**
- Purpose: Remove quiz-type branching from engine
- Pattern: Each mode specifies DOM IDs, item picker, prompt/answer extractors, normalization
- Benefit: `startMode()`, `checkMode()`, `skipMode()` work for all modes without if/else

**StateField Manifest:**
- Purpose: Declare which properties persist server-side
- Pattern: Getter/setter tuple stored in `STATE_FIELDS` array
- Benefit: Centralized persistence logic; adding fields requires one line

## Entry Points

**Frontend (Browser):**
- Location: `templates/index.html` + `src/ts/init.ts`
- Triggers: Page load
- Responsibilities: Load cached wordlist/mapping, fetch server state, render initial UI, attach event handlers
- Flow: DOM parser → `<script src="/static/js/app.js">` → IIFE executes → `init()` runs

**Backend (Django):**
- Location: `config/urls.py` → `trainer/urls.py`
- Routes:
  - `/` → `index_view()` (renders `templates/index.html`)
  - `/api/wordlist` → JSON dict
  - `/api/mapping` → JSON dict (digit→consonant sounds)
  - `/api/state` → GET/POST QuizState JSON
  - `/api/candidates/<digits>` → JSON array of word suggestions
  - `/api/encode` → POST, encodes text to digits
  - `/login/`, `/register/`, `/logout/` → Auth views

## Error Handling

**Strategy:** Graceful degradation. Network failures don't break the app; state persists locally.

**Patterns:**
- Quiz API failures: Fetch errors caught with `.catch(() => {})`, app continues with offline state
- Invalid input: Normalize/trim user input before validation; reject invalid words (must match `/^[a-z]/`)
- Type mismatches: Backend validates types in `state_view()` POST (checks `isinstance()`); frontend trusts API responses
- State corruption: Old localStorage keys (`quizPool`, `quizMastered`) detected and cleared on load
- Timer cleanup: Always clear countdown timers before starting new question (prevent stale intervals)

## Cross-Cutting Concerns

**Logging:** `logActivity()` increments daily counter in `appState.activityLog[today]`; synced to server via state persistence.

**Validation:**
- Frontend: User words must match `/^[a-z]/` (lowercase letter start)
- Backend: Score/theme/bool fields validated by type check; wordlist words case-insensitive but stored lowercase
- Encoding: CMU phoneme lookup via `word_to_digits()` (returns "" if word invalid)

**Authentication:**
- Sessions: Django session cookies for logged-in users
- Anonymous: IP-based identification (QuizState.ip_address)
- State ownership: `get_quiz_state()` returns QuizState for current user OR IP

**Theming:**
- Runtime CSS custom properties (--text-primary, --bg-base, etc.) updated via `[data-theme]` attribute
- Themes: dark, light, oled, high-contrast
- Persistence: localStorage.theme + server state.theme

**Accessibility:**
- ARIA labels on buttons, inputs (aria-label)
- Live regions on feedback (aria-live="polite")
- High-contrast theme meets WCAG AAA
- OpenDyslexic font toggle (loaded via CDN, applied to body via class)

---

*Architecture analysis: 2026-03-25*
