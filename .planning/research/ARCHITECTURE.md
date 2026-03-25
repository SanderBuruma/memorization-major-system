# Architecture Research

**Domain:** HSL hue-based constant-brightness color system for TypeScript SPA with CSS custom properties theming
**Researched:** 2026-03-25
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         RENDER TRIGGER                          │
│  score change → updateMasteryColors() in src/ts/ui.ts           │
│  theme change → setTheme() in src/ts/theme.ts                   │
├─────────────────────────────────────────────────────────────────┤
│                      COLOR COMPUTATION (JS)                     │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  scoreToHue(score: number): number                     │     │
│  │  masteryColor(score, theme): { bg: string, fg: string }│     │
│  └────────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────┤
│                       DOM WRITE (JS)                            │
│  el.style.backgroundColor = oklch(L% C H)                      │
│  el.style.color            = oklch(L% C H)   (same H, diff L)  │
│  el.style.backgroundColor = ''  (score === 0, revert to CSS)   │
├─────────────────────────────────────────────────────────────────┤
│                  THEME CONSTANTS (CSS / SCSS)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  dark theme  │  │  light theme │  │  oled / hi-contrast  │  │
│  │  L=35% C=.12 │  │  L=80% C=.10 │  │  per-theme overrides │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Location |
|-----------|----------------|----------|
| `scoreToHue()` | Maps numeric score (-10..+10) to a hue angle (0..360) | `src/ts/ui.ts` |
| `masteryColor()` | Produces oklch bg + fg strings from score + theme L/C constants | `src/ts/ui.ts` |
| `updateMasteryColors()` | Reads scores, calls masteryColor, writes inline styles | `src/ts/ui.ts` (existing) |
| Theme L/C constants | Per-theme lightness and chroma values, read at call time | CSS custom props or JS const map |
| `_variables.scss` | Removes old `--bg-mastery-*` / `--color-mastery-*` vars, keeps theme tokens | `src/scss/_variables.scss` |
| `_grid.scss` | Removes old `.mastery-0..4` classes; inline styles own all mastery color now | `src/scss/_grid.scss` |

## Recommended Project Structure

No new files needed. The change is contained within two existing files:

```
src/
├── ts/
│   └── ui.ts           # Add scoreToHue(), masteryColor(); rewrite updateMasteryColors()
└── scss/
    ├── _variables.scss  # Remove --bg-mastery-* / --color-mastery-* custom props
    └── _grid.scss       # Remove .mastery-0..4 CSS class rules
```

### Structure Rationale

- **No new module:** Color computation is a 20-line utility tightly coupled to `updateMasteryColors()`. Extracting to a separate file adds indirection without benefit at this scale.
- **Inline styles, not CSS classes:** The hue value is continuous (not tiered), so CSS classes cannot represent it. Inline `style.backgroundColor` / `style.color` is the only viable DOM write pattern.
- **CSS custom props for L/C:** Theme-specific lightness and chroma live in `_variables.scss` as custom properties. JS reads them at call time via `getComputedStyle`, the same pattern already used for `--bg-surface`. This avoids a JS/CSS split-brain problem where theme constants live in two places.

## Architectural Patterns

### Pattern 1: Score-to-Hue Linear Mapping

**What:** Map the score range (-10..+10) to a hue arc. Negative scores rotate toward warm hues (red/yellow), positive scores toward cool/green. Score 0 receives no color.

**When to use:** Any continuous mastery metric driving a perceptual color gradient.

**Trade-offs:** Simple and predictable. Does not account for perceptual non-uniformity of hue (oklch chroma compensates partially). Clamping to -10..+10 is already done in the current code.

**Hue mapping (from PROJECT.md spec):**
```
score -10  →  hue   0  (red)
score  -5  →  hue  60  (yellow)
score  -1  →  hue 240  (blue)
score   0  →  no color  (theme background)
score  +1  →  hue 240  (blue)
score +10  →  hue 140  (green)
```

**Example:**
```typescript
function scoreToHue(score: number): number {
  if (score < 0) {
    // -10..0 → red(0)..blue(240), via yellow(60) at -5
    if (score >= -5) return 60 + (score + 5) / 5 * 180;  // -5..0 → 60..240
    return (score + 10) / 5 * 60;                         // -10..-5 → 0..60
  }
  // 0..+10 → blue(240)..green(140)
  return 240 - score / 10 * 100;                          // +1..+10 → 230..140
}
```

### Pattern 2: Theme-Aware L/C Constants via CSS Custom Properties

**What:** Define per-theme oklch lightness (L) and chroma (C) values as CSS custom properties. JS reads them at paint time with `getComputedStyle`. This is identical to the existing `--bg-surface` read pattern in `updateMasteryColors()`.

**When to use:** When colors must behave differently per theme (dark themes need lower L for backgrounds; light themes need higher L).

**Trade-offs:** Slightly more indirection than hardcoded JS constants, but keeps theme definitions in a single place (_variables.scss) and avoids re-implementing theme detection in JS.

**Example — SCSS:**
```scss
:root, [data-theme="dark"] {
  --mastery-bg-L: 28%;
  --mastery-bg-C: 0.12;
  --mastery-fg-L: 75%;
  --mastery-fg-C: 0.15;
}

[data-theme="light"] {
  --mastery-bg-L: 88%;
  --mastery-bg-C: 0.09;
  --mastery-fg-L: 35%;
  --mastery-fg-C: 0.18;
}

[data-theme="oled"] {
  --mastery-bg-L: 18%;
  --mastery-bg-C: 0.14;
  --mastery-fg-L: 80%;
  --mastery-fg-C: 0.16;
}

[data-theme="high-contrast"] {
  --mastery-bg-L: 14%;
  --mastery-bg-C: 0.20;
  --mastery-fg-L: 90%;
  --mastery-fg-C: 0.22;
}
```

**Example — JS read:**
```typescript
function getMasteryConstants(): { bgL: string; bgC: string; fgL: string; fgC: string } {
  const style = getComputedStyle(document.documentElement);
  return {
    bgL: style.getPropertyValue('--mastery-bg-L').trim(),
    bgC: style.getPropertyValue('--mastery-bg-C').trim(),
    fgL: style.getPropertyValue('--mastery-fg-L').trim(),
    fgC: style.getPropertyValue('--mastery-fg-C').trim(),
  };
}
```

### Pattern 3: OKLCH for Perceptually Uniform Constant-Brightness Colors

**What:** Use `oklch(L% C H)` rather than `hsl(H, S%, L%)`. OKLCH maintains perceived lightness across all hue angles; HSL does not (yellow at 50% HSL-L is visually much brighter than blue at the same value).

**When to use:** Any time hue varies while brightness must feel constant — exactly this use case.

**Trade-offs:** Requires OKLCH browser support (Baseline Widely Available since November 2025 — Chrome 111+, Safari 15.4+, Firefox 113+). No polyfill needed for a web-first 2026 project. HSL is simpler but will produce noticeably uneven brightness across hues.

**Example — full color write:**
```typescript
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

## Data Flow

### Color Update Flow

```
Quiz answer checked
      ↓
MODES.quiz.scores[key] updated
      ↓
updateMasteryColors() called
      ↓
For each grid cell:
  raw = sum of quiz + reverse + mixed scores
  score = clamp(raw, -10, 10)
      ↓
  score === 0?
    → clear inline styles (CSS --bg-surface applies)
  score !== 0?
    → scoreToHue(score) → H
    → read --mastery-bg-L/C, --mastery-fg-L/C from computed style
    → el.style.backgroundColor = oklch(bgL bgC H)
    → el.style.color           = oklch(fgL fgC H)
```

### Theme Change Flow

```
setTheme(theme) called
      ↓
document.documentElement.setAttribute('data-theme', theme)
      ↓
CSS custom properties change (browser recomputes --mastery-bg-L etc.)
      ↓
updateMasteryColors() called again
  (already called on theme change? If not, add call to setTheme())
      ↓
getMasteryConstants() reads fresh computed values
      ↓
All inline styles rewritten with new L/C for active theme
```

**Note:** `setTheme()` currently does not call `updateMasteryColors()`. A single line must be added there so that color weights recompute when the theme changes.

### Key Data Flows

1. **Score update → color:** `quiz.ts` increments `MODES.*.scores[key]`, then calls `updateMasteryColors()` (current behavior unchanged — only the color computation inside changes).
2. **Theme switch → color:** `theme.ts:setTheme()` switches the `data-theme` attribute, then must call `updateMasteryColors()` so L/C constants are re-read for the new theme.
3. **Page load → color:** `init.ts` calls `updateMasteryColors()` after state is restored (current behavior unchanged).

## Anti-Patterns

### Anti-Pattern 1: Using HSL Instead of OKLCH

**What people do:** Replace `lerpRGB()` with an HSL hue rotation, keeping hsl() in the color string.

**Why it's wrong:** HSL lightness is not perceptually uniform. Yellow at `hsl(60, 70%, 35%)` appears much brighter than blue at `hsl(240, 70%, 35%)`. The requirement is constant visual weight across all cells — HSL cannot satisfy this without complex per-hue lightness compensation tables.

**Do this instead:** Use `oklch()`. Same three-param signature, true perceptual uniformity, no additional computation.

### Anti-Pattern 2: Hardcoding L/C in JavaScript

**What people do:** Write `const BG_LIGHTNESS = { dark: '28%', light: '88%', ... }` in ui.ts, then switch on the current theme in JS.

**Why it's wrong:** Theme constants are already owned by `_variables.scss`. Duplicating them in JS creates a split-brain: any theme adjustment requires two edits, and the JS theme detection is redundant with the existing `data-theme` attribute system.

**Do this instead:** Define `--mastery-bg-L`, `--mastery-bg-C`, `--mastery-fg-L`, `--mastery-fg-C` in `_variables.scss` per `[data-theme]` block. Read them in JS with `getComputedStyle` at paint time. One source of truth.

### Anti-Pattern 3: Adding CSS Classes for Each Score Tier

**What people do:** Define `.mastery-score-3`, `.mastery-score-7`, etc. in SCSS and assign them in JS.

**Why it's wrong:** Hue is continuous. Any discretization loses the smooth gradient across cells. The current system already proved this is suboptimal — it's exactly what's being replaced.

**Do this instead:** Write inline styles directly. Continuous score → continuous hue → continuous color.

### Anti-Pattern 4: Calling getComputedStyle Per Cell

**What people do:** Move the `getComputedStyle` call inside the `cells.forEach` loop.

**Why it's wrong:** `getComputedStyle` triggers layout in some browsers when called repeatedly in a loop. The L/C constants don't change per cell — they're theme-level. Read them once before the loop.

**Do this instead:** Call `getMasteryConstants()` once above the loop, then use the cached values inside.

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `ui.ts` → `_variables.scss` | JS reads CSS custom props via `getComputedStyle` | Same pattern as existing `--bg-surface` read |
| `theme.ts:setTheme()` → `ui.ts:updateMasteryColors()` | Direct function call (add one line) | Required so colors recompute on theme switch |
| `quiz.ts` → `ui.ts:updateMasteryColors()` | Direct function call (unchanged) | Already called after score updates |
| `init.ts` → `ui.ts:updateMasteryColors()` | Direct function call (unchanged) | Already called on page load |

### SCSS Cleanup Boundary

The old CSS class system (`.mastery-0..4` and `--bg-mastery-*` / `--color-mastery-*` custom properties) is fully replaced. These can be deleted once inline styles take over. The JS side must also remove the `el.className.replace(/mastery-\d/g, '').trim()` line from `updateMasteryColors()` since those classes will no longer exist.

## Sources

- [MDN: oklch()](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/oklch) — HIGH confidence
- [OKLCH in CSS: why we moved from RGB and HSL](https://evilmartians.com/chronicles/oklch-in-css-why-quit-rgb-hsl) — MEDIUM confidence (authoritative deep-dive)
- [oklch() | CSS-Tricks](https://css-tricks.com/almanac/functions/o/oklch/) — MEDIUM confidence
- [Can I use: oklch](https://caniuse.com/mdn-css_types_color_oklch) — HIGH confidence (browser support data)
- [Color Manipulation With CSS Variables and HSL](https://codesalad.dev/blog/color-manipulation-with-css-variables-and-hsl-16) — MEDIUM confidence (CSS custom props pattern)

---
*Architecture research for: HSL/OKLCH hue-based mastery colors — Major System Trainer*
*Researched: 2026-03-25*
