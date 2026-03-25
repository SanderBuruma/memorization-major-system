---
phase: 2
slug: theme-integration
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-03-25
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Django TestCase) |
| **Config file** | none — run from project root |
| **Quick run command** | `python -m pytest tests/test_theme.py -x` |
| **Full suite command** | `python -m pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_theme.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | THEME-01 | unit | `python -m pytest tests/test_theme.py::TestThemeCompleteness -x` | ✅ (already passing) | ⬜ pending |
| 2-01-02 | 01 | 1 | THEME-01 | manual | Visual: switch themes, check scored grid cells | N/A | ⬜ pending |
| 2-01-03 | 01 | 1 | THEME-02 | manual | Visual: theme switch refreshes colors immediately | N/A | ⬜ pending |
| 2-01-04 | 01 | 1 | THEME-03 | manual | Visual: high-contrast cells readable at all hue endpoints | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| L/C values produce correct visual result per theme | THEME-01 | Requires browser rendering of OKLCH inline styles | Switch themes with scored cells, verify colors match theme character |
| Theme switch refreshes mastery colors | THEME-02 | Requires browser DOM update observation | Switch themes, verify no stale colors remain |
| High-contrast meets WCAG AA | THEME-03 | Requires computed OKLCH contrast ratio check | Use browser dev tools to check fg vs bg contrast at yellow/green hue endpoints |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
