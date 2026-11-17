# Example · craft-setup

**Prompt:** "Set up the design for my new app: a booking app for a small yoga studio." The folder has a README (pt-BR only, members over 60, a sage and paper brand, a lotus logo) and a small `tokens.css`.

## Turn 1: read first, then one question

> Here's what's already settled, so I won't ask about any of it: product (members book on phones, instructors on a laptop) · language (pt-BR: 15/11, 18h30, R$ 120,00) · brand (sage green, warm paper, lotus) · accessibility (members over 60 → ~18px text, 48px taps).
> Two things I noticed but won't fix yet: the README points to /brand/lotus.svg, which isn't here, and --color-surface is a cool white, not warm paper. Both go on the open questions list.
>
> **First question: how should the app talk to members?**
> 1. Warm and casual · 2. Friendly but brief · 3. Calm and gentle · 4. Formal and precise · Something else

## If the person says "skip the questions, just design it"

It wrote `DESIGN.md` with all eight sections (Product, Audience and voice, Mood, Brand, References, Constraints, Decisions log, Open questions), with every guess marked "(assumed)", and named the three assumptions that matter most:

1. The most-used screen is this week's classes, with one-tap booking.
2. Calm, warm, unhurried; never a gym app, a generic dashboard or anything neon.
3. Members' screens get 18px text and 48px taps; the instructors' laptop screens are denser.

Then it built the foundations through `craft-system`: it extended `tokens.css` without renaming anything, made a foundations page with a full interaction-states table, and stopped for approval.
