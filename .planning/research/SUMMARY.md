# Project Research Summary

**Project:** Major System Trainer — HSL/OKLCH Mastery Color Milestone
**Domain:** Hue-based data visualization in a multi-theme TypeScript SPA
**Researched:** 2026-03-25
**Confidence:** HIGH

## Executive Summary

This milestone replaces the existing RGB lerp mastery color system in `src/ts/ui.ts` with a perceptually-uniform hue-rotation system. The current system fades cells from the theme surface color toward green (positive) or red/yellow (negative), meaning low-score cells are nearly invisible while high-score cells are vivid — visual weight is inconsistent. The replacement uses constant perceived brightness, varying only hue across the score range (red → yellow → blue → green), so every non-zero cell has equal visual presence regardless of score magnitude.

The clear recommendation from all four research streams is to use OKLCH rather than HSL. HSL lightness is not perceptually uniform — yellow at `hsl(60, 70%, 35%)` appears dramatically brighter than blue at the same L value, which is precisely the problem being solved. OKLCH's `L` component is the perceived lightness from the Oklab model; equal L values produce equal perceived brightness across all hues. This is baseline widely-available since mid-2023 (Chrome 111+, Firefox 113+, Safari 15.4+), requires no new dependencies, and replaces only one function in `ui.ts`. The change is surgical.

The primary risks are: (1) the high-contrast theme must be gated out of the computed-color path entirely — arbitrary HSL/OKLCH injected via inline styles breaks WCAG contrast guarantees and interacts poorly with Windows Forced Colors; (2) the red-green hue axis is the canonical color blindness failure and affects ~4.5% of the population — the existing spec is intentionally accepting this tradeoff, but it should be documented; (3) `setTheme()` in `theme.ts` must explicitly call `updateMasteryColors()` after setting the `data-theme` attribute, or theme-switched cells will display stale colors until the next quiz event.

## Key Findings

### Recommended Stack

OKLCH is the correct color space. No library is needed — `oklch(L C H)` is a native CSS function and the three parameters are simple numbers computed in TypeScript. The entire change is scoped to `updateMasteryColors()` in `src/ts/ui.ts`, with new CSS custom properties (`--mastery-bg-L`, `--mastery-bg-C`, `--mastery-fg-L`, `--mastery-fg-C`) added to `_variables.scss` per `[data-theme]` block. JS reads them with `getComputedStyle` at paint time — the same pattern already used for `--bg-surface`. No new files, no new build steps, no new dependencies.

**Core technologies:**
- `oklch()` (native CSS): color output — perceptually uniform constant-brightness hue rotation, Baseline widely-available since May 2023
- CSS custom properties (`_variables.scss`): per-theme L/C constants — keeps theme definitions in one place, avoids JS/CSS split-brain
- TypeScript `updateMasteryColors()` in `ui.ts`: color computation — inline `style.backgroundColor` / `style.color` writes, same pattern as current implementation

### Expected Features

**Must have (table stakes):**
- Score 0 = no color — unquizzed cells must not be colored; clear inline styles so CSS surface applies
- Positive vs negative visually distinct — green (good) vs red/yellow (bad), universal mental model
- Consistent visual weight at all non-zero scores — the core problem being solved; every scored cell must look equally present
- Monotonic hue progression — score +5 must visually sit between +1 and +10
- Theme compatibility in all 4 themes — dark, light, oled, high-contrast each need distinct L/C constants
- Font color legibility — same hue at contrasting L value; WCAG 4.5:1 minimum
- Synchronous color update after quiz answer — `updateMasteryColors()` called immediately after score change (already the case)

**Should have (differentiators):**
- Blue as neutral/near-zero hue — reads as "cool/neutral" rather than positive or negative, reinforces meaning
- Same hue family for background and font per cell — unified color language, text reinforces background
- Score-to-hue curve with sqrt/power easing — carried over from current RGB lerp for perceptual separation at low scores

**Defer to later:**
- Legend/tooltip mapping scores to colors — separate UX task, not needed for core feature
- Colorblind-safe alternative encoding — separate a11y milestone; red-green axis limitation is an accepted tradeoff
- Remove legacy `--bg-mastery-*` SCSS vars and `.mastery-0..4` CSS classes — safe cleanup, not needed for feature to work

### Architecture Approach

The change requires no new files or modules. `scoreToHue()` and `masteryColor()` are ~20-line utilities added directly to `ui.ts`, tightly coupled to `updateMasteryColors()`. Theme-aware L/C constants live as CSS custom properties in `_variables.scss` (one block per `[data-theme]`); JS reads them once per `updateMasteryColors()` call via `getComputedStyle` before the cell loop — not per-cell, to avoid repeated layout triggers. One additional wiring change is required: `theme.ts:setTheme()` must call `updateMasteryColors()` synchronously after `setAttribute('data-theme', ...)`.

**Major components:**
1. `scoreToHue(score)` — maps -10..+10 to hue angle; piecewise: -10→0 (red), -5→60 (yellow), -1/+1→240 (blue), +10→140 (green)
2. `getMasteryConstants()` — reads `--mastery-bg-L/C` and `--mastery-fg-L/C` from computed style; called once per paint
3. `updateMasteryColors()` (rewritten) — iterates all grid cells, calls above two functions, writes `oklch(...)` inline styles; score=0 clears styles
4. `_variables.scss` additions — `--mastery-bg-L/C` and `--mastery-fg-L/C` per `[data-theme]` block
5. `setTheme()` wiring — one added call to `updateMasteryColors()` after theme attribute is set

### Critical Pitfalls

1. **HSL lightness non-uniformity** — blue cells appear perceptually darker than yellow/green at the same HSL L value, defeating the "constant weight" goal. Avoid by using OKLCH, where L is perceived lightness. If HSL is used as a fallback, per-hue lightness compensation tables are required.

2. **High-contrast theme broken by inline styles** — the high-contrast theme uses a fixed yellow-on-black palette tuned for WCAG compliance. Injecting arbitrary oklch colors via inline styles overrides those guarantees and interacts badly with Windows Forced Colors. Prevention: gate the computed-color path behind a theme check; skip inline styles for `high-contrast` and retain the existing CSS class approach (`mastery-0` through `mastery-4`).

3. **Theme switch produces stale colors** — `setTheme()` currently does not call `updateMasteryColors()`. After a theme change, non-zero cells retain the previous theme's L/C constants until the next quiz event. Fix: add one synchronous call to `updateMasteryColors()` inside `setTheme()`, after `setAttribute('data-theme', ...)`.

4. **Red-green color blindness** — the planned hue axis (red negative, green positive) is invisible to deuteranopes and protanopes (~4.5% of the population). This is an accepted tradeoff for this milestone. Document it. A secondary cue (slight luminance variation with score magnitude) would partially mitigate this.

5. **Font contrast flips between dark and light themes** — a `+L` offset that gives 4.5:1 contrast on a dark background may give less than 2:1 on a light background because absolute luminance compresses non-linearly at high values. Prevention: define separate fg-L values per theme, verify with a contrast checker at the red and blue hue endpoints for each theme.

## Implications for Roadmap

Based on research, this milestone is a single-phase change with three ordered work items inside it.

### Phase 1: Core Color Computation

**Rationale:** The score-to-hue mapping and OKLCH string generation are the foundational change; all other work depends on them being correct first.
**Delivers:** Working `scoreToHue()` and rewritten `updateMasteryColors()` using `oklch(...)` inline styles; constant-brightness hue rotation visible in the default (dark) theme.
**Addresses:** All table-stakes features — score-0 neutral, positive/negative distinction, consistent visual weight, monotonic progression, font color same-hue readability.
**Avoids:** OKLCH over HSL (Pitfall 1); piecewise hue constants over lerp (Pitfall 5); `getComputedStyle` called once before loop, not per-cell (Architecture anti-pattern 4).

### Phase 2: Theme Constants and Wiring

**Rationale:** Core computation works in one theme first; then extend to all four themes and wire the theme-switch trigger.
**Delivers:** `--mastery-bg-L/C` and `--mastery-fg-L/C` CSS custom properties for all four themes; `setTheme()` wired to call `updateMasteryColors()`; per-theme contrast verification.
**Uses:** CSS custom properties pattern from `_variables.scss`; `getComputedStyle` pattern already used for `--bg-surface`.
**Implements:** Theme-aware L/C constants component; theme-switch data flow.
**Avoids:** High-contrast inline style injection (Pitfall 4) — gate clause added; font contrast flip (Pitfall 6) — per-theme fg-L values.

### Phase 3: Cleanup and Verification

**Rationale:** Dead code removal and cross-browser/cross-theme verification after the feature is working.
**Delivers:** Removed legacy `.mastery-0..4` CSS class rules from `_grid.scss`; removed `--bg-mastery-*` / `--color-mastery-*` CSS vars from `_variables.scss`; removed `el.className.replace(/mastery-\d/g, '')` line from `updateMasteryColors()`; verified grid quiz section (`#gridquiz-grid .grid-cell`) is handled; contrast ratios checked per theme.
**Avoids:** Broken profile section bars (the `--color-mastery-*` vars used in `_profile.scss` must be checked before deletion — Pitfall from FEATURES.md known constraints).

### Phase Ordering Rationale

- Compute-first ordering ensures each theme extension only touches constants, not the core logic, reducing regression risk.
- Theme wiring in Phase 2 (not Phase 1) avoids a moving target during core development — the dark theme is sufficient for validating correctness.
- Cleanup is last because the legacy CSS classes serve as a visual regression fallback during development.

### Research Flags

Phases with well-documented patterns (skip research-phase):
- **All phases:** This is a surgical, well-scoped change with high-confidence research. The CSS color space, architecture, and DOM write pattern are all established and verified. No additional research-phase runs are needed before implementation.

Areas requiring visual tuning during implementation (not research, but calibration):
- **Phase 1:** OKLCH L/C starting values (dark: L=0.65 C=0.18; light: L=0.52 C=0.16; high-contrast: L=0.75 C=0.22) are estimates. Final values require visual inspection across all score values.
- **Phase 2:** Font contrast ratios must be manually verified at red and blue hue endpoints for each theme using a contrast checker.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | OKLCH browser support verified via MDN Baseline badge and caniuse; no-library approach confirmed by architecture constraints |
| Features | HIGH | Derived directly from existing codebase analysis and PROJECT.md spec; table stakes are observable in the live product |
| Architecture | HIGH | Patterns are an extension of the existing `getComputedStyle` / inline-style approach; no speculative new patterns |
| Pitfalls | HIGH | HSL non-uniformity, red-green axis, and forced-colors behavior are all documented by W3C, MDN, and Wikipedia — not inference |

**Overall confidence:** HIGH

### Gaps to Address

- **OKLCH L/C starting values** — the research provides approximate ranges but final values require visual calibration during implementation. The lightness values in STACK.md (dark: L=0.65 C=0.18 etc.) and ARCHITECTURE.md (dark: L=28% C=0.12 etc.) are inconsistent and will need reconciliation. Treat the ARCHITECTURE.md CSS custom property values as the implementation target; the STACK.md values are starting points for the TypeScript constants approach which was ultimately rejected in favor of CSS custom props.
- **Profile section dependency** — `_profile.scss` uses `--color-mastery-*` vars for bar chart fill colors. These must be audited before cleanup in Phase 3 to determine whether they reference the vars being deleted or separate vars. Do not delete until verified.
- **Grid quiz section coverage** — `updateMasteryColors()` targets `#grid .grid-cell`. Verify during Phase 3 whether `#gridquiz-grid .grid-cell` should also receive mastery colors and extend the selector if so.

## Sources

### Primary (HIGH confidence)
- [oklch() — MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/oklch) — Baseline support, parameter spec
- [Can I use: oklch](https://caniuse.com/mdn-css_types_color_oklch) — Browser support data
- [HSL and HSV — Wikipedia](https://en.wikipedia.org/wiki/HSL_and_HSV) — Non-perceptual nature of HSL lightness
- [Web Accessibility: Understanding Colors and Luminance — MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/Guides/Colors_and_Luminance) — WCAG contrast requirements
- [Understanding WCAG 1.4.3 Contrast (Minimum) — W3C WAI](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html) — Contrast standard
- [Types of Colour Blindness — Colour Blind Awareness](https://www.colourblindawareness.org/colour-blindness/types-of-colour-blindness/) — Prevalence data
- Existing codebase: `src/ts/ui.ts`, `src/scss/_variables.scss`, `src/scss/_grid.scss` — Authoritative source on current implementation

### Secondary (MEDIUM confidence)
- [OKLCH in CSS: why we moved from RGB and HSL — Evil Martians](https://evilmartians.com/chronicles/oklch-in-css-why-quit-rgb-hsl) — HSL perceptual problems, migration rationale
- [Perceptually uniform color spaces — Programming Design Systems](https://programmingdesignsystems.com/color/perceptually-uniform-color-spaces/) — HSL non-uniformity documentation
- [It's Time to Learn oklch Color — Keith J. Grant](https://keithjgrant.com/posts/2023/04/its-time-to-learn-oklch-color/) — Hue degree reference values
- [OKLCH Color Picker — oklch.fyi](https://oklch.fyi/) — Practical chroma/lightness ranges
- [Forced colors explained — Polypane](https://polypane.app/blog/forced-colors-explained-a-practical-guide/) — High-contrast / forced-colors interaction
- [Windows High Contrast Mode, Forced Colors and CSS Custom Properties — Smashing Magazine](https://www.smashingmagazine.com/2022/03/windows-high-contrast-colors-mode-css-custom-properties/) — Inline style behavior in forced colors
- [Coloring for Colorblindness — David Nichols](https://davidmathlogic.com/colorblind/) — Red-green axis failure modes
- PROJECT.md — Authoritative specification for score-to-hue mapping requirements

---
*Research completed: 2026-03-25*
*Ready for roadmap: yes*
