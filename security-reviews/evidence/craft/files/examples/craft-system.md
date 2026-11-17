# Example · craft-system

## Create: "Start a style guide for a dental clinic booking app."

**Turn 1** produced two pages and stopped:

- `1-foundations.html`:
  - role-named tokens over a raw palette (`--color-text-muted`, `--color-border-hover`, `--color-danger-bg`);
  - type sizes named by use (`caption` to `display`), a 4px spacing scale, radius, two shadows (floating things only);
  - layout widths, motion durations, and "how we write".
- `2-interaction-rules.html`: the states rules, once:
  - **bordered** pieces darken only the border on hover;
  - **borderless** pieces get a translucent tint;
  - **primary** has its own ladder.

  Selected is stronger than hover and never bolds the text; focus shows only from the keyboard; loading keeps the size.

> "I haven't built any components yet … Do the teal, the 15px body text and the tone work? Is there an existing brand colour?"

**Turn 2** ("Foundations approved, continue with the button") added `3-button.html`:

| Variant | Normal | Hover | Pressed | Focus | Disabled | Loading | Selected |
|---|---|---|---|---|---|---|---|
| Primary · Secondary · Text · Danger · 48px | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (same width) | n/a, a button is an action, not a choice |

It also added a Button row to the component index.

## Audit: "Audit this style guide and the appointments screen."

A ranked report and **no file changed**:

```
High    "Confirmed" green 3.3:1 on white, hard-coded, no status tokens → add success/danger roles
        Button has no focus/disabled/loading → add them + draw the states matrix
        Pressed colour hard-coded → --color-primary-pressed
Medium  Card padding 22px on the screen vs 16px in the guide → spacing scale, or a named variant
        4 near-duplicates (#f3f3f6 vs --color-fill #f2f2f5, …) → use the token
        Radius 10 vs 12 → a radius scale
Low     No type, spacing, shadow or motion tokens; fonts written inline
Nothing has been changed. Tell me which fixes to apply.
```
