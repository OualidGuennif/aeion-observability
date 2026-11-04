// Only this typed verdict leaves the review sandbox; its path is set by the supervisor.
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { defineTool } from '@flue/runtime';
import * as v from 'valibot';

export function submitReview(resultFile: string) {
  if (!resultFile.startsWith('/')) throw new Error('Absolute supervisor result path required');
  return defineTool({
    name: 'submit_review',
    description: 'Submit your independent verdict on the complete frozen artifact. A rejection blocks publication.',
    input: v.strictObject({ verdict: v.picklist(['approve', 'reject']),
      reason: v.pipe(v.string(), v.maxLength(120)) }),
    run({ data }) {
      if (existsSync(resultFile)) {
        if (readFileSync(resultFile, 'utf-8') !== JSON.stringify(data)) throw new Error('Review is immutable');
        return 'Review already recorded.';
      }
      writeFileSync(resultFile, JSON.stringify(data), { mode: 0o600, flag: 'wx' });
      return 'Review recorded.';
    },
  });
}
