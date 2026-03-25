---
phase: 1
slug: core-color-computation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 1 — Validation Strategy

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
| 1-01-01 | 01 | 1 | COLOR-01 | unit | `python -m pytest tests/test_theme.py::TestThemeCompleteness -x` | ✅ (needs var updates) | ⬜ pending |
| 1-01-02 | 01 | 1 | COLOR-01 | unit | `python -m pytest tests/test_theme.py::TestThemeCompleteness::test_all_themes_cover_same_variables -x` | ✅ (needs new vars in all themes) | ⬜ pending |
| 1-01-03 | 01 | 1 | COLOR-02 | manual | Visual: unquizzed cells show theme background | N/A | ⬜ pending |
| 1-01-04 | 01 | 1 | COLOR-02 | manual | Visual: score=-10 shows red, score=+10 shows green | N/A | ⬜ pending |
| 1-01-05 | 01 | 1 | COLOR-03 | manual | Visual: scored cells have visible font color matching hue | N/A | ⬜ pending |
| 1-01-06 | 01 | 1 | COLOR-04 | unit | `python -m pytest tests/test_mastery_colors.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mastery_colors.py` — pure Python unit tests for scoreToHue hue anchor values and sqrt-easing math (COLOR-04). Logic ported 1:1 from TypeScript since it's pure arithmetic.

*Existing test_theme.py covers CSS custom property assertions but needs var list updates.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Score 0 clears inline style | COLOR-02 | Requires browser DOM — no browser test harness in project | Open app, verify unquizzed cells = theme background |
| Score extremes show correct hues | COLOR-02 | Requires rendered OKLCH in browser | Open app with test scores, verify red (-10) and green (+10) |
| Font color matches background hue | COLOR-03 | Requires browser CSS evaluation | Open app, verify scored cells have readable matching-hue text |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
