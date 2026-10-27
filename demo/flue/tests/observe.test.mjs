import test from 'node:test';
import assert from 'node:assert/strict';
import { toRecord } from '../src/observe.ts';

const CANARY = 'PRIVATE_CANARY';

test('turn events keep usage metadata and drop model content', () => {
  const record = toRecord({
    type: 'turn', instanceId: 'run-1', conversationId: 'conv_1', isError: false, durationMs: 50,
    request: { requestedModel: 'glm', systemPrompt: CANARY },
    response: { output: { role: 'assistant', content: [{ type: 'text', text: CANARY }] }, finishReason: 'toolUse',
                usage: { input: 900, output: 10, cacheRead: 100, cacheWrite: 0, totalTokens: 1010, cost: { total: 0.001 } } },
  });
  assert.deepEqual(record, { type: 'step_finish', instance: 'run-1', conversation: 'conv_1', error: false, finish: 'toolUse', durationMs: 50,
                             usage: { input: 900, output: 10, cacheRead: 100, cacheWrite: 0, cost: 0.001 } });
  assert.doesNotMatch(JSON.stringify(record), new RegExp(CANARY));
});

test('tool events keep only a known name and a status', () => {
  const record = toRecord({ type: 'tool', toolName: 'bash', isError: true, result: { content: [{ text: CANARY }] },
                            effectiveResult: CANARY, description: CANARY });
  assert.deepEqual(record, { type: 'tool', name: 'bash', status: 'error' });
  assert.deepEqual(toRecord({ type: 'tool', toolName: CANARY }), { type: 'tool', name: 'other', status: 'completed' });
});

test('content-bearing and unknown events are dropped; unknown labels are normalized', () => {
  for (const type of ['turn_request', 'turn_messages', 'message_end', 'text_delta', 'operation', 'log', 'agent_start'])
    assert.equal(toRecord({ type, text: CANARY }), null);
  assert.deepEqual(toRecord({ type: 'submission_settled', outcome: CANARY, error: { message: CANARY } }),
                   { type: 'settled', outcome: 'other' });
  assert.equal(toRecord({ type: 'turn', response: { finishReason: CANARY } }).finish, 'other');
  assert.deepEqual(toRecord({ type: 'compaction_start' }), { type: 'compaction' });
});
