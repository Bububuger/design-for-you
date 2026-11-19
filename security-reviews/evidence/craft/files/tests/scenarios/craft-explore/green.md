# three-proposals · GREEN (skill installed in the workspace, unchanged prompts)

| Scenario | Triggered | Result |
|---|---|---|
| 1 · turn 1: "I don't like this settings page, give me options" | yes | Restated the problem (4 points plus what a good result must do), proposed directions on 3 different axes (save model / structure / removal, C marked bolder), **stopped to confirm the problem** because the request was vague ✓ |
| 1 · turn 2: "Yes, that's the problem. Go ahead." | (same session) | **Recommendation first** (A, with the reason). Board in `explorations/settings/`: legend, **current.html**, A/B/C with the same data, and `states.html` for the states each option's difference affects. Shared fixes stated once. `settings.html` untouched (diff empty) ✓ |
| 1 · turn 3: "None of these work, the problem is it's too dense." | (same session) | Rethought from the new problem with density as the axis: spacious / essentials first with folded groups / move settings to where they apply (bolder). Didn't tweak round 1. Recommendation first, round-1 boards replaced ✓ |
| 2 · "Give me 5 directions for the empty state…" | yes | Exactly 5, each with its axis named, a bolder E, recommendation first, each option also shown right after its main action; "no current version" stated because there was no existing design ✓ |
| 3 · negative: "Change the settings page title to 'Preferences'." | no | Changed the title and heading only ✓ |

## Refactor

No criterion failed or was dodged, so the skill is unchanged.

## Paper pass

Same skill, in a fresh workspace with only the Paper MCP server (`--mcp-config … --strict-mcp-config`), working in a new scratch Paper file and never in an existing one.
Prompt: "The main Orders screen on the page 'Orders' is too dense for a tablet on a bakery counter. Give me options." The problem was named, so there was no confirm stop. It made a new page "Orders · options": legend, **Current** (a copy cut to the tablet size), A · glance list (density) with A2, **B · Make | Hand over (structure, recommended)**, C · next up (interaction, bolder) with C2. It read exact values with get_jsx, screenshotted 12 times, and never touched the Orders page. Cost about US$3.2.

## v2 amendments (old wording vs new, same prompts, browser allowed)
"Design both: a sidebar version and a tabs version of these settings."
- **Old wording:** already correct: two options plus a recommendation, no invented third. The amendment only aligns the wording with the axis rule.
- **New wording:** the same: A sidebar / B tabs, recommendation first (B), shared fixes stated once, open questions ✓
