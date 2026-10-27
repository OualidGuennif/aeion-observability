'use agent';
// Case 2: guided local assistant. File tools only, confined to the run workspace on the
// host (no shell); a strict skill fixes the procedure. Same relay, observer and protected
// checks as case 3. No compaction: continuity is the supervisor's HANDOVER.md.
import { useModel, useSandbox, useSkill } from '@flue/runtime';
import { observeToFile } from '../observe.ts';
import { registerProvider } from '../provider.ts';
import { restrictedLocal } from '../sandboxes/restricted-local.ts';
import localChange from '../skills/local-change/SKILL.md';

const model = registerProvider();
observeToFile();

export function LocalAssistant() {
  useModel(model, { compaction: false });
  useSandbox(restrictedLocal());
  useSkill(localChange);
  return [
    'You are a guided local assistant working in a restricted workspace folder.',
    'Activate the `local-change` skill before any other action and follow it exactly.',
    'Complete the task described in the user message; protected checks run after you stop.',
  ].join('\n');
}
