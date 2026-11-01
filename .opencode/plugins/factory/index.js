// Spec: knowledge/operations/agent-compatibility.md
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

function invoke(root, event) {
  const result = spawnSync('python3', [resolve(root, 'tools/agents/hook.py'), 'opencode'], {
    cwd: root, input: JSON.stringify(event), encoding: 'utf8', timeout: 15000, maxBuffer: 128 * 1024,
  });
  if (result.error || result.status !== 0) throw new Error('Æion Factory hook unavailable; action refused.');
  const output = JSON.parse(result.stdout);
  const reason = output.stopReason || (output.decision === 'block' && output.reason)
    || (output.hookSpecificOutput?.permissionDecision === 'deny' && output.hookSpecificOutput.permissionDecisionReason);
  return { output, reason };
}

// OpenCode may start in a subfolder (demo/), so the hooks live in the nearest folder above that has them.
function projectRoot(directory) {
  for (let folder = resolve(directory); ; folder = dirname(folder)) {
    if (existsSync(resolve(folder, 'tools/agents/hook.py'))) return folder;
    if (dirname(folder) === folder) return directory;
  }
}

function toolEvent(event, name, usage) {
  return {
    session_id: event.sessionID, hook_event_name: name,
    tool_use_id: event.id,
    tool_name: ({ bash: 'Bash', shell: 'Bash', read: 'Read', grep: 'Grep', edit: 'Edit', write: 'Write' })[event.tool] || event.tool,
    tool_input: event.input,
    // The last step's tokens feed the shared 250k/300k rule; null until OpenCode reports a step.
    observed_tokens: usage.get(event.sessionID) ?? null,
  };
}

// A step's prompt, cache and answer are the context the next step starts from.
function contextTokens(tokens) {
  const cache = tokens.cache || { read: tokens.cacheRead, write: tokens.cacheWrite };
  return [tokens.input, tokens.output, cache.read, cache.write].reduce((sum, value) => sum + (Number.isInteger(value) ? value : 0), 0);
}

// OpenCode reports each step's tokens when the step ends; the newest one is the session's context size.
async function measure(ctx, usage) {
  try {
    for await (const event of ctx.event.subscribe({ types: ['session.step.ended'] })) {
      if (event.data?.sessionID && event.data.tokens) usage.set(event.data.sessionID, contextTokens(event.data.tokens));
    }
  } catch {
    // Without the stream the shared rule keeps the last count, and native compaction still needs a verified handover.
  }
}

export default {
  id: 'aeion.factory',
  async setup(ctx) {
    const root = projectRoot(ctx.location.directory);
    const usage = new Map();
    const compacting = new Set();
    if (ctx.event?.subscribe) measure(ctx, usage);
    await ctx.session.hook('prompt', async (event) => {
      const { reason } = invoke(root, { session_id: event.sessionID, hook_event_name: 'SessionStart', source: 'startup' });
      if (reason) throw new Error(reason);
    });
    await ctx.tool.hook('execute.before', async (event) => {
      const { reason } = invoke(root, toolEvent(event, 'PreToolUse', usage));
      if (reason) throw new Error(reason);
    });
    await ctx.tool.hook('execute.after', async (event) => {
      if (event.status !== 'completed') return;
      const { reason, output } = invoke(root, toolEvent(event, 'PostToolUse', usage));
      // A verified handover past 250k compacts now, not when the model window is nearly full.
      if (output.aeion?.compact && !compacting.has(event.sessionID)) {
        compacting.add(event.sessionID);
        await ctx.session.compact({ sessionID: event.sessionID });
      }
      const message = reason || output.hookSpecificOutput?.additionalContext;
      if (!message) return;
      const content = event.result.content;
      const parts = typeof content === 'string' ? [{ type: 'text', text: content }] : [...(content || [])];
      event.result = { ...event.result, content: [...parts, { type: 'text', text: `Æion Factory feedback: ${message}` }] };
    });
    await ctx.session.hook('compaction', async (event) => {
      const { reason, output } = invoke(root, { session_id: event.sessionID, hook_event_name: 'PreCompact' });
      if (reason) throw new Error(reason);
      compacting.delete(event.sessionID);
      usage.delete(event.sessionID);
      event.system.push({ type: 'text', text: `${output.systemMessage}. Recover from this handover and read AGENTS.md.` });
    });
  },
};
