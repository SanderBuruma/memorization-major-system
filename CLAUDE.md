# CLAUDE.md - Major System Trainer

## Architecture
- Single-page app: `index.html` handles all views as JS-rendered sections (Grid, Quiz, Reference, Translate, Profile, Settings)
- New features should be added as sections within the SPA, not as separate Django templates/pages
- Section switching via `showSection(name)` — add HTML as `<div id="section-{name}" class="section">`, render content in JS
- Onboarding tutorial: 5-step overlay, auto-shown when `tutorialSeen` is false, replayable from settings

## TypeScript / JS Structure
- Source lives in `src/ts/` (8 files): types → state → persistence → theme → quiz → ui → profile → init
- Built with esbuild into `static/js/app.js` (IIFE bundle, not committed — built by CI and VPS deploy)
- Typecheck with `tsc --noEmit`; build + check via `npm run check`
- State consolidated into `appState` object and `MODES` configs (per-quiz-mode scores, history, DOM IDs)
- Quiz modes share a generic engine (`startMode`/`checkMode`/`skipMode`); mode-specific behavior lives in MODES config
- Scoring is time-based: piecewise contribution (+5 at ≤0.5s, 0 at 2s, -5 at ≥10s), stored as weighted running average of up to 10 values (0.7 decay, newest weighs most)
- Each mode has `scoreHistory: Record<string, number[]>` (raw contributions) alongside `scores: Record<string, number>` (computed weighted averages)
- Response timer pauses for 500ms when typed text is a correct prefix of the answer (only thinking time counts)
- Persistence uses `STATE_FIELDS` manifest — add new persisted fields there, not in saveState/loadState individually
- HTML onclick handlers exposed via `Object.assign(window, ...)` in init.ts
- Custom word validation: must match `/^[a-z]/`
- Cache busting via `ManifestStaticFilesStorage` — `collectstatic` hashes filenames

## SCSS / CSS Structure
- Source lives in `src/scss/` (12 files): variables, base, topbar, grid, quiz, reference, translate, profile, settings, tutorial, responsive, main
- Compiled with `sass` into `static/css/app.css` (compressed, no source map, not committed — built by CI and VPS deploy)
- CSS custom properties (runtime theme values) defined in `_variables.scss`; SCSS variables for compile-time constants
- 4 themes via `[data-theme]` attribute: dark, light, oled, high-contrast
- Build: `npm run build:css`; full build: `npm run build` (JS + CSS)

## Python Structure
- `trainer/validator.py` — CMU phoneme → Major System digit encoding
- `trainer/generator.py` — word selection + wordlist generation logic
- `scripts/lookup.py` — CLI tool for number/word lookups
- `tests/` — all test files (test_api, test_aria, test_associations, test_candidates, test_dyslexia_font, test_encode, test_mastery_colors, test_persistence, test_pool_quiz, test_theme, test_time_scoring, test_tutorial, test_wiki_data)

## API
- `views.py` uses `_FIELD_MAP` dict to map JS keys to model fields with type validation
- Score, theme, `tutorialSeen`, and `dyslexiaFont` have special handling outside the field map
- `GET /api/candidates/<digits>` — returns concrete noun suggestions for a 1- or 2-digit number (from `build_candidate_map`)
- `POST /api/encode` — encodes words to Major System digits, body: `{"text": "..."}`, returns `[{"word", "digits"}]`

## QuizState model fields
- `tutorial_seen` (bool) — whether onboarding tutorial was completed
- `dyslexia_font` (bool) — OpenDyslexic font preference
- `theme` (str, max 20) — active theme name (dark/light/oled/high-contrast)

## Deployment
- Pushing to `master` triggers CI/CD (GitHub Actions: test → deploy to VPS)
- **Always check deployment status** after pushing before ending the conversation
  - Use `gh run list --limit 1` and `gh run watch <id>` to monitor
  - If the deploy fails, fix and push again before stopping
