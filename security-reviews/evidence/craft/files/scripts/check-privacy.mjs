// The author's pre-push gate: private names (denylist) and colour values shared with private token files.
// CRAFT_DENYLIST: one term per line (default ~/.config/craft/denylist.txt).
// CRAFT_PRIVATE_TOKENS: colon-separated paths to private token files to compare colour values against.
import { readFileSync, existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { scanDenylist, sharedHex, listFiles } from './checks.mjs';

// Pure black and white are in every palette; matching them proves nothing.
const UNIVERSAL = new Set(['#000000', '#ffffff']);
const root = resolve(import.meta.dirname, '..');
const listPath = process.env.CRAFT_DENYLIST ?? join(homedir(), '.config/craft/denylist.txt');
const terms = existsSync(listPath) ? readFileSync(listPath, 'utf8').split('\n').map((s) => s.trim()).filter(Boolean) : [];
const tokenFiles = (process.env.CRAFT_PRIVATE_TOKENS ?? '').split(':').filter(Boolean);
const problems = [];
if (terms.length === 0) problems.push(`denylist missing or empty at ${listPath}: name scan did not run`);
else problems.push(...scanDenylist(root, terms));
if (tokenFiles.length === 0) problems.push('CRAFT_PRIVATE_TOKENS not set: colour scan did not run');
for (const t of tokenFiles) {
  if (!existsSync(t)) { problems.push(`private token file not found: ${t}`); continue; }
  const theirs = readFileSync(t, 'utf8');
  for (const f of listFiles(root)) for (const h of sharedHex(readFileSync(f, 'utf8'), theirs).filter((x) => !UNIVERSAL.has(x))) problems.push(`${f.slice(root.length + 1)}: colour ${h} also in a private token file`);
}
for (const p of problems) console.log(p);
console.log(problems.length ? `${problems.length} problem(s)` : 'ok');
process.exit(problems.length ? 1 : 0);
