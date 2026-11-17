# design-setup · GREEN (skill + design-system installed, unchanged prompt)

| Run | Turn | Result |
|---|---|---|
| Empty folder | 1 | Triggered from its description. Read the folder ("no README, no tokens"), then **one question** with 5 options (where it's used) plus the main screen's job ✓ |
| Empty folder | 2: "On their phones. Main screen: this week's schedule, book a class in two taps." | Took the answer, then **one** next question (voice) with examples, plus language/locale ✓ |
| README + tokens | 1 | Summarised what the files settle (product, pt-BR, brand, accessibility) and **asked none of it**; flagged that the "off-white" token is actually a cool white and the logo file is missing (→ open questions); one question on voice ✓ |
| README + tokens | 1 (separate run) | Same reading; asked only the remaining gap (the main screen's job) ✓ |
| README + tokens | 2: "Skip the questions, just design it." | Wrote DESIGN.md with **all 8 sections** and **12 "(assumed)" marks**, named the 3 assumptions that matter most, then design-system create: extended tokens.css **renaming nothing**, a foundations page with a full interaction-states table, and **stopped for approval** ✓ |
