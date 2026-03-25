# Phase 2: Theme Integration - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Make OKLCH mastery colors work correctly across all four themes (dark, light, oled, high-contrast) and update immediately on theme switch. No new color logic — just per-theme L/C tuning + wiring setTheme() to trigger recompute.

</domain>

<decisions>
## Implementation Decisions

### Theme Treatment
- Same OKLCH hue-rotation system for ALL themes, including high-contrast — no special-casing or bypassing
- Each theme only differs in L (lightness) and C (chroma) values via CSS custom properties
- Overrides prior Phase 1 decision: "High-contrast bypasses computed colors" → now high-contrast uses the same OKLCH system with appropriate L/C values

### Color Intensity
- Subtle tint approach: colored cells should blend into the theme, not pop aggressively
- Color is secondary to the cell content — it's an ambient signal, not a loud indicator

### Light Theme
- Colored background with dark text: cell background gets a light tint of the hue, text is a darker shade of the same hue
- Must still feel like a light theme — no dark colored cells on white background

### OLED Theme
- Same L/C values as dark theme — no separate tuning needed
- OLED and dark share mastery color values

### Claude's Discretion
- Exact L/C numeric values per theme — Claude tunes for readability and subtle-tint feel
- Whether to extract the hue-to-color logic further or keep it inline
- High-contrast L/C values (Claude picks values that pass WCAG AA minimum)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `getMasteryConstants()` in `src/ts/ui.ts` — already reads CSS custom props via `getComputedStyle`, no changes needed
- `updateMasteryColors()` — already writes OKLCH inline styles, already called from init and persistence
- `_variables.scss` — already has `--mastery-bg-L`, `--mastery-bg-C`, `--mastery-fg-L`, `--mastery-fg-C` in all four theme blocks

### Established Patterns
- Theme switching via `[data-theme]` attribute on `<html>` — `setTheme()` in `src/ts/theme.ts`
- CSS custom properties update instantly when `data-theme` changes — but inline styles from `updateMasteryColors()` don't auto-update (need explicit call)

### Integration Points
- `setTheme()` in `src/ts/theme.ts` — must add `updateMasteryColors()` call after `setAttribute`
- `toggleTheme()` calls `setTheme()` — so toggle is covered transitively
- Theme select dropdown in settings also calls `setTheme()` — covered transitively

</code_context>

<specifics>
## Specific Ideas

No specific requirements — Claude tunes L/C values for each theme based on "subtle tint" preference and readability. Visual calibration during implementation.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-theme-integration*
*Context gathered: 2026-03-25*
