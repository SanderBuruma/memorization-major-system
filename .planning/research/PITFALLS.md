# Domain Pitfalls: HSL Color Visualization for Mastery Grid

**Domain:** Hue-based data visualization in a multi-theme SPA
**Researched:** 2026-03-25
**Confidence:** HIGH (verified against MDN, W3C, Wikipedia HSL/HSV article, and multiple practitioner sources)

---

## Critical Pitfalls

Mistakes that cause rewrites or major accessibility regressions.

---

### Pitfall 1: HSL Lightness Does Not Equal Perceived Brightness

**What goes wrong:**
Yellow and green at `hsl(60, 70%, 35%)` and `hsl(200, 70%, 35%)` share the same `L` value, but yellow appears dramatically brighter to the human eye. The eye's red- and green-sensitive cones vastly outnumber blue-sensitive cones, so yellow-green wavelengths register as much more luminous. When the plan calls for "constant brightness, only hue changes," HSL cannot deliver that guarantee — it only keeps the *model* value constant, not the *perceived* brightness.

**Why it happens:**
HSL is a device-oriented model, not a perceptual one. Its lightness channel correlates poorly with CIELAB luminance. The Wikipedia article on HSL/HSV documents this explicitly: "the selected lightness value does not predict the actual displayed luminance nor the perception thereof." Perceptually uniform spaces (OKLCH, HCL, HSLuv) fix this, but plain HSL does not.

**Consequences in this project:**
- Green cells (high mastery, score +10) will appear to "pop" more than blue cells (score ±1) even at the same HSL lightness, making the grid look uneven.
- Blue (the planned neutral at ±1 boundary) is the dimmest hue in HSL — it will appear nearly invisible against a dark background even at the chosen lightness, defeating the "consistent visual weight" goal.
- Yellow-green hues (medium mastery) will visually dominate the grid even when most cells are near-neutral.

**Prevention:**
Accept that some perceived brightness variation is unavoidable with plain HSL. Compensate deliberately: raise lightness for blue (e.g. L=55%) and lower it for yellow-green (e.g. L=30%) to achieve approximate perceptual evenness. Test visually at each theme background. Do not assume `L=X` is equal across hues.

**Detection (warning sign):**
After implementation, scan the grid with a mix of scores from -10 to +10. If any hue stands out as noticeably brighter or more muted than neighbors at similar scores, the compensation is wrong.

**Phase:** Color computation implementation phase.

---

### Pitfall 2: Red-Green Hue Axis Is the Canonical Color Blindness Failure

**What goes wrong:**
The planned hue range maps negative scores to red, positive to green, with blue near zero. This is exactly the palette that is indistinguishable for deuteranopia (green-blind) and protanopia (red-blind), which together affect ~8% of men (~4.5% of the total population). A deuteranope sees both red and green as muddy yellow-brown. The entire scoring signal disappears for them.

**Why it happens:**
Red and green share the same confusion axis for both common forms of red-green color blindness. Relying on hue *alone* to convey mastery level — with no luminance, pattern, or text fallback — makes the grid unreadable for a significant minority.

**Consequences:**
- The grid's primary function (visual mastery feedback) is completely lost for colorblind users.
- The `high-contrast` theme is not a fallback for this — it changes contrast, not the hue system.
- WCAG 1.4.1 (Use of Color) requires that color not be the *only* means of conveying information.

**Prevention:**
Supplement hue with a secondary cue. Options in this codebase's context:
- Vary lightness *slightly* alongside hue (high mastery = lighter background, low mastery = darker). This also helps perceptual uniformity.
- Keep a numeric score indicator visible in cells at extreme values (optional tooltip or text).
- For the `high-contrast` theme specifically, fall back to the existing discrete CSS class system (`mastery-0` through `mastery-4`) instead of computed HSL colors.

**Detection:**
Run the grid through a deuteranopia simulator (e.g. Coblis or the browser devtools "Emulate vision deficiency" in Chrome). If the grid looks uniform grey-brown, the scheme is inaccessible.

**Phase:** Color computation implementation phase and theme compatibility review.

---

### Pitfall 3: JavaScript Inline `style.backgroundColor` Fights Theme Switching

**What goes wrong:**
The current `updateMasteryColors()` sets `el.style.backgroundColor = 'rgb(...)'`. This inline style has the highest CSS specificity and is entirely disconnected from the CSS custom property system. The new HSL implementation will likely continue this pattern, writing `el.style.backgroundColor = 'hsl(...)'`. The problem: when the user switches theme, `updateMasteryColors()` must be re-called — but if the theme switch happens before the function is triggered (e.g. on page load before the grid renders), cells will briefly display the wrong background color. The theme's `--bg-surface` value is read at call time; stale calls produce stale colors.

**Why it happens:**
Inline styles are outside the cascade. CSS variables propagate automatically on theme change; inline overrides do not. The current code already has this coupling — `updateMasteryColors()` reads `getComputedStyle(document.documentElement).getPropertyValue('--bg-surface')` to get the theme baseline. Any async gap between theme change and color recomputation produces visible glitches.

**Consequences:**
- After a theme switch, cells with score=0 correctly revert (they clear `style.backgroundColor`), but non-zero cells retain the old theme's color until `updateMasteryColors()` runs.
- In the OLED theme (pure black background), colors computed for the dark theme will look washed-out. In the light theme, colors computed for dark will look very dark.

**Prevention:**
Call `updateMasteryColors()` explicitly in `setTheme()` (in `theme.ts`) immediately after `setAttribute('data-theme', ...)`. Verify the call order: the attribute must be set *before* reading computed style so that `--bg-surface` resolves to the new theme's value. Check that `setTheme` is also called on page load (it currently is — `savedTheme` is applied at module load, but `updateMasteryColors` is not guaranteed to run after grid render).

**Detection:**
Switch themes rapidly while the grid is visible. Any cell that holds the previous theme's color for more than one frame indicates the timing is wrong.

**Phase:** Theme integration / wiring phase.

---

### Pitfall 4: The `high-contrast` Theme Must Not Use Computed HSL Colors

**What goes wrong:**
The `high-contrast` theme (`--bg-page: #000`, `--text-primary: #ffff00`) is designed for maximum contrast using a fixed yellow-on-black palette. Injecting arbitrary HSL hue colors via inline style overrides the carefully-chosen high-contrast values and produces cells that may fail WCAG contrast ratios entirely (e.g. a dark blue background with yellow text is fine; a dark red background with yellow text may fail).

Furthermore, browsers in Windows High Contrast Mode (Forced Colors) will attempt to override inline color styles, but only partially — the interaction between forced colors and arbitrary inline HSL values is undefined and browser-dependent.

**Why it happens:**
The CSS `forced-colors: active` media query strips many color declarations, but `style.backgroundColor` set via JavaScript is handled inconsistently by browsers unless the element also sets `forced-color-adjust: none`, which itself disables all forced-color protections.

**Consequences:**
- High-contrast users get a visually broken grid with unpredictable foreground/background combinations.
- The mastery information may be entirely invisible or cause eye strain for users who need high contrast most.

**Prevention:**
Gate the computed-HSL path behind a theme check. For `high-contrast`, skip setting `style.backgroundColor` entirely and fall back to the existing CSS class approach (`mastery-0` through `mastery-4`). The theme variables for those classes are already tuned for high contrast.

```typescript
// In updateMasteryColors()
const theme = document.documentElement.getAttribute('data-theme');
if (theme === 'high-contrast') {
  // Apply discrete mastery class, skip inline HSL
  return;
}
```

**Detection:**
Switch to `high-contrast` theme and verify the grid cells show the correct class-based colors, not inline HSL.

**Phase:** Theme compatibility / accessibility review.

---

## Moderate Pitfalls

---

### Pitfall 5: Hue Wrapping at Boundaries Produces Unexpected Colors

**What goes wrong:**
CSS `hsl()` accepts hue as a number; values outside 0–360 wrap. If the score-to-hue mapping uses arithmetic that produces values near 0 or 360, small floating point differences can produce a color near red when green was intended (or vice versa). More importantly, if hue is interpolated linearly between e.g. 200 (blue) and 0 (red), the path goes through green and yellow unexpectedly because the shortest hue arc is 160 degrees clockwise but a naive `lerp` would go the long way around.

**Prevention:**
Define hue values as explicit named constants, not computed from lerp. The current plan maps discrete score ranges to specific hues (red, yellow, blue, green); keep it as piecewise lookup rather than a continuous numeric interpolation over hue. If interpolation is added later, implement shortest-arc logic.

**Phase:** Color computation implementation phase.

---

### Pitfall 6: Font Color HSL at Same Hue Varies in Contrast Across Themes

**What goes wrong:**
The plan calls for font color to use the same hue as the background but at a different lightness for readability. In a dark theme, a lighter shade of the hue over the darker background works. In a light theme, the background cell is lighter to begin with — a "lighter" font shade at the same hue may have *less* contrast than the background, not more. The relationship between font lightness offset and actual contrast ratio flips between dark and light themes.

**Why it happens:**
WCAG contrast is computed from *relative luminance*, which is non-linear. A `+20%` lightness offset that provides 4.5:1 contrast on a dark background may provide only 1.8:1 on a light background because absolute luminance compresses at high values.

**Prevention:**
Compute font lightness as a function of the background's resolved lightness, not as a fixed offset. Alternatively, define separate light/dark font-lightness values per theme. Verify contrast ratios at each theme using a contrast checker tool (e.g. WebAIM Contrast Checker) for at least the red and blue endpoints, which are the most likely to fail.

**Phase:** Font color implementation and theme verification.

---

### Pitfall 7: `updateMasteryColors()` Does Not Cover the Grid Quiz Section

**What goes wrong:**
`updateMasteryColors()` currently targets `#grid .grid-cell`. The grid quiz section (`#gridquiz-grid .grid-cell`) is a separate DOM tree. If the milestone adds hue-based colors to the mastery grid, the grid quiz may be missed and will display un-colored cells or stale colors.

**Prevention:**
Check whether mastery colors should also apply to the grid quiz view. If yes, extend the selector or call a shared color-update utility for both grids.

**Phase:** Implementation and integration testing.

---

## Minor Pitfalls

---

### Pitfall 8: Reading `--bg-surface` After Theme Change Requires Sync

**What goes wrong:**
`getComputedStyle(document.documentElement).getPropertyValue('--bg-surface')` reads the *current* computed value. If called in the same synchronous block as `setAttribute('data-theme', ...)`, it correctly returns the new theme's value because `setAttribute` is synchronous and style recalculation happens before the next layout. But if called in a `setTimeout` or async callback *before* the browser repaints, the value may be from the previous theme depending on browser behavior.

**Prevention:**
Call `updateMasteryColors()` synchronously after `setAttribute('data-theme', theme)` in `setTheme()`, with no `await` or `setTimeout` in between. This is already the correct pattern for synchronous CSS variable reads.

**Phase:** Theme integration wiring.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| Score-to-hue mapping | HSL perceived brightness inequality (Pitfall 1) | Manual lightness compensation per hue; visual testing across score range |
| Color computation (JavaScript) | RGB lerp pattern repeated in HSL (Pitfall 3) | Ensure `updateMasteryColors()` is called on theme switch, synchronously |
| Theme compatibility | High-contrast broken by inline HSL (Pitfall 4) | Guard clause: skip HSL for high-contrast theme, use CSS classes |
| Font color implementation | Contrast ratio flips between themes (Pitfall 6) | Per-theme lightness offsets; verify with contrast checker |
| Color blindness | Red-green axis invisible to deuteranopes (Pitfall 2) | Add luminance variation or use blue-orange axis instead of red-green |
| Hue interpolation (if added) | Hue wrapping through wrong arc (Pitfall 5) | Use piecewise named constants instead of linear hue lerp |
| Grid quiz section | Mastery colors not applied to second grid (Pitfall 7) | Audit all `grid-cell` containers, not just `#grid` |

---

## Sources

- [HSL and HSV — Wikipedia](https://en.wikipedia.org/wiki/HSL_and_HSV) — Documents the non-perceptual nature of HSL lightness; HIGH confidence
- [Perceptually uniform color spaces — Programming Design Systems](https://programmingdesignsystems.com/color/perceptually-uniform-color-spaces/) — MEDIUM confidence
- [Building a contrast-based color system with HSLuv — Guavapay Design on Medium](https://medium.com/design-at-guavapay/building-a-contrast-based-color-system-with-hsluv-39605c16febd) — MEDIUM confidence
- [OKLCH in CSS: why we moved from RGB and HSL — Evil Martians](https://evilmartians.com/chronicles/oklch-in-css-why-quit-rgb-hsl) — MEDIUM confidence
- [Web Accessibility: Understanding Colors and Luminance — MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/Guides/Colors_and_Luminance) — HIGH confidence
- [Understanding WCAG 1.4.3 Contrast (Minimum) — W3C WAI](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html) — HIGH confidence
- [Forced colors explained — Polypane](https://polypane.app/blog/forced-colors-explained-a-practical-guide/) — MEDIUM confidence
- [Windows High Contrast Mode, Forced Colors and CSS Custom Properties — Smashing Magazine](https://www.smashingmagazine.com/2022/03/windows-high-contrast-colors-mode-css-custom-properties/) — MEDIUM confidence
- [Coloring for Colorblindness — David Math Logic](https://davidmathlogic.com/colorblind/) — MEDIUM confidence
- [Types of Colour Blindness — Colour Blind Awareness](https://www.colourblindawareness.org/colour-blindness/types-of-colour-blindness/) — HIGH confidence
