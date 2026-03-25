# Phase 3: Cleanup - Research

**Researched:** 2026-03-25
**Domain:** Dead code removal — legacy RGB lerp logic and mastery CSS class system
**Confidence:** HIGH

## Summary

Phase 3 removes two independent layers of legacy code that were deliberately preserved during Phase 1:
the RGB-lerp coloring system (JS side) and the discrete CSS class tier system (SCSS/JS side). Both
layers are now fully superseded by the OKLCH inline-style approach from Phases 1–2. No new
functionality is added; the goal is a clean, regressionless removal pass.

The critical constraint is `_profile.scss`: it reads `--color-mastery-*` vars for bar chart fill
colors. These vars overlap with the `--bg-mastery-*` / `--color-mastery-*` vars being deleted.
The profile bars will break silently if the vars are removed without replacement. Additionally,
`wiki.ts` uses `var(--color-mastery-*)` inline styles in its help text.

The test suite in `tests/test_theme.py` explicitly tracks `--bg-mastery-*` and `--color-mastery-*`
as classified variables in `BG_VARS` and `FG_ACCENT_VARS`. Those test lists must be updated in
lockstep with the SCSS deletions, or every test class will fail.

**Primary recommendation:** Remove vars and classes in a single coordinated edit across
`_variables.scss`, `_grid.scss`, `ui.ts`, `wiki.ts`, `_profile.scss`, and `test_theme.py`.
`_profile.scss` and `wiki.ts` must migrate to replacement tokens before the vars are deleted.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLEAN-01 | Legacy mastery-0..4 CSS classes and --bg-mastery-*/--color-mastery-* SCSS vars removed (profile section dependency audited first) | Full audit complete — see Standard Stack and Architecture Patterns sections for exact locations and migration plan |
| CLEAN-02 | Dead JS code removed: lerpRGB(), GRADIENT_GREEN/YELLOW/RED constants, parseColor() helper | Exact lines identified (ui.ts:577–593); `type RGB` alias also dead and must be removed |
</phase_requirements>

---

## Audit: Complete Reference Map

### CLEAN-02: Dead JS (ui.ts)

All dead code is in a contiguous block in `src/ts/ui.ts`:

| Lines | Symbol | Status |
|-------|--------|--------|
| 577 | `type RGB = [number, number, number]` | Dead — only used by parseColor/lerpRGB |
| 579–585 | `function parseColor(s: string): RGB` | Dead — not called anywhere |
| 587–589 | `function lerpRGB(a: RGB, b: RGB, t: number): RGB` | Dead — not called anywhere |
| 591 | `const GRADIENT_YELLOW: RGB = [224, 160, 80]` | Dead — not referenced anywhere |
| 592 | `const GRADIENT_RED: RGB = [239, 83, 80]` | Dead — not referenced anywhere |
| 593 | `const GRADIENT_GREEN: RGB = [76, 218, 106]` | Dead — not referenced anywhere |

Additionally on line 632 inside `updateMasteryColors()`:
```
el.className = el.className.replace(/mastery-\d/g, '').trim();
```
This strips the legacy CSS class from cells. Once `.mastery-*` classes are gone from the stylesheet
this line is harmless but dead. Remove it as part of CLEAN-01 to avoid confusion.

### CLEAN-01: CSS Classes (_grid.scss)

Lines 127–132 in `src/scss/_grid.scss`:
```scss
// Mastery grid colors (tiers 0-4: struggling → mastered)
.mastery-0 { background-color: var(--bg-mastery-0) !important; color: var(--color-mastery-0); }
.mastery-1 { background-color: var(--bg-mastery-1) !important; color: var(--color-mastery-1); }
.mastery-2 { /* neutral tier — no highlight, inherits default grid-cell styling */ }
.mastery-3 { background-color: var(--bg-mastery-3) !important; color: var(--color-mastery-3); }
.mastery-4 { background-color: var(--bg-mastery-4) !important; color: var(--color-mastery-4); }
```
Delete the comment line and all 5 class rules.

### CLEAN-01: CSS Vars (_variables.scss)

Present in all four theme blocks. Lines per theme:

| Theme | Lines | Vars |
|-------|-------|------|
| dark (`:root`) | 30–33 | `--bg-mastery-0/1/3/4`, `--color-mastery-0/1/3/4` |
| light | 61–64 | same 8 vars |
| oled | 92–95 | same 8 vars |
| high-contrast | 123–126 | same 8 vars |

Total: 32 var declarations across 4 themes.

### CLEAN-01: Consumers that block deletion

**`src/scss/_profile.scss` (lines 72–76)** — bar chart fill colors:
```scss
.m0 .bar-fill { background: var(--color-mastery-0); }
.m1 .bar-fill { background: var(--color-mastery-1); }
.m2 .bar-fill { background: var(--color-primary); }   // already migrated
.m3 .bar-fill { background: var(--color-mastery-3); }
.m4 .bar-fill { background: var(--color-mastery-4); }
```
`.m2` already uses `--color-primary` — no change needed there. Lines 72, 73, 75, 76 reference the
deleted vars. These 4 rules must be updated to a replacement token before deletion.

**`src/ts/wiki.ts` (lines 128–129, 131–132)** — inline styles in help text HTML:
```typescript
<li><strong style="color:var(--color-mastery-0)">Red</strong>
<li><strong style="color:var(--color-mastery-1)">Orange</strong>
<li><strong style="color:var(--color-mastery-3)">Green</strong>
<li><strong style="color:var(--color-mastery-4)">Bright green</strong>
```
The help text describes the old 5-tier discrete system. After OKLCH inline styles, the system is
continuous hue-based — the text is also conceptually stale. Both the colors and the labels need
updating.

**`tests/test_theme.py` (lines 19–23)** — var classification lists:
```python
BG_VARS = {..., "--bg-mastery-0", "--bg-mastery-1", "--bg-mastery-3", "--bg-mastery-4"}
FG_ACCENT_VARS = {..., "--color-mastery-0", "--color-mastery-1", "--color-mastery-3", "--color-mastery-4"}
```
These lists must have the mastery entries removed. The `test_all_vars_classified` test will fail if
vars are removed from the SCSS but remain in the Python lists (no such vars → parse returns nothing,
tests may pass vacuously). More critically: if vars remain in SCSS but are removed from the
classification lists, `test_all_vars_classified` will fail. Both edits must be atomic.

---

## Standard Stack

This phase has no library additions. The work is pure deletion and migration.

| Tool | Purpose |
|------|---------|
| `npm run check` | TypeScript typecheck + esbuild build (validates JS deletions) |
| `python -m pytest tests/test_theme.py` | Validates SCSS var deletions + classification |
| `npm run build:css` | Validates SCSS compiles after class/var deletions |

---

## Architecture Patterns

### Deletion Order

Safest order within a single atomic edit session:

1. **Migrate consumers first** — update `_profile.scss` bars and `wiki.ts` help text to replacement
   tokens (see Migration Decisions below)
2. **Remove SCSS vars** — delete 8 var declarations from each of 4 theme blocks in `_variables.scss`
3. **Remove SCSS classes** — delete `.mastery-0..4` rules from `_grid.scss`
4. **Remove JS dead code** — delete `type RGB`, `parseColor`, `lerpRGB`, `GRADIENT_*` from `ui.ts`
5. **Remove JS class-strip line** — delete `el.className.replace(...)` from `updateMasteryColors()`
6. **Update test lists** — remove mastery entries from `BG_VARS` and `FG_ACCENT_VARS` in `test_theme.py`
7. **Build and test** — `npm run check && npm run build:css && python -m pytest tests/`

### Migration Decisions for Consumers

**`_profile.scss` bar colors** — two options:

| Option | Approach | Verdict |
|--------|----------|---------|
| A | Hardcode the same hex values that existed in the vars | Simple, self-contained in profile, works across all themes |
| B | Add new dedicated `--color-bar-m*` vars to `_variables.scss` | More correct, but adds vars that CLEAN-01 is trying to reduce |

Option A is correct here. The profile bars are a fixed legend (m0=red, m1=orange, m3=green, m4=bright green)
not dependent on the OKLCH system. Use per-theme hardcoded values matching the existing var content:

```scss
// dark / oled
.m0 .bar-fill { background: #ef5350; }
.m1 .bar-fill { background: #e0a050; }
.m3 .bar-fill { background: #8cbf60; }
.m4 .bar-fill { background: #4cda6a; }

// light
.m0 .bar-fill { background: #c62828; }
.m1 .bar-fill { background: #b87020; }
.m3 .bar-fill { background: #558b2f; }
.m4 .bar-fill { background: #2e7d32; }

// high-contrast
.m0 .bar-fill { background: #ff6b6b; }
.m1 .bar-fill { background: #ffaa00; }
.m3 .bar-fill { background: #00ff00; }
.m4 .bar-fill { background: #00ff66; }
```

Wait — `_profile.scss` does not currently have `[data-theme]` scoping. The existing rules at lines
72–76 apply globally, meaning they rely on CSS cascade from `_variables.scss`. To properly scope bar
colors per theme without re-introducing global vars, add `[data-theme]` overrides to `_profile.scss`
for the three non-dark themes, or use existing theme-scoped rules if the file already has them.

Check whether `_profile.scss` has any existing `[data-theme]` selectors.

**`wiki.ts` help text** — the existing text names discrete tiers that no longer map to the OKLCH
system. The text should describe the continuous hue system: red (low score) → blue (neutral) →
green (high score). Strip the `var(--color-mastery-*)` inline styles and use hardcoded semantic
colors or update the description to match the new system.

### Anti-Patterns to Avoid

- **Partial deletion across files**: Deleting vars from SCSS before migrating `_profile.scss` will
  cause profile bars to silently lose color. Always migrate consumers first.
- **Leaving `type RGB` behind**: It exists solely for `parseColor`/`lerpRGB`. Deleting the functions
  without the type alias leaves a TS lint warning for unused type.
- **Removing mastery entries from test lists before removing from SCSS**: `test_all_vars_classified`
  will fail because the vars are still present but unclassified. Edit SCSS and test lists together.
- **Updating test lists without running tests**: The `test_all_themes_cover_same_variables` test
  ensures all four theme blocks define the same set. If one theme block still has the mastery vars
  after partial deletion, this test catches it.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Verifying no mastery var references remain | Custom grep script | `grep -r -- '--bg-mastery\|--color-mastery' src/` as a verification step |
| Verifying no mastery class references remain | Custom script | `grep -r 'mastery-[0-4]' src/` as a verification step |

---

## Common Pitfalls

### Pitfall 1: Silent profile bar color loss
**What goes wrong:** `_profile.scss` `.m0/.m1/.m3/.m4` bars lose background color; bars render
as the default (likely white/transparent).
**Why it happens:** `--color-mastery-*` vars are removed from `_variables.scss` but `_profile.scss`
still references them.
**How to avoid:** Migrate `_profile.scss` bar rules to hardcoded values before deleting vars.
**Warning signs:** Profile section shows all bars in same neutral color.

### Pitfall 2: Test suite failure from unclassified vars
**What goes wrong:** `test_all_vars_classified` in `test_theme.py` fails because the mastery vars
remain in SCSS (oops, missed a theme block) but were removed from Python classification lists.
**Why it happens:** All four theme blocks must have vars removed together; easy to miss one.
**How to avoid:** After SCSS edits, run `python -m pytest tests/test_theme.py::TestThemeCompleteness`
immediately to catch mismatches.

### Pitfall 3: Stale wiki.ts color descriptions
**What goes wrong:** Help text still says "Orange" and "Bright green" tiers with hardcoded inline
styles that reference deleted vars — the vars render as empty string, so styled text loses color.
**Why it happens:** `wiki.ts` is a TS string template, not compiled SCSS — easy to overlook.
**How to avoid:** Grep for `--color-mastery` across `src/ts/` before declaring CLEAN-01 done.

### Pitfall 4: `type RGB` orphan
**What goes wrong:** TypeScript compiler emits no error (unused type aliases are not errors by
default in most tsconfig setups), so the alias persists invisibly.
**How to avoid:** Delete `type RGB` at line 577 as part of the same edit that removes the functions.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (Python) + tsc + esbuild |
| Config file | `pytest.ini` or none (run from `tests/`) |
| Quick run command | `python -m pytest tests/test_theme.py -x` |
| Full suite command | `python -m pytest tests/ && npm run check` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLEAN-01 | `--bg-mastery-*` vars absent from `_variables.scss` | unit | `python -m pytest tests/test_theme.py::TestThemeCompleteness::test_all_vars_classified -x` | ✅ (will pass once vars removed from both SCSS and Python lists) |
| CLEAN-01 | All four themes define the same var set | unit | `python -m pytest tests/test_theme.py::TestThemeCompleteness::test_all_themes_cover_same_variables -x` | ✅ |
| CLEAN-01 | `.mastery-*` classes absent from compiled CSS | smoke | `npm run build:css && grep -c 'mastery-[0-4]' static/css/app.css; test $? -eq 1` | built by CI |
| CLEAN-02 | `lerpRGB`, `parseColor`, `GRADIENT_*` absent from TS | unit | `npm run check` (tsc --noEmit) | ✅ (typecheck passes only if deletions are clean) |
| CLEAN-02 | No runtime references in built bundle | smoke | `npm run build && grep -c 'lerpRGB\|parseColor\|GRADIENT_' static/js/app.js; test $? -eq 1` | built by CI |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_theme.py -x && npm run check`
- **Per wave merge:** `python -m pytest tests/ && npm run check && npm run build:css`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
None — existing test infrastructure covers all phase requirements. The test_theme.py completeness
tests already enforce var classification and cross-theme parity.

---

## Open Questions

1. **Does `_profile.scss` have existing `[data-theme]` overrides?**
   - What we know: Lines 72–76 use `--color-mastery-*` globally with no theme scoping visible in
     the read window.
   - What's unclear: Whether earlier in the file there are `[data-theme]` scoped blocks that would
     need per-theme hardcoded bar colors, or whether the bars are intentionally single-color across
     themes.
   - Recommendation: Read `_profile.scss` from top before writing migration. If no theme scoping
     exists, replace the 4 global rules with the dark theme hardcoded values (since dark is default)
     and add `[data-theme="light"]`, `[data-theme="high-contrast"]` overrides for the other
     per-theme hex values.

2. **Should `wiki.ts` mastery help text be updated or simply de-colored?**
   - What we know: The text describes a 5-tier discrete system that no longer exists. The colors
     referenced (`--color-mastery-*`) will be deleted.
   - What's unclear: Whether updating the description to match the OKLCH continuous system is in
     scope for Phase 3 or a separate docs task.
   - Recommendation: Minimum viable: strip the `style="color:var(...)"` inline styles and keep
     text descriptions. Optional but cleaner: rewrite the list to say "red (struggling) → blue
     (neutral) → green (mastered)" to match the OKLCH system. Treat as in scope since the vars
     will break otherwise.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase read — `src/ts/ui.ts` lines 577–642 (exact dead code block + updateMasteryColors)
- Direct codebase read — `src/scss/_variables.scss` full file (all 4 theme blocks, exact line ranges)
- Direct codebase read — `src/scss/_grid.scss` lines 127–132 (mastery class rules)
- Direct codebase read — `src/scss/_profile.scss` lines 72–76 (consumer dependency)
- Direct codebase read — `src/ts/wiki.ts` lines 128–132 (consumer dependency)
- Direct codebase read — `tests/test_theme.py` full file (classification lists, test structure)
- `.planning/STATE.md` — known constraint documented: `_profile.scss` uses `--color-mastery-*`

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY.md` — phase 3 delivery summary confirms `el.className.replace` line
  must also be removed

---

## Metadata

**Confidence breakdown:**
- Audit completeness: HIGH — full grep across all source files, exact line numbers confirmed
- Migration plan: HIGH — consumers identified, values preserved from existing vars
- Test impact: HIGH — test_theme.py read in full, classification change understood

**Research date:** 2026-03-25
**Valid until:** Until next significant refactor of `_variables.scss` or `_profile.scss`
