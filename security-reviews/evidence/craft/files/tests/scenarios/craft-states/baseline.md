# screen-states · RED baseline (no skill)

Runner: `claude -p --setting-sources project --permission-mode acceptEdits` in an empty folder (no project instructions, hooks or plugins).

## Scenario 1

> Design the orders screen for a small bakery's web app. Owners see today's orders and mark them ready. Work in this folder; produce plain HTML/CSS files.

**What it did:** it drew everything in one pass (`index.html`, `states.html`, `styles.css`). It covered loading, no orders, all caught up, couldn't load, offline, an empty section, and every state of an order card (saving, save failed, late, due soon, undo).

**Violations against the pass criteria**
- No written state list and no stop before drawing.
- Missed: many/overflow (scrolling), very long names and text, someone else already did it, changed while viewing, roles and permissions, slow.
- All the extra states sit unnamed on one `states.html`, with no board naming or order.
- It couldn't render (no permission) and said so. Good.

## Scenario 2 (negative trigger)

> In orders.html, make the 'Mark ready' button 2px taller.

**What it did:** changed `height:36px` to `38px` and nothing else. This is the expected behaviour, and it must stay this way with the skill installed.
