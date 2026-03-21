# CLAUDE.md - Major System Trainer

## Architecture
- Single-page app: `index.html` handles all views as JS-rendered sections (Grid, Quiz, Reference, Translate, Profile)
- New features should be added as sections within the SPA, not as separate Django templates/pages
- Section switching via `showSection(name)` — add HTML as `<div id="section-{name}" class="section">`, render content in JS

## TypeScript / JS Structure
- Source lives in `src/ts/` (8 files): types → state → persistence → theme → quiz → ui → profile → init
- Built with esbuild into `static/js/app.js` (IIFE bundle, not committed — built by CI and VPS deploy)
- Typecheck with `tsc --noEmit`; build + check via `npm run check`
- State consolidated into `appState` object and `MODES` configs (per-quiz-mode scores, history, DOM IDs)
- Quiz modes share a generic engine (`startMode`/`checkMode`/`skipMode`); mode-specific behavior lives in MODES config
- Persistence uses `STATE_FIELDS` manifest — add new persisted fields there, not in saveState/loadState individually
- HTML onclick handlers exposed via `Object.assign(window, ...)` in init.ts
- Custom word validation: must match `/^[a-z]/`
- Cache busting via `ManifestStaticFilesStorage` — `collectstatic` hashes filenames

## SCSS / CSS Structure
- Source lives in `src/scss/` (10 files): variables, base, topbar, grid, quiz, reference, translate, profile, responsive, main
- Compiled with `sass` into `static/css/app.css` (compressed, no source map, not committed — built by CI and VPS deploy)
- CSS custom properties (runtime theme values) defined in `_variables.scss`; SCSS variables for compile-time constants
- Build: `npm run build:css`; full build: `npm run build` (JS + CSS)

## Python Structure
- `trainer/validator.py` — CMU phoneme → Major System digit encoding
- `trainer/generator.py` — word selection + wordlist generation logic
- `scripts/lookup.py` — CLI tool for number/word lookups
- `tests/` — all test files (test_api, test_associations, test_persistence, test_pool_quiz, test_theme)

## API
- `views.py` uses `_FIELD_MAP` dict to map JS keys to model fields with type validation
- Score and theme have special handling outside the field map

## Deployment
- Pushing to `master` triggers CI/CD (GitHub Actions: test → deploy to VPS)
- **Always check deployment status** after pushing before ending the conversation
  - Use `gh run list --limit 1` and `gh run watch <id>` to monitor
  - If the deploy fails, fix and push again before stopping
