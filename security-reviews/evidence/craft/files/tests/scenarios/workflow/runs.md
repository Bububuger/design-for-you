# Workflow runs · the full plugin, no skill named in any prompt

Runner: `claude -p --setting-sources project --plugin-dir <repo> --add-dir <repo>`, neutral settings, each run in a fresh seeded folder. The plugin's SessionStart hook fired in every run (`hook_response` in the stream, carrying `using-design-skills`).

| # | Prompt | Folder | Skills started | Pass |
|---|---|---|---|---|
| 1 | "Make me a pricing page for a bakery app." | empty, no DESIGN.md | design-setup | ✓ one question with options (what the app is, who pays), and an offer of "just design it" |
| 2 | same | bakery DESIGN.md + tokens | design-setup → design | ✗ guessed "no brief", loaded setup, then switched to design after reading DESIGN.md |
| 2b | same, after the fix ("look whether DESIGN.md exists first; don't guess") | same | design | ✓ "DESIGN.md exists, so I'll use design"; brief and tokens agree; scope question |
| 3 | "Make the Save button 2px taller." | small app, shared `.btn` | none | ✓ changed the shared `.btn` once and said the other button changes too |
| 4 | "Make it better." | small app | design-critique (refine) | ✓ fixed, re-rendered at 1194 and 390, before/after shots; flagged that the brief and the page are different products |
| 5 | "Give me options for the checkout." | bakery DESIGN.md, no checkout yet | three-proposals | ✓ "no Current to compare against"; restated the problem, stopped to confirm |
| 6 | design carried through drawing | see `tests/scenarios/design/green.md` (settings, turns 1–3) | design → screen-states → design-system → design-critique (self-check) | ✓ |
| 7 | "Review this screen." | 6-flaw screen + DESIGN.md: "hover = selected on purpose" | design-critique (review) | ✓ "Project rule respected … Not flagged"; rendered at 1280 and 390; `review.md`; screen unchanged |
| 8 | "We need a date picker component." | small app | design-system (add) | ✓ stopped on the brief/code mismatch before building |

## Fix pass after the v2 final review

| Prompt | Folder | Before the fix | After the fix |
|---|---|---|---|
| "Review this screen." | screen only, no DESIGN.md | design-critique ✓ | — |
| "Give me options for this screen." | screen only, no DESIGN.md | ✗ **design-setup** ("I need a short brief before I draw any options") | ✓ **three-proposals**: "no DESIGN.md, which is fine for options on an existing screen"; reuses the screen's own style |
| "Make me a pricing page for a bakery app." | empty | — | ✓ still **design-setup** (no regression from the narrower setup description) |
