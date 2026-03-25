# Roadmap: Major System Trainer — Grid Mastery Colors

**Milestone:** Hue-based OKLCH mastery color system
**Granularity:** Coarse
**Coverage:** 9/9 v1 requirements mapped

---

## Phases

- [x] **Phase 1: Core Color Computation** - OKLCH hue rotation working in the dark theme
- [ ] **Phase 2: Theme Integration** - All four themes supported, theme-switch wired
- [ ] **Phase 3: Cleanup** - Dead RGB lerp code and legacy CSS classes removed

---

## Phase Details

### Phase 1: Core Color Computation
**Goal**: Grid cells display consistent-weight hue-based mastery colors in the dark theme
**Depends on**: Nothing (first phase)
**Requirements**: COLOR-01, COLOR-02, COLOR-03, COLOR-04
**Success Criteria** (what must be TRUE):
  1. Every non-zero scored cell on the grid has equal visual weight regardless of score magnitude — no cell fades toward invisible
  2. Negative scores show red/yellow hues, positive scores show blue/green hues, score 0 shows the plain theme background with no color applied
  3. The score-to-hue progression is monotonic: score +5 sits visually between +1 and +10, score -5 sits visually between -1 and -10
  4. Cell font color uses the same hue as the background at a contrasting lightness, remaining readable on dark theme background
**Plans:** 2 plans
Plans:
- [x] 01-01-PLAN.md — CSS custom properties + scoreToHue test scaffold
- [x] 01-02-PLAN.md — TypeScript OKLCH implementation + visual verification

### Phase 2: Theme Integration
**Goal**: Mastery colors work correctly across all four themes and update immediately on theme switch
**Depends on**: Phase 1
**Requirements**: THEME-01, THEME-02, THEME-03
**Success Criteria** (what must be TRUE):
  1. Switching between dark, light, and oled themes immediately re-renders all scored grid cells with the correct per-theme brightness and chroma — no stale colors
  2. Per-theme OKLCH lightness and chroma constants are defined as CSS custom properties in _variables.scss (not hardcoded in JS)
  3. The high-contrast theme does not inject computed OKLCH inline styles — cells display correctly using the existing CSS class approach
**Plans**: TBD

### Phase 3: Cleanup
**Goal**: Legacy RGB lerp code and mastery CSS classes are fully removed with no regressions
**Depends on**: Phase 2
**Requirements**: CLEAN-01, CLEAN-02
**Success Criteria** (what must be TRUE):
  1. The profile section activity bars and any other components that used the old mastery CSS vars still render correctly after the legacy SCSS vars and CSS classes are deleted
  2. No references to lerpRGB(), GRADIENT_GREEN, GRADIENT_YELLOW, GRADIENT_RED, or parseColor() remain in the codebase
  3. The build (tsc --noEmit + sass compilation) passes cleanly with no errors after cleanup
**Plans**: TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Color Computation | 2/2 | Complete | 2026-03-25 |
| 2. Theme Integration | 0/? | Not started | - |
| 3. Cleanup | 0/? | Not started | - |

---
*Roadmap created: 2026-03-25*
