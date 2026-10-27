'use agent';
// Case 3: autonomous coding. Tools run only inside the supervisor's OpenShell sandbox;
// model calls go through the counting relay. No compaction: context continuity is the
// supervisor's HANDOVER.md, delivered to a fresh session in the user message.
import { useModel, useSandbox } from '@flue/runtime';
import { observeToFile } from '../observe.ts';
import { registerProvider } from '../provider.ts';
import { openshell } from '../sandboxes/openshell.ts';

const model = registerProvider();
observeToFile();

export function Coder() {
  useModel(model, { compaction: false });
  useSandbox(openshell());
  return [
    'You are a coding agent working in a sandboxed workspace.',
    'Complete the task described in the user message using the file and shell tools.',
    'Follow the task constraints exactly; protected checks run after you stop.',
  ].join('\n');
}
