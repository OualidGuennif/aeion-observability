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
  assert.deepEqual(model.compat, { supportsDeveloperRole: false, supportsStore: false, supportsReasoningEffort: true,
                                   thinkingFormat: 'zai', supportsUsageInStreaming: true, maxTokensField: 'max_tokens' });
  assert.deepEqual(model.cost, { input: 0.15, output: 0.5, cacheRead: 0.03, cacheWrite: 0 });
});

test('only a bounded supervisor setting can increase the output window', () => {
  const meta=JSON.parse(env.AEION_MODEL_JSON);
  assert.equal(modelFromEnv({...env,AEION_MODEL_JSON:JSON.stringify({...meta,maxOutputTokens:65536})}).maxTokens,65536);
  for(const value of [0,65537,true,Infinity]) {
    assert.throws(()=>modelFromEnv({...env,AEION_MODEL_JSON:JSON.stringify({...meta,maxOutputTokens:value})}));
  }
});

test('a non-loopback endpoint, a missing token or missing metadata is refused', () => {
  assert.throws(() => modelFromEnv({ ...env, AEION_RELAY_URL: 'https://opencode.ai/inference/go/openai/v1' }));
  assert.throws(() => modelFromEnv({ ...env, AEION_RELAY_TOKEN: '' }));
  assert.throws(() => modelFromEnv({ ...env, AEION_MODEL_JSON: '{}' }));
});

test('Anthropic SDK appends /v1/messages once and retains the supervisor session', () => {
  const model = modelFromEnv({ ...env, AEION_CONVERSATION_ID: 'fixture-review-1',
    AEION_MODEL_JSON: JSON.stringify({ id: 'qwen3.8-flash', name: 'Qwen', context: 1000000,
      api: 'anthropic-messages', input: 0.15, output: 0.47, cacheRead: 0.016, cacheWrite: 0.2 }) });
  assert.equal(model.baseUrl, 'http://127.0.0.1:43210');
  assert.equal(model.headers['x-opencode-session'], 'fixture-review-1');
});

test('DeepSeek declares its native thinking protocol and explicit effort mapping', () => {
  const model=modelFromEnv({...env,AEION_MODEL_JSON:JSON.stringify({
    ...JSON.parse(env.AEION_MODEL_JSON),id:'deepseek-v4.1-flash'})});
  assert.equal(model.compat.thinkingFormat,'deepseek');
  assert.equal(model.compat.supportsReasoningEffort,true);
  assert.equal(model.thinkingLevelMap.low,'low');
  assert.equal(model.thinkingLevelMap.medium,'high');
});

test('every authorized model maps the agents\' max level to its native maximum', () => {
  const meta = JSON.parse(env.AEION_MODEL_JSON);
  const anthropic = { api: 'anthropic-messages', cacheWrite: 0.2 };
  for (const [id, extra, adaptive] of [['glm-5.3-flash', {}, false], ['deepseek-v4.1-flash', {}, false],
    ['claude-haiku-5-5', anthropic, true], ['qwen3.8-flash', anthropic, true]]) {
    const model = modelFromEnv({ ...env, AEION_CONVERSATION_ID: 'fixture-1',
      AEION_MODEL_JSON: JSON.stringify({ ...meta, id, ...extra }) });
    assert.equal(model.thinkingLevelMap.max, 'max', id);
    if (adaptive) assert.equal(model.compat.forceAdaptiveThinking, true, id);
    else assert.equal(model.compat.supportsReasoningEffort, true, id);
  }
});
