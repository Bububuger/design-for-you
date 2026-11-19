# screen-states · GREEN (skill installed in the workspace, unchanged prompts)

The skill was copied to `<workspace>/.claude/skills/screen-states/`. The prompts don't mention it, so the description had to trigger it.

## Scenario 1, turn 1

**Triggered:** yes (the Skill tool loaded `screen-states`).

**What it did:**
- Wrote `STATES.md` with 15 states, including 60 orders, long names and a 9-item order, someone else already marked it ready, new orders while looking, changed by the customer, and slow saving.
- Listed what doesn't apply, with reasons, and asked 5 open questions.
- **Stopped before drawing.** ✓

## Scenario 1, turn 2

> The list looks right, go ahead. Owner and staff both use it; staff don't see totals. Statuses as you assumed. Marking ready notifies the customer. Tablet on the counter mainly. Show paid or not.

**What it did:**
- 11 full boards and 2 state sheets, named `3.1-orders-<state>.html`, plus an `index.html` in canvas order with decisions and open questions.
- Shared tokens and one standard empty/error panel.
- The answers became design decisions: the text to the customer waits for the 8-second Undo window to end; the staff view keeps the money column's width; a double mark sends only one text.

**Pass criteria:**
- State list and stop ✓
- Main, empty, loading, couldn't load, many/overflow and long names drawn ✓
- Every error or empty state has an action ✓
- Naming scheme ✓
- Render check: blocked by the runner's permissions, and the agent said so plainly ✓ (honest reporting, as the skill requires)

## Scenario 2 (negative trigger)

**Triggered:** no. It changed the height from 36 to 38 px and nothing else ✓

## Refactor

No criterion failed or was dodged, so the skill is unchanged.

## Cost note

Turn 2 cost about US$3 (13 boards). Expect a full state pass to be the most expensive skill to run.

## Paper pass

Same skill, in a fresh workspace with only the Paper MCP server (`--mcp-config … --strict-mcp-config`), working in a new scratch Paper file and never in an existing one.
Turn 1 loaded the Paper guide and file info, wrote the state list and design brief, and **stopped before creating anything**. Turn 2 ("draw only main, empty first time, many/overflow and couldn't load") made an Orders page with a cover note and 4 boards named `3.1 · Orders · <state>`: 16 write_html, 9 screenshots after sections, duplicate_nodes for state variants, finish_working_on_nodes. Every adapter verb mapped cleanly. Cost about US$2.2.
