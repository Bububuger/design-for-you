# Example · craft-critique

**Prompt:** "Review this screen." It's a project tracker's task screen with six planted flaws.

The agent rendered it with headless Chrome at 1280 and 390 wide and looked at both before writing anything. (The narrow capture was cut off, because desktop Chrome won't make a window that small. It said so, and marked the phone finding as unconfirmed.) Then the ranked report, with nothing changed:

```
First glance: the headline wins, then three identical black buttons. The tasks and the next action don't stand out.

Blocks or misleads
1. Three primary buttons, two duplicates → one primary (Publish), Save changes secondary, drop the extra Save
2. The loading button changes width (~50% wider) and reads "⟳ Save Saving…" → keep the width,
   hide the label, centre a spinner on top
3. Hover looks the same as selected, and selected barely differs from the card → stronger selected,
   softer hover
4. Badge text 2.2:1 at 12px → darken to ≈#55555a

Slows down
5. The 420px empty box is the biggest thing on the screen → size it to its content, label it "Archived"
6. Spacing groups the buttons with the empty box, not the tasks → more space under the button row
7. No viewport meta, so phones shrink it → add it, then check with a real mobile emulator (unconfirmed)

Looks careless
8. The headline's last line is one word, "place", and it's marketing copy → a plain title, or text-wrap: balance
9. Badges start at different x positions → a fixed right-aligned slot
10. "Publish" doesn't say what → "Publish plan"

Checked, no issues: one strong colour, consistent radii, native buttons with focus intact, no motion.
Shared button? Then fixes 1–2 change it everywhere: go through whoever owns the shared styles.

Tell me which items to fix and I'll apply only those, render again and re-check.
```

With the project's guide saying "hover and selected share one tint on purpose", the same review wrote: *"Difference from the defaults, noted rather than flagged."* With "Refine this screen", it applied exactly the fixes and listed what it left out of scope.
