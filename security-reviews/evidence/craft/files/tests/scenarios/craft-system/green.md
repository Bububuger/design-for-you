# design-system · GREEN (skill installed in the workspace, unchanged prompts)

| Scenario | Triggered | Result |
|---|---|---|
| 1 · create, turn 1 | yes | Foundations (role-named tokens over a raw palette, type, spacing, radius, two shadows, layout, motion, voice) and a separate interaction-rules page. **Stopped before components** with 2 questions ✓ |
| 1 · create, turn 2: "Foundations approved, continue with the button. Patient flow only for now." | (same session) | `3-button.html`: legend with rules and why, sizes, real-content examples, a **states matrix** of every variant × normal/hover/pressed/focus/disabled/loading, with "selected: n/a, a button is an action". Loading keeps its width. **Component index row added** ✓ |
| 2 · audit (seeded flaws) | yes | Ranked High/Medium/Low report covering all four seeded classes plus contrast, each with location, why and fix. **No file changed:** `diff` against the seeds is empty ✓ |
| 3 · existing guide conflict | yes | Followed the guide's "hover fills with brand tint", said so, and made selected different from hover without changing weight. Full states matrix; the draft waits for approval before the index row ✓ |
| 4 · negative trigger | no | Answered `#2563eb`, changed nothing ✓ |

## Refactor

No criterion failed or was dodged, so the skill is unchanged.

## Paper pass

Same skill, in a fresh workspace with only the Paper MCP server (`--mcp-config … --strict-mcp-config`), working in a new scratch Paper file and never in an existing one.
It made a "Clinic guide" page with three boards (colour roles; type and scales; interaction rules with a 3-family × 7-state matrix drawn with real pieces, plus "How we write"), and **stopped before components**. It asked before registering file-wide tokens, which the adapter didn't cover. Fix: the Paper adapter now says to register tokens with create_tokens/set_tokens as part of the foundations approval. Cost about US$2.1.

## v2 amendments (old wording vs new, same prompts, browser allowed)
Seeded guide: "cards carry a soft shadow on purpose; two primaries on the booking screen on purpose". Prompt: "Audit this guide and the booking screen."
- **Old wording:** "Your guide asks for two things the skill's fixed rules forbid: shadows on cards and two primary buttons" → reported as breaking a fixed rule ✗
- **New wording:** "Your guide differs from my defaults here on purpose, so I haven't counted these as problems" ✓. No file changed (diff empty) ✓
