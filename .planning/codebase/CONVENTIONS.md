# Coding Conventions

**Analysis Date:** 2026-03-25

## Naming Patterns

**Files:**
- TypeScript: `camelCase.ts` (`quiz.ts`, `persistence.ts`, `theme.ts`)
- Python: `snake_case.py` (`generator.py`, `validator.py`)
- Test files: `test_<module>.py` (e.g., `test_api.py`, `test_persistence.py`)

**Functions:**
- TypeScript: `camelCase` for all functions (`startMode`, `checkQuiz`, `saveState`, `rebuildWordlist`)
- TypeScript: HTML event handlers exposed via `Object.assign(window, ...)` in `init.ts` — use camelCase names
- Python: `snake_case` for all functions (`get_quiz_state`, `build_candidate_map`, `is_concrete_noun_synset`)
- Private/internal functions: TypeScript uses `_camelCase` prefix (e.g., `_syncTimer`, `_get_concrete_roots()`)

**Variables:**
- TypeScript module scope: `camelCase` (`countdownInterval`, `activeDropdown`, `candidateCache`)
- TypeScript: Single-letter loop vars acceptable in `for...of` and `.forEach()` (e.g., `for (const name of keys)`)
- Python: `snake_case` for all variables, constants in `UPPER_SNAKE_CASE` (e.g., `SINGLE_DIGIT_WORDS`, `TIME_LIMITS`, `MAX_RECENT_GUESSES`)

**Types/Interfaces:**
- TypeScript: `PascalCase` (e.g., `AppState`, `QuizMode`, `WordQuizItem`)
- Python: `PascalCase` for Django models (`QuizState`)

**Constants:**
- TypeScript: `UPPER_SNAKE_CASE` (e.g., `MAX_RECENT_GUESSES = 100`, `NEXT_QUESTION_DELAY_MS = 1800`)
- Python: `UPPER_SNAKE_CASE` (e.g., `WORDLIST_PATH`, `BLOCKED_WORDS`)
- TypeScript: Use `as const` for literal constant declarations to enable type narrowing (`export const THEMES = ['dark', 'light', 'oled', 'high-contrast'] as const`)

## Code Style

**Formatting:**
- TypeScript: No linter/formatter configured — follows natural spacing and readability conventions
- Python: No linter configured — follows PEP 8 conventions naturally
- Line length: No strict limit enforced, but functions favor conciseness

**Linting:**
- TypeScript: `tsc --noEmit` for type checking only, no runtime linting
- JavaScript build: `esbuild` with `--keep-names` flag to preserve function names (used by JSON test runner)
- Python: No configured linter; relies on developer discipline

**Build Tools:**
- TypeScript: Built with `esbuild` into single IIFE bundle (`static/js/app.js`)
- CSS: Compiled from SCSS with `sass` CLI into single compressed file (`static/css/app.css`)
- Build command: `npm run build` (runs both JS and CSS)
- Typecheck: `npm run check` (typecheck + build)

## Import Organization

**TypeScript Order:**
1. Relative imports from `./` (e.g., `import { appState } from './state'`)
2. All imports grouped by dependency (imports for a feature together)

**Examples:**
```typescript
// From quiz.ts
import { appState, MODES, logActivity } from './state';
import { QuizItem, QuizMode } from './types';
import { saveState } from './persistence';
import { updateAccuracy } from './ui';

// From init.ts
import { appState, rebuildWordlist } from './state';
import { getCookie, loadState, applyState, saveState } from './persistence';
import { toggleTheme, setTheme, updateToggleIcon } from './theme';
import { checkQuiz, skipQuiz, checkReverse, ... } from './quiz';
```

**Python Order:**
1. Standard library (`os`, `json`, `re`, etc.)
2. Third-party libraries (`django`, `nltk`, etc.)
3. Local imports (same project)

```python
# From generator.py
import json
import logging
import random
from pathlib import Path
import nltk
from trainer.validator import word_to_digits, number_to_digits
```

**Path Aliases:**
- TypeScript: No aliases configured; uses relative paths exclusively
- Python: Imports use absolute project paths (`from trainer.validator import ...`)

## Error Handling

**TypeScript Patterns:**
- Silent failures for non-critical operations: `try { ... } catch {}` (e.g., in `init.ts` for fetch failures, `ui.ts` for DOM operations)
- Return early on null/undefined: Check and return before proceeding (e.g., `if (!mode.current) return;`)
- Non-null assertion `!` used where type is guaranteed by control flow (e.g., `document.getElementById(mode.promptId)!`)

**Python Patterns:**
- Specific exception catching: `except (json.JSONDecodeError, ValueError):` rather than bare `except`
- JsonResponse with status codes for HTTP errors: `JsonResponse({'error': '...'}, status=400)`
- Global singletons wrapped with None checks: `if _wordlist is None:` pattern in `views.py`

## Logging

**TypeScript:**
- No logging framework used
- Uses browser `console` implicitly (logged statements don't appear; app is client-focused)
- No explicit log statements in source code

**Python:**
- Uses standard `logging` module: `logger = logging.getLogger(__name__)`
- Located in `trainer/generator.py`: `logger.info()` for informational messages
- Log level configured via Django settings (not explicitly set in source)

## Comments

**When to Comment:**
- Complex business logic: e.g., comments explaining mastery tier calculations (`MASTERY_THRESHOLDS`)
- Non-obvious DOM manipulations: e.g., quiz fade-out transitions with force-reflow comments
- Algorithm choices: e.g., "Two-tier concreteness system" comment in `generator.py`
- Workarounds/migrations: e.g., old state format detection (`if (stored.quizPool || stored.quizMastered)`)

**JSDoc/TSDoc:**
- Not used systematically
- Inline comments (line-by-line) for complex sections
- Function purpose inferred from name and context

**Python Docstrings:**
- Module-level docstrings present (e.g., `trainer/generator.py`)
- No function-level docstrings for simple functions
- Complex functions documented (e.g., `is_concrete_noun_synset`)

## Function Design

**Size:**
- TypeScript: Functions 5-50 lines typical; longer functions broken into helpers where cohesion unclear
  - `startMode` (25 lines) — handles both initial and subsequent question setup
  - `startCountdown` (22 lines) — countdown display and timer management
  - Small utilities (<5 lines): `clearCountdown`, `getTimeLimit`, `getQuizArea`

- Python: Functions 10-80 lines typical
  - Generator functions 40-80 lines (data processing)
  - API handlers 20-40 lines
  - Validation functions 5-20 lines

**Parameters:**
- TypeScript: Generic type parameters used to abstract over quiz modes (e.g., `<T extends QuizItem>`)
- Python: Positional args preferred; keyword args for optional settings
- No destructuring for DOM elements; prefer direct parameter passing

**Return Values:**
- TypeScript: Void functions dominate (handle DOM side effects); few return values
- Functions returning data: Explicit types (e.g., `Record<string, string[]>`, `string[]`)
- Python: Return data or status; side-effect functions return `None`
- API views always return `JsonResponse` with status codes

## Module Design

**Exports:**
- TypeScript: Named exports only (no default exports)
  - `export function name() { ... }`
  - `export const CONSTANT = ...`
  - `export interface Type { ... }`
- All module-level state exported for cross-module access

**Barrel Files:**
- Not used; each module imports directly from its source file
- `init.ts` imports everything needed for initialization but doesn't re-export

**Module Cohesion:**
- `state.ts`: Global app state + MODES config (quiz-mode definitions)
- `persistence.ts`: State serialization (localStorage + server sync)
- `quiz.ts`: Quiz engine (startMode, checkMode, skipMode + countdown)
- `ui.ts`: DOM rendering + event handlers (grid, references, imports, settings)
- `types.ts`: TypeScript interfaces only (no implementation)
- `theme.ts`: Theme switching + icon updates
- `tutorial.ts`: Onboarding overlay logic
- `profile.ts`: User stats rendering
- `wiki.ts`: Reference material + consonant mapping

---

*Convention analysis: 2026-03-25*
