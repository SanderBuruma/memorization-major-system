# Major System Trainer

## What This Is

A web-based memorization trainer for the Major System mnemonic technique. Users learn to associate numbers (00-99) with words via phoneme-based encoding, practicing through multiple quiz modes with mastery tracking. Built as a Django SPA with TypeScript frontend.

## Core Value

Users can drill number-to-word associations and see their mastery improve over time through visual feedback on the grid.

## Requirements

### Validated

- ✓ Grid view showing all 00-99 number-word associations — existing
- ✓ Four quiz modes (number→word, word→number, mixed, consonant) via generic engine — existing
- ✓ Per-cell mastery scoring with color-coded grid feedback — existing
- ✓ Custom word selection per cell with candidate suggestions from API — existing
- ✓ State persistence (localStorage + server sync via QuizState model) — existing
- ✓ User authentication (session-based) with anonymous IP fallback — existing
- ✓ Four themes (dark, light, oled, high-contrast) — existing
- ✓ OpenDyslexic font toggle — existing
- ✓ Onboarding tutorial (5-step overlay) — existing
- ✓ Profile section with accuracy stats and activity heatmap — existing
- ✓ Reference section with Major System encoding table — existing
- ✓ Translate section for encoding arbitrary text to digits — existing
- ✓ Hash-based URL routing for section navigation — existing
- ✓ CI/CD pipeline (GitHub Actions → VPS deploy on push to master) — existing

### Active

- [ ] Hue-based grid mastery colors: constant brightness, only hue changes with score
- [ ] Grid cell font color shifts hue alongside background (same hue, different lightness for readability)

### Out of Scope

- Mobile app — web-first, responsive design handles mobile
- Additional quiz modes beyond the existing four — not requested

## Context

The current grid coloring system uses RGB lerp from the theme surface color toward green/yellow/red targets. This means brightness varies with score — low scores are near-invisible (close to background), high scores are vivid. The user wants consistent visual weight across all non-zero cells, with only hue indicating mastery level.

**Desired hue mapping (score → hue):**
- Score -10 (worst): Red
- Score ~-5: Yellow
- Score -1: Blue
- Score 0: Theme background (no color)
- Score +1: Blue
- Score +10 (best): Green

Both background and font color use the same hue at different lightness values for readability.

## Constraints

- **Tech stack**: Django + TypeScript SPA, SCSS for styles — must stay within existing architecture
- **Theme compatibility**: Must work across all 4 themes (dark, light, oled, high-contrast)
- **Build**: esbuild IIFE bundle, sass compilation — no new build tooling

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| HSL color space for grid cells | Allows independent control of hue vs brightness | — Pending |
| Same hue for font + background | User preference for unified color language per cell | — Pending |
| Blue at score boundary (±1) | Provides cool neutral color near zero, warm colors for negative | — Pending |

---
*Last updated: 2026-03-25 after initialization*
