# design-critique · GREEN (skill installed in the workspace, unchanged prompts)

| Scenario | Triggered | Result |
|---|---|---|
| 1 · review | yes | Tried to render; the sandbox blocked the browser, which it **said at the top**, marking findings "⚠ render". Ranked by impact (blocks / slows / careless). **Found all 6 seeded flaws:** the loading button **changes width** (layout shift named as such), three primaries, hover = selected, badge contrast 2.2:1, the oversized empty box, and a **one-word last line** in the headline. Plus ragged badge alignment. Shared-component note on the badge. **No file changed** (diff empty) ✓ |
| 2 · guide says hover = selected on purpose | yes | "Difference from the defaults, noted rather than flagged" ✓. Same ranked report, no file changed ✓ |
| 3 · refine | yes | Fixed only the findings (one primary, loading keeps its width, contrast, softer hover, aligned badges, sized empty box, balanced headline, keyboard-only focus). Listed what it **didn't** do as out of scope, flagged the shared components for the design-system process, and was honest that it couldn't re-render ✓ |
| 4 · negative: "Fix the typo 'recieve'" | no | Fixed the typo and mentioned one serious issue in a sentence without fixing it ✓ |

## Note on rendering

The test runner (`--permission-mode acceptEdits`) blocks headless Chrome, so no run could render. Every run reported that limit and marked what it couldn't verify, which is the behaviour the skill asks for. Rendering through the Paper adapter is exercised in the Paper pass.

## Refactor

No criterion failed or was dodged, so the skill is unchanged.

## Paper pass

Same skill, in a fresh workspace with only the Paper MCP server (`--mcp-config … --strict-mcp-config`), working in a new scratch Paper file and never in an existing one.
It rendered the default board at its 1194px width with get_screenshot, read exact values with get_computed_styles, and used the page's cover note as the project's rules. Ranked findings, led by "'Due soon' is louder than 'late'" and an allergy note styled like small print. It changed nothing. This is the run where rendering worked, and it found issues only visible rendered. Cost about US$0.5.

## v2 amendments (old wording vs new, same prompts, browser allowed)
- **Review, old wording, browser allowed:** rendered at 1280 and 390, ranked 10 findings including all 6 planted ones, changed nothing ✓ (the example in `examples/design-critique.md` is from this run)
- **Refine, old wording:** fixed, but **"I couldn't render either file"** and no re-check; it also added a new state-sheet file ✗
- **Refine, new wording (self-check/refine render-again step):** fixed only the findings, no new files ✓. Rendering was still blocked: its commands chained `cd … &&` and wrote to `/tmp`, which the runner's permission pattern doesn't match. Fix in the HTML adapters: render with one plain command, writing the image inside the working folder. The render step itself is proven by the review run above.
- **Review, new wording:** report in `review.md`, `screen.html` unchanged ✓
