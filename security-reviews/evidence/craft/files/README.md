<p align="center">
  <img src="assets/banner.png" alt="craft" width="100%">
</p>

<p align="center">
  <b>Design skills for AI agents.</b> Complete screens with every state, and a design system that stays consistent.<br>
  Works with Paper, Figma or plain HTML, in Claude Code, Codex, OpenCode, Cursor and other agents.
</p>

<p align="center">
  <a href="https://skills.sh/diego3g/craft"><img src="https://skills.sh/b/diego3g/craft" alt="skills.sh"></a>
</p>

---

Ask your agent for "a pricing page" and, with craft installed, it works like a careful designer:
- it writes a short design brief first;
- it lists every state the screen can be in;
- it uses your design system's pieces;
- it checks its own work before showing it.

It stops for your "yes" where it matters and writes its decisions down for next time.

## Install

### Claude Code, Claude Desktop and claude.ai

Install craft as a plugin. Inside a Claude Code session:

```
/plugin marketplace add diego3g/craft
/plugin install craft@craft
```

- The plugin adds a session-start hook, so every request goes to the right skill by itself.
- Skills carry the plugin name: `/craft:craft`, `/craft:craft-setup` and so on.
- Update from your shell with `claude plugin update craft@craft`.

In Claude Desktop or claude.ai, go to Customize › Plugins › Add › Add marketplace, then enter `diego3g/craft`.

### Codex, OpenCode, Cursor and other agents

Install the skills with the [skills CLI](https://skills.sh):

```
npx skills add diego3g/craft
```

It asks which agents to install into. You can also name the agent yourself:

| Agent | Command |
|---|---|
| Codex | `npx skills add diego3g/craft -a codex` |
| OpenCode | `npx skills add diego3g/craft -a opencode` |
| Cursor | `npx skills add diego3g/craft -a cursor` |
| Gemini CLI | `npx skills add diego3g/craft -a gemini-cli` |
| GitHub Copilot | `npx skills add diego3g/craft -a github-copilot` |
| Windsurf | `npx skills add diego3g/craft -a windsurf` |

- Add `-g` to install for every project instead of only the current one.
- Run `npx skills update` to update later.

These agents don't run the session-start hook. Paste the routing below into your `AGENTS.md` so the agent still picks the right skill.

<details>
<summary><b>Routing for AGENTS.md</b></summary>

```markdown
## Design skills
Before responding to anything that designs, reviews or changes a UI, check this table and use the skill.
First look whether DESIGN.md exists at the project root.
- No DESIGN.md and a design task → craft-setup, then craft
- Design / create / redesign a page, screen, flow or element → craft
- "Options", "alternatives", "I don't like it" → craft-explore
- "Review", "refine", "make it better", or before showing your own design → craft-critique
- Tokens, style guide, a component, "audit" → craft-system
- "Bring our design system into <tool>", "apply the guide changes to the code" → craft-sync
- "What states are missing?" → craft-states
Small edits the person described exactly (one value, label or size): just make them.
A stop means ending your turn with the question. Never decide a stop for the person.
```

</details>

**By hand:** copy the folders in `skills/` into your project's `.agents/skills/`, then add the routing above.

## The skills

| Skill | What it does |
|---|---|
| **`craft-setup`** | Interviews you one question at a time: product, audience and voice, mood, brand, references, constraints. It then writes `DESIGN.md` and builds the foundations (tokens and base components). |
| **`craft`** | The main command, for designing a page, screen, flow or element. It confirms the scope, then for each screen lists the states, draws with your system's pieces and checks the result. |
| **`craft-states`** | Lists every state a screen can be in (empty, loading, error, long content, permissions, offline…) using realistic messy data, then draws and names each one. |
| **`craft-explore`** | Draws three directions that really differ in structure, interaction or density, never just new colours. They sit next to the current design, with a recommendation first. |
| **`craft-system`** | Looks after the design system: role-named tokens, interaction rules defined once, a states matrix per component, and a component index. Before a change spreads, it lists the screens the change affects. |
| **`craft-sync`** | Brings a design system that already lives in code into your design tool. Later it sends the guide's changes back to the code as a reviewed diff. |
| **`craft-critique`** | Renders the design and looks at it, then checks hierarchy, spacing, contrast, text, consistency and motion. Findings are ranked by impact. In review mode it changes nothing. |

The hidden `using-craft` skill does the routing: it sends each request to the right skill.

Agents with slash commands run them by name: `/craft`, `/craft-setup`… (`/craft:craft`, `/craft:craft-setup`… with the Claude Code plugin). In any agent you can also just ask in plain words.

## The best workflow

1. **Start with the brief.** Run `craft-setup` once per project. It writes `DESIGN.md`, which every other skill reads first. If your repo already has a component library or token files, `craft-setup` offers `craft-sync` instead, so nothing gets invented twice.
2. **Design with `craft`.** Describe what you need ("a settings page with billing and team"). It stops to confirm the scope and the list of states, then draws.
3. **Unsure about the direction?** Say "give me options" and `craft-explore` draws three directions. Pick one, or mix two.
4. **Review before you ship.** Say "review this" for a `craft-critique` report. `craft` already runs this check on its own work before showing it.
5. **Keep the system healthy.** Ask for "an audit" from time to time (`craft-system`). After changing the guide in your design tool, say "apply the guide changes to the code" (`craft-sync`).

Small edits ("make the button 2px taller") skip all of this: the agent makes the change, and says so when it touches a shared piece.

## Good to know

- **`DESIGN.md`** has eight short sections: Product, Audience and voice, Mood, Brand, References, Constraints, a dated Decisions log and Open questions. It's how Monday's decisions survive into Thursday's session.
- **Your project wins.** Every rule about *look* is a default. If your design system does something else, the agent follows yours.
- **Some rules hold in every project**, because they're about process, not taste:
  - cover the states;
  - stop for approval;
  - give options that really differ;
  - make every colour a token;
  - use one icon set;
  - change design and code together.
- **Tool-agnostic.** The skills describe actions ("create a board", "render and look"), and adapters map them to Paper (MCP), Figma (MCP) or plain HTML. Plain HTML is also the fallback. The Figma adapter hasn't been tested yet, so reports are welcome.

## Contributing

```
npm test        # validator and hook tests
npm run check   # skill format, links, no tool names outside adapters
```

Every skill was written test-first: scenarios ran without the skill, then with it (see [`tests/scenarios/`](tests/scenarios/)). Changes to a skill should come with a scenario that fails before the change and passes after it.

## Credits

The session-start hook and the "one entry skill that routes to the rest" idea come from [obra/superpowers](https://github.com/obra/superpowers) (MIT). The banner uses [Departure Mono](https://departuremono.com) (OFL).

## License

MIT
