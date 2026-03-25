---
phase: 3
slug: cleanup
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-03-25
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + tsc + esbuild |
| **Config file** | none — run from project root |
| **Quick run command** | `python -m pytest tests/test_theme.py -x && npm run check` |
| **Full suite command** | `python -m pytest tests/ && npm run check` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_theme.py -x && npm run check`
- **After every plan wave:** Run `python -m pytest tests/ && npm run check && npm run build:css`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | CLEAN-01 | unit | `python -m pytest tests/test_theme.py -x` | ✅ | ⬜ pending |
| 3-01-02 | 01 | 1 | CLEAN-01 | smoke | `npm run build:css && ! grep -q 'mastery-[0-4]' static/css/app.css` | ✅ | ⬜ pending |
| 3-01-03 | 01 | 1 | CLEAN-02 | unit | `npm run check` | ✅ | ⬜ pending |
| 3-01-04 | 01 | 1 | CLEAN-02 | smoke | `npm run build && ! grep -q 'lerpRGB\|parseColor\|GRADIENT_' static/js/app.js` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Profile section bars still render | CLEAN-01 | Requires browser to check visual rendering after var migration | Open profile, check activity bars still have colors |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
