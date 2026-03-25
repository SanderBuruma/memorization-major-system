# Technology Stack

**Project:** Major System Trainer — HSL/OKLCH Mastery Color Milestone
**Researched:** 2026-03-25
**Scope:** Color space selection for hue-rotation mastery colors at constant perceptual brightness

---

## Recommendation: OKLCH, computed in TypeScript, written as inline `style` strings

No new dependencies. No SCSS changes required. Pure replacement of the existing
`updateMasteryColors()` function in `src/ts/ui.ts`.

---

## Color Space Decision

### Use OKLCH — not HSL

**Recommended:** `oklch(L C H)`
**Reject:** `hsl(H S% L%)`

**Why HSL fails for this use case:**

HSL's `L` component is not perceptually uniform. At 50% lightness, blue appears
significantly darker than yellow to human vision — the same numeric L produces
visually different brightness across hues. This means that if you lerp hue from
red (0°) to green (120°) at a fixed HSL lightness, the cell brightness will
visually pulse up and down across the color spectrum. This is the exact problem
the user wants to eliminate.

**Why OKLCH works:**

OKLCH's `L` component is the *perceived* lightness from the Oklab model. Equal
numeric L values produce equal perceived brightness across all hues. Rotating
from hue 30 (red) through 85 (yellow) to 145 (green) to 264 (blue) while
holding L and C constant produces a visually uniform weight across all cells.
This is precisely what the milestone requires.

**Confidence:** HIGH — confirmed by MDN documentation, Evil Martians technical
analysis, and cross-referenced with the Oklab perceptual model specification.

---

## Browser Support

OKLCH has been baseline widely-available since **May 2023**. Supported in:
- Chrome/Edge 111+ (released March 2023)
- Safari 15.4+ (mobile), 16.4+ (desktop)
- Firefox 113+ (released May 2023)

As of 2025, global support exceeds 92%. No fallback is needed for this project.

**Confidence:** HIGH — sourced from MDN "Baseline: Widely Available" badge and
cross-referenced with multiple current sources.

---

## Compute Colors in TypeScript — not CSS

**Where to compute:** TypeScript (`updateMasteryColors()` in `ui.ts`)
**How to apply:** `el.style.backgroundColor = \`oklch(${L} ${C} ${H})\``

**Why compute in JS, not CSS:**

The mastery score is a runtime value in `appState`. The hue mapping is a
non-linear function of score (distinct segments for negative/positive scores,
with score=0 meaning no color). This logic cannot be expressed in CSS alone
without a per-element custom property per cell. Using TypeScript to map score
to OKLCH parameters and writing the result as an inline style is the same
approach the existing `updateMasteryColors()` already uses — this is a direct
replacement of RGB lerp with OKLCH strings.

**Why not CSS `color-mix()` or `@property` gradients:**

Those tools are for static or transition-based color changes. The mastery score
is arbitrary per cell and changes on quiz events. Template-driven CSS cannot
handle per-cell numeric score mapping. JS remains the correct layer.

**Confidence:** HIGH — consistent with existing architecture pattern.

---

## Theme Compatibility

**Pattern:** Use per-theme lightness/chroma constants, same hue mapping for all themes.

The four themes (dark, light, oled, high-contrast) differ in background
brightness. A fixed L value will look correct in dark themes but may clash in
light themes or wash out in oled. The correct approach is to define per-theme
L and C constants in TypeScript (or read them from CSS custom properties), then
apply the same hue function across all themes.

Practical starting values (to be tuned visually):
- Dark/OLED: L=0.65, C=0.18
- Light: L=0.52, C=0.16
- High-contrast: L=0.75, C=0.22 (higher chroma is expected in this theme)

**High-contrast note:** The high-contrast theme uses saturated cyan/yellow text
conventions. The hue-rotation system should still apply but with higher C values.

**Confidence:** MEDIUM — L/C values are starting estimates based on OKLCH range
research; final values require visual tuning per theme.

---

## Hue Map for Score → Color

OKLCH hue degrees differ from HSL by approximately +30° (hues are shifted).

Approximate OKLCH hue values for target colors:
| Color  | OKLCH Hue | HSL Equivalent |
|--------|-----------|----------------|
| Red    | ~20–30    | 0°             |
| Yellow | ~85–95    | 60°            |
| Blue   | ~255–270  | 240°           |
| Green  | ~140–150  | 120°           |

Score-to-hue mapping (from PROJECT.md spec):
- Score -10 (worst): Red (~27)
- Score ~-5: Yellow (~90)
- Score -1 to +1 boundary: Blue (~264)
- Score +10 (best): Green (~145)

Score=0 maps to no color (transparent / theme surface background), same as the
existing system. This segment needs a guard: `if (score === 0) { el.style.backgroundColor = ''; return; }`.

**Confidence:** MEDIUM — hue positions are approximate from multiple OKLCH
reference sources. Fine-tuning needed when the feature is implemented.

---

## Font Color

**Pattern:** Same hue as background, different lightness.

Per PROJECT.md: font color uses the same hue as the background cell at a
different lightness for readability. In OKLCH this is trivial — keep H and C
the same, adjust L (e.g., bg at L=0.65, text at L=0.90 for dark themes; bg at
L=0.52, text at L=0.20 for light themes).

**Confidence:** HIGH — OKLCH L independence from H makes this straightforward.

---

## What Not to Use

| Option | Reject Because |
|--------|----------------|
| HSL | Non-uniform lightness across hues — the core problem being fixed |
| LCH | Hue drift on achromatic boundaries; OKLCH is the improved successor |
| CSS `color-mix()` | Cannot encode score-to-hue mapping logic; designed for blending |
| `chroma.js` or other color libs | Zero value for this use case; OKLCH strings need only 3 numbers computed in plain JS |
| CSS `@property` + `calc()` | Cannot encode the multi-segment non-linear hue function per cell |

---

## Implementation Shape

The entire change is scoped to `updateMasteryColors()` in `src/ts/ui.ts`.

Replace:
```typescript
// Old: RGB lerp from surface to target color
el.style.backgroundColor = `rgb(${bg[0]},${bg[1]},${bg[2]})`;
```

With:
```typescript
// New: OKLCH at constant L/C, varying H by score
const H = scoreToHue(score);   // map score → hue angle
const L = themeL();            // read from CSS var or theme constant
const C = themeC();
el.style.backgroundColor = `oklch(${L} ${C} ${H})`;
el.style.color = `oklch(${textL} ${C} ${H})`;
```

No new files, no new build steps, no new dependencies.

---

## Sources

- [oklch() — MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/oklch) — Baseline support, parameter spec (HIGH confidence)
- [OKLCH in CSS: why we moved from RGB and HSL — Evil Martians](https://evilmartians.com/chronicles/oklch-in-css-why-quit-rgb-hsl) — HSL perceptual problems, migration rationale (HIGH confidence)
- [It's Time to Learn oklch Color — Keith J. Grant](https://keithjgrant.com/posts/2023/04/its-time-to-learn-oklch-color/) — Hue degree reference values (MEDIUM confidence)
- [OKLCH Color Picker — oklch.fyi](https://oklch.fyi/) — Practical chroma/lightness ranges (MEDIUM confidence)
- [OKLCH: The Modern CSS Color Space — Medium/Alexander Burgos](https://medium.com/@alexdev82/oklch-the-modern-css-color-space-you-should-be-using-in-2025-52dd1a4aa9d0) — 2025 adoption context (MEDIUM confidence)
