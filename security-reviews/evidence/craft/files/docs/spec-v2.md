# design-skills v2: a workflow that triggers itself

Date: 2026-11-15 · Status: approved.
This document supersedes the **Structure**, **Shared conventions**, **Testing** and **Publishing** sections of `spec.md`, and amends its four skill sections. Everything in `spec.md` not changed here still holds.

## Goal

Make the pack as easy to use as a coding-workflow plugin such as superpowers. Install it once. From then on the right design skill starts by itself: the person says "make me a pricing page" and the agent sets up the project's design brief if there is none, plans the screens, covers their states, offers options when the direction is open, critiques its own work before showing it, and keeps the design system in step.

## The model (borrowed from superpowers, credited in the README)

1. **An entry skill injected at session start.** A `SessionStart` hook prints `using-design-skills` into the context. Its core rule: *if there is even a small chance a design skill applies, invoke it before responding, including before clarifying questions.*
2. **One front door that chains the rest.** `design` names its sub-skills with **REQUIRED SUB-SKILL** markers at the step where each applies.
3. **Hard gates** stay exactly as in v1.
4. **Every skill is also a slash command** (Claude Code exposes skills as `/name`; through the plugin they appear as `/design-skills:<name>`).

## Skills

| Skill | Role | Starts |
|---|---|---|
| `using-design-skills` (new) | Entry: the rule above, plus a **routing table** from situations to skills, plus the skill priority | Hook, every session |
| `design-setup` (new) | Interview, then `DESIGN.md`, then foundations through `design-system` (create mode) | Automatically when a design task starts and no `DESIGN.md` exists, or `/design-setup` |
| `design` (new, front door) | Designs one or more pages or elements end to end | `/design`, or any "design / create / redesign a page, screen, flow, element" request |
| `screen-states` | v1, amended | Auto, and as a step of `design` |
| `three-proposals` | v1, amended | Auto ("options", "I don't like it"), and as a step of `design` when the direction is open |
| `design-system` | v1, amended | Auto, and as a step of `design-setup` and `design` |
| `design-critique` | v1, amended; also the **gate before showing** any design | Auto, and as the last step of `design` |

Not in v2: `design-handoff` (the author's decision, 2026-11-15).

### `using-design-skills`

- `<SUBAGENT-STOP>`: a subagent dispatched for one task ignores it, the same pattern as superpowers.
- **The rule:** check the routing table before any design-related response or action. Announce "Using <skill> to <purpose>".
- **Routing table** (situation → skill):
  - any request to design, create or redesign a page, screen, flow or element → `design`;
  - a design task in a project with no `DESIGN.md` → `design-setup` first, then `design`;
  - "options", "alternatives", "I don't like it", "rethink" → `three-proposals`;
  - "review", "refine", "polish", "feels off", or you're about to show your own design → `design-critique`;
  - tokens, the style guide, a component, "make consistent", "audit" → `design-system`;
  - "what states are missing?", "is this ready for dev?" → `screen-states`.
- **Priority:** setup before design; `design` before its sub-skills (it calls them in order); critique last.
- **Small edits never trigger the process:** a change to one value, one label or one element's size, which the person described exactly, is made directly. This holds even on a shared piece: change the token or component once, say which screens it affects, and don't open a full states pass. This resolves the v1 collisions the review found (a 2px change on a shared button; "make it better" vs three-proposals).
- **Red flags table:** "this is just a quick mockup", "I'll skip the brief, it's obvious", "I'll show it and critique later" → each paired with the reality.
- About 150 lines or fewer, because it loads into every session.

### `design-setup`

- **Interview, one question at a time,** multiple choice where possible, stopping when the answers are enough. In order:
  1. **Product:** what it is, who uses it, where (phone, desktop, counter tablet), and the one job of its main screen.
  2. **Audience and tone:** technical level, formality, language and locale formats.
  3. **Mood:** 2–3 mood words picked from options, plus "what it must never look like".
  4. **Brand assets:** logo, colours, fonts, existing design system or design file. Read anything that exists and only ask about what's missing.
  5. **References:** 2–5 products or pages they like. For each, ask what to **take** and what to **avoid**, and look at it if it's a link or image the agent can open.
  6. **Constraints:** platforms, accessibility needs, light or dark, icon set, motion appetite.
- **Infer first:** read the codebase, existing CSS/tokens and the design file before asking. Never ask what is already answered there.
- **Output:** `DESIGN.md` at the project root (template in `references/design-md-template.md`). It has these sections: Product, Audience and voice, Mood (words and never-like), Brand, References (take / avoid), Constraints, Decisions log (date, decision, why), and Open questions. **Stop and show the person `DESIGN.md`.**
- Then **REQUIRED SUB-SKILL:** `design-system` (create mode) for the foundations, which keeps its own gate.
- **Done when:** `DESIGN.md` is approved and the foundations are approved.

### `design`

1. **Context:** read `DESIGN.md`. If it's missing → **REQUIRED SUB-SKILL:** `design-setup`, then continue. Read the design system and the related screens.
2. **Scope in words:** list the pages and elements to make, each with its job and the one next action. **Stop and confirm the list** when more than one item is involved or the request is vague. Otherwise go on.
3. **For each item, in order:**
   1. **REQUIRED SUB-SKILL:** `screen-states`. Its written state list and gate come first.
   2. If the direction is open (new kind of screen, no precedent in the system, or the person asked for ideas) → **REQUIRED SUB-SKILL:** `three-proposals` *before drawing the states*. Once a direction is picked, the states are drawn in it.
   3. Draw the main state and the other states, using only system pieces and tokens. Anything new goes through `design-system` (add mode).
   4. **REQUIRED SUB-SKILL:** `design-critique` in **self-check mode** (see below) on every board before showing it.
4. **Close:** a short summary for the person:
   - what was made, and where;
   - decisions taken (also appended to `DESIGN.md`'s Decisions log);
   - pieces added or changed in the system, and the screens they affect;
   - open questions.

## Amendments to the v1 skills (from the final review)

### All four
- **Fallback wording:** "If no adapter matches your tool, do the same verbs in your tool and say which ones you mapped by hand. With no design tool at all, build in HTML (`html.md`). If an image is all you have, say that values read from it are estimates."
- Each skill starts by reading `DESIGN.md` when it exists.
- `html.md` is tailored per skill: board names that fit the skill, plus rows for the component index (design-system) and the comparison board (three-proposals).

### `screen-states`
- If the project has no states matrix, draw the interaction states that change layout or content on a state sheet, and suggest `design-system` to make the matrix.
- The worked example says it is trimmed.

### `design-system`
- **Firm rules (any project):** every colour is a token; one icon set; every interactive piece has a states matrix; design and code change together, design first; a change to a shared piece is listed with the screens it affects before it propagates.
- **Moved to defaults:** "shadows only on floating things" and "at most one primary action". The audit checklist reports them as **differences from the defaults** when the project's guide says otherwise, not as rule breaks.
- **`token-roles.md` example:** all values are replaced with a palette and type scale invented for the example and checked against the source products. No value may match the author's product tokens.
- The Paper adapter's token row adds: "after registering tokens, rebind the foundation boards to them".

### `three-proposals`
- The rule reads **"different directions: a different axis, or clearly different values on one axis when the person names the axis"** (consistent with `divergence-axes.md` and the density round).
- **"Both":** two options; the bolder-option rule is waived when the person named both options.

### `design-critique`
- **Modes:**
  - **review:** the person asks about a design;
  - **refine:** the person asks to improve one;
  - **self-check:** triggered by your own unshown work, including from `design`. In self-check, fix what you find within the scope of the task, re-render, then show the design with a short list of what the check changed.

  In review mode, nothing changes.
- Add the rule **"Toasts match the system"**.
- The cursor line in `SKILL.md` carries the web caveat ("on the web, follow the project's convention").
- Rebuild `examples/design-critique.md` from a run that actually rendered, and fix its numbering.

## Structure

```
design-skills/
├── README.md, LICENSE, package.json (engines: node >=20.11)
├── .claude-plugin/{plugin.json, marketplace.json}
├── hooks/{hooks.json, run-hook.cmd, session-start}   (SessionStart → using-design-skills)
├── skills/{using-design-skills, design-setup, design, screen-states, three-proposals, design-system, design-critique}/
├── docs/{spec.md, spec-v2.md}
├── examples/   (one per workflow skill)
├── scripts/, test/   (validator)
└── tests/scenarios/<skill>/   (+ tests/scenarios/workflow/ for the cross-skill runs)
```

The hook is adapted from superpowers' polyglot `run-hook.cmd` + `session-start` (MIT, credited in the README and in the files' headers). It emits the Claude Code field (`hookSpecificOutput.additionalContext`), the Cursor field and the SDK-standard field, chosen by environment.

**Other agents:** the README has a short "add this to your `AGENTS.md`" snippet: the core rule plus the routing table. It is the fallback where there's no hook.

## Validator (from the review)

- `npm run check` checks structure only and works for any contributor. `npm run check:privacy` runs the denylist and fails if it is missing or empty; it is the author's pre-push gate.
- **Links:**
  - ignore code fences;
  - handle `<…>` targets, `"title"` suffixes and reference-style definitions;
  - decode `%20`, strip `?query`;
  - treat a Windows drive path as leaving the skill.
- **Tool names:** add `get_basic_info`, `get_tokens`, `create_tokens`, `set_tokens`, `get_guide`, `finish_working_on_nodes`, `get_font_family_info`. The adapters exemption is exactly the `references/adapters/` folder.
- **Frontmatter:**
  - strip a BOM and normalise CRLF;
  - accept a quoted description;
  - allow exactly `name` and `description`;
  - the 250-line limit counts lines, not newline characters.
- `engines` in `package.json`.

## Testing

- **Per skill:** the v1 RED/GREEN records stay. New skills get their own RED/GREEN, with the same neutral runner.
- **Rendering:** the runner allows the headless browser command (`--allowedTools "Bash(*Chrome*)"`), so "render it" is exercised.
- **Hook:** a unit test runs `hooks/session-start` with each environment variable set and checks the JSON field and that the entry skill's text is present.
- **Workflow (with the full plugin installed, no skill named in the prompts):**
  1. "Make me a pricing page for a bakery app" with no `DESIGN.md` → `design-setup` starts, interviews, writes `DESIGN.md` and stops.
  2. The same with a `DESIGN.md` present → `design` starts, then `screen-states` lists the states and stops.
  3. "Make the Save button 2px taller" on a shared button → a direct edit, with no process.
  4. "Make it better" on an existing screen → `design-critique` (refine), not three proposals.
  5. "Give me options for the checkout" → `three-proposals`.
  6. A `design` run carried through drawing → `design-critique` self-check runs before showing, and the summary lists what it changed.
  7. Review Focus 1 (the project's hover rule) rerun with all skills present.
- **Cost:** each workflow run is capped in scope (2–3 boards).

## Publishing (amended)

- The privacy gate now covers values too. Run an intersection of every hex value in the repo against the author's product token files (paths given at run time, never committed). It must come back empty.
- **Commit author e-mail:** the author keeps their personal e-mail as the commit author (decided 2026-11-15); the history scan does not treat it as a leak.
