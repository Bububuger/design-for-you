# design-system · RED baseline (no skill)

Runner: `claude -p --setting-sources project --permission-mode acceptEdits` in a folder with only the seed files.

## Scenario 1 · create

> Start a style guide for a dental clinic booking app. Work in this folder; produce plain HTML/CSS files.

**What it did:** in one pass, tokens (role names over a teal/coral palette), components and a guide page with about 10 components (buttons, fields, badges, alerts, cards, booking pieces).

**Violations against the pass criteria**
- No stop after the foundations: the whole guide in one go.
- Interaction states not defined once as a rule; buttons list "disabled" but there is no states matrix.
- No component index.

## Scenario 2 · audit (seeded: 4 loose hex colours, 2 near-duplicate greys, a button missing focus and disabled, a padding that drifts)

> Audit this style guide (guide.html, guide.css) and the appointments screen.

**What it did:** good findings (all four seeded classes, plus contrast). Then it **rewrote guide.css, guide.html and appointments.html without asking**, saving the originals to `original/`.

**Violation:** changed files during an audit. The person never chose which fixes to apply.

## Scenario 3 · existing guide conflict (seeded: hover fills the background with the brand tint)

> Add a dropdown component to our guide (see guide.md and guide.css).

**What it did:** followed the seeded hover rule ✓. Described the states in prose with no matrix.

## Scenario 4 · negative trigger

> What hex is our primary colour in guide.css?

**What it did:** answered and changed nothing ✓ (an earlier run had a missing seed and was rerun.)
