# design-skills v3: sync a design system between code and the design tool

Date: 2026-11-15 · Status: approved.
Amends `spec-v2.md`. Everything in v2 not changed here still holds.

## Problem

In a repo that already has a design system in code (a UI package, tokens, components), `/design` used the code's tokens directly and never created a guide in the design tool. The person gets no guidelines page or component index in Paper, and changes made later in the tool's guide have no path back to the code.

## New skill: `design-system-sync`

Description (triggers only): "Use when a project already has a design system in code (a UI package, design tokens, a component library, guideline docs) and the design tool doesn't mirror it, when asked to import or bring the design system, tokens or components into the design tool, or to apply, push or sync changes from the design tool's guide back to the code."

### Import (code → design tool)

1. **Detect** (`references/detect.md`). Look for:
   - **Tokens:** CSS custom properties, a Tailwind theme or config, design-token JSON (W3C / Style Dictionary), theme files in any language.
   - **Components:** `packages/ui`, `components/ui`, shadcn's `components.json`, Storybook stories, an exported component index.
   - **Docs:** `guidelines.md`, Storybook docs, a README with usage rules.
2. **Inventory, then stop.** Show counts and where each thing lives:
   - tokens by role (colour / type / spacing / radius / shadow / motion);
   - components, each with its variants (from props, variant maps or stories) and its file path;
   - any guideline docs.

   **Ask which components to draw now** (the author's decision, 2026-11-15: "ask each time"). Suggest the ones the next screens need.
3. **Build in the tool:**
   - register the tokens **with the same names as in code**, so code and tool share names and no mapping file is needed;
   - make a foundations guide page using the `design-system` component anatomy;
   - make a **component index** with one row per component: name, variants, code path, status (`drawn` / `in code only`);
   - draw the chosen components with their full states matrix. Values come from the code (styles, variant maps, stories), never from screenshots; with no rendered source, state that values are read from code.
   - Guideline docs become the legend text of their sections.
4. **Self-check:** render the guide boards. When the code can render the component (Storybook, a demo page), render it at the same size and compare.
5. **Record** in `DESIGN.md`:
   - Brand gets "Design system source: code at `<paths>`; the design tool's guide mirrors it";
   - a dated line in the Decisions log: "Imported N tokens, drew components A, B, C".

### Export (design tool → code)

1. **Read** exact values from the tool's guide (adapter) and from the code by the shared names.
2. **Diff**: changed token values, changed component styles or variants, new tokens and new components (new ones only when the person approved them in the tool).
3. **Propose the edits:** every file and line, plus the components and screens each change affects. **Stop for approval.**
4. **Apply** only the approved edits, run the project's own checks (lint, typecheck, tests, visual tests if present), and report the results.
5. **Record** a dated sync line in `DESIGN.md` › Decisions log.

### Rules

| Rule | Why |
|---|---|
| Shared names between code and tool, never a parallel naming | One name per decision; no mapping file to drift |
| Inventory and pick before drawing anything | Big UI packages make "draw everything" slow and expensive; the person decides |
| Values from code, not screenshots | Screenshots round colours and sizes |
| Export proposes, then stops; no silent code edits | Code changes ship to users; the person approves the diff |
| The project's own checks run after an export | The design skill doesn't know the codebase's contracts; its tests do |
| Code is the source of truth until the person says otherwise | Matches v2's "code beats a stale brief" |

Adapters: Paper (`get_tokens`/`create_tokens`/`set_tokens`, the guide page, component boards); Figma (variables, components); HTML (a `guide/` folder with `tokens.css` importing the code's token file, and pages per section).

## Changes to existing skills

- **`design-setup`**, step 1. When the read finds a design system in code, say so with the counts, and offer the import (**REQUIRED SUB-SKILL:** `design-system-sync` import) **instead of** `design-system` create. Brand questions the code answers are skipped. With "skip", the import is still offered, because it is about the tool, not the brief.
- **`design`**, step 3.3. When a needed component exists in code but its status is `in code only` (or the tool has no guide yet), import just that component first (**REQUIRED SUB-SKILL:** `design-system-sync`, import of one component). Never draw a look-alike.
- **`design-system`**, change mode. When `DESIGN.md` names code as the design system source, propagating an approved guide change ends with **REQUIRED SUB-SKILL:** `design-system-sync` export.
- **`using-design-skills`**, routing table:
  - "import / bring our design system / components / tokens into <tool>" → `design-system-sync`;
  - "apply / push / sync the guide's changes to the code" → `design-system-sync`;
  - a design task with no `DESIGN.md` in a repo with a design system in code → `design-setup`, which offers the import.

## Testing

- **RED / GREEN, HTML adapter.** A repo with `packages/ui/` (a token file, 3 components with variant maps, a `guidelines.md`) and no `DESIGN.md`.
  1. "Design the settings page." Expect: setup notices the system and offers the import → the inventory → stop → (turn 2 picks 2 components) a guide with foundations and an index (2 drawn, 1 in code only) → DESIGN.md records the source.
  2. "Bring our design system into the design tool." Expect: `design-system-sync` import directly.
- **Export.** Same repo, with the guide already imported and one token changed in the guide. "Apply the guide changes to the code." Expect: a diff that touches only that token line, the affected components listed, a stop; after approval, the edit plus the project's checks run.
- **On-demand import.** A `design` run where the screen needs the component that's `in code only`: it imports that one first.
- **Paper pass.** One import run against a scratch Paper file; never an existing one.
- **Regressions:** `npm test` and `npm run check`; workflow runs 1, 2b and 3 from v2 still route the same.

## Amendment after the v3 review (2026-11-15)

- **`design-sync.json` replaces the git-commit base.** It sits at the project root and records the source, the tool, the naming rule, the date, the token values **both sides agreed on** at the last sync, and each component's status.
  - A full import writes it.
  - A one-component import changes only that component's status.
  - An export updates the agreed values.
  - Without the file, an export lists every difference and asks the direction for each.

  Git is no longer needed. The "no mapping file" rule stands: this is a record of agreed values, not a name mapping.
- **Naming rule:** CSS names as written; otherwise the CSS name the system emits; otherwise the full key path joined with `-`. Types the tool can't hold are listed on the guide as "not registered".
- **Generated token files:** export edits the source input, never the build output.
- **Existing tool tokens with other values** are conflicts at the inventory stop, never overwritten silently.
- **A sync-only `DESIGN.md`** (no Product section) is treated as missing by `design`, so setup still runs.
- **Declining the import** is logged. `design` then asks once before importing a component, and otherwise builds from the code's values on the board.
- **`design` with a guide that differs from code** classifies by `design-sync.json` (code changed → refresh the guide; guide changed → a pending export), instead of calling the guide stale.
