import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import * as v from 'valibot';
import { submitPreparation } from '../src/tools/submit-preparation.ts';

test('preparation supplies bounded test data and cannot select commands, paths or authority', () => {
  const tool = submitPreparation('/private/tmp/unused-preparation-fixture.json');
  const good = { status: 'ready', contract: 'class Acceptance {}', reason: 'Fixture' };
  assert.equal(v.safeParse(tool.input, good).success, true);
  for (const bad of [{ ...good, command: ['bash'] }, { ...good, path: '/etc/hosts' },
    { ...good, merge: true }, { ...good, contract: 'x'.repeat(48001) },
    { ...good, status: 'approved' }, { ...good, reason: 'x'.repeat(121) }]) {
    assert.equal(v.safeParse(tool.input, bad).success, false);
  }
  assert.throws(() => submitPreparation('relative.json'));
});

test('the supervisor result is immutable, while an identical replay is harmless', async (t) => {
  const directory = await mkdtemp(join(tmpdir(), 'aeion-prepare-tool-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const path = join(directory, 'result.json');
  const tool = submitPreparation(path);
  const data = { status: 'ready', contract: 'class Acceptance {}', reason: 'Fixture' };
  tool.run({ data, toolCallId: 'first' });
  tool.run({ data, toolCallId: 'replay' });
  assert.throws(() => tool.run({ data: { ...data, contract: 'weakened' }, toolCallId: 'changed' }), /immutable/);
  assert.deepEqual(JSON.parse(await readFile(path, 'utf-8')), data);
});
