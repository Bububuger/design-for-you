# Example · design

**Prompt:** "Design the settings page." An invented bakery app with a `DESIGN.md` whose brand says "deep teal", while `tokens.css` ships a blue primary.

## Turn 1: brief, conflict, scope, states, stop

> One conflict before I start: DESIGN.md says the accent is deep teal, but tokens.css has a blue primary. I'll use the token, because that's what ships, and add the mismatch to Open questions.
>
> **1 · Settings** (customer phone app, 390px): profile, pickup, notifications, account. One next action: Save changes, a bar that appears after the first edit.
> **Screen states for your approval:** default (long name, long email) · empty first time · very long text (sheet) · missing optional fields · saving / couldn't save · offline · signed out · … · doesn't apply: filtered, many items (no lists).

## Turn 2: "Approved, draw default and empty first time"

The system had no field, switch or settings row, so it went to `craft-system` (add mode) first. It proposed those pieces with full states and a component index, listed the screens they affect, and stopped.

## Turn 3: "Pieces approved"

```
Made: 1.1-settings-default.html, 1.1-settings-empty-first-time.html, index.html (+ guide.html, tokens.css)
Decisions: edited in place, saved together with one Save bar · empty fields show a reason instead of "Not set" ·
           the blue primary stays for now (also in DESIGN.md › Decisions log)
System changes: section & row, field, switch, text button (+ danger) and their tokens — affects: Settings only
Self-check fixed: placeholder contrast (→ ≈4.6:1), a faint switch outline, an oversized row, reduced motion
Open questions: field borders ≈1.3:1 (darken for fields only, or everywhere?) · teal or blue? · pay in app or at the counter?
```

`DESIGN.md` gained seven dated decision lines and the open questions above.
