# design-system-sync · GREEN (the full plugin, prompts unchanged)

| Prompt | Turn | Result |
|---|---|---|
| (b) "Bring our design system into the design tool." | 1 | Triggered from its description. **Inventory, then a stop:** 22 tokens by role (two value-named ones kept, roles as open questions), 3 components with variants and paths, guidelines as legend text, gaps (no hover/focus anywhere, loading looks normal, hard-coded badge colours, a low-contrast warn badge). **"Which components should I draw?"** No files written ✓ |
| | 2: "Draw Button and Badge." | `guide/tokens.css` = the code's tokens under **the same names**; foundations with the guidelines as legend; **component index: Button and Badge drawn, Input in code only**; Button's missing states drawn on a hatched background marked **"Proposed"**; all pages rendered and layout fixed; badge contrast measured (warn ≈3.1:1, success ≈4.2:1, flagged); DESIGN.md records the source and the import ✓ |
| (c) "Apply the guide changes to the code." | 1 | Triggered. Three-way diff with the base commit from DESIGN.md: accent = guide changed (affects Button primary → Home "New entry", contrast 6.0 → 4.5:1); radius = **both changed, asked which wins**; code-only changes: none. **Nothing edited**; stated up front that the repo has no checks ✓ |
| | 2: "Apply the accent. For the radius, the code wins (12px)." | Edited only the accent line in `packages/ui/tokens.css`, set the guide's radius to 12px, logged the sync, said there were no checks to run, and noted that the base commit must be updated once the change is committed ✓ |

## Wired into setup, design and routing (the full plugin)

| Prompt | Turn | Result |
|---|---|---|
| (a) "Design the settings page." (UI package, no DESIGN.md) | 1 | design-setup: "A design system already exists in code in `packages/ui`: 22 tokens, 3 components, 5 guidelines. I won't ask about colours, fonts or button rules" ✓ |
| | 2: "Skip the questions." (first run) | ✗ Wrote the brief and went straight to design → screen-states, **without offering the import**. Cause: the skip paragraph only kept the foundations step "if the project has no tokens" |
| — refactor: skip waives the interview and the brief's approval, **never step 6**; with a system in code it still asks the one import question | | |
| | 2 (rerun) | Minimal brief with assumptions; then "There's one question I need answered before drawing anything, because skipping the interview doesn't skip it: should I first import the design system?" ✓ |
| | 3: "Yes, import it. Draw Button and Input." | design-system-sync (import) → design → screen-states: the settings page planned from the imported Button and Input, stopped at the states list ✓ |
| On-demand: "Design the sign-in page." (guide exists; Input "in code only") | 1 | design → screen-states list, stop ✓ |
| | 2: "States approved. Draw only the default and error boards." | **design-system-sync imported just Input first** (values read from `Input.tsx`, focus noted as missing in code), the index row flipped to "drawn", then boards drawn, self-check ran, decisions logged ✓ |

Regressions: "pricing page" with an empty folder → design-setup ✓; with a bakery DESIGN.md → design ✓; "2px taller" → a direct edit of the shared `.btn` ✓.

## Paper pass

Fieldnote repo, new scratch Paper file, the full plugin plus only the Paper MCP. Prompt: "Bring our design system into Paper, in the file 'design-skills sync test' … on a page you create named 'Guide'."
- **Turn 1:** inventory in the reference format, then "you need to choose which components to draw first". Nothing drawn ✓
- **Turn 2:** "Draw Button and Badge."
  - `get_tokens` → `create_tokens`: **all 22 tokens registered under the code's names and values** (verified with `get_tokens` afterwards: an exact match, `--sand-200` and `--sand-400` included);
  - five boards (Foundations · Colour, Foundations · Type & scales, Component index, Button, Badge) built with `write_html`, 8 screenshots, `finish_working_on_nodes`;
  - missing states dashed and labelled "proposed";
  - Input "in code only";
  - DESIGN.md records the source;
  - stated that the components weren't compared with the real ones (no Storybook) and that the folder isn't a git repo, so a later export has no base commit ✓
- Cost about US$2.2.

## Fix pass after the v3 review: `design-sync.json` replaces the git-commit base

The reviewer replayed the old rules on the recorded runs: a one-component import moved the commit base and turned a both-changed radius into a "clean" guide change; there was no base after an export or without git. The base is now `design-sync.json` (the values both sides agreed on).

**End-to-end chain, no git, a single session:**

| Turn | Prompt / action | Result |
|---|---|---|
| 1 | "Bring our design system into the design tool." | Inventory, then a stop ✓ |
| 2 | "Draw Button and Badge." | Guide built; **`design-sync.json` written**: 22 agreed token values, Button/Badge drawn, Input in code only ✓ |
| — | (by hand) guide: accent → #3d7f69, radius → 8px; code: radius → 12px | |
| 3 | "Import Input into the guide." | Drew Input (states from code, focus "proposed"), status → drawn; **agreed token values unchanged** (diff empty) ✓ |
| 4 | "Apply the guide changes to the code." | "last agreed: design-sync.json": accent = guide changed (contrast 6.0 → 4.5:1); **radius = both changed, asked which wins**; components match; "proposed" states not exported; no checks exist (said); **nothing edited** (code still #2e6b57 / 12px) ✓ |

**Trigger narrowing (#9), in a repo with a UI package:** "Review this screen" → design-critique only ✓; "Make the primary button 2px taller" → a direct edit in `Button.tsx`, no sync ✓.

**Still not run (text only):** design-system's propagation → export; setup's offer after the full interview; a bare "yes" (inventory inside the hand-off); a "no" to the offer; the Paper export read; two UI packages.
