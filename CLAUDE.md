# CLAUDE.md - Major System Trainer

## Architecture
- Single-page app: `index.html` handles all views as JS-rendered sections (Grid, Quiz, Reference, Translate, Profile)
- New features should be added as sections within the SPA, not as separate Django templates/pages
- Section switching via `showSection(name)` — add HTML as `<div id="section-{name}" class="section">`, render content in JS

## JS Structure
- All JS lives in `templates/js/`, included via `{% include %}` in order: state → persistence → theme → quiz → ui → profile → init
- State consolidated into `S` object (wordlist, mapping, score, etc.) and `MODES` configs (per-quiz-mode scores, history, DOM IDs)
- Quiz modes share a generic engine (`startMode`/`checkMode`/`skipMode`); mode-specific behavior lives in MODES config functions
- Persistence uses `STATE_FIELDS` manifest — add new persisted fields there, not in saveState/loadState individually
- Thin wrapper functions (`checkQuiz`, `skipQuiz`, etc.) keep HTML onclick compatibility
- Custom word validation: must match `/^[a-z]/`

## API
- `views.py` uses `_FIELD_MAP` dict to map JS keys to model fields with type validation
- Score and theme have special handling outside the field map

## Deployment
- Pushing to `master` triggers CI/CD (GitHub Actions: test → deploy to VPS)
- **Always check deployment status** after pushing before ending the conversation
  - Use `gh run list --limit 1` and `gh run watch <id>` to monitor
  - If the deploy fails, fix and push again before stopping
