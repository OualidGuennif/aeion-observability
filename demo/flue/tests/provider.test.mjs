import test from 'node:test';
import assert from 'node:assert/strict';
import { modelFromEnv } from '../src/provider.ts';

const env = {
  AEION_RELAY_URL: 'http://127.0.0.1:43210/v1', AEION_RELAY_TOKEN: 'relay-only',
  AEION_MODEL_JSON: JSON.stringify({ id: 'glm-5.3-flash', name: 'GLM 5.3 Flash', context: 1000000, input: 0.15, output: 0.5, cacheRead: 0.03 }),
};

test('the model targets the loopback relay with counted, role-compatible requests', () => {
  const model = modelFromEnv(env);
  assert.equal(model.baseUrl, env.AEION_RELAY_URL);
  assert.equal(model.maxTokens, 4096);
  assert.deepEqual(model.compat, { supportsDeveloperRole: false, supportsStore: false, supportsReasoningEffort: false,
                                   supportsUsageInStreaming: true, maxTokensField: 'max_tokens' });
  assert.deepEqual(model.cost, { input: 0.15, output: 0.5, cacheRead: 0.03, cacheWrite: 0 });
});

test('a non-loopback endpoint, a missing token or missing metadata is refused', () => {
  assert.throws(() => modelFromEnv({ ...env, AEION_RELAY_URL: 'https://opencode.ai/inference/go/openai/v1' }));
  assert.throws(() => modelFromEnv({ ...env, AEION_RELAY_TOKEN: '' }));
  assert.throws(() => modelFromEnv({ ...env, AEION_MODEL_JSON: '{}' }));
});
