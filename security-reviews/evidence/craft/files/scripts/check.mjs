// Structure checks every contributor can run: skill format, links, tool names.
import { resolve } from 'node:path';
import { listSkills, checkSkill } from './checks.mjs';

const root = resolve(import.meta.dirname, '..');
const problems = listSkills(root).flatMap(checkSkill);
for (const p of problems) console.log(p);
console.log(problems.length ? `${problems.length} problem(s)` : 'ok');
process.exit(problems.length ? 1 : 0);
