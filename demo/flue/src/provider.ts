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
  thinking?: 'medium';
  maxOutputTokens?: number;
};

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
    // Reasoning is replayed as reasoning_content. DeepSeek has an explicit native
    // effort mapping below; other OpenAI-compatible models retain their provider defaults.
    reasoning: true,
    input: ['text' as const],
    cost: { input: meta.input, output: meta.output, cacheRead: meta.cacheRead, cacheWrite: meta.cacheWrite ?? 0 },
    contextWindow: meta.context,
    maxTokens: maxOutputTokens,
    ...(meta.id === 'deepseek-v4.1-flash' ? { thinkingLevelMap: {
      minimal: 'low', low: 'low', medium: 'high', high: 'high', xhigh: 'high', max: 'max',
    } as const } : {}),
    compat: api === 'anthropic-messages' ? {
      forceAdaptiveThinking: meta.id === 'claude-haiku-5-5',
      supportsTemperature: meta.id !== 'claude-haiku-5-5',
    } : {
      supportsDeveloperRole: false,
      supportsStore: false,
      supportsReasoningEffort: meta.id === 'deepseek-v4.1-flash',
      ...(meta.id === 'deepseek-v4.1-flash' ? { thinkingFormat: 'deepseek' as const } : {}),
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
