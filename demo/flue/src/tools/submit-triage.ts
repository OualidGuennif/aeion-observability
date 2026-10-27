// Tier 1 output channel: the only way a triage result leaves the in-memory sandbox. Calls are
// validated against the supplied event ids and label vocabulary, then written atomically on
// the host for the supervisor's independent check.
import { readFileSync, renameSync, writeFileSync } from 'node:fs';
import { defineTool } from '@flue/runtime';
import * as v from 'valibot';

export type TriageInput = {
  labels: { severity: string[]; component: string[]; route: string[] };
  events: { id: string }[];
};

export function triageFromEnv(env: NodeJS.ProcessEnv = process.env) {
  if (!env.AEION_TRIAGE_INPUT?.startsWith('/')) throw new Error('AEION_TRIAGE_INPUT must be an absolute path');
  if (!env.AEION_RESULT_FILE?.startsWith('/')) throw new Error('AEION_RESULT_FILE must be an absolute path');
  const input: TriageInput = JSON.parse(readFileSync(env.AEION_TRIAGE_INPUT, 'utf-8'));
  return { input, resultFile: env.AEION_RESULT_FILE };
}

export function submitTriage(input: TriageInput, resultFile: string) {
  const ids = input.events.map((event) => event.id);
  const id = v.picklist(ids);
  return defineTool({
    name: 'submit_triage',
    description: 'Submit the complete triage: exactly one result per event. A later call replaces the previous submission.',
    input: v.object({
      results: v.array(v.strictObject({
        id,
        severity: v.picklist(input.labels.severity),
        component: v.picklist(input.labels.component),
        route: v.picklist(input.labels.route),
        duplicate_of: v.nullable(id),
      })),
    }),
    run({ data }) {
      const seen = new Set(data.results.map((result) => result.id));
      if (seen.size !== data.results.length) throw new Error('Each event id must appear exactly once');
      const missing = ids.filter((event) => !seen.has(event));
      if (missing.length) throw new Error(`Missing results for: ${missing.join(', ')}`);
      const temporary = `${resultFile}.tmp`;
      writeFileSync(temporary, JSON.stringify({ results: data.results }) + '\n', { mode: 0o644 });
      renameSync(temporary, resultFile);
      return `Recorded ${data.results.length} results.`;
    },
  });
}
