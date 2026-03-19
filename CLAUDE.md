# CLAUDE.md - Major System Trainer

## Architecture
- Single-page app: `index.html` handles all views as JS-rendered sections (Grid, Quiz, Reference, Translate, Profile)
- New features should be added as sections within the SPA, not as separate Django templates/pages
- Section switching via `showSection(name)` — add HTML as `<div id="section-{name}" class="section">`, render content in JS

## Deployment
- Pushing to `master` triggers CI/CD (GitHub Actions: test → deploy to VPS)
- **Always check deployment status** after pushing before ending the conversation
  - Use `gh run list --limit 1` and `gh run watch <id>` to monitor
  - If the deploy fails, fix and push again before stopping
