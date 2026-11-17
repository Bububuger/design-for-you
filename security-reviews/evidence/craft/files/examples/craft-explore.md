# Example · craft-explore

**Prompt:** "I don't like this settings page, give me options." It's a project tracker's settings page: 7 equal buttons, a flat list of 8 checkboxes, and danger actions mixed into the form.

## Turn 1: the problem, then a stop

The request didn't say what was wrong, so the agent named it first:

> Too many actions in the wrong places · everything has the same weight · notifications are a 3×2 grid pretending to be a list · personal and workspace settings mixed.
> A good result shows where you are and what changed, has one way to save (or none), and keeps destructive actions apart.

| | Main axis | Idea | Trade-off |
|---|---|---|---|
| A | Interaction | Autosave with "All changes saved" | Fast; no "undo all" |
| B | Structure | Sub-navigation, one section at a time, each with Save | Scales; one more click |
| C (bolder) | Removal | A summary with "Change" links; digests merged; the rare things under Advanced | Calmest; power users go deeper |

> "Is that the problem you meant?"

## Turn 2: "Yes. Go ahead."

> **I recommend A.** The seven Save/Reset/Import/Export buttons are the main problem, and autosave removes them without adding navigation.

The board is `explorations/settings/index.html`: legend, **current.html**, then A, B and C with the same people and data, plus `states.html` for the states each option's difference creates (A's undo toast, B's unsaved-changes warning, C's expanded row). `settings.html` is untouched.

## Turn 3: "None of these work, the problem is it's too dense."

No tweaking of round 1. A new set on the density axis: **A** spacious (everything visible, one per row) · **B** essentials first, the rest folded with their current values shown (recommended: 20 visible controls → 5) · **C** settings moved to where they apply (bolder; changes navigation).
