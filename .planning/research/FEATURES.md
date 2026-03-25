# Feature Landscape: Grid Mastery Color System

**Domain:** Mastery/progress visualization — color-coded scoring feedback in a memorization trainer grid
**Researched:** 2026-03-25
**Milestone scope:** Replacing the existing RGB lerp (brightness-varies-with-score) system with a hue-based system at constant brightness

---

## Context: What Currently Exists

The existing system in `src/ts/ui.ts` (`updateMasteryColors`) uses RGB lerp:

- Score 0: theme background (transparent, no style)
- Score +1 to +10: lerp from `--bg-surface` toward green (`#4cda6a`), with `Math.sqrt` easing
- Score -1 to -5: lerp from `--bg-surface` toward yellow (`#e0a050`)
- Score -5 to -10: lerp from yellow toward red (`#ef5350`)

Problem: cells near zero are nearly invisible (close to surface color), cells near max are vivid. Visual weight is not consistent across non-zero cells.

The SCSS also has legacy CSS class tiers (`mastery-0` through `mastery-4`) that are no longer used by the current JS (the JS clears those class names) but still exist in the stylesheet.

---

## Table Stakes

Features users expect from any score-to-color feedback system. Missing or broken = trust in the feedback collapses.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Score 0 = no color / neutral | Unquizzed cells must not be colored; color implies data | Low | Already implemented. Score 0 → transparent. Must be preserved. |
| Positive score → visually distinct from negative | Red-means-bad, green-means-good is universal mental model | Low | Users import this mapping from traffic lights, grading systems, etc. |
| Consistent visual weight at non-zero scores | Cells at score ±1 must be as visually present as cells at ±10 | Medium | This is the core problem being solved. RGB lerp fails here. |
| Monotonic hue progression | Score +5 should be clearly between +1 and +10 in appearance | Medium | Non-monotonic mappings confuse users ("why is this cell darker than a higher-score cell?") |
| Theme compatibility | Must work correctly in dark, light, oled, and high-contrast themes | Medium | Current approach reads `--bg-surface` at runtime. New approach must adapt similarly. |
| Font color readability against colored background | Text on a colored cell must remain legible | Medium | WCAG contrast 4.5:1 for body text. Failing this makes the cell unreadable. |
| Color changes update immediately after quiz answer | Grid reflects new score synchronously with the score update | Low | Already expected; `updateMasteryColors()` is called after each answer. |

---

## Differentiators

Features beyond baseline expectations that meaningfully improve the experience.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Hue-only encodes score (constant lightness/saturation) | Eliminates the "fading into background" problem at low scores; every non-zero cell has equal visual weight | Medium | The core goal of this milestone. Use `hsl()` with fixed `s%` and `l%`, varying only hue. |
| Same hue family for background and font color | Unified color language per cell — text reinforces background rather than conflicting with it | Low | User-specified preference. Background at one lightness, font at a complementary lightness of the same hue. |
| Blue as the neutral/near-zero hue (±1) | Blue reads as "cool/neutral" rather than positive or negative; creates meaningful separation between "just started" and "well practiced" | Low | Requires mapping score to a non-linear hue curve: red (worst) → yellow → blue (near-zero) → green (best). |
| Score-to-hue curve with sqrt/power easing | Visual separation between score 1 and 10 is perceptually larger than raw linear interpolation provides | Low | Already used in current RGB lerp. Should carry over to hue interpolation. |
| High-contrast theme special-casing | High-contrast theme uses extreme chromatic values (`#00ff00`, `#ff6b6b`, `#ffff00` text); hue-based system should maintain this or gracefully override | Medium | Current mastery SCSS vars for high-contrast are already extreme. The new JS system must not clobber them with muddy mid-saturation colors. |
| Legend or tooltip mapping scores to colors | Users can understand what a cell color means without mental arithmetic | Low | A simple legend ("blue = recently tried, green = mastered, red = needs work") reduces cognitive load. Not currently present. |

---

## Anti-Features

Features to deliberately NOT build for this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Per-theme hardcoded hue values in SCSS vars | The current `--bg-mastery-*` / `--color-mastery-*` vars in `_variables.scss` were meant for the old CSS-class tier system; replicating that pattern for the new system adds maintenance burden across 4 themes | Compute all cell colors in JS via `hsl()` inline styles, same as the current approach. Remove unused legacy `--bg-mastery-*` vars after transition. |
| Perceptually uniform color space (OKLCH/HCL) | More accurate but requires a math library or lookup table; HSL is sufficient for this use case and already understood by the team | Use `hsl()`. Document the known limitation: equal HSL lightness steps are not perceptually equal across hues (green appears brighter than blue at the same L%). Accept this tradeoff. |
| Colorblind-safe replacement (blue/orange instead of red/green) | This is a memorization app, not a safety-critical system. Colorblind users can still function; adding a second non-color cue (pattern, icon) is a separate a11y milestone | Add a note in PITFALLS.md. Do not change the hue mapping from the user-specified red/yellow/blue/green scheme. |
| Animated color transitions per score change | Looks polished but adds complexity; `updateMasteryColors` runs synchronously on every quiz answer, transitions may conflict with quiz state changes | The existing `transition` in `.grid-cell` covers border/shadow; leave background transitions off or use a very short CSS transition if needed. Not a priority. |
| Separate positive vs negative saturation levels | Tempting to make negative scores "pop" more by boosting saturation; adds a second dimension to an already multi-variable system | Keep saturation constant for all non-zero cells. |
| Persistence of computed color values | Storing the hsl() string per cell adds complexity with no user benefit | Recompute from score on every call to `updateMasteryColors()`, as today. |

---

## Feature Dependencies

```
Score aggregation (MODES.quiz.scores + MODES.reverse.scores + MODES.mixed.scores)
  → Raw score clamped to [-10, +10]
    → Score-to-hue mapping function (new)
      → hsl(hue, saturation%, lightness%) for background
        → Complementary lightness offset for font color (same hue)
          → el.style.backgroundColor + el.style.color set inline

Theme detection (getComputedStyle → --bg-surface)
  → Determines baseline saturation / lightness to use per theme
    → Light theme needs different L% than dark theme (same hue, different lightness)
```

Additional dependency:

```
Legacy mastery-* CSS classes in _grid.scss
  → Must be stripped from el.className before setting inline styles
    (Already done: el.className.replace(/mastery-\d/g, ''))
```

---

## MVP Recommendation

The milestone is narrowly scoped. The MVP is:

1. Replace the `lerpRGB` / `GRADIENT_*` logic in `updateMasteryColors` with a hue-based function using `hsl()`.
   - Map score -10 → hue ~0 (red), score -5 → ~55 (yellow), score -1 → ~220 (blue), score 0 → no color, score +1 → ~220 (blue), score +10 → ~130 (green).
   - Keep saturation constant (e.g., 70-80%).
   - Adjust lightness per theme: lower L% on dark/oled (e.g., 30-35%), higher on light (e.g., 45-50%), extreme on high-contrast.
2. Set font color to the same hue at a contrasting lightness (e.g., if background is hsl(H, S%, 30%), text is hsl(H, 60%, 75%)).
3. Verify legibility against WCAG 4.5:1 for each theme manually before shipping.

Defer:

- Legend/tooltip explaining the color scale (separate UX task)
- Removing legacy `--bg-mastery-*` SCSS vars (safe cleanup, not needed for feature to work)
- Accessibility audit / colorblind-safe alternative encoding (separate a11y milestone)

---

## Known Constraints Affecting Feature Decisions

- HSL `lightness` is not perceptually uniform. Blue at `hsl(220, 70%, 35%)` will appear perceptually darker than green at `hsl(130, 70%, 35%)`. This is acceptable for this product but should be documented.
- The high-contrast theme uses `--text-primary: #ffff00` (yellow text). Font color set to a hue-shifted value may conflict with the user's expectation of yellow text everywhere in that theme. Consider clamping hue-derived font colors to a higher lightness in high-contrast, or use white (`hsl(H, 0%, 95%)`) as the font override for that theme only.
- `updateMasteryColors` iterates all 100 cells on every call. At this scale it is fine. No performance concern.
- The profile section uses `--color-mastery-*` variables for bar chart fill colors (`_profile.scss` lines 72-75). If those CSS vars are removed during cleanup, the profile bars lose their coloring. The JS-computed colors in the grid are separate from the profile section coloring.

---

## Sources

- Existing codebase analysis: `src/ts/ui.ts` (updateMasteryColors), `src/scss/_variables.scss`, `src/scss/_grid.scss`
- [Diverging vs sequential color scales — Datawrapper Blog](https://www.datawrapper.de/blog/diverging-vs-sequential-color-scales) (MEDIUM confidence — aligns with diverging scale principles)
- [Perceptually uniform color spaces — Programming Design Systems](https://programmingdesignsystems.com/color/perceptually-uniform-color-spaces/) (HIGH confidence — documents HSL non-uniformity limitation)
- [Coloring for Colorblindness — David Nichols](https://davidmathlogic.com/colorblind/) (MEDIUM confidence — red/green colorblind safety tradeoffs)
- [Anki Review Heatmap — glutanimate](https://github.com/glutanimate/review-heatmap) (MEDIUM confidence — precedent for hue-scaled activity visualization in memorization tools)
- [HCL-Based Color Palettes — colorspace R package](https://colorspace.r-forge.r-project.org/articles/hcl_palettes.html) (HIGH confidence — constant-luminance diverging palettes rationale)
- PROJECT.md — authoritative specification for score-to-hue mapping requirements
