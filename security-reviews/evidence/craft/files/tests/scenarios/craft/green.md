# design · GREEN (the full plugin via --plugin-dir; prompts unchanged)

| Prompt | Turn | Skills started | Result |
|---|---|---|---|
| "Design the pricing page." | 1 (first run) | design → screen-states → three-proposals → design-system → design-critique | Ran the whole chain, but **decided every stop itself**: "this session couldn't stop for your answers, so I made all three calls" ✗ |
| — refactor: added "Stops are real" + two rationalisation rows to `design`, one red flag to `using-design-skills` | | | |
| "Design the pricing page." | 1 (rerun) | design | Stated its reading (price list, not plans), asked the scope questions, **built nothing** ✓ |
| "Design the onboarding: welcome, sign-up, verify phone." | 1 | design → screen-states | A scope table (job and next action per page) and the states per page, then **stopped** ✓ |
| "Design the settings page." (stale brief) | 1 | design → screen-states | "I'll use the token, because that's what ships, and add the mismatch to Open questions" ✓; states list, stopped ✓ |
| — | 2: states approved, draw 2 boards | design-system (add) | The system lacked settings pieces: proposed section/row, field, switch, text button with full states and a component index, listed the screens affected, **stopped** ✓ |
| — | 3: "Pieces approved. Go ahead." | design-critique (self-check) | Drew `1.1-settings-default` and `1.1-settings-empty-first-time`, rendered them; **self-check fixed 4 things before showing** (placeholder contrast, switch outline, row height, reduced motion); the closing summary in the skill's shape; **7 dated lines appended to DESIGN.md › Decisions log**; the teal/blue conflict and a border-contrast finding in Open questions ✓ |
