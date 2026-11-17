# design-skills: a shareable pack of design skills for AI agents

Date: 2026-11-15 · Status: approved; superseded in parts by `spec-v2.md`

## Goal

A public, MIT-licensed GitHub repo, `design-skills`, on the author's personal account. It holds four agent skills that carry the author's recurring design rules: state coverage, design-system creation and upkeep, three proposals for comparison, and a design critique pass. Developers who design with an AI agent and a design tool can use them to get designer-grade, complete screens.

The rules come from the author's own design work: chats with agents, and boards in Paper across several products. They are restated generically. No product's names, colours, copy or decisions appear in the pack.

## Audience and language

- Developers designing with AI (agent + Paper MCP, Figma MCP, or plain HTML). They are not trained designers, so every rule carries a short "why".
- Written in English.

## Non-goals

- No separate skills for screen inventory, canvas organisation or change propagation. Their useful parts are folded into the four skills, as noted below.
- No tool-specific code or MCP calls in skill bodies.
- No content, names, data or screenshots from any real project.

## Structure (approach A: four self-contained skills)

```
design-skills/
├── README.md                    what each skill does; install for Claude Code, Codex, Cursor, others
├── LICENSE                      MIT
├── .claude-plugin/plugin.json   one-command install as a Claude Code plugin
├── skills/
│   ├── screen-states/      SKILL.md, references/{state-catalog.md, naming-and-sheets.md, adapters/{paper,figma,html}.md}
│   ├── design-system/      SKILL.md, references/{token-roles.md, component-anatomy.md, audit-checklist.md, adapters/…}
│   ├── three-proposals/    SKILL.md, references/{divergence-axes.md, comparison-board.md, adapters/…}
│   └── design-critique/    SKILL.md, references/{rules.md, adapters/…}
└── examples/                    one invented worked example per skill
```

Each skill works when copied alone. A few rules repeat across skills on purpose (for example "no layout shift" in states and in critique). Each repeat is one or two lines.

## Shared conventions

- **Frontmatter:** `name`, plus a `description` written as trigger situations ("Use when …").
- **Body shape:** when to use; steps; approval gates ("stop and show the person before …"); done criteria; common mistakes. Each `SKILL.md` stays under about 250 lines, and detail goes in `references/`.
- **Tool-agnostic verbs:** bodies say "create a board", "read exact values from the design, never from a screenshot", "screenshot and check". Each tool's adapter maps those verbs to that tool:
  - **Paper:** artboards, `get_jsx`, `duplicate_nodes`, tokens.
  - **Figma MCP:** frames, variables.
  - **HTML:** files in a folder, CSS custom properties.
- **Project first:** every skill starts by reading the project's existing design system and design file. The pack's rules are defaults: on look, the project wins. Process rules are firm: state coverage, approval gates, real divergence between options, tokens only, one icon set.
- **Examples** use invented products and people (a bakery, a clinic, a project tracker).

## Skill 1: `screen-states`

**Triggers:** designing or redesigning a screen, flow or component; "cover all states"; "what states are missing?"; before handing a screen to code.

**Steps**
1. Read the context: the design system, related screens, who uses the screen, what they do there, and the next action.
2. List the states in words before drawing. Walk the catalogue and mark each one applies, doesn't apply (with a reason) or open question. **Gate:** show the list and stop.
3. Draw the main state first, one section at a time, with realistic invented data. Draw the most complex realistic case.
4. Draw the other states:
   - a state that changes the whole screen (empty, offline) gets a full board;
   - a state that changes one part (a failed row, a loading button) goes on a state sheet that shows just that part.
5. Check each state for no layout shift between states, and for an action that resolves it.
6. Name the boards `<number> · <screen> · <state>`. Put the main state first, the other states next and sheets last. Start each row with a cover note listing its contents.

**Catalogue** (`references/state-catalog.md`)
- **Data:** default; empty (first time vs. filtered to nothing); one item; few; many or overflow (with scroll); very long text and names; missing optional fields.
- **System:** first load vs. refresh; couldn't load; offline; partly failed; slow; changed while viewing; already done by someone else; expired.
- **Activity:** in progress; waiting on someone else; just finished; undo window; paused by choice vs. failed.
- **People:** role or permission differences; first-time vs. returning; pending approval.
- **Interaction** (per interactive piece): normal, hover, pressed, focus (keyboard), disabled, loading, selected. These come from the design system's states matrix and are not redrawn on every screen.

**Rules**
- No state without a way out: say what to do next and who does it.
- Word a failure as a failure, never as a deliberate pause.
- One standard empty-state component.
- A whole-app problem goes in a top banner; a problem with one item goes inline on that item.
- Loading and label swaps keep the element's size.

**Done when:** every catalogue item is drawn, marked "doesn't apply" with a reason, or listed as an open question.

## Skill 2: `design-system`

**Triggers:** starting a system or style guide; adding a component or token; "standardize", "make consistent", "audit the guide"; loose colours or one-off pieces.

**Mode: create**
1. Foundations first: colour roles, type scale, spacing, radius, shadow, containers, motion, and a short "how we write" section.
2. Name tokens by role (`references/token-roles.md`):
   - `text`, `text-muted`, `text-placeholder`, `surface`, `fill-1/2`;
   - `border`, `border-hover`, `tint-hover/selected/pressed`, `focus`;
   - per status: base, `-bg`, `-text`, `-strong`, `-action`.
3. Define the interaction-state rules once, as a foundation, for bordered pieces, borderless pieces and the primary action.
4. Add components one at a time, starting with what the first screens need.

**Mode: add or change a piece**
1. Prefer an existing component plus a variant over a one-off.
2. Every guide section has the same anatomy: a legend column (name, plus the rule in prose: when to use it and why), the examples, and a states matrix (variants × states) for anything interactive. Pieces that only show information get data states.
3. A new colour or icon becomes a token or an icon-set entry the same day.
4. Propagate the change:
   - update every screen that uses the piece;
   - update the code, if any;
   - update the component index;
   - report what changed.

**Mode: audit**
- Scan for loose colours, near-duplicate values, pieces missing from the states matrix, and screens that drift from the guide.
- Report a ranked list. **Gate:** fix nothing before approval.

**Component index** (`references/component-anatomy.md`): one table of piece → where its states are drawn → code location → status.

**Firm rules**
- Every colour is a token.
- One icon set.
- Shadows only on floating things, at two fixed strengths.
- One primary action per screen.
- The design file and the code change together, design first.

**Default rules**
- Hover darkens only the border on bordered pieces.
- Hover is subtler than selected.
- Selecting never changes font weight.
- Placeholders are lighter than muted text.
- Stacked list items never touch.
- The focus ring appears only from the keyboard.

## Skill 3: `three-proposals`

**Triggers:** "give me options", "3 variations", "design both so I can pick", "other directions", "I don't like it, try something else", "rethink this".

**Steps**
1. Restate the problem in one or two sentences: what is wrong today, and what a good result must do. If the request is vague, name the problem you see and confirm it.
2. Choose three directions that differ on a real axis (`references/divergence-axes.md`): structure or placement, interaction model (inline, popover, page, conversation), density, emphasis, or what gets removed. Write each direction's idea and trade-off in one line. No two directions may share an axis value.
3. Build a comparison board in a separate, temporary area. Never edit the real screens. The board holds:
   - a legend card: each option's idea, strengths, costs, and the recommendation with its reason;
   - a "Current" copy of today's design, if one exists;
   - options A, B and C at the same size with the same data. Sub-variants (A2, A3) are allowed.
4. Draw every option at final-screen care, including the states its difference affects.
5. Present the recommendation first. **Gate:** stop. The person picks, combines or rejects.
6. On a pick: apply the option to the real screens and the system (through the `design-system` propagation), then clear the temporary area. On a full rejection: rethink from the problem statement, and allow changes to the surrounding parts. Never fall back to small tweaks.

**Rules**
- Three by default; two for "both"; more only on request.
- No straw men.
- Equal fidelity across options.
- One deliberately bolder option.

`references/comparison-board.md` holds the board layout and the legend-card template.

## Skill 4: `design-critique`

**Triggers:** "review this design", "refine", "something feels off", "too busy", "polish", finishing a screen, before handoff.

**Steps**
1. Look at the screen as its user would: what draws the eye first, whether that is the most important thing, and what the one next action is.
2. Run the rules in `references/rules.md`. Each rule has a check, a why and a typical fix.
3. Report findings ranked by impact: problem, location, fix. **Gate:** apply nothing unless the person asked for "refine" directly.
4. After fixes, screenshot again and re-run the checks on what changed.

**Rule groups**
- **Hierarchy and restraint**
  - One idea per block.
  - When in doubt, remove.
  - When too much competes for attention, calm the secondary elements; don't enlarge the primary.
  - Shorter text.
  - At most one primary action.
- **Space**
  - No dead space or oversized containers.
  - No cramped groups.
  - A box fits its content.
  - Repeated rows align in fixed-width slots.
- **Stability**
  - No layout shift from loading, label swaps, selection or toggles.
  - Containers that swap content keep their height.
- **Interaction feel**
  - Hover is subtle and softer than selected.
  - Pressed is instant.
  - Focus comes only from the keyboard.
  - Default cursor; pointer only on links.
  - No text cursor on menu items.
  - Native OS controls where they exist.
- **Contrast and colour**
  - Text and dots stay readable on tinted grounds.
  - Badges on colour are checked.
  - The active item stands out from its container.
  - One strong colour moment.
- **Text**
  - No orphans or one-word last lines; balance or pretty wrapping on titles.
  - Headlines capped at a set number of lines.
  - Row titles on one line with an ellipsis.
  - Plain words for the audience.
  - Say what happens next and who does it.
- **Consistency**
  - The same piece looks the same everywhere.
  - Banners only for whole-app problems.
  - Toasts match the system.
  - Actions in lists are real buttons.
- **Motion**
  - Only where it helps.
  - Opening is slower than closing.
  - Hover-in is quick and hover-out softer.
  - Respect reduced motion.

**Calibration:** each rule is a default. The project's system wins, and the critique notes the conflict. A fix that changes a shared component hands off to `design-system`.

## Testing

Method from the writing-skills skill: RED (baseline without the skill), GREEN (with the skill), REFACTOR (close the loopholes the agent found).

| Skill | Baseline task (fresh subagent) | Pass criteria |
|---|---|---|
| screen-states | "Design the orders screen for a bakery app" | Lists the states and stops before drawing; covers the catalogue; no state without an action |
| design-system | "Start a style guide for a clinic booking app"; "audit this guide" (seeded with loose colours) | Role-named tokens; a states matrix; the audit reports and does not fix |
| three-proposals | "Give me options for this settings page" | Three directions on different axes; legend with a recommendation; equal fidelity; stops for the pick |
| design-critique | Review a seeded screen with known flaws (layout shift, a weak hover, an orphan word, two primary buttons) | Finds the seeded flaws, ranked; fixes nothing before approval |

- Run every test with the HTML adapter.
- Run one Paper pass per skill in a scratch Paper file, so the Paper adapter is proven against the real MCP. No existing project file is touched.

## Privacy gate (before any push)

- A scripted scan of the repo for a private denylist: the real client, family and project names, product names, and anything shaped like an API key. The denylist lives outside the repo and is never committed. The scan must return nothing.
- The author reads the README and every `SKILL.md` before the first push.

## Publishing

- Built in a new local repo, `~/www/design-skills`.
- Pushed to the author's personal GitHub only after the author has read it.
- Install paths tested: the Claude Code plugin, and a manual copy into `.claude/skills/` or `.agents/skills/`.
- This spec moves into the new repo's `docs/` when the repo is created.
