// OpenCode Go through the supervisor's counting relay. The real Go key never
// reaches this process: the relay token authenticates to the relay only.
import { createProvider } from '@earendil-works/pi-ai';
import { openAICompletionsApi } from '@earendil-works/pi-ai/api/openai-completions.lazy';
import { setProvider } from '@flue/runtime';

export const PROVIDER_ID = 'opencode-go';

type ModelMetadata = {
  id: string;
  name: string;
  context: number;
  input: number;
  output: number;
  cacheRead: number;
};

export function modelFromEnv(env: NodeJS.ProcessEnv = process.env) {
  const relayUrl = env.AEION_RELAY_URL;
  if (!relayUrl || !/^http:\/\/127\.0\.0\.1:\d+\/v1$/.test(relayUrl)) throw new Error('AEION_RELAY_URL must be the loopback relay');
  if (!env.AEION_RELAY_TOKEN) throw new Error('AEION_RELAY_TOKEN is required');
  const meta: ModelMetadata = JSON.parse(env.AEION_MODEL_JSON ?? 'null');
  if (!meta || typeof meta.id !== 'string' || !Number.isSafeInteger(meta.context)) throw new Error('AEION_MODEL_JSON is invalid');
  return {
    id: meta.id,
    name: meta.name,
    api: 'openai-completions' as const,
    provider: PROVIDER_ID,
    baseUrl: relayUrl,
    // Matches the previous OpenCode catalog: reasoning is returned and replayed
    // as reasoning_content; no effort parameter is sent, so the model default applies.
    reasoning: true,
    input: ['text' as const],
    cost: { input: meta.input, output: meta.output, cacheRead: meta.cacheRead, cacheWrite: 0 },
    contextWindow: meta.context,
    maxTokens: 4096,
    compat: {
      supportsDeveloperRole: false,
      supportsStore: false,
      supportsReasoningEffort: false,
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
    api: openAICompletionsApi(),
  }));
  return `${PROVIDER_ID}/${model.id}`;
}
