# design-system-sync · RED (the v2 plugin, before this skill existed)

Seed: an invented journaling app "Fieldnote" with `packages/ui/` (22 tokens, a few named by value; Button/Input/Badge with variant maps; `guidelines.md`), `apps/web`, no Storybook. For (c), the same repo as a git history, with a `guide/` folder imported at a recorded commit; since then the guide changed `--color-accent` and `--radius-md`, and the code changed `--radius-md` too.

| Prompt | Skills started | What it did | Gap |
|---|---|---|---|
| (a) "Design the settings page." (no DESIGN.md) | design-setup | Read the tokens, guidelines and components well and skipped the brand questions the code answers; asked one question | **Never offered to bring the code's design system into the design tool**, which is the case the author hit |
| (b) "Bring our design system into the design tool." | design-system | Foundations guide linked to the code's token file, a component index with code paths, gaps in a separate proposed-tokens file; stopped before components | **No inventory and no "which components should I draw?"**; the components were neither offered nor picked |
| (c) "Apply the guide changes to the code." | design-system | Used DESIGN.md's recorded sync commit and git history: accent = clean guide change (affects Button primary, Home's "New entry"), radius = changed on both sides (10 → guide 8 / code 12), proposed and **edited nothing** | Already good; the new skill formalises it |
