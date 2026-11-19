# Example · craft-sync

An invented journaling app, "Fieldnote", already has `packages/ui/`: 22 tokens, Button, Input, Badge and a `guidelines.md`.

## Import: "Bring our design system into the design tool."

```
Design system found: packages/ui (React)
Tokens · 22 · colour 12 (sand-200*, sand-400* named by value: names kept, roles → open questions) · type 4 · spacing 4 · radius 2
Components · Button (primary · secondary · ghost × sm · md, loading) · Input (default · error · disabled) · Badge (neutral · success · warn)
Guidelines · 5 rules → legend text
Gaps · no hover/pressed/focus anywhere · loading looks like normal · hard-coded badge colours
Which components should I draw now?
```

After "Draw Button and Badge":
- a guide with the code's tokens under the same names;
- foundations, with the guidelines as the legend text;
- an index (Button, Badge drawn; Input in code only);
- Button's missing states drawn and labelled **Proposed**;
- a warn badge flagged at ≈3.1:1;
- `DESIGN.md`: "Design system source: code at packages/ui; the guide mirrors it", plus the import logged with its commit.

## Export: "Apply the guide changes to the code."

```
Sync guide → code (base: commit 4d4dee4)
Guide changed   --color-accent  #2e6b57 → #3d7f69  packages/ui/tokens.css:8  → Button primary, Home "New entry" (contrast 6.0 → 4.5:1)
Both changed    --radius-md     synced 10 · guide 8 · code 12 (7a3b5b5 "Rounder cards"): which wins?
Nothing has been edited.
```

"Apply the accent; the code wins for the radius" → the edit to the one line in code, the guide set to 12px, the sync logged, and "no lint, typecheck or test scripts to run" stated.
