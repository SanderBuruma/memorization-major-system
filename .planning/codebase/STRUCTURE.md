# Codebase Structure

**Analysis Date:** 2026-03-25

## Directory Layout

```
memorization-major-system/
├── src/                    # Source code (TypeScript + SCSS)
│   ├── ts/                 # TypeScript modules (esbuild → static/js/app.js)
│   └── scss/               # SCSS stylesheets (sass → static/css/app.css)
├── trainer/                # Django app (models, views, URL routes)
├── config/                 # Django project settings
├── templates/              # Django HTML templates (login.html, index.html)
├── static/                 # Built/served assets (compiled JS, CSS, favicon)
├── tests/                  # Python test suite
├── scripts/                # CLI tools (e.g., lookup.py)
├── docs/                   # Documentation
├── .planning/              # GSD planning artifacts
├── wordlist.json           # Default Major System 0-99 noun associations
├── manage.py               # Django management script
├── package.json            # Node.js build dependencies (esbuild, sass)
├── tsconfig.json           # TypeScript compilation config
└── requirements.txt        # Python dependencies (Django, NLTK, etc.)
```

## Directory Purposes

**`src/ts/`:**
- Purpose: TypeScript source modules for the single-page app
- Contains: Type definitions, state management, quiz engine, UI rendering, persistence
- Key files: `init.ts` (entry point), `state.ts` (global state), `quiz.ts` (game logic), `ui.ts` (rendering)
- Build output: Compiled to `static/js/app.js` (IIFE bundle, not committed)

**`src/scss/`:**
- Purpose: SCSS stylesheets organized by feature/section
- Contains: Theme definitions (via CSS custom properties), component styles, responsive breakpoints
- Key files: `main.scss` (imports all), `_variables.scss` (CSS custom properties), `_quiz.scss` (quiz UI), `_grid.scss` (grid section)
- Build output: Compiled to `static/css/app.css` (not committed)

**`trainer/`:**
- Purpose: Django app encapsulating quiz logic and data generation
- Contains: Models (QuizState), views (REST endpoints), URL routing, word generation/validation
- Key files: `models.py` (QuizState), `views.py` (API endpoints), `generator.py` (wordlist curation), `validator.py` (phoneme→digit mapping)

**`config/`:**
- Purpose: Django project configuration
- Contains: Settings (database, installed apps, static files), URL routing, WSGI entry point
- Key files: `settings.py` (app config), `urls.py` (root URL patterns), `wsgi.py` (production entry)

**`templates/`:**
- Purpose: Django HTML templates rendered server-side
- Contains: `index.html` (SPA shell with section divs), `login.html` (auth form)
- Pattern: `index.html` uses Django template tags (`{% load static %}`) for static file URLs; all UI rendering happens in JavaScript after load

**`static/`:**
- Purpose: Compiled assets served to browser
- Contains: `js/app.js` (esbuild output), `css/app.css` (sass output), `favicon.svg`
- Generated: Built locally via `npm run build` and in CI; NOT committed to git

**`tests/`:**
- Purpose: Python test suite (pytest)
- Contains: Tests for validator, generator, API endpoints, persistence, theme, accessibility
- Patterns: Test files named `test_*.py`; CI runs via GitHub Actions

**`scripts/`:**
- Purpose: Standalone CLI utilities
- Key files: `lookup.py` (number↔word lookup tool)

**`.planning/`:**
- Purpose: GSD orchestration artifacts (planning documents, analysis)
- Contains: `codebase/` (ARCHITECTURE.md, STRUCTURE.md, etc.), `phases/` (implementation plans)

## Key File Locations

**Entry Points:**

- `templates/index.html` — Server-rendered SPA shell; loads quiz history form, defines section divs
- `src/ts/init.ts` — Frontend bootstrap; runs on script load, initializes state/UI/event handlers
- `trainer/views.py` — Backend API entry; handles GET/POST for all data endpoints
- `config/urls.py` → `trainer/urls.py` — Django URL routing (maps paths to views)

**Configuration:**

- `tsconfig.json` — TypeScript compiler options (target ES2020, strict mode)
- `package.json` — npm build scripts (`npm run build` = esbuild + sass)
- `requirements.txt` — Python dependencies (Django, NLTK, CMU dict, pytest, etc.)
- `wordlist.json` — Default Major System noun map (0-99 numbers → words); regenerated if missing

**Core Logic:**

- `src/ts/state.ts` — Global `appState` object, `MODES` config, `STATE_FIELDS` persistence manifest
- `src/ts/quiz.ts` — Question picking, answer checking, scoring, timer countdown
- `trainer/generator.py` — Word selection logic (WordNet filtering for concreteness)
- `trainer/validator.py` — CMU phoneme → Major System digit encoding

**Testing:**

- `tests/` — Full pytest suite; run with `pytest` or `python -m pytest`
- Key test files: `test_encode.py` (validator), `test_associations.py` (generator), `test_api.py` (endpoints)

## Naming Conventions

**Files:**

- TypeScript: `camelCase.ts` (e.g., `quiz.ts`, `persistence.ts`)
- SCSS: `_featureName.scss` (e.g., `_quiz.scss`, `_grid.scss`); `_` prefix indicates partial (imported by main.scss)
- Python: `snake_case.py` (e.g., `generator.py`, `validator.py`)
- Tests: `test_featureName.py` (e.g., `test_quiz.ts` → `test_encode.py` for validator tests)

**Directories:**

- `src/` — Source (pre-build)
- `static/` — Built/served assets
- `trainer/` — Django app (lowercase, singular per convention)
- `tests/` — Test suite root
- `_` prefix in SCSS — Partial/mixin file (not standalone stylesheet)

## Where to Add New Code

**New Feature (e.g., new quiz mode):**
- Quiz engine logic: Add mode to `MODES` in `src/ts/state.ts` (define prompt/answer/scoring rules)
- UI rendering: Add section div to `templates/index.html` (id="section-{name}"), render function to `src/ts/ui.ts`
- Styling: Add `src/scss/_{name}.scss`, import in `src/scss/main.scss`
- API support: No changes (quiz modes use existing `/api/state` endpoint)
- Tests: Add test file `tests/test_{feature}.py` for any backend logic

**New Component/Module:**
- Create new file in `src/ts/{componentName}.ts` with TypeScript exports
- Import in `src/ts/init.ts` (if needs to expose to HTML onclick handlers)
- Add to `Object.assign(window, {...})` in init.ts if HTML needs to call it
- Re-export from state.ts if it modifies global state

**Utilities & Helpers:**
- Shared utilities: `src/ts/utils.ts` (e.g., escapeHTML, formatters)
- Constants: `src/ts/constants.ts` (e.g., MATH_CONSTANTS)
- Backend: `trainer/validator.py` for word/phoneme logic, `trainer/generator.py` for data generation

**API Endpoints:**
- Add view function to `trainer/views.py`
- Add URL pattern to `trainer/urls.py` (path and view)
- Frontend calls via `fetch('/api/{endpoint}')` in relevant UI module

**Styling:**
- Global/base: `src/scss/_base.scss`, `src/scss/_variables.scss`
- Feature-specific: Create `src/scss/_{featureName}.scss`, add `@import` to `main.scss`
- Responsive: Rules can live in feature files or `_responsive.scss`

**Tests:**
- Backend: `tests/test_{feature}.py` (pytest)
- Frontend: No Jest setup; manual testing via browser or playwright (if needed)

## Special Directories

**`collected_static/`:**
- Purpose: Django staticfiles output (admin panel assets, collected from all apps)
- Generated: `python manage.py collectstatic`
- Committed: No (generated, git-ignored)

**`migrations/` (trainer/migrations/):**
- Purpose: Django database migration history
- Committed: Yes (allows reproducible schema)
- Pattern: Django auto-generates; commit to version control

**`venv/`:**
- Purpose: Python virtual environment
- Committed: No (git-ignored; recreate with `python -m venv venv && pip install -r requirements.txt`)

**`node_modules/`:**
- Purpose: npm dependencies (esbuild, sass, typescript)
- Committed: No (git-ignored; recreate with `npm install`)

**`.git/`, `.github/workflows/`:**
- Purpose: Git repository and CI/CD
- Committed: Yes (.github/workflows/ defines GitHub Actions tests/deploy)

**`.pytest_cache/`, `.ruff_cache/`, `__pycache__/`:**
- Purpose: Tool caches
- Committed: No (git-ignored)

## Build & Development

**Frontend Build:**
```bash
npm run build       # Compile TypeScript (esbuild) + SCSS (sass)
npm run build:ts    # TypeScript only
npm run build:css   # SCSS only
npm run check       # Run tsc --noEmit (typecheck without emit)
```

**Backend:**
```bash
python manage.py runserver     # Development server (Django)
python manage.py migrate       # Apply database migrations
python manage.py collectstatic # Collect static files for production
```

**Testing:**
```bash
pytest              # Run all tests
pytest tests/test_quiz.py -v   # Run specific test file with verbose output
```

**Watch Mode:**
- No built-in watch; use `npm run build && npm run build` with file watcher (e.g., nodemon, fswatch)

---

*Structure analysis: 2026-03-25*
