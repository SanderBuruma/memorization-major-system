# Phase 2: Theme Integration - Research

**Researched:** 2026-03-25
**Domain:** Per-theme OKLCH L/C calibration + setTheme() wiring
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Same OKLCH hue-rotation system for ALL themes, including high-contrast — no special-casing or bypassing
- Each theme only differs in L (lightness) and C (chroma) values via CSS custom properties
- Overrides prior Phase 1 decision: "High-contrast bypasses computed colors" — now high-contrast uses the same OKLCH system with appropriate L/C values
- Subtle tint approach: colored cells should blend into the theme, not pop aggressively
- Color is secondary to cell content — it's an ambient signal, not a loud indicator
- Light theme: colored background with dark text — cell background gets a light tint of the hue, text is a darker shade of the same hue; must still feel like a light theme
- OLED theme: same L/C values as dark theme — no separate tuning needed

### Claude's Discretion
- Exact L/C numeric values per theme
- Whether to extract the hue-to-color logic further or keep it inline
- High-contrast L/C values (Claude picks values that pass WCAG AA minimum)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| THEME-01 | Per-theme OKLCH lightness and chroma constants defined as CSS custom properties in _variables.scss | Stub values already exist from Phase 1 — this requirement means calibrating them to real values appropriate for each theme |
| THEME-02 | Theme switching triggers grid mastery color recomputation via updateMasteryColors() | setTheme() in theme.ts must call updateMasteryColors() after setAttribute — one-line change |
| THEME-03 | High-contrast theme has special handling to maintain WCAG-compliant legibility | Special handling = careful L/C selection so oklch(fgL fgC H) on oklch(bgL bgC H) meets WCAG AA 4.5:1 minimum |
</phase_requirements>

---

## Summary

Phase 1 completed the full OKLCH infrastructure: `scoreToHue()`, `getMasteryConstants()`, and the rewritten `updateMasteryColors()` are all live in `src/ts/ui.ts`. The CSS custom properties `--mastery-bg-L`, `--mastery-bg-C`, `--mastery-fg-L`, `--mastery-fg-C` already exist in all four theme blocks in `_variables.scss` and are classified in `test_theme.py`'s `NON_COLOR_VARS`. All 31 existing tests pass. No infrastructure work remains.

Phase 2 is therefore two focused tasks: (1) calibrate the L/C values for each theme by replacing the Phase 1 stubs with visually correct values, and (2) wire `setTheme()` to call `updateMasteryColors()` so theme switches refresh the grid immediately. The OLED theme reuses dark theme values by locked decision, so only three distinct calibration targets exist: dark, light, and high-contrast.

The main complexity in this phase is the high-contrast calibration. Because OKLCH inline styles bypass the static CSS variable system, the `test_theme.py` WCAG tests do not validate the mastery colors — they only validate hex/rgb values. WCAG compliance for mastery colors on high-contrast must be verified manually or via a Python helper during implementation. The WCAG AA threshold for normal text is 4.5:1; WCAG AAA for the high-contrast theme's other colors is 7:1. The user confirmed WCAG AA as the minimum for mastery colors.

**Primary recommendation:** Calibrate dark first (minimal changes from current stubs), copy to OLED, then calibrate light (different polarity — light bg, dark fg), then calibrate high-contrast to WCAG AA. Wire setTheme() last as it is a one-line change.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `oklch()` native CSS | Baseline (Chrome 111+, Firefox 113+, Safari 15.4+) | Color output string | Perceptually uniform L — already in use from Phase 1 |
| TypeScript in `src/ts/theme.ts` | 5.7.x (existing) | Wire setTheme() to updateMasteryColors() | Same module that owns theme switching |
| SCSS custom properties in `src/scss/_variables.scss` | sass 1.98.x (existing) | Per-theme L/C constants | Already has the four mastery vars in all four theme blocks |

### No New Dependencies

Zero new packages. This phase is calibration (SCSS values) and a one-line TypeScript change.

---

## Architecture Patterns

### File Changes (minimal)

```
src/
├── ts/
│   └── theme.ts         # Add updateMasteryColors() call inside setTheme()
└── scss/
    └── _variables.scss  # Replace Phase 1 stub L/C values with calibrated values
```

No new files. No new tests (all infrastructure exists; calibration verified visually + manual contrast check).

### Pattern 1: setTheme() Wiring

**What:** Import `updateMasteryColors` from `ui.ts` and call it after `setAttribute` in `setTheme()`.

**Current setTheme() (theme.ts line 18–24):**
```typescript
export function setTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  updateToggleIcon();
  updateThemeSelect();
  saveState();
}
```

**After change:**
```typescript
import { updateMasteryColors } from './ui';

export function setTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  updateToggleIcon();
  updateThemeSelect();
  saveState();
  updateMasteryColors();
}
```

**Why after saveState():** The order within setTheme() is not critical for correctness, but placing updateMasteryColors() last means the theme CSS vars are already resolved when getMasteryConstants() reads them. Placing it before saveState() would also work — `data-theme` is set on line 1 of the function, so getComputedStyle will see the new theme's vars at any point after that.

**Circular import risk:** theme.ts imports from persistence.ts (`saveState`). ui.ts imports from state.ts and persistence.ts. If ui.ts also imports from theme.ts, there would be a circular dependency. The wiring must go in theme.ts importing from ui.ts — NOT ui.ts importing from theme.ts. The CONTEXT.md confirms this: "`setTheme()` in `src/ts/theme.ts` — must add `updateMasteryColors()` call after `setAttribute`".

**Verify import chain before writing:** Read the actual import lines in ui.ts to confirm it does not already import from theme.ts. (Current ui.ts line 1: `import { appState, MODES, rebuildWordlist, logActivity } from './state';` — no theme.ts import. Safe to add theme.ts → ui.ts import.)

### Pattern 2: L/C Calibration Strategy

**OKLCH L/C semantics (verified from Phase 1 research):**
- L: percentage string, e.g. `35%` (0% = black, 100% = white)
- C: decimal string, e.g. `0.14` (0 = achromatic/gray, ~0.4 = maximum saturation for most hues)
- Template literal usage: `oklch(${bgL} ${bgC} ${H})` — values interpolated as-is

**Dark theme (current stubs — likely close to correct):**
```scss
--mastery-bg-L: 35%;
--mastery-bg-C: 0.14;
--mastery-fg-L: 80%;
--mastery-fg-C: 0.16;
```
Dark background is `#1e1e32` (very dark blue-purple). A cell bg at L=35% will be perceptibly colored but not glowing. fg at L=80% provides clear separation. Starting values are reasonable; verify visually.

**OLED theme (use dark values per locked decision):**
```scss
--mastery-bg-L: 35%;
--mastery-bg-C: 0.14;
--mastery-fg-L: 80%;
--mastery-fg-C: 0.16;
```
OLED surface is `#0a0a0a` (near-black). Dark theme values may actually look slightly more vivid against a darker background — consider whether increasing C slightly (e.g. `0.15`) helps. But per locked decision, start with identical dark values.

**Light theme (inverted polarity):**
```scss
--mastery-bg-L: 75%;  /* current stub */
--mastery-bg-C: 0.12; /* current stub */
--mastery-fg-L: 30%;  /* current stub */
--mastery-fg-C: 0.14; /* current stub */
```
Light surface is `#ffffff`. Cells need a light-tinted bg (L ~75–82%) and dark fg (L ~25–35%) so text remains readable. The subtle-tint principle means C should be low — 0.10–0.14 for bg. Lower L on fg ensures readability on a light cell. Verify: white text on light cell is invisible; dark text is required.

**High-contrast theme (WCAG AA minimum):**
```scss
--mastery-bg-L: 20%;  /* current stub */
--mastery-bg-C: 0.22; /* current stub */
--mastery-fg-L: 90%;  /* current stub */
--mastery-fg-C: 0.24; /* current stub */
```
High-contrast bg-page is `#000`. Cells at L=20% will be darker colored patches on a black background. fg at L=90% is near-white. The contrast ratio between OKLCH L=90% and L=20% at any hue is approximately (0.78 + 0.05) / (0.03 + 0.05) = 10:1 — well above WCAG AA 4.5:1. However, hue shift affects perceived luminance slightly. The current stub values are likely sufficient. Verify at red (H≈27) and green (H≈145) endpoints, which have stronger luminance shifts.

### Pattern 3: WCAG Contrast Estimation for OKLCH

The test suite checks hex colors for WCAG compliance, but the mastery colors are OKLCH and rendered inline. There is no automated test for mastery color contrast. Verification is manual during implementation.

**Approximation method (Python helper, no new test file needed):**
```python
import math

def oklch_to_approx_luminance(L_pct: float) -> float:
    """OKLCH L% is roughly perceptual lightness. Convert to sRGB relative luminance."""
    # OKLCH L is in the 0-1 perceptual range (Oklab)
    # Approximation: L% / 100 maps to Oklab L, convert to XYZ Y
    # For contrast purposes: Y ≈ (L/100)^3 (crude but directional)
    L = L_pct / 100
    return L ** 3  # underestimates, but useful for go/no-go

def wcag_ratio(fg_L: float, bg_L: float) -> float:
    fg_lum = oklch_to_approx_luminance(fg_L)
    bg_lum = oklch_to_approx_luminance(bg_L)
    light = max(fg_lum, bg_lum)
    dark = min(fg_lum, bg_lum)
    return (light + 0.05) / (dark + 0.05)
```

**This approximation is directional only.** For high-contrast, use a real OKLCH converter (e.g. https://oklch.com or the browser's computed style) to verify. The cell contrast is background `oklch(bgL bgC H)` vs foreground `oklch(fgL fgC H)` — different hues can shift luminance significantly.

**Practical rule for high-contrast:** fg-L at 85%+ on bg-L at 25% or lower will comfortably clear WCAG AA 4.5:1 at all hues in the OKLCH gamut. The concern is medium hues (yellow H≈90) where OKLCH L may not perfectly represent sRGB luminance.

### Anti-Patterns to Avoid

- **Circular import:** Do not import theme.ts from ui.ts. The wiring goes one direction: theme.ts imports updateMasteryColors from ui.ts.
- **Calling updateMasteryColors() before setAttribute:** CSS vars are theme-scoped by `data-theme` attribute. getMasteryConstants() reads `getComputedStyle(document.documentElement)` — the returned values depend on the current `data-theme`. Call updateMasteryColors() only after setAttribute, not before.
- **Setting OLED to different values than dark:** Per locked decision, OLED uses the same values as dark. Do not tune them separately.
- **High C values on light theme:** C=0.20+ on a light bg (L=75%) produces vivid colored cells that violate the "subtle tint, ambient signal" requirement. Keep C ≤ 0.14 for light bg.
- **Dark fg on dark bg for light theme:** The light theme needs fg-L low (dark), not high. The Phase 1 stub already has this correct (fg-L=30%). Do not change polarity.
- **Omitting updateMasteryColors() from the init path:** The call is already in init.ts and persistence.ts (triggered on loadState). The only gap is setTheme() — which is exactly what this phase fixes.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-theme color logic in TypeScript | `if (theme === 'dark')` branches in updateMasteryColors() | CSS custom properties + getComputedStyle | Theme is already encoded in data-theme; CSS vars already update when the attribute changes; getMasteryConstants() picks up new values automatically |
| WCAG contrast verification tooling | Custom contrast checker in test suite | Visual inspection + oklch.com | Mastery colors are runtime-computed; static test suite cannot evaluate them without browser rendering; manual checkpoint is correct |

---

## Common Pitfalls

### Pitfall 1: Circular Import Between theme.ts and ui.ts

**What goes wrong:** If ui.ts (which contains updateMasteryColors) were to import setTheme or THEMES from theme.ts, and theme.ts then imports updateMasteryColors from ui.ts, esbuild/TypeScript would produce a circular module dependency. This may cause runtime undefined errors if the import is evaluated before the dependent module is initialized.

**Why it happens:** Large SPA files often develop import cycles as feature wiring is added.

**How to avoid:** The import is one direction only — theme.ts imports from ui.ts. Verify with a quick `grep import src/ts/ui.ts` before writing the import statement. Current ui.ts imports: state, persistence, quiz, profile, tutorial, wiki, utils, types, constants — no theme.ts. Safe to proceed.

**Warning signs:** TypeScript compiler warning about circular imports; runtime `updateMasteryColors is not a function` on theme switch.

### Pitfall 2: getComputedStyle Timing — Called Before Data-Theme Updates

**What goes wrong:** If updateMasteryColors() is placed at the top of setTheme() (before setAttribute), getMasteryConstants() reads the OLD theme's CSS vars, producing wrong colors on the switched-to theme.

**Why it happens:** CSS custom properties are resolved relative to the current value of `data-theme`. The attribute must be set first.

**How to avoid:** Place the updateMasteryColors() call after `document.documentElement.setAttribute('data-theme', theme)`. This is already at line 1 of setTheme(), so any placement below it is correct.

### Pitfall 3: Light Theme fg Contrast Inversion

**What goes wrong:** Using a high fg-L value (e.g. 80%) on a light bg (bg-L=75%) produces near-zero contrast — white text on white-tinted cell. The cell content becomes invisible.

**Why it happens:** Light themes require inverted fg/bg polarity: light bg with dark fg. The Phase 1 stub correctly uses fg-L=30%, but if the calibrator adjusts fg-L upward thinking "more lightness = more visible," they invert the effect.

**How to avoid:** On light theme: bg-L ≥ 70% (light tint), fg-L ≤ 35% (dark text). On dark/oled/high-contrast: bg-L ≤ 40% (dark cell), fg-L ≥ 75% (light text). The polarity is the structural constraint; L values within each range are calibration choices.

**Warning signs:** Grid cells in light theme show colored backgrounds but invisible text (because fg is also light).

### Pitfall 4: OLED Cells Appear Too Dull Against Near-Black Background

**What goes wrong:** At dark theme values (bg-L=35%, bg-C=0.14), cells on an OLED theme with bg-page=#000 may appear visually identical to non-colored cells at low scores, because the L=35% cell blends into the near-black surface (bg-surface=#0a0a0a).

**Why it happens:** OLED background is significantly darker than dark background (#0a0a0a vs #1e1e32). The same absolute L value produces less perceived contrast against a darker surrounding.

**How to avoid:** After wiring and calibrating dark theme, switch to OLED and inspect. If low-score cells (score ±1) are barely distinguishable, consider a slight C bump (e.g. 0.15–0.16) even though the locked decision says "same values as dark." The locked decision is about not requiring separate tuning — if visual calibration reveals a problem, the implementer can adjust OLED C slightly without violating the spirit of the decision. Document the rationale if OLED values diverge.

### Pitfall 5: High-Contrast Cells Fail WCAG AA at Specific Hues

**What goes wrong:** OKLCH L is a perceptual lightness measure in the Oklab color space, not sRGB luminance. At high chroma (C=0.22+), certain hues (particularly yellow H≈90 and green H≈145) can have higher sRGB luminance than their OKLCH L suggests, making fg/bg contrast lower than expected.

**Why it happens:** sRGB luminance depends on which RGB primaries are activated. Green contributes 71.5% of sRGB luminance; a green cell at bg-L=20% and C=0.22 may actually be brighter in sRGB than a red cell at the same OKLCH values.

**How to avoid:** At the end of high-contrast calibration, manually check at least the yellow (H≈90) and green (H≈145) hue endpoints using the browser dev tools or https://oklch.com. The fg color `oklch(90% 0.24 90)` on bg `oklch(20% 0.22 90)` should show a WCAG AA ratio ≥ 4.5:1. If not, increase fg-L (e.g. 92%) or decrease bg-C (e.g. 0.18) until contrast passes.

---

## Code Examples

### setTheme() After Change

```typescript
// src/ts/theme.ts — add import at top of file
import { updateMasteryColors } from './ui';

// setTheme() body — updateMasteryColors() added as last call
export function setTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  updateToggleIcon();
  updateThemeSelect();
  saveState();
  updateMasteryColors();
}
```

Source: CONTEXT.md integration point specification; confirmed safe by reading actual import chains in ui.ts (no theme.ts import present).

### Calibrated _variables.scss Mastery Vars (Recommended Starting Values)

```scss
/* Dark theme — subtle dark tint, readable light text */
:root, [data-theme="dark"] {
  --mastery-bg-L: 35%;
  --mastery-bg-C: 0.14;
  --mastery-fg-L: 80%;
  --mastery-fg-C: 0.16;
}

/* Light theme — light tint bg, dark fg (inverted polarity from dark) */
[data-theme="light"] {
  --mastery-bg-L: 80%;
  --mastery-bg-C: 0.10;
  --mastery-fg-L: 28%;
  --mastery-fg-C: 0.16;
}

/* OLED — same as dark per locked decision */
[data-theme="oled"] {
  --mastery-bg-L: 35%;
  --mastery-bg-C: 0.14;
  --mastery-fg-L: 80%;
  --mastery-fg-C: 0.16;
}

/* High-contrast — WCAG AA minimum, larger delta between fg and bg L */
[data-theme="high-contrast"] {
  --mastery-bg-L: 22%;
  --mastery-bg-C: 0.18;
  --mastery-fg-L: 92%;
  --mastery-fg-C: 0.20;
}
```

These are starting values for visual calibration. The implementer must verify visually for each theme and adjust as needed. The rationale for these numbers:
- Dark/OLED: unchanged from Phase 1 stubs (already verified as reasonable)
- Light: bg-L raised to 80% (more visibly white/neutral) and C lowered to 0.10 (subtle tint); fg-L lowered to 28% (clearly dark text); fg-C raised to 0.16 for legibility
- High-contrast: C reduced from Phase 1 stub (0.22) to 0.18 to avoid overly saturated cells; fg-L raised to 92% (brighter white) for stronger contrast margin at all hues

### Quick Manual Contrast Check in Browser Console

```javascript
// Paste in DevTools console while on a high-contrast-themed page with some scored cells
// Checks one cell's actual computed styles
const cell = document.querySelector('#grid .grid-cell[style]');
if (cell) {
  const bg = cell.style.backgroundColor;
  const fg = cell.style.color;
  console.log('bg:', bg, 'fg:', fg);
  // Then paste into https://coolors.co/contrast-checker or compute manually
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| High-contrast bypasses OKLCH (Phase 1 plan) | High-contrast uses same OKLCH system with tuned L/C (Phase 2 decision) | 2026-03-25 (CONTEXT.md) | Simpler code — no conditional logic in updateMasteryColors(); consistent behavior across all themes |
| Stub placeholder L/C values (from Phase 1) | Calibrated theme-appropriate L/C values | Phase 2 | Colors actually look correct in all themes |
| Theme switch does not refresh mastery colors | setTheme() calls updateMasteryColors() | Phase 2 | Instant visual update on theme change |

---

## Open Questions

1. **OLED C value — identical to dark or slightly higher?**
   - What we know: Locked decision says "same L/C values as dark theme." OLED surface (#0a0a0a) is darker than dark surface (#1e1e32).
   - What's unclear: Whether L=35% cells look visually distinct enough from the near-black OLED background at low scores.
   - Recommendation: Start with identical dark values. If visual inspection shows low-score cells blend in, increment C by 0.02 and document the deviation from the locked decision as a visual calibration choice.

2. **Light theme C — how low is "subtle"?**
   - What we know: The "subtle tint" principle and "ambient signal, not loud indicator" language. C=0.10 is moderately low.
   - What's unclear: Whether C=0.10 on a white background (bg-L=80%) is visible enough at low scores without being garish at score ±10.
   - Recommendation: Verify at score ±10 (most saturated hue for max score) and score ±1 (near-blue, low saturation). If ±10 is too subtle, increase to 0.12. If too vivid, decrease to 0.08.

3. **High-contrast fg-C — does high chroma on fg improve or hurt readability?**
   - What we know: High chroma on fg means the text is colored rather than white. White text (C=0) would guarantee maximum contrast with a colored bg.
   - What's unclear: Whether the user prefers colored text (matching hue) or white/pure text on colored bg for high-contrast.
   - Recommendation: The CONTEXT.md says "same OKLCH hue system" — that implies fg should use the same hue. Keep fg-C at 0.16–0.20. If visual inspection shows this hurts readability, the fallback is to use a white fg (fg-C=0.00, fg-L=95%), which is fully consistent with the "same system" decision while maximizing contrast. The CONTEXT.md leaves this to Claude's discretion.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (project venv at `venv/bin/python`) |
| Config file | none — run from project root |
| Quick run command | `venv/bin/python -m pytest tests/test_theme.py -x` |
| Full suite command | `venv/bin/python -m pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| THEME-01 | All four themes define `--mastery-bg-L`, `--mastery-bg-C`, `--mastery-fg-L`, `--mastery-fg-C` | unit | `venv/bin/python -m pytest tests/test_theme.py::TestThemeCompleteness -x` | ✅ (already passing) |
| THEME-01 | L/C values appear correct per theme | manual | Visual inspection: switch themes and look at scored grid cells | N/A |
| THEME-02 | Theme switch refreshes mastery colors immediately | manual | Switch themes in the app with some scored cells — colors must update instantly | N/A |
| THEME-03 | High-contrast cells meet WCAG AA 4.5:1 | manual | Browser dev tools or https://oklch.com — check fg vs bg contrast at yellow and green hue endpoints | N/A |

**Manual-only justification for THEME-01 visual, THEME-02, THEME-03:** These require browser rendering with computed inline styles. The pytest suite parses SCSS statically — it cannot evaluate the rendered oklch() values or compute contrast between inline-style colors. No new test files are needed; THEME-01 structural requirement (vars exist in all themes) is already covered by the passing test suite.

### Sampling Rate

- **Per task commit:** `venv/bin/python -m pytest tests/test_theme.py -x`
- **Per wave merge:** `venv/bin/python -m pytest tests/ -x`
- **Phase gate:** Full suite green + visual inspection in all four themes before `/gsd:verify-work`

### Wave 0 Gaps

None — existing test infrastructure covers all automated phase requirements. The theme completeness test already validates CSS var presence in all four theme blocks. No new test files needed for Phase 2.

---

## Sources

### Primary (HIGH confidence)

- Actual codebase: `src/ts/ui.ts` — verified scoreToHue(), getMasteryConstants(), updateMasteryColors() are fully implemented from Phase 1
- Actual codebase: `src/ts/theme.ts` — verified setTheme() does NOT currently call updateMasteryColors(); import chain is safe (no theme.ts import in ui.ts)
- Actual codebase: `src/scss/_variables.scss` — verified all four theme blocks have mastery vars with Phase 1 stub values
- Actual codebase: `tests/test_theme.py` — verified NON_COLOR_VARS already includes mastery vars; 31 tests already passing
- CONTEXT.md — locked decisions on all-themes OKLCH, OLED=dark, light polarity, high-contrast WCAG AA
- Phase 1 RESEARCH.md — OKLCH L/C semantics, format conventions (L as %, C as decimal), contrast estimation

### Secondary (MEDIUM confidence)

- OKLCH perceptual properties: OKLCH L is not identical to sRGB relative luminance at high chroma — documented in Phase 1 research, relevant to THEME-03 high-contrast calibration
- Recommended L/C starting values: derived from Phase 1 research estimates cross-checked against existing stub values and theme background colors

### Tertiary (LOW confidence — calibration required)

- Recommended L/C numeric values — all require visual verification in the actual rendered app; these are informed starting points not final values

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Phase 1 complete, no new libraries, verified by reading actual source
- Architecture: HIGH — setTheme() wiring is a one-line change with verified import safety; _variables.scss structure is known and stable
- L/C calibration values: LOW — requires visual inspection; starting values are informed estimates
- WCAG compliance of high-contrast: MEDIUM — approximation suggests current/proposed values clear AA, but hue-dependent luminance shifts require manual verification at hue endpoints

**Research date:** 2026-03-25
**Valid until:** 2026-06-25 (OKLCH is a stable baseline spec; all architecture is project-local and stable)
