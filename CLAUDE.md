# CLAUDE.md - Major System Trainer

## Deployment
- Pushing to `master` triggers CI/CD (GitHub Actions: test → deploy to VPS)
- **Always check deployment status** after pushing before ending the conversation
  - Use `gh run list --limit 1` and `gh run watch <id>` to monitor
  - If the deploy fails, fix and push again before stopping
