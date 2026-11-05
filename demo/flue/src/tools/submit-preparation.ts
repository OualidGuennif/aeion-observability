// Spec: knowledge/components/factory-flue.md
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { defineTool } from '@flue/runtime';
import * as v from 'valibot';

export function submitPreparation(resultFile: string) {
  if (!resultFile.startsWith('/')) throw new Error('Absolute supervisor result path required');
  return defineTool({
    name: 'submit_preparation',
    description: 'Submit one independent protected acceptance file in the frozen task format, or report blocked. Never supply a command.',
    input: v.strictObject({
      status: v.picklist(['ready', 'blocked']),
      contract: v.pipe(v.string(), v.maxLength(48000)),
      reason: v.pipe(v.string(), v.maxLength(120)),
    }),
    run({ data }) {
      const text = JSON.stringify(data);
      if (existsSync(resultFile)) {
        if (readFileSync(resultFile, 'utf-8') !== text) throw new Error('Preparation is immutable');
        return 'Preparation already recorded.';
      }
      writeFileSync(resultFile, text, { mode: 0o600, flag: 'wx' });
      return 'Preparation recorded.';
    },
  });
}
