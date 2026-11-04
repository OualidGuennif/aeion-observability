// The model can request the supervisor's fixed check, never choose its command or evaluator.
import { defineTool } from '@flue/runtime';
import * as v from 'valibot';
import { bridgeFromEnv } from '../sandboxes/openshell.ts';

export function factoryChecks() {
  const config = bridgeFromEnv();
  return defineTool({
    name: 'run_protected_checks',
    description: 'Snapshot the current scoped artifact and run its fixed independent checks. Returns bounded diagnostics and an artifact digest.',
    input: v.strictObject({}),
    async run() {
      const response = await fetch(`${config.url}/v1/check`, {
        method: 'POST',
        headers: { authorization: `Bearer ${config.token}`, 'content-type': 'application/json' },
        body: '{}',
      });
      const result = await response.json();
      if (!response.ok || result.ok !== true) throw new Error('Protected check unavailable');
      return JSON.stringify(result.result);
    },
  });
}
