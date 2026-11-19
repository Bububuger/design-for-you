# design-critique · RED baseline (no skill)

Seeded screen with 6 flaws: a loading button that grows wider, hover as strong as selected, a headline whose last line is one word, two (three) primary buttons, a grey badge on a grey card (low contrast), and an oversized empty card.

## Scenario 1 · review

> Review this screen (screen.html).

**What it did:** found contrast, hover = selected, the loading button ("broken", extra text), three primaries, and the oversized empty box. **Wrote `screen-revised.html` with its own redesign** (a new title, outlines, a blue bar, a centred layout) in the same turn.

**Violations against the pass criteria**
- Never rendered the screen (judged from the source).
- Missed the class "layout shift" (it called the button broken, not width-changing) and the one-word last line.
- Built a fixed version before the person chose fixes.

## Scenario 2 · project guide says hover = selected on purpose

**What it did:** respected the guide and didn't flag hover ✓. Again produced a revised copy unasked.

## Scenario 3 · refine

> Refine this screen (screen.html).

**What it did:** rewrote the file in place and **expanded scope**: a new header structure, sections, a 720px max width, a phone layout, CSS split into `styles.css`. **No re-render or re-check** after the changes.

## Scenario 4 · negative trigger

> Fix the typo 'recieve' on this screen.

**What it did:** fixed the typo, mentioned two problems without fixing them ✓
