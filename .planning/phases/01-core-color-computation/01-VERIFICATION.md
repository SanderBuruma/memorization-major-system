---
phase: 01-core-color-computation
verified: 2026-03-25T00:00:00Z
status: human_needed
score: 4/4 must-haves verified
human_verification:
  - test: "Dark theme grid — visual weight uniformity"
    expected: "Every non-zero scored cell has equal visual saturation/brightness regardless of whether the score is ±1 or ±10. No cell fades toward invisible at low scores."
    why_human: "OKLCH constant-L/C property cannot be confirmed without rendering the browser; getPropertyValue reads are verified in code but rendered output requires visual inspection."
  - test: "Dark theme grid — hue direction"
    expected: "Negative scores show warm hues (red/yellow); positive scores show cool hues (blue/green). Score 0 cells show the plain dark background with no color applied at all."
    why_human: "The score-to-hue formula is unit-tested and the CSS write is code-verified, but whether the browser actually renders oklch() strings as visually distinct hues requires a human to confirm."
  - test: "Dark theme grid — font readability"
    expected: "Cell text (numbers and words) is readable on colored backgrounds. The same hue is used for foreground and background, just at a contrasting lightness (fgL=80% vs bgL=35% in dark theme)."
    why_human: "OKLCH contrast ratio cannot be numerically verified here; requires visual confirmation that no hue makes text unreadable."
  - test: "Dark theme grid — monotonic progression"
    expected: "Score +5 is visually between +1 and +10 (between blue and green). Score -5 is visually between -1 and -10 (between blue and yellow). The color steps feel gradual, not jumpy."
    why_human: "Monotonicity is verified by math tests for the Python port; TypeScript implementation matches by code review. Whether the visual result feels perceptually monotonic requires eyes-on review."
---

# Phase 1: Core Color Computation Verification Report

**Phase Goal:** Grid cells display consistent-weight hue-based mastery colors in the dark theme
**Verified:** 2026-03-25
**Status:** human_needed (all automated checks passed; 4 visual items require human confirmation)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every non-zero scored cell has equal visual weight regardless of score magnitude — no cell fades toward invisible | ? NEEDS HUMAN | `updateMasteryColors()` writes constant bgL/bgC (35%/0.14 dark) to every non-zero cell via OKLCH. Code is correct; visual output requires browser rendering. |
| 2 | Negative scores show red/yellow hues, positive scores show blue/green hues, score 0 shows plain theme background | ? NEEDS HUMAN | `scoreToHue()` formula verified: -10→27(red), -5→90(yellow), 0→no inline style, +10→145(green). Score 0 clears both `backgroundColor` and `color`. Visual requires human. |
| 3 | Score-to-hue progression is monotonic: +5 between +1 and +10; -5 between -1 and -10 | ✓ VERIFIED | 3 monotonicity unit tests pass in `test_mastery_colors.py`; TypeScript `scoreToHue()` in `ui.ts:595-606` matches the tested Python port exactly (same formula, same corrected direction). |
| 4 | Cell font color uses same hue as background at a contrasting lightness, remaining readable | ? NEEDS HUMAN | Code at `ui.ts:639-640` writes `oklch(${fgL} ${fgC} ${H})` to `el.style.color` using same H. Dark theme: fgL=80% vs bgL=35% — contrasting lightness confirmed by values. Readability requires visual. |

**Score:** 4/4 truths verified or pending human only (no automated failures)

---

## Required Artifacts

### Plan 01-01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/scss/_variables.scss` | Per-theme OKLCH mastery constants as CSS custom properties | ✓ VERIFIED | Lines 34-38, 65-69, 96-101, 127-132 each define `--mastery-bg-L`, `--mastery-bg-C`, `--mastery-fg-L`, `--mastery-fg-C` with theme-appropriate values. |
| `tests/test_mastery_colors.py` | Pure-math unit tests for scoreToHue anchors and sqrt easing (min 30 lines) | ✓ VERIFIED | 124 lines, 11 test methods in 3 classes. Covers boundaries (-10,-5,-1,+1,+5,+10), monotonicity (3 segments), and sqrt easing (positive + negative). All 11 tests pass. |
| `tests/test_theme.py` | Updated NON_COLOR_VARS classification for mastery vars | ✓ VERIFIED | Line 26-28: `NON_COLOR_VARS` includes all four mastery vars. `test_all_vars_classified` passes (31 total tests pass, 98 subtests). |

### Plan 01-02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ts/ui.ts` | `scoreToHue()`, `getMasteryConstants()`, rewritten `updateMasteryColors()` | ✓ VERIFIED | `scoreToHue` at lines 595-606; `getMasteryConstants` at lines 610-618; `updateMasteryColors` at lines 620-642. All three present and substantive. TypeScript compiles clean, build produces 77.0kb bundle. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_theme.py` | `src/scss/_variables.scss` | CSS var parsing + NON_COLOR_VARS classification | ✓ WIRED | `extract_css_vars()` parses `_variables.scss` at line 16. `NON_COLOR_VARS` at line 26-28 classifies all four mastery vars. `TestThemeCompleteness.test_all_vars_classified` asserts every parsed var is classified. |
| `src/ts/ui.ts` | `src/scss/_variables.scss` | `getComputedStyle` reads `--mastery-bg-L`, `--mastery-bg-C`, `--mastery-fg-L`, `--mastery-fg-C` | ✓ WIRED | `getMasteryConstants()` at lines 611-617 reads all four properties via `getPropertyValue`. Called once before the cell loop in `updateMasteryColors()`. |
| `src/ts/ui.ts` | `DOM #grid .grid-cell` | `el.style.backgroundColor` and `el.style.color` set to `oklch()` strings | ✓ WIRED | Lines 639-640: `el.style.backgroundColor = \`oklch(${bgL} ${bgC} ${H})\`` and `el.style.color = \`oklch(${fgL} ${fgC} ${H})\``. Both styles cleared at score 0 (lines 634-635). |
| `src/ts/init.ts` + `persistence.ts` | `updateMasteryColors` in `ui.ts` | Import and call sites | ✓ WIRED | Imported in `init.ts:6` and `persistence.ts:2`; called at `init.ts:53`, `init.ts:94`, `persistence.ts:30`, and `ui.ts:442` (importJSON handler). Function is actively wired into the application lifecycle. |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| COLOR-01 | 01-01 + 01-02 | Grid cells use OKLCH color space with constant lightness and chroma, varying only hue | ✓ SATISFIED | `updateMasteryColors()` writes `oklch(${bgL} ${bgC} ${H})` — L and C are constants from CSS vars, only H varies per score. |
| COLOR-02 | 01-01 + 01-02 | Score-to-hue: red (-10) → yellow (~-5) → blue (±1) → green (+10), score 0 shows theme background | ✓ SATISFIED | `scoreToHue()` anchors: -10→27(red), -5→90(yellow), ±0→264(blue), +10→145(green). Score 0: both inline styles cleared (`ui.ts:634-635`). Validated by 6 boundary unit tests. |
| COLOR-03 | 01-02 | Font color uses same hue as background at contrasting lightness for readability | ✓ SATISFIED (code) / ? NEEDS HUMAN (visual) | `ui.ts:640` writes `fgL`/`fgC` from `--mastery-fg-L`/`--mastery-fg-C` with same H. Dark theme: fgL=80% vs bgL=35% is a 45pp lightness separation. Visual readability needs human confirmation. |
| COLOR-04 | 01-01 + 01-02 | Score-to-hue curve uses sqrt easing for better perceptual separation at low scores | ✓ SATISFIED | `scoreToHue()` uses `Math.sqrt(score/10)` etc. at `ui.ts:598,601,604`. 2 sqrt-easing unit tests confirm sqrt gives more separation than linear at low scores. |

No orphaned requirements: REQUIREMENTS.md maps COLOR-01 through COLOR-04 to Phase 1 (all claimed by plans 01-01 and 01-02). THEME-01 through THEME-03 are mapped to Phase 2; CLEAN-01 and CLEAN-02 to Phase 3 — none are orphaned for Phase 1.

---

## Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `src/ts/ui.ts:591-593` | `parseColor`, `lerpRGB`, `GRADIENT_*` dead RGB lerp code preserved | ℹ Info | Intentional: PLAN 01-02 explicitly defers removal to Phase 3. No functional impact. |

No TODO/FIXME/placeholder comments found in any modified file. No stub implementations found.

---

## Human Verification Required

### 1. Visual Weight Uniformity

**Test:** Open the dark theme grid after taking quizzes to generate scores at several different magnitudes (e.g., one cell at ±1, one at ±5, one at ±10). Compare the visual intensity of cells side-by-side.
**Expected:** All non-zero cells appear equally saturated and bright. A cell with score +1 should not look washed out compared to a cell with score +10 — they should both look equally "present" as colors, just at different hues.
**Why human:** OKLCH constant-L/C guarantees this mathematically, but the actual rendered result depends on browser OKLCH support and display calibration.

### 2. Hue Direction and Score-0 Clearing

**Test:** In the dark theme grid, identify cells with negative scores, positive scores, and unquizzed cells (score 0).
**Expected:** Negative-score cells show warm colors (red/orange/yellow). Positive-score cells show cool colors (blue/teal/green). Unquizzed cells show the plain dark background (#121220) with no color tint at all.
**Why human:** The `scoreToHue()` math and the inline style writes are code-verified, but whether the oklch() strings render as visually distinct warm vs cool colors needs eyes-on confirmation.

### 3. Font Readability on Colored Backgrounds

**Test:** Look at the numbers and words inside colored grid cells across a range of scores, including cells near the extremes (score -10 red, score +10 green) and mid-range.
**Expected:** All cell text is clearly readable. The font color should be a lighter/brighter version of the same hue as the background (not black or white, but hue-matched), remaining legible against the dark background.
**Why human:** OKLCH contrast ratio cannot be numerically verified in this context. The 45pp lightness gap (bgL=35%, fgL=80%) should be sufficient, but real-world readability depends on rendering.

### 4. Monotonic Visual Progression

**Test:** Compare cells at scores +1, +5, and +10 side by side (or -1, -5, -10). The progression should feel gradual.
**Expected:** Score +5 looks visually between +1 (near blue) and +10 (green). No sudden jumps. The sqrt easing should give a natural, not mechanical, feel.
**Why human:** Math tests verify monotonicity numerically; the subjective "feels gradual" quality requires human judgment.

---

## Summary

All automated verification passed. The four artifacts exist, are substantive, and are correctly wired. All four COLOR requirements are satisfied by the implementation. The 31 automated tests (20 theme + 11 mastery math) all pass. The TypeScript build is clean. No stubs, no placeholders, no broken connections.

The four human verification items are visual quality checks — they cannot fail in a way that would block the phase, but they are the final confirmation that the OKLCH implementation renders correctly in a browser.

---

_Verified: 2026-03-25_
_Verifier: Claude (gsd-verifier)_
