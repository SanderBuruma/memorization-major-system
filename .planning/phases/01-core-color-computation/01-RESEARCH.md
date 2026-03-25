# Phase 1: Core Color Computation - Research

**Researched:** 2026-03-25
**Domain:** OKLCH hue-rotation color computation in TypeScript; pure function replacement inside existing `updateMasteryColors()`
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COLOR-01 | Grid cells use OKLCH color space with constant lightness and chroma, varying only hue based on mastery score | OKLCH `oklch(L C H)` string written to `el.style.backgroundColor`; L and C held constant per theme, H derived from score |
| COLOR-02 | Score-to-hue mapping follows red (score -10) → yellow (~-5) → blue (±1) → green (+10), with score 0 showing theme background (no color) | Piecewise linear `scoreToHue()` function; score 0 clears inline style |
| COLOR-03 | Font color uses same hue as cell background at a contrasting lightness value for readability | Same H and C, separate fg-L value; written to `el.style.color` in the same cell loop |
| COLOR-04 | Score-to-hue curve uses sqrt easing for better perceptual separation at low scores | `Math.sqrt(t)` applied to the linear interpolation parameter before computing H; mirrors existing lerpRGB sqrt pattern |
</phase_requirements>

---

## Summary

Phase 1 replaces the RGB-lerp approach in `updateMasteryColors()` (src/ts/ui.ts, lines 595–617) with a hue-rotation approach using the OKLCH color space. The current implementation interpolates from the surface color toward fixed RGB targets (`GRADIENT_GREEN`, `GRADIENT_YELLOW`, `GRADIENT_RED`), producing cells with inconsistent perceived brightness — a green at score +10 is vivid while a green at score +3 is nearly invisible. The replacement holds perceived lightness (L) and chroma (C) constant and varies only the hue angle (H), so every scored cell has equal visual presence.

The scope is narrow: three new pure functions (`scoreToHue`, `getMasteryConstants`, and the rewritten `updateMasteryColors`) added to `ui.ts`, plus four new CSS custom properties added to `_variables.scss` under the `:root`/dark block only. Phase 1 targets the dark theme exclusively; other themes are Phase 2. No new files, no new dependencies, no build-step changes.

The main technical consideration is that `scoreToHue` must use OKLCH hue values (approximately +30° offset from HSL) and that sqrt easing must be applied to the linear interpolation parameter — not to the hue angle directly — to preserve the correct inflection shape. The theme test in `tests/test_theme.py` validates CSS variables against a parsed `_variables.scss`; when adding `--mastery-bg-L` etc. to the dark block the test's completeness assertion (`test_all_themes_cover_same_variables`) will fail until the same variables are added to light, oled, and high-contrast blocks too. This must be handled during Phase 1 by adding placeholder values to all four blocks even though only dark is exercised visually.

**Primary recommendation:** Add `scoreToHue()` and `getMasteryConstants()` as module-level functions above `updateMasteryColors()`, rewrite that function body, and add the four CSS custom props to all four theme blocks in `_variables.scss`. Keep the old `lerpRGB`, `parseColor`, and gradient constants in place — they are cleaned up in Phase 3.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `oklch()` native CSS | Baseline (Chrome 111+, Firefox 113+, Safari 15.4+) | Color output string | Perceptually uniform L; no lib needed; 92%+ global support |
| TypeScript in `src/ts/ui.ts` | 5.7.x (existing) | Compute H from score, write inline styles | Same layer as existing `updateMasteryColors()` |
| SCSS custom properties in `_variables.scss` | existing sass 1.98.x | Per-theme L/C constants | Single source of truth; matches existing `--bg-surface` pattern |

### No New Dependencies
This phase adds zero new packages. OKLCH strings are plain template literals:
```
`oklch(${bgL} ${bgC} ${H})`
```

---

## Architecture Patterns

### Recommended File Changes

```
src/
├── ts/
│   └── ui.ts           # Add scoreToHue(), getMasteryConstants(); rewrite updateMasteryColors() body
└── scss/
    └── _variables.scss  # Add --mastery-bg-L, --mastery-bg-C, --mastery-fg-L, --mastery-fg-C to ALL four theme blocks
```

### Pattern 1: scoreToHue — Piecewise Linear with Sqrt Easing

**What:** Map score (-10..+10) to an OKLCH hue angle using two piecewise segments with sqrt easing on the interpolation parameter.

**OKLCH hue reference values (approximate; require visual tuning):**
- Red: H ≈ 27
- Yellow: H ≈ 90
- Blue: H ≈ 264
- Green: H ≈ 145

**Score 0 is handled by the caller** — `scoreToHue` is only called for non-zero scores.

**Sqrt easing:** The existing `updateMasteryColors()` already applies `Math.sqrt(score / 10)` as the lerp parameter. The new implementation must preserve this shape. Apply `Math.sqrt(t)` to `t` before using it to interpolate between hue anchors.

```typescript
// Source: derived from existing lerpRGB sqrt pattern + ARCHITECTURE.md hue map
function scoreToHue(score: number): number {
  if (score < 0) {
    if (score >= -5) {
      // -5..0 → yellow(90)..blue(264), sqrt-eased
      const t = Math.sqrt((-score) / 5);   // 0..1 as score goes -5..0 away from 0
      return 264 - t * (264 - 90);         // 264 at score 0-side, 90 at score -5
    } else {
      // -10..-5 → red(27)..yellow(90), sqrt-eased
      const t = Math.sqrt((-score - 5) / 5);
      return 90 - t * (90 - 27);           // 90 at score -5-side, 27 at score -10
    }
  } else {
    // +1..+10 → blue(264)..green(145), sqrt-eased
    const t = Math.sqrt(score / 10);
    return 264 - t * (264 - 145);          // 264 at score 0-side, 145 at score +10
  }
}
```

**Note:** The exact hue anchor values (27, 90, 264, 145) are estimates from STACK.md and will need visual calibration during implementation. The structure and easing shape are correct.

### Pattern 2: getMasteryConstants — Read CSS Vars Once Before the Loop

**What:** Read the four CSS custom properties from `getComputedStyle(document.documentElement)` a single time before the cell iteration loop.

**Why this matters:** `getComputedStyle` can trigger layout recalculation if called inside a `forEach` loop over DOM elements. The L/C constants are theme-level (same for every cell), so reading them once is both correct and avoids repeated layout triggers.

```typescript
// Source: ARCHITECTURE.md Pattern 2; mirrors existing --bg-surface read in updateMasteryColors()
interface MasteryConstants { bgL: string; bgC: string; fgL: string; fgC: string; }

function getMasteryConstants(): MasteryConstants {
  const style = getComputedStyle(document.documentElement);
  return {
    bgL: style.getPropertyValue('--mastery-bg-L').trim(),
    bgC: style.getPropertyValue('--mastery-bg-C').trim(),
    fgL: style.getPropertyValue('--mastery-fg-L').trim(),
    fgC: style.getPropertyValue('--mastery-fg-C').trim(),
  };
}
```

### Pattern 3: Rewritten updateMasteryColors — Inline OKLCH Styles

**What:** Replace the RGB lerp body with OKLCH string writes. Score 0 clears both `backgroundColor` and `color` inline styles so the CSS `--bg-surface` applies naturally.

```typescript
// Source: ARCHITECTURE.md Pattern 3 (adapted from authoritative code example)
export function updateMasteryColors(): void {
  if (!appState.keys.length) return;
  const { bgL, bgC, fgL, fgC } = getMasteryConstants();
  const cells = document.querySelectorAll('#grid .grid-cell');
  cells.forEach((cell) => {
    const key = cell.getAttribute('data-key');
    if (!key) return;
    const raw = (MODES.quiz.scores[key] ?? 0)
              + (MODES.reverse.scores[key] ?? 0)
              + (MODES.mixed.scores[key] ?? 0);
    const score = Math.max(-10, Math.min(10, raw));
    const el = cell as HTMLElement;
    el.className = el.className.replace(/mastery-\d/g, '').trim();  // kept until Phase 3
    if (score === 0) {
      el.style.backgroundColor = '';
      el.style.color = '';
      return;
    }
    const H = scoreToHue(score);
    el.style.backgroundColor = `oklch(${bgL} ${bgC} ${H})`;
    el.style.color = `oklch(${fgL} ${fgC} ${H})`;
  });
}
```

### Pattern 4: CSS Custom Properties for Dark Theme (Phase 1)

**What:** Add to the `:root, [data-theme="dark"]` block in `_variables.scss`. Also add stub values to light, oled, and high-contrast blocks to prevent `test_all_themes_cover_same_variables` failure.

Dark theme starting values (require visual calibration):
```scss
// Source: ARCHITECTURE.md Pattern 2 example values; reconciled from STACK.md estimates
:root, [data-theme="dark"] {
  /* ... existing vars ... */
  --mastery-bg-L: 35%;
  --mastery-bg-C: 0.14;
  --mastery-fg-L: 80%;
  --mastery-fg-C: 0.16;
}
```

Stub values for other themes (exact calibration is Phase 2):
```scss
[data-theme="light"] {
  /* ... existing vars ... */
  --mastery-bg-L: 75%;
  --mastery-bg-C: 0.12;
  --mastery-fg-L: 30%;
  --mastery-fg-C: 0.14;
}

[data-theme="oled"] {
  /* ... existing vars ... */
  --mastery-bg-L: 25%;
  --mastery-bg-C: 0.16;
  --mastery-fg-L: 85%;
  --mastery-fg-C: 0.18;
}

[data-theme="high-contrast"] {
  /* ... existing vars ... */
  --mastery-bg-L: 20%;
  --mastery-bg-C: 0.22;
  --mastery-fg-L: 90%;
  --mastery-fg-C: 0.24;
}
```

### Anti-Patterns to Avoid

- **Using HSL instead of OKLCH:** HSL L is not perceptually uniform; blue at `hsl(240, 70%, 35%)` appears much darker than yellow at the same L. The entire point of this phase is perceptual uniformity. Use `oklch()` only.
- **Hardcoding L/C in TypeScript:** Duplicates what `_variables.scss` already owns. Use `getComputedStyle` to read CSS vars at call time.
- **Applying sqrt to hue angle directly:** `Math.sqrt(H)` distorts the hue scale non-linearly in ways not related to perceptual score separation. Apply sqrt to the segment-local `t` parameter (0..1), then linearly interpolate hue anchors.
- **Calling getMasteryConstants() inside forEach:** Triggers repeated style recalculation. Read once before the loop.
- **Omitting score 0 guard:** An unquizzed cell with score 0 must show the theme surface background. Clear `el.style.backgroundColor` and `el.style.color` on score 0 — do not write `oklch(L C 264)` for it.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Perceptually uniform color space | Custom per-hue brightness compensation table | `oklch()` native CSS | OKLCH's L component is already perceptual; compensation tables are fragile and unverifiable |
| Color library for OKLCH strings | `chroma.js`, `culori`, etc. | Plain template literals | 3 numbers; zero library value for this use case |
| Theme detection in JS | `if (theme === 'dark')` switch | CSS custom props + `getComputedStyle` | Theme is already encoded in `data-theme` attribute and CSS vars; duplicating in JS creates split-brain |

---

## Common Pitfalls

### Pitfall 1: test_all_themes_cover_same_variables Failure

**What goes wrong:** `tests/test_theme.py::TestThemeCompleteness::test_all_themes_cover_same_variables` checks that every CSS variable present in the dark theme block also exists in light, oled, and high-contrast blocks. Adding `--mastery-bg-L` etc. only to the dark block will fail this test.

**Why it happens:** The test intentionally enforces symmetry to prevent theme-specific undefined vars.

**How to avoid:** Add all four new `--mastery-*` custom properties to every theme block in `_variables.scss` in the same commit. Stub values for non-dark themes are fine for Phase 1; they will be calibrated in Phase 2.

### Pitfall 2: test_all_vars_classified Failure

**What goes wrong:** `tests/test_theme.py::TestThemeCompleteness::test_all_vars_classified` verifies every CSS variable is in a named category set. New `--mastery-bg-L` etc. are not in any existing set (`BG_VARS`, `TEXT_VARS`, etc.), so the test will fail.

**Why it happens:** The test enforces explicit classification of all CSS vars. `--mastery-bg-L` is a numeric constant, not a color, so it does not belong to `BG_VARS`.

**How to avoid:** Add the four new vars to a new set (e.g., `NON_COLOR_VARS`) in `test_theme.py` and add that set to `ALL_CLASSIFIED`. Since these are numeric values (not hex colors), the existing luminance assertions should not run against them — adding to `NON_COLOR_VARS` is the correct approach.

**Warning signs:** CI failure on `test_all_vars_classified` immediately after adding CSS vars.

### Pitfall 3: Score 0 Produces a Blue Cell Instead of No Color

**What goes wrong:** If the score 0 guard is omitted or misplaced, `scoreToHue(0)` falls through to the positive branch and returns hue 264 (blue), producing a blue-tinted cell for unquizzed items.

**Why it happens:** The positive branch uses `Math.sqrt(0 / 10) = 0`, which maps to hue 264. That is a valid color, not transparent.

**How to avoid:** Check `if (score === 0)` before calling `scoreToHue`. Clear both `backgroundColor` and `color` inline styles and return.

### Pitfall 4: OKLCH L Value Semantics — Percentage vs Decimal

**What goes wrong:** OKLCH L can be specified as a percentage (`35%`) or a decimal (`0.35`). `getComputedStyle` returns the value as-is from the SCSS definition. If the CSS var uses `35%` and the JS template literal includes it directly, the resulting `oklch(35% 0.14 264)` is valid. But mixing formats (e.g., using `0.35` in the var but expecting a percentage) produces `oklch(0.35 0.14 264)` which is also valid in the 0..1 range. Be consistent: use percentage strings (`35%`) in `--mastery-bg-L`/`--mastery-fg-L`, and decimal strings (`0.14`) for `--mastery-bg-C`/`--mastery-fg-C`. The template literal `oklch(${bgL} ${bgC} ${H})` then works correctly with no conversion.

**Why it happens:** The CSS spec accepts both; inconsistency is easy to introduce when values come from CSS vars as raw strings.

**How to avoid:** Document the format choice in the CSS comment. Keep L as percentage, C as decimal.

### Pitfall 5: Sqrt Easing Applied at Wrong Stage

**What goes wrong:** Applying sqrt to the final hue angle (e.g., `return Math.sqrt(baseH)`) produces wrong hue values and non-monotonic behavior at the segment boundaries.

**Why it happens:** Sqrt easing means applying a power curve to the normalized parameter `t` (0..1) within each segment, then using linear interpolation between hue anchors.

**How to avoid:** The correct form is:
```
t_eased = Math.sqrt(t_linear)
H = anchor_start + t_eased * (anchor_end - anchor_start)
```
Never apply sqrt to H directly.

---

## Code Examples

### Complete scoreToHue with Sqrt Easing

```typescript
// Source: derived from ARCHITECTURE.md Pattern 1 + existing lerpRGB sqrt usage
// OKLCH hue anchors (approximate; tune visually):
//   red ≈ 27, yellow ≈ 90, blue ≈ 264, green ≈ 145
function scoreToHue(score: number): number {
  if (score < 0) {
    if (score >= -5) {
      // -5..0 toward blue: sqrt-eased, yellow(90) to blue(264)
      const t = Math.sqrt((-score) / 5);
      return 90 + t * (264 - 90);
    }
    // -10..-5: sqrt-eased, red(27) to yellow(90)
    const t = Math.sqrt((-score - 5) / 5);
    return 27 + t * (90 - 27);
  }
  // +1..+10: sqrt-eased, blue(264) to green(145)
  const t = Math.sqrt(score / 10);
  return 264 - t * (264 - 145);
}
```

**Direction note:** As score moves from 0 toward -5, `t` increases from 0 to 1. The formula should move hue from blue (near-zero) toward yellow (moderate negative). Verify direction at the boundaries: score -1 → near 264 (blue); score -5 → near 90 (yellow); score -10 → near 27 (red); score +10 → near 145 (green).

### Dark Theme CSS Custom Properties

```scss
// Add to :root, [data-theme="dark"] block in src/scss/_variables.scss
// L as percentage string, C as decimal — format is consistent for direct use in oklch()
--mastery-bg-L: 35%;   // perceived lightness for cell background
--mastery-bg-C: 0.14;  // chroma for cell background
--mastery-fg-L: 80%;   // perceived lightness for cell font
--mastery-fg-C: 0.16;  // chroma for cell font (slightly higher for legibility)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| RGB lerp from surface to target color | OKLCH hue rotation at constant L/C | Phase 1 | Consistent visual weight across all score values |
| `lerpRGB()` + `parseColor()` + RGB gradient constants | `scoreToHue()` + `getMasteryConstants()` + template literals | Phase 1 | Simpler code, no color parsing, no color blending |
| `el.style.backgroundColor` only | `el.style.backgroundColor` + `el.style.color` | Phase 1 | Font color also hue-matched to background (COLOR-03) |

**Deprecated after Phase 3 (not Phase 1):**
- `lerpRGB()` — will be deleted in Phase 3 once old path is fully confirmed dead
- `parseColor()` — same
- `GRADIENT_YELLOW`, `GRADIENT_RED`, `GRADIENT_GREEN` constants — same
- `el.className.replace(/mastery-\d/g, '')` line — stays until Phase 3 cleanup

---

## Open Questions

1. **Exact OKLCH hue anchor values**
   - What we know: OKLCH hues are approximately HSL hues + 30°; red ≈ 27, yellow ≈ 90, blue ≈ 264, green ≈ 145 (from STACK.md; multiple sources agree on approximate ranges)
   - What's unclear: Whether these are the optimal perceptual values at the chosen C value; perceived hue shifts with chroma in Oklab
   - Recommendation: Use the estimated anchors, then visually inspect the full score range (-10 to +10) against the dark theme and adjust if yellow looks orange or blue looks purple

2. **Optimal L/C starting values for dark theme**
   - What we know: ARCHITECTURE.md suggests dark bg-L=28%, STACK.md suggests L=0.65. These are inconsistent. ARCHITECTURE.md's percentage notation is what the CSS template literal expects.
   - What's unclear: Whether 35% bg-L produces sufficient saturation without looking neon
   - Recommendation: Start with bg-L=35%, bg-C=0.14. If cells look washed out, increase C. If cells look garish, decrease C or increase L.

3. **Font color contrast at extreme hues**
   - What we know: bg-L=35% with fg-L=80% gives ~3.6:1 WCAG ratio at most hues in OKLCH (rough estimate)
   - What's unclear: Whether 3.6:1 is sufficient or whether 4.5:1 is needed; WCAG AA for normal text is 4.5:1
   - Recommendation: After visual calibration, run at least one quick contrast check at the red and blue hue endpoints using an OKLCH contrast tool. Adjust fg-L upward if ratio is below 4.5:1. This is a calibration step during implementation, not a blocker for the phase.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing; no version pin in project) |
| Config file | none — run from project root via `python -m pytest tests/` |
| Quick run command | `python -m pytest tests/test_theme.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COLOR-01 | OKLCH custom props exist in dark theme block | unit | `python -m pytest tests/test_theme.py::TestThemeCompleteness -x` | ✅ (needs var updates) |
| COLOR-01 | All themes define the same var set | unit | `python -m pytest tests/test_theme.py::TestThemeCompleteness::test_all_themes_cover_same_variables -x` | ✅ (needs new vars added to all themes) |
| COLOR-02 | score=0 clears inline style (no background) | manual-only | Visual inspection: open app, ensure unquizzed cells show theme background | N/A |
| COLOR-02 | score=-10 shows red, score=+10 shows green | manual-only | Visual inspection in app | N/A |
| COLOR-03 | Font color writes to el.style.color | manual-only | Visual inspection: scored cells have visible font color matching hue | N/A |
| COLOR-04 | Sqrt easing produces correct hue values | unit | `python -m pytest tests/test_mastery_colors.py -x` | ❌ Wave 0 |

**Manual-only justification for COLOR-02, COLOR-03:** These involve DOM rendering with inline styles and `getComputedStyle` behavior that requires a real browser environment. The project has no browser-based test harness (no Jest, no Playwright configured). The pytest suite is Django-based and cannot evaluate computed CSS or inline styles. Visual verification is the correct gate for these.

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_theme.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green + visual inspection of dark theme grid before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_mastery_colors.py` — covers COLOR-04: pure Python unit tests for `scoreToHue` hue anchor and sqrt-easing math. The logic can be ported 1:1 from TypeScript to Python for pure function testing since it is arithmetic only (no DOM).

*(All other test infrastructure exists. The `test_theme.py` suite needs the new CSS vars added to its classification sets — that is a code change, not a missing file.)*

---

## Sources

### Primary (HIGH confidence)
- MDN Web Docs: `oklch()` — browser support, parameter semantics (L/C/H ranges, percentage vs decimal for L)
- Existing codebase: `src/ts/ui.ts` lines 577–617 — authoritative source on current implementation shape, sqrt easing pattern, score clamping
- Existing codebase: `src/scss/_variables.scss` — authoritative source on current theme structure and CSS var naming conventions
- Existing codebase: `tests/test_theme.py` — authoritative source on what test assertions will be affected by adding new CSS vars
- `.planning/research/ARCHITECTURE.md` — verified architecture patterns
- `.planning/research/STACK.md` — verified stack decisions and hue reference values
- `.planning/research/SUMMARY.md` — executive summary and confidence assessment

### Secondary (MEDIUM confidence)
- ARCHITECTURE.md Pattern 1 `scoreToHue` example — code example cross-checked against SUMMARY.md hue mapping spec
- STACK.md hue map table (red ~27, yellow ~90, blue ~264, green ~145) — approximate values cross-referenced with multiple OKLCH reference sources in SUMMARY.md

### Tertiary (LOW confidence — calibration required)
- ARCHITECTURE.md CSS custom prop L/C values (dark bg-L=28%, light bg-L=88%) — estimates only; require visual tuning
- STACK.md L/C estimates (dark L=0.65, C=0.18) — inconsistent with ARCHITECTURE.md; treat as lower bound for visual calibration starting point

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — OKLCH native, no deps, existing inline-style pattern
- Architecture: HIGH — direct extension of existing patterns in the codebase; all patterns verified against actual source
- Pitfalls: HIGH — `test_theme.py` classification pitfall is verified by reading the actual test; others are documented in prior research
- L/C calibration values: LOW — require visual inspection; estimates are reasonable starting points only

**Research date:** 2026-03-25
**Valid until:** 2026-06-25 (OKLCH is a stable baseline spec; test infrastructure is project-local and stable)
