import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import extension from '../../../.pi/extensions/factory/index.js';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const sessionID = `factory-pi-extension-test-${process.pid}`;

// A stand-in for Pi's ExtensionAPI and ExtensionContext: it records handlers and notifications.
function load(cwd) {
  const handlers = {};
  const notes = [];
  const sent = [];
  extension({ on: (name, handler) => { handlers[name] = handler; }, sendUserMessage: (text) => sent.push(text) });
  const ctx = { cwd, sessionManager: { getSessionId: () => sessionID }, ui: { notify: (text, kind) => notes.push([kind, text]) } };
  return { handlers, notes, ctx, sent };
}

const bash = (command) => ({ type: 'tool_call', toolCallId: 'call-1', toolName: 'bash', input: { command } });

test('Pi registers the start, tool and compaction events', () => {
  const { handlers } = load(root);
  assert.deepEqual(Object.keys(handlers).sort(),
    ['agent_before_settle', 'before_agent_start', 'session_before_compact', 'session_compact', 'tool_call', 'tool_result']);
});

test('Pi tool calls that read a secret are blocked before execution', async () => {
  const { handlers, ctx } = load(root);
  assert.equal((await handlers.tool_call(bash('cat .env'), ctx)).block, true);
  const read = { type: 'tool_call', toolCallId: 'call-2', toolName: 'read', input: { path: `${root}/.env` } };
  assert.equal((await handlers.tool_call(read, ctx)).block, true);
  assert.equal(await handlers.tool_call(bash('git status --short'), ctx), undefined);
});

test('Pi treats an unknown tool carrying a command as a shell call', async () => {
  const { handlers, ctx } = load(root);
  const custom = { type: 'tool_call', toolCallId: 'call-3', toolName: 'codemode_shell', input: { command: 'cat .env' } };
  assert.equal((await handlers.tool_call(custom, ctx)).block, true);
});

test('Pi started in a subfolder finds the project hooks', async () => {
  const { handlers, ctx } = load(`${root}/demo`);
  assert.equal(await handlers.tool_call(bash('git status --short'), ctx), undefined);
  assert.equal((await handlers.tool_call(bash('cat .env'), ctx)).block, true);
});

test('Pi compaction is cancelled without a verified checkpoint', async () => {
  const { handlers, notes, ctx } = load(root);
  assert.deepEqual(await handlers.session_before_compact({ type: 'session_before_compact', reason: 'threshold' }, ctx), { cancel: true });
  assert.match(notes[0][1], /checkpoint/);
});

test('Pi gives the factory context once per session, and again after a compaction', async () => {
  const { handlers, ctx } = load(root);
  const first = await handlers.before_agent_start({ type: 'before_agent_start', messageType: 'user', prompt: 'hi' }, ctx);
  assert.match(first.message.content, /Æion Factory pi checkpoint profile/);
  assert.equal(await handlers.before_agent_start({ type: 'before_agent_start', messageType: 'user', prompt: 'again' }, ctx), undefined);
  await handlers.session_compact({ type: 'session_compact', reason: 'manual' }, ctx);
  assert.ok(await handlers.before_agent_start({ type: 'before_agent_start', messageType: 'user', prompt: 'after' }, ctx));
});

test('Pi past 250k is held to closure by its own context measure', async () => {
  const { handlers, ctx } = load(root);
  const measured = { ...ctx, sessionManager: { getSessionId: () => `${sessionID}-250k` }, getContextUsage: () => ({ tokens: 260000, contextWindow: 1000000, percent: 26 }) };
  const write = { type: 'tool_call', toolCallId: 'call-4', toolName: 'write', input: { path: `${root}/src.py`, content: 'x' } };
  const refused = await handlers.tool_call(write, measured);
  assert.equal(refused.block, true);
  assert.match(refused.reason, /250k alert/);
});

test('Pi compacts itself once the hook reports a verified handover, then resumes from it', async () => {
  // A stand-in adapter answers as the shared rule does after a verified checkpoint past 250k.
  const folder = mkdtempSync(join(tmpdir(), 'pi-compact-'));
  mkdirSync(join(folder, 'tools/agents'), { recursive: true });
  writeFileSync(join(folder, 'tools/agents/hook.py'), 'import json\nprint(json.dumps({"aeion": {"compact": True}}))\n');
  const { handlers, ctx, sent } = load(folder);
  let compacted = 0;
  const result = { type: 'tool_result', toolCallId: 'call-5', toolName: 'bash', input: { command: 'true' }, content: [], isError: false };
  const compact = (options) => { compacted += 1; options.onComplete({}); };
  await handlers.tool_result(result, { ...ctx, getContextUsage: () => ({ tokens: 260000 }), compact });
  rmSync(folder, { recursive: true, force: true });
  assert.equal(compacted, 1);
  // Compacting aborts the running turn, so without this message the session would sit idle.
  assert.equal(sent.length, 1);
  assert.match(sent[0], /handover/);
});

test('Pi bounds a repeated closure refusal instead of looping one alert', async () => {
  // Regression: a settlement that never verified its checkpoint re-injected the same 250k alert forever.
  // The closure refusal is a terminal stop too, and it is the one that still earns a few more requests.
  const folder = mkdtempSync(join(tmpdir(), 'pi-settle-loop-'));
  mkdirSync(join(folder, 'tools/agents'), { recursive: true });
  writeFileSync(join(folder, 'tools/agents/hook.py'),
    'import json\nprint(json.dumps({"continue": False, "stopReason": "Æion Factory 250k alert: fill the handover and verify the checkpoint"}))\n');
  const { handlers, notes, ctx } = load(folder);
  const outcomes = [];
  for (let attempt = 0; attempt < 4; attempt += 1) {
    outcomes.push(await handlers.agent_before_settle({ type: 'agent_before_settle', entries: [], continue: false }, ctx));
  }
  rmSync(folder, { recursive: true, force: true });
  assert.deepEqual(outcomes.map((outcome) => outcome?.continue ?? false), [true, true, true, false]);
  assert.equal(notes.length, 1);
  assert.match(notes[0][1], /checkpoint/);
});

test('Pi compacts at settlement when the checkpoint is verified', async () => {
  const folder = mkdtempSync(join(tmpdir(), 'pi-settle-compact-'));
  mkdirSync(join(folder, 'tools/agents'), { recursive: true });
  writeFileSync(join(folder, 'tools/agents/hook.py'), 'import json\nprint(json.dumps({"aeion": {"compact": True}}))\n');
  const { handlers, ctx, sent } = load(folder);
  let compacted = 0;
  const compact = (options) => { compacted += 1; options.onComplete({}); };
  const result = await handlers.agent_before_settle({ type: 'agent_before_settle', entries: [], continue: false }, { ...ctx, compact });
  rmSync(folder, { recursive: true, force: true });
  assert.equal(result, undefined);
  assert.equal(compacted, 1);
  assert.equal(sent.length, 1);
  assert.match(sent[0], /handover/);
});

test('Pi turns a sign-off finding at settlement into one more request (Pi FB-004)', async () => {
  const folder = mkdtempSync(join(tmpdir(), 'pi-stop-'));
  mkdirSync(join(folder, 'tools/agents'), { recursive: true });
  writeFileSync(join(folder, 'tools/agents/hook.py'), [
    'import json, sys',
    'event = json.load(sys.stdin)',
    "print(json.dumps({'decision': 'block', 'reason': 'Sign off: update CHANGELOG.md'} if event['hook_event_name'] == 'Stop' else {}))",
  ].join('\n') + '\n');
  const { handlers, ctx } = load(folder);
  const result = await handlers.agent_before_settle({ type: 'agent_before_settle', entries: [], continue: false }, ctx);
  rmSync(folder, { recursive: true, force: true });
  assert.equal(result.continue, true);
  assert.equal(result.entries[0].content, 'Sign off: update CHANGELOG.md');
  // No finding lets the run settle.
  const clean = mkdtempSync(join(tmpdir(), 'pi-stop-clear-'));
  mkdirSync(join(clean, 'tools/agents'), { recursive: true });
  writeFileSync(join(clean, 'tools/agents/hook.py'), 'import json\nprint(json.dumps({}))\n');
  const quiet = load(clean);
  assert.equal(await quiet.handlers.agent_before_settle({ type: 'agent_before_settle', entries: [], continue: false }, quiet.ctx), undefined);
  rmSync(clean, { recursive: true, force: true });
});

test('Pi settles a terminal stop instead of turning it into another request (Pi FB-005)', async () => {
  const folder = mkdtempSync(join(tmpdir(), 'pi-stop-terminal-'));
  mkdirSync(join(folder, 'tools/agents'), { recursive: true });
  writeFileSync(join(folder, 'tools/agents/hook.py'), [
    'import json, sys',
    'event = json.load(sys.stdin)',
    "print(json.dumps({'continue': False, 'stopReason': 'Æion Factory context run is stopped'} if event['hook_event_name'] == 'Stop' else {}))",
  ].join('\n') + '\n');
  const { handlers, notes, ctx } = load(folder);
  const outcomes = [];
  for (let attempt = 0; attempt < 2; attempt += 1) {
    outcomes.push(await handlers.agent_before_settle({ type: 'agent_before_settle', entries: [], continue: false }, ctx));
  }
  rmSync(folder, { recursive: true, force: true });
  // Settling twice, never a new request, and the user is told why the run ended.
  assert.deepEqual(outcomes, [undefined, undefined]);
  assert.deepEqual(notes.map((note) => note[1]), ['Æion Factory context run is stopped', 'Æion Factory context run is stopped']);
});
