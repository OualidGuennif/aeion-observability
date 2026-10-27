// Metadata-only event stream for the supervisor. Runtime events also carry prompts,
// model output, tool arguments and results; none of those fields are ever copied.
import { closeSync, openSync, writeSync } from 'node:fs';
import { observe } from '@flue/runtime';

// `task` is always listed by Flue; with no declared subagent every delegation is refused.
const TOOLS = new Set(['read', 'write', 'edit', 'bash', 'grep', 'glob', 'task']);
const FINISH = new Set(['stop', 'toolUse', 'length', 'error', 'aborted']);
const OUTCOMES = new Set(['completed', 'failed', 'aborted']);

const count = (value: unknown) => (typeof value === 'number' ? value : null);

export function toRecord(event: any): Record<string, unknown> | null {
  switch (event?.type) {
    case 'turn_start':
      return { type: 'step_start' };
    case 'turn': {
      const usage = event.response?.usage;
      const finish = event.response?.finishReason;
      return {
        type: 'step_finish',
        instance: typeof event.instanceId === 'string' ? event.instanceId : null,
        conversation: typeof event.conversationId === 'string' ? event.conversationId : null,
        error: event.isError === true,
        finish: FINISH.has(finish) ? finish : 'other',
        durationMs: count(event.durationMs),
        usage: usage
          ? { input: count(usage.input), output: count(usage.output), cacheRead: count(usage.cacheRead),
              cacheWrite: count(usage.cacheWrite), cost: count(usage.cost?.total) }
          : null,
      };
    }
    case 'tool':
      return { type: 'tool', name: TOOLS.has(event.toolName) ? event.toolName : 'other',
               status: event.isError === true ? 'error' : 'completed' };
    case 'compaction_start':
    case 'compaction':
      return { type: 'compaction' };
    case 'submission_settled':
      return { type: 'settled', outcome: OUTCOMES.has(event.outcome) ? event.outcome : 'other' };
    default:
      return null;
  }
}

export function observeToFile(path: string | undefined = process.env.AEION_EVENTS_FILE) {
  if (!path) throw new Error('AEION_EVENTS_FILE is required');
  const fd = openSync(path, 'a', 0o600);
  const stop = observe((event) => {
    const record = toRecord(event);
    if (record) writeSync(fd, JSON.stringify(record) + '\n');
  });
  return () => { stop(); closeSync(fd); };
}
