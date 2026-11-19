# Example · craft-states

*(Trimmed: the full list also covered the interaction states and every catalogue item.)*

**Prompt:** "Design the orders screen for a small bakery's web app. Owners see today's orders and mark them ready."

## Turn 1: the list, then a stop

The agent read the folder (no design system yet), then wrote `STATES.md` instead of drawing:

```
Data      default (18 orders, mixed statuses, long names, a 9-item order, a long allergy note)
          empty · first time ("No orders yet" + Copy order link)
          empty · filtered ("Nothing matches 'croissant'" + Clear search)
          one order · 60 orders (sticky header, grouped by pickup hour)
          missing fields (no phone, no note)
System    first load (skeleton in the final layout) · refresh ("Updating…")
          couldn't load (+ Try again) · offline (keep the list, queue "Waiting to send")
          slow save ("Still saving…" after 2 s) · one row failed (inline Try again)
          someone else did it ("Ana already marked this ready at 9:12")
          changed while viewing ("2 new orders" pill; "Changed 10:42" flag)
Activity  just marked ready (toast with Undo · 8s)
People    signed out (sign in again, keep your place)
Doesn't apply: multi-step progress (marking ready is one action) · paused vs failed (nothing pauses)
Questions: owner only, or staff too? Does marking ready notify the customer? Tablet or desktop?
```

…and stopped: *"Once you approve or edit the list, I'll build each screen."*

## Turn 2: drawing

The person answered the questions ("staff don't see totals; marking ready texts the customer; mostly a counter tablet"). The agent drew 11 full boards and 2 state sheets, `3.1-orders-<state>.html`, with an `index.html` in canvas order. Three of the answers became design decisions:

- The text to the customer goes out only after the 8-second Undo window ends, because a sent text can't be unsent.
- The staff view keeps the money column's width ("Unpaid · ring up #1043 at the till"), so nothing shifts between roles.
- If two people mark the same order, the second sees who did it, and the customer gets one text.
