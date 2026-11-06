// Spec: knowledge/components/factory-flue.md
// The author's owner-only note leaves the sandbox through the supervisor bridge, never a file.
import { defineTool } from '@flue/runtime';
import * as v from 'valibot';
import { FEEDBACK_LIMIT } from '../context.ts';
import { bridgeFromEnv } from '../sandboxes/openshell.ts';

let submitted = false;

export function feedbackSubmitted() {
  return submitted;
}

export const FEEDBACK_REMINDER = 'You have not left owner feedback. Use submit_feedback once with "RAS" '
  + 'or a short note on your difficulties, then stop.';

export function submitFeedback() {
  const config = bridgeFromEnv();
  return defineTool({
    name: 'submit_feedback',
    description: 'Leave your owner-only feedback before you stop: "RAS" or a short note on difficulties.',
    input: v.strictObject({ text: v.pipe(v.string(), v.minLength(1), v.maxLength(FEEDBACK_LIMIT)) }),
    async run({ data }) {
      const response = await fetch(`${config.url}/v1/feedback`, {
        method: 'POST',
        headers: { authorization: `Bearer ${config.token}`, 'content-type': 'application/json' },
        body: JSON.stringify({ text: data.text }),
      });
      const result = await response.json();
      if (!response.ok || result.ok !== true) throw new Error('Feedback not recorded');
      submitted = true;
      return 'Feedback recorded.';
    },
  });
}
