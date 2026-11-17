# craft v0.4: the rename

Date: 2026-11-15 · Status: approved.
Amends the earlier specs. Nothing changes in what the skills do; only names.

Claude already has commands with "design" in the name (Claude Design), so the project is now **craft** (plugin, marketplace and repo), and its skills drop the `design-` prefix. In Claude Code they're invoked as `craft:<name>`.

| Before 0.4.0 | Now |
|---|---|
| `using-design-skills` | `using-craft` (entry, loaded by the hook) |
| `design` (`/design`) | `craft:make` |
| `design-setup` | `craft:setup` |
| `design-system` | `craft:system` |
| `design-system-sync` | `craft:sync` |
| `screen-states` | `craft:states` |
| `three-proposals` | `craft:explore` |
| `design-critique` | `craft:critique` |

Kept: `DESIGN.md` and `design-sync.json` (files in the person's project, not commands).
The older specs and the test records in `tests/scenarios/` keep the old names as they were written.
Private check settings moved too: `CRAFT_DENYLIST`, `CRAFT_PRIVATE_TOKENS`, `~/.config/craft/`.

## 0.5.0: `make` becomes `craft`

The main skill's folder and name are now `craft`, matching the package: `/craft` when installed with `npx skills` (skills keep their plain names there), `/craft:craft` in the Claude Code plugin. The other skills keep their names.

## 0.6.0: every skill carries the package name

Installed with `npx skills`, skills keep their plain folder names, so `setup`, `sync` and `system` would clash with other packages. They are now `craft-setup`, `craft-states`, `craft-explore`, `craft-system`, `craft-sync` and `craft-critique`; `craft` and `using-craft` stay. In the Claude Code plugin they read `/craft:craft-setup` and so on. Skill text names them by these names; older test records keep the names they ran with.
