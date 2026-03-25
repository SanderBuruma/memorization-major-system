---
plan: 03-01
phase: 03-cleanup
status: complete
started: 2026-03-25
completed: 2026-03-25
---

# Plan 03-01 Summary: Cleanup Legacy Code

## What Was Built

Removed all legacy RGB lerp code and mastery CSS classes/vars from the codebase, migrating consumers first to prevent regressions.

## Tasks Completed

| Task | Name | Status | Commit |
|------|------|--------|--------|
| 1 | Migrate consumers + delete legacy SCSS vars/classes | ✓ | 2343dd5 |
| 2 | Delete dead JS code from ui.ts | ✓ | 488772a |

## Key Changes

### Task 1 — SCSS + Consumer Migration
- `_profile.scss`: Migrated bar-fill colors from `--color-mastery-*` vars to hardcoded hex values
- `wiki.ts`: Rewrote mastery color help text to describe OKLCH hue system
- `_variables.scss`: Deleted all `--bg-mastery-*` and `--color-mastery-*` vars from 4 theme blocks (32 declarations)
- `_grid.scss`: Deleted `.mastery-0..4` class rules
- `test_theme.py`: Removed mastery entries from `BG_VARS` and `FG_ACCENT_VARS` classification lists

### Task 2 — Dead JS Removal
- `ui.ts`: Deleted `type RGB`, `parseColor()`, `lerpRGB()`, `GRADIENT_YELLOW`, `GRADIENT_RED`, `GRADIENT_GREEN`, and `el.className.replace(/mastery-\d/g, '')` line

## Deviations

None — plan executed as written.

## Self-Check: PASSED

- [x] 197 tests pass
- [x] TypeScript compiles cleanly
- [x] CSS builds without errors
- [x] No references to lerpRGB/parseColor/GRADIENT_* remain
- [x] Profile section bars use hardcoded hex (no broken var references)

## key-files

### created
(none)

### modified
- `src/scss/_variables.scss`
- `src/scss/_grid.scss`
- `src/scss/_profile.scss`
- `src/ts/wiki.ts`
- `src/ts/ui.ts`
- `tests/test_theme.py`
