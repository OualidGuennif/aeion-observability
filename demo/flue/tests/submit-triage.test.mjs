import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import * as v from 'valibot';
import { submitTriage, triageFromEnv } from '../src/tools/submit-triage.ts';

const input = {
  labels: { severity: ['critical', 'high', 'low'], component: ['payments', 'auth'], route: ['page-oncall', 'ticket', 'ignore'] },
  events: [{ id: 'evt-1' }, { id: 'evt-2' }],
};
const one = (id, extra = {}) => ({ id, severity: 'low', component: 'auth', route: 'ignore', duplicate_of: null, ...extra });

async function setup(t) {
  const dir = await mkdtemp(join(tmpdir(), 'aeion-triage-'));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const resultFile = join(dir, 'result.json');
  return { dir, resultFile, tool: submitTriage(input, resultFile) };
}

test('the input schema accepts only supplied ids and labels', async (t) => {
  const { tool } = await setup(t);
  assert.equal(tool.name, 'submit_triage');
  assert.equal(v.safeParse(tool.input, { results: [one('evt-1'), one('evt-2', { duplicate_of: 'evt-1' })] }).success, true);
  for (const bad of [{ results: [one('evt-9')] }, { results: [one('evt-1', { severity: 'urgent' })] },
                     { results: [one('evt-1', { duplicate_of: 'evt-9' })] }, { results: [one('evt-1', { note: 'x' })] },
                     { results: [{ id: 'evt-1' }] }, {}])
    assert.equal(v.safeParse(tool.input, bad).success, false, JSON.stringify(bad));
});

test('a complete submission replaces the result file atomically', async (t) => {
  const { resultFile, tool } = await setup(t);
  await writeFile(resultFile, '{"results": []}\n');
  const results = [one('evt-1', { severity: 'high', route: 'ticket' }), one('evt-2')];
  assert.equal(await tool.run({ data: { results }, toolCallId: 't1' }), 'Recorded 2 results.');
  assert.deepEqual(JSON.parse(await readFile(resultFile, 'utf-8')), { results });
});

test('duplicate or missing ids are reported to the model and nothing is written', async (t) => {
  const { resultFile, tool } = await setup(t);
  await writeFile(resultFile, '{"results": []}\n');
  assert.throws(() => tool.run({ data: { results: [one('evt-1'), one('evt-1')] }, toolCallId: 't1' }), /exactly once/);
  assert.throws(() => tool.run({ data: { results: [one('evt-1')] }, toolCallId: 't2' }), /Missing results for: evt-2/);
  assert.equal(await readFile(resultFile, 'utf-8'), '{"results": []}\n');
});

test('input and result locations must be absolute', async (t) => {
  const { dir } = await setup(t);
  const path = join(dir, 'input.json');
  await writeFile(path, JSON.stringify(input));
  assert.throws(() => triageFromEnv({ AEION_RESULT_FILE: '/r.json' }), /AEION_TRIAGE_INPUT/);
  assert.throws(() => triageFromEnv({ AEION_TRIAGE_INPUT: path, AEION_RESULT_FILE: 'r.json' }), /AEION_RESULT_FILE/);
  assert.deepEqual(triageFromEnv({ AEION_TRIAGE_INPUT: path, AEION_RESULT_FILE: '/r.json' }), { input, resultFile: '/r.json' });
});
