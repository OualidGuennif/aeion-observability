'use agent';
// Case 1: triage in an emulated shell over an in-memory filesystem, rebuilt for each session.
// No host files, processes, network, Python or JavaScript; the only output is submit_triage.
// Same relay and observer as the other cases. No compaction: continuity is HANDOVER.md.
import { bash, useModel, useSandbox, useTool } from '@flue/runtime';
import { Bash, InMemoryFs } from 'just-bash';
import { observeToFile } from '../observe.ts';
import { registerProvider } from '../provider.ts';
import { submitTriage, triageFromEnv } from '../tools/submit-triage.ts';

const model = registerProvider();
observeToFile();
const { input, resultFile } = triageFromEnv();
const submit = submitTriage(input, resultFile);

export function Triage() {
  useModel(model, { compaction: false });
  useSandbox(bash(() => new Bash({
    fs: new InMemoryFs({ '/data/events.json': JSON.stringify(input.events, null, 2) + '\n' }),
    cwd: '/data',
    executionLimitProfile: 'hardened',
  })));
  useTool(submit);
  return [
    'You are a triage agent working in an emulated shell over an in-memory filesystem.',
    'Inspect /data/events.json with the shell and file tools, apply the rules in the user message,',
    'then submit the complete result with the submit_triage tool. Your reply does not decide acceptance.',
  ].join('\n');
}
