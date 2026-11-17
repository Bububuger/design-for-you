import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, relative, resolve, dirname, sep } from 'node:path';

const TOOL_NAMES = /\b(mcp__[a-z0-9_]+|get_jsx|write_html|duplicate_nodes|get_screenshot|update_styles|create_artboard|get_tree_summary|get_computed_styles|set_text_content|get_basic_info|get_tokens|create_tokens|set_tokens|get_guide|finish_working_on_nodes|get_font_family_info|use_figma|get_design_context|get_variable_defs)\b/g;
const SKIP_DIRS = new Set(['.git', 'node_modules', 'scratch']);
const LINE_LIMIT = 250;
// The entry skill routes to other skills and never touches a design tool, so it has no adapters.
const NO_ADAPTERS = new Set(['using-craft']);

const normalise = (text) => text.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n');

export function parseFrontmatter(raw) {
  const m = normalise(raw).match(/^---\n([\s\S]*?)\n---\n/);
  if (!m) return null;
  const fields = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (kv) fields[kv[1]] = kv[2].trim().replace(/^(["'])(.*)\1$/, '$2');
  }
  return { name: fields.name, description: fields.description, keys: Object.keys(fields) };
}

function walk(dir) {
  return readdirSync(dir).flatMap((n) => {
    if (SKIP_DIRS.has(n)) return [];
    const p = join(dir, n);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

export function listSkills(root) {
  const d = join(root, 'skills');
  return existsSync(d) ? readdirSync(d).map((n) => join(d, n)).filter((p) => statSync(p).isDirectory()) : [];
}

// Every link target in a markdown text: inline links (with <…> and "title"), reference definitions; code fences skipped.
function linkTargets(text) {
  const prose = normalise(text).replace(/^```[\s\S]*?^```/gm, '');
  const inline = [...prose.matchAll(/\]\(\s*(?:<([^>]+)>|([^)\s]+))(?:\s+"[^"]*")?\s*\)/g)].map((m) => m[1] ?? m[2]);
  const refs = [...prose.matchAll(/^\s*\[[^\]]+\]:\s*<?([^>\s]+)>?/gm)].map((m) => m[1]);
  return [...inline, ...refs];
}

export function checkSkill(dir) {
  const problems = [];
  const folder = dir.split(sep).pop();
  const skillMd = join(dir, 'SKILL.md');
  if (!existsSync(skillMd)) return [`${folder}: missing SKILL.md`];
  const text = normalise(readFileSync(skillMd, 'utf8'));
  const fm = parseFrontmatter(text);
  if (!fm) problems.push(`${folder}/SKILL.md: missing frontmatter`);
  else {
    if (fm.name !== folder) problems.push(`${folder}/SKILL.md: name "${fm.name}" does not match folder`);
    if (!fm.description?.startsWith('Use when')) problems.push(`${folder}/SKILL.md: description must start with "Use when"`);
    if ((fm.description?.length ?? 0) > 1024) problems.push(`${folder}/SKILL.md: description over 1024 characters`);
    if (fm.keys.join(',') !== 'name,description') problems.push(`${folder}/SKILL.md: frontmatter keys must be exactly name and description`);
  }
  if (text.replace(/\n$/, '').split('\n').length > LINE_LIMIT) problems.push(`${folder}/SKILL.md: over ${LINE_LIMIT} lines`);
  if (!NO_ADAPTERS.has(folder) && !existsSync(join(dir, 'references/adapters/html.md'))) problems.push(`${folder}: missing references/adapters/html.md`);
  const adaptersDir = join(dir, 'references', 'adapters') + sep;
  for (const file of walk(dir).filter((f) => f.endsWith('.md'))) {
    const rel = `${folder}/${relative(dir, file)}`;
    const body = readFileSync(file, 'utf8');
    if (!file.startsWith(adaptersDir)) {
      const hits = [...new Set(body.match(TOOL_NAMES) || [])];
      if (hits.length) problems.push(`${rel}: tool API name outside adapters: ${hits.join(', ')}`);
    }
    for (const target of linkTargets(body)) {
      if (target.startsWith('#')) continue;
      const windows = /^[A-Za-z]:[\\/]/.test(target);
      if (!windows && /^[a-z][a-z0-9+.-]*:/i.test(target)) continue;
      const clean = decodeURI(target.split(/[?#]/)[0]);
      const abs = resolve(dirname(file), clean);
      if (windows || !abs.startsWith(resolve(dir) + sep)) problems.push(`${rel}: link leaves the skill: ${target}`);
      else if (!existsSync(abs)) problems.push(`${rel}: broken link: ${target}`);
    }
  }
  return problems;
}

function compile(terms) {
  // plain terms match as whole words (accented letters count as letters); "re:" lines are raw regexes
  return terms.filter(Boolean).map((t) => t.startsWith('re:')
    ? new RegExp(t.slice(3), 'g')
    : new RegExp(`(?<![\\p{L}\\p{N}])${t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\p{L}\\p{N}])`, 'giu'));
}

export function scanText(text, terms, label = 'text') {
  return compile(terms).flatMap((re) => [...text.matchAll(re)].map((m) => `${label}: denylisted "${m[0]}"`));
}

export function scanDenylist(root, terms) {
  return walk(root).flatMap((file) => scanText(readFileSync(file, 'utf8'), terms, relative(root, file)));
}

// 6-digit colours from "#rrggbb[aa]" or "0xrrggbb[aa]", lower-cased, alpha dropped.
export function hexValues(text) {
  return new Set([...text.matchAll(/(?:#|0x)([0-9a-fA-F]{6})(?:[0-9a-fA-F]{2})?(?![0-9a-fA-F])/g)].map((m) => `#${m[1].toLowerCase()}`));
}

export function sharedHex(ours, theirs) {
  const other = hexValues(theirs);
  return [...hexValues(ours)].filter((h) => other.has(h)).sort();
}

export function listFiles(root) {
  return walk(root);
}
