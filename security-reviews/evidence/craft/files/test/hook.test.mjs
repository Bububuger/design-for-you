import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const run = (env) => JSON.parse(execFileSync('bash', [resolve(root, 'hooks/run-hook.cmd'), 'session-start'],
  { env: { PATH: process.env.PATH, ...env }, encoding: 'utf8' }));

test('Claude Code gets hookSpecificOutput.additionalContext with the entry skill', () => {
  const out = run({ CLAUDE_PLUGIN_ROOT: root });
  assert.equal(out.hookSpecificOutput.hookEventName, 'SessionStart');
  assert.match(out.hookSpecificOutput.additionalContext, /name: using-craft/);
});

test('Cursor gets additional_context', () => {
  assert.match(run({ CURSOR_PLUGIN_ROOT: root }).additional_context, /using-craft/);
});

test('other agents get the SDK-standard additionalContext', () => {
  assert.match(run({}).additionalContext, /using-craft/);
});

test('an unknown hook script exits 0 with no output', () => {
  const r = spawnSync('bash', [resolve(root, 'hooks/run-hook.cmd'), 'no-such-hook'], { encoding: 'utf8' });
  assert.equal(r.status, 0); assert.equal(r.stdout, ''); assert.equal(r.stderr, '');
});

test('without bash on PATH the wrapper exits 0 with no output', () => {
  const r = spawnSync('/bin/sh', [resolve(root, 'hooks/run-hook.cmd'), 'session-start'], { encoding: 'utf8', env: { PATH: '/nonexistent' } });
  assert.equal(r.status, 0); assert.equal(r.stdout, ''); assert.equal(r.stderr, '');
});

test('the hook files keep LF line endings on every checkout', () => {
  const attrs = readFileSync(resolve(root, '.gitattributes'), 'utf8');
  for (const rule of ['*.cmd text eol=lf', 'hooks/session-start text eol=lf']) assert.ok(attrs.includes(rule), rule);
  for (const f of ['hooks/run-hook.cmd', 'hooks/session-start']) assert.ok(!readFileSync(resolve(root, f), 'utf8').includes('\r'), f);
});
