# using-design-skills · RED (the plugin with the four v1 skills, the hook and an empty entry skill)

Runner: `--plugin-dir ~/www/design-skills`, neutral settings. Seeded workspace: a small yoga-studio class list (`index.html`, `tokens.css`) and no `DESIGN.md`.

| Prompt | Skill started | Notes |
|---|---|---|
| "Make me a pricing page." | `screen-states` | Wrote the state list and stopped (good), but **no brief**: it read the style off one page, and `design-setup`/`design` didn't exist yet |
| "Make the Save button 2px taller." | none | A direct edit, but only on that one button while the style is shared; it offered the shared change afterwards |
| "Make it better." | `design-critique` | Refined directly (refine mode) |
| "We need a date picker component." | `design-system` | Built the component with a states table and new tokens |

The descriptions already route the v1 cases well. What's missing is a brief before the first design, and a single front door for "make me a page". The `design-setup` and `design` routes are checked with the full plugin in `tests/scenarios/workflow/`.

Harness note: reading the plugin's `references/` files was denied, because the plugin folder sits outside the run folder. Later runs add `--add-dir` for it. Installed plugins live where Claude Code can read them.
