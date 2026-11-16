import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { parseFrontmatter, checkSkill, scanDenylist, scanText, hexValues, sharedHex } from '../scripts/checks.mjs';

function skill(files, name = 'demo-skill') {
  const root = mkdtempSync(join(tmpdir(), 'ds-'));
  const dir = join(root, 'skills', name);
  for (const [rel, body] of Object.entries(files)) {
    mkdirSync(join(dir, rel, '..'), { recursive: true });
    writeFileSync(join(dir, rel), body);
  }
  return { root, dir };
}
const fm = (name = 'demo-skill', desc = 'Use when testing.') => `---\nname: ${name}\ndescription: ${desc}\n---\n`;
const adapters = { 'references/adapters/html.md': '# HTML\n', 'references/adapters/paper.md': 'get_jsx get_basic_info\n', 'references/adapters/figma.md': '# Figma\n' };

test('parseFrontmatter reads name and description', () => {
  assert.deepEqual(parseFrontmatter(fm()), { name: 'demo-skill', description: 'Use when testing.', keys: ['name', 'description'] });
  assert.equal(parseFrontmatter('# no frontmatter'), null);
});

test('parseFrontmatter tolerates BOM, CRLF and a quoted description', () => {
  const text = '\uFEFF---\r\nname: demo-skill\r\ndescription: "Use when quoted."\r\n---\r\n';
  assert.deepEqual(parseFrontmatter(text), { name: 'demo-skill', description: 'Use when quoted.', keys: ['name', 'description'] });
});

test('a clean skill has no problems', () => {
  const { dir } = skill({ 'SKILL.md': fm() + 'See [catalog](references/a.md).\n', 'references/a.md': 'x', ...adapters });
  assert.deepEqual(checkSkill(dir), []);
});

test('name must match folder, description must start with "Use when", no extra keys', () => {
  const { dir } = skill({ 'SKILL.md': '---\nname: other\ndescription: Does things.\nversion: 1\n---\n', ...adapters });
  const p = checkSkill(dir).join('\n');
  assert.match(p, /name "other" does not match folder/);
  assert.match(p, /description must start with "Use when"/);
  assert.match(p, /frontmatter keys must be exactly name and description/);
});

test('250 lines with a trailing newline passes; 251 fails', () => {
  const at = (n) => fm() + 'line\n'.repeat(n - 4);
  assert.deepEqual(checkSkill(skill({ 'SKILL.md': at(250), ...adapters }).dir), []);
  assert.match(checkSkill(skill({ 'SKILL.md': at(251), ...adapters }).dir).join('\n'), /over 250 lines/);
});

test('tool API names outside adapters fail, inside adapters pass', () => {
  const { dir } = skill({ 'SKILL.md': fm() + 'Call get_jsx, then get_basic_info and mcp__paper__write_html.\n', ...adapters });
  const p = checkSkill(dir).filter((x) => x.includes('tool API name'));
  assert.equal(p.length, 1);
  assert.match(p[0], /get_jsx/); assert.match(p[0], /get_basic_info/);
});

test('a file named like adapters but outside the folder is not exempt', () => {
  const { dir } = skill({ 'SKILL.md': fm(), 'references/adapters-x.md': 'get_tokens\n', ...adapters });
  assert.match(checkSkill(dir).join('\n'), /adapters-x\.md: tool API name/);
});

test('links must stay inside the skill and resolve, in every link form', () => {
  const body = [
    '[a](../other/SKILL.md)', '[b](references/missing.md "a title")', '[c](<../o o.md>)',
    '[d]: ../ref.md', '[e](C:\\Users\\x.md)', '[f](https://example.com)', '[g](#anchor)',
    '[h](references/a.md?x=1)', '[i](references/a%20b.md)', '```', '[j](../in-fence.md)', '```',
  ].join('\n');
  const { dir } = skill({ 'SKILL.md': fm() + body + '\n', 'references/a.md': 'x', 'references/a b.md': 'x', ...adapters });
  const p = checkSkill(dir).join('\n');
  assert.match(p, /link leaves the skill: \.\.\/other\/SKILL\.md/);
  assert.match(p, /broken link: references\/missing\.md/);
  assert.match(p, /link leaves the skill: \.\.\/o o\.md/);
  assert.match(p, /link leaves the skill: \.\.\/ref\.md/);
  assert.match(p, /link leaves the skill: C:\\Users\\x\.md/);
  assert.doesNotMatch(p, /example\.com|#anchor|a\.md\?x|a%20b|in-fence/);
});

test('every skill needs an HTML adapter', () => {
  const { dir } = skill({ 'SKILL.md': fm(), 'references/adapters/paper.md': 'x' });
  assert.match(checkSkill(dir).join('\n'), /missing references\/adapters\/html\.md/);
});

test('the entry skill needs no adapters', () => {
  const { dir } = skill({ 'SKILL.md': fm('using-craft') }, 'using-craft');
  assert.deepEqual(checkSkill(dir), []);
});

test('denylist finds whole-word terms case-insensitively and key patterns', () => {
  const fakeKey = 'sk_' + 'a'.repeat(26);
  const { root } = skill({ 'SKILL.md': fm() + `Made for ACME Bakery by Bob. Bobsled zone. key ${fakeKey}\n`, ...adapters });
  assert.equal(scanDenylist(root, ['acme bakery', 'bob', 're:sk[-_][A-Za-z0-9_-]{20,}']).length, 3);
});

test('scanText checks a single text', () => {
  assert.equal(scanText('Built at Acme.', ['acme']).length, 1);
});

test('hexValues normalises case and drops alpha; sharedHex finds overlaps', () => {
  assert.deepEqual([...hexValues('a #13579B b #2468aCe6 c 0x13579bff #abc')].sort(), ['#13579b', '#2468ac']);
  assert.deepEqual(sharedHex('x #112233 #445566', 'y 0x445566FF'), ['#445566']);
});
