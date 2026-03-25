# Requirements: Major System Trainer — Grid Mastery Colors

**Defined:** 2026-03-25
**Core Value:** Users can see their mastery improve over time through consistent, hue-based visual feedback on the grid

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Color Computation

- [x] **COLOR-01**: Grid cells use OKLCH color space with constant lightness and chroma, varying only hue based on mastery score
- [x] **COLOR-02**: Score-to-hue mapping follows red (score -10) → yellow (~-5) → blue (±1) → green (+10), with score 0 showing theme background (no color)
- [x] **COLOR-03**: Font color uses same hue as cell background at a contrasting lightness value for readability
- [x] **COLOR-04**: Score-to-hue curve uses sqrt easing for better perceptual separation at low scores

### Theme Integration

- [ ] **THEME-01**: Per-theme OKLCH lightness and chroma constants defined as CSS custom properties in _variables.scss
- [ ] **THEME-02**: Theme switching triggers grid mastery color recomputation via updateMasteryColors()
- [ ] **THEME-03**: High-contrast theme has special handling to maintain WCAG-compliant legibility

### Cleanup

- [ ] **CLEAN-01**: Legacy mastery-0..4 CSS classes and --bg-mastery-*/--color-mastery-* SCSS vars removed (profile section dependency audited first)
- [ ] **CLEAN-02**: Dead JS code removed: lerpRGB(), GRADIENT_GREEN/YELLOW/RED constants, parseColor() helper

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### UX Enhancement

- **UX-01**: Color legend or tooltip explaining the score-to-color mapping on the grid view

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Colorblind-safe alternative encoding | Separate a11y milestone; hue is not the sole feedback mechanism (numbers are always visible) |
| Animated color transitions on score change | Adds complexity; quiz state changes happen rapidly, transitions may conflict |
| OKLCH polyfill or library | Native browser support 92%+, Baseline Widely Available since Nov 2025 |
| Separate saturation for positive vs negative scores | Adds second dimension to already multi-variable system; keep saturation constant |
| Persistence of computed color values | Recompute from score on each call, as today; no benefit to caching |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| COLOR-01 | Phase 1 | Complete |
| COLOR-02 | Phase 1 | Complete |
| COLOR-03 | Phase 1 | Complete |
| COLOR-04 | Phase 1 | Complete |
| THEME-01 | Phase 2 | Pending |
| THEME-02 | Phase 2 | Pending |
| THEME-03 | Phase 2 | Pending |
| CLEAN-01 | Phase 3 | Pending |
| CLEAN-02 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0

---
*Requirements defined: 2026-03-25*
*Last updated: 2026-03-25 after roadmap creation — traceability complete*
