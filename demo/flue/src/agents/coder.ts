'use agent';
// Case 3: autonomous coding. Tools run only inside the supervisor's OpenShell sandbox;
// model calls go through the counting relay. No compaction: context continuity is the
// supervisor's HANDOVER.md, delivered to a fresh session in the user message.
import { useModel, useSandbox, useTool } from '@flue/runtime';
import { observeToFile } from '../observe.ts';
import { registerProvider } from '../provider.ts';
import { openshell } from '../sandboxes/openshell.ts';
import { factoryChecks } from '../tools/factory-checks.ts';

const model = registerProvider();
observeToFile();

export function Coder() {
  useModel(model, { compaction: false, thinkingLevel: 'medium' });
  useSandbox(openshell());
  if (process.env.AEION_FACTORY_BUILD === '1') useTool(factoryChecks());
  return [
    'You are a coding agent working in a sandboxed workspace.',
    'Complete the task described in the user message using the file and shell tools.',
    'Follow the task constraints exactly; protected checks run after you stop.',
    // The same five rules as demo/factory/boundary.py; test_factory_boundary.py proves it.
    'Work only inside your workspace and only inside the write scope named in the task.',
    'Commit to your own branch only: push nothing, open no pull request, merge nothing.',
    'Never review your own work. Two models from other families review it after you stop.',
    "Stop when the task's checks pass, or when you cannot continue; say why in HANDOVER.md.",
    "Do not wait for a reviewer, do not poll for one, and never merge on anyone's behalf.",
    'Stop now and end your turn: no push, no pull request, no review, no merge.',
  ].join('\n');
}
