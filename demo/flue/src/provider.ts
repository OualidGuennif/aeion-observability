// OpenCode Go through the supervisor's counting relay. The real Go key never
// reaches this process: the relay token authenticates to the relay only.
import { createProvider } from '@earendil-works/pi-ai';
import { openAICompletionsApi } from '@earendil-works/pi-ai/api/openai-completions.lazy';
import { anthropicMessagesApi } from '@earendil-works/pi-ai/api/anthropic-messages.lazy';
import { setProvider } from '@flue/runtime';

export const PROVIDER_ID = 'opencode-go';

type ModelMetadata = {
  id: string;
  name: string;
  context: number;
  input: number;
  output: number;
  cacheRead: number;
  cacheWrite?: number;
  api?: 'openai-completions' | 'anthropic-messages';
  thinking?: 'max';
  maxOutputTokens?: number;
};

// Native effort names per model. Agents use only 'max', or 'low' for a bounded review recovery.
const MAX_THINKING: Record<string, Record<string, string>> = {
  'deepseek-v4.1-flash': { minimal: 'low', low: 'low', medium: 'high', high: 'high', xhigh: 'max', max: 'max' },
  'glm-5.3-flash': { minimal: 'low', low: 'low', medium: 'high', high: 'high', xhigh: 'max', max: 'max' },
  'claude-haiku-5-5': { xhigh: 'max', max: 'max' },
  'qwen3.8-flash': { xhigh: 'max', max: 'max' },
  // Measured 2026-11-06: GPT-6 Luna accepts reasoning_effort "max"; Mistral Large 4 tops out at "high".
  'gpt-6-luna': { minimal: 'low', low: 'low', medium: 'medium', high: 'high', xhigh: 'max', max: 'max' },
  'mistral-large-4': { minimal: 'low', low: 'low', medium: 'high', high: 'high', xhigh: 'high', max: 'high' },
};
const OPENAI_EFFORT = new Set(['gpt-6-luna', 'mistral-large-4']);
const ADAPTIVE = new Set(['claude-haiku-5-5', 'qwen3.8-flash']);

export function modelFromEnv(env: NodeJS.ProcessEnv = process.env) {
  const relayUrl = env.AEION_RELAY_URL;
  if (!relayUrl || !/^http:\/\/127\.0\.0\.1:\d+\/v1$/.test(relayUrl)) throw new Error('AEION_RELAY_URL must be the loopback relay');
  if (!env.AEION_RELAY_TOKEN) throw new Error('AEION_RELAY_TOKEN is required');
  const meta: ModelMetadata = JSON.parse(env.AEION_MODEL_JSON ?? 'null');
  if (!meta || typeof meta.id !== 'string' || !Number.isSafeInteger(meta.context)) throw new Error('AEION_MODEL_JSON is invalid');
  const api = meta.api ?? 'openai-completions';
  if (!['openai-completions', 'anthropic-messages'].includes(api)) throw new Error('Unsupported model protocol');
  const maxOutputTokens = meta.maxOutputTokens === undefined ? 4096 : meta.maxOutputTokens;
  if (!Number.isSafeInteger(maxOutputTokens) || maxOutputTokens < 1 || maxOutputTokens > 65536) {
    throw new Error('Supervisor output bound invalid');
  }
  const session = env.AEION_CONVERSATION_ID;
  if (api === 'anthropic-messages' && (!session || !/^[a-zA-Z0-9-]{1,100}$/.test(session))) {
    throw new Error('Supervisor conversation identity required');
  }
  return {
    id: meta.id,
    name: meta.name,
    api,
    provider: PROVIDER_ID,
    // Anthropic SDK appends /v1/messages; the OpenAI SDK appends /chat/completions.
    baseUrl: api === 'anthropic-messages' ? relayUrl.slice(0, -3) : relayUrl,
    ...(api === 'anthropic-messages' ? { headers: { 'x-opencode-session': session! } } : {}),
    // Reasoning is replayed as reasoning_content. Every authorized model declares its native
    // maximum so the agents' 'max' level reaches the provider instead of being clamped down.
    // Measured 2026-11-06 on the paid Go endpoint: GLM and DeepSeek accept reasoning_effort
    // "max"; Haiku and Qwen accept adaptive thinking with output_config.effort "max".
    reasoning: true,
    input: ['text' as const],
    cost: { input: meta.input, output: meta.output, cacheRead: meta.cacheRead, cacheWrite: meta.cacheWrite ?? 0 },
    contextWindow: meta.context,
    maxTokens: maxOutputTokens,
    thinkingLevelMap: MAX_THINKING[meta.id] ?? {},
    compat: api === 'anthropic-messages' ? {
      forceAdaptiveThinking: ADAPTIVE.has(meta.id),
      supportsTemperature: meta.id !== 'claude-haiku-5-5',
    } : {
      supportsDeveloperRole: false,
      supportsStore: false,
      supportsReasoningEffort: meta.id in MAX_THINKING,
      ...(meta.id === 'deepseek-v4.1-flash' ? { thinkingFormat: 'deepseek' as const } : {}),
      // GLM honors reasoning_effort only beside its Z.ai thinking object (measured 2026-11-06).
      ...(meta.id === 'glm-5.3-flash' ? { thinkingFormat: 'zai' as const } : {}),
      ...(OPENAI_EFFORT.has(meta.id) ? { thinkingFormat: 'openai' as const } : {}),
      supportsUsageInStreaming: true,
      maxTokensField: 'max_tokens' as const,
    },
  };
}

export function registerProvider(env: NodeJS.ProcessEnv = process.env) {
  const model = modelFromEnv(env);
  const token = env.AEION_RELAY_TOKEN;
  setProvider(createProvider({
    id: PROVIDER_ID,
    name: 'OpenCode Go via AEion relay',
    baseUrl: model.baseUrl,
    auth: { apiKey: { name: 'AEion relay token', resolve: async () => ({ auth: { apiKey: token } }) } },
    models: [model],
    api: model.api === 'anthropic-messages' ? anthropicMessagesApi() : openAICompletionsApi(),
  }));
  return `${PROVIDER_ID}/${model.id}`;
}
