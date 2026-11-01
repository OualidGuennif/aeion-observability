import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import plugin from '../../../.opencode/plugins/factory/index.js';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const hooks = {};
const register = (domain) => async (name, callback) => { hooks[`${domain}.${name}`] = callback; };
await plugin.setup({ location: { directory: root }, tool: { hook: register('tool') }, session: { hook: register('session') } });
const sessionID = `factory-v2-plugin-test-${process.pid}`;

test('OpenCode V2 registers native tool and compaction hooks', () => {
  assert.deepEqual(Object.keys(hooks).sort(), ['session.compaction', 'session.prompt', 'tool.execute.after', 'tool.execute.before']);
});

test('OpenCode V2 shell/read payloads refuse secrets before execution', async () => {
  await assert.rejects(hooks['tool.execute.before']({ tool: 'shell', sessionID, input: { command: 'cat .env' } }));
  await assert.rejects(hooks['tool.execute.before']({ tool: 'read', sessionID, input: { filePath: `${root}/.env` } }));
  await hooks['tool.execute.before']({ tool: 'shell', sessionID, input: { command: 'git status --short' } });
});

test('OpenCode V2 started in a subfolder finds the project hooks', async () => {
  const nested = {};
  const record = (domain) => async (name, callback) => { nested[`${domain}.${name}`] = callback; };
  await plugin.setup({ location: { directory: `${root}/demo` }, tool: { hook: record('tool') }, session: { hook: record('session') } });
  await nested['tool.execute.before']({ tool: 'shell', sessionID, input: { command: 'git status --short' } });
  await assert.rejects(nested['tool.execute.before']({ tool: 'shell', sessionID, input: { command: 'cat .env' } }), /secret/);
});

test('OpenCode V2 compaction refuses a missing checkpoint', async () => {
  const event = { sessionID, system: [] };
  await assert.rejects(hooks['session.compaction'](event), /checkpoint/);
  assert.deepEqual(event.system, []);
});

test('OpenCode V2 past 250k is held to closure by its step tokens', async () => {
  const measured = {};
  const record = (domain) => async (name, callback) => { measured[`${domain}.${name}`] = callback; };
  const session = `${sessionID}-250k`;
  const compactions = [];
  // A stand-in event stream with one finished step at 260k tokens, as OpenCode 2.2.0 reports it.
  async function* steps() {
    yield { type: 'session.step.ended', data: { sessionID: session, tokens: { input: 10000, output: 2000, reasoning: 0, cache: { read: 248000, write: 0 } } } };
  }
  await plugin.setup({
    location: { directory: root }, tool: { hook: record('tool') },
    session: { hook: record('session'), compact: async (input) => { compactions.push(input); } },
    event: { subscribe: () => steps() },
  });
  await new Promise((done) => setImmediate(done));
  await assert.rejects(measured['tool.execute.before']({ tool: 'write', sessionID: session, input: { filePath: `${root}/src.py` } }), /250k alert/);
  assert.deepEqual(compactions, []);
});

test('OpenCode V2 compacts itself once the hook reports a verified handover', async () => {
  // A stand-in adapter answers as the shared rule does after a verified checkpoint past 250k.
  const folder = mkdtempSync(join(tmpdir(), 'opencode-compact-'));
  mkdirSync(join(folder, 'tools/agents'), { recursive: true });
  writeFileSync(join(folder, 'tools/agents/hook.py'), 'import json\nprint(json.dumps({"aeion": {"compact": True}}))\n');
  const stub = {};
  const record = (domain) => async (name, callback) => { stub[`${domain}.${name}`] = callback; };
  const compactions = [];
  await plugin.setup({ location: { directory: folder }, tool: { hook: record('tool') },
    session: { hook: record('session'), compact: async (input) => { compactions.push(input); } } });
  const done = { tool: 'shell', sessionID, status: 'completed', input: { command: 'true' }, result: { content: '' } };
  await stub['tool.execute.after'](done);
  await stub['tool.execute.after'](done);
  rmSync(folder, { recursive: true, force: true });
  assert.deepEqual(compactions, [{ sessionID }]);
});
