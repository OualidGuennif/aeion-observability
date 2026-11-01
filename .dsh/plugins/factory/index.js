// Spec: knowledge/operations/agent-compatibility.md
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { seam } from './seam.js';

export const name = 'aeion-factory';
export const inject = ['tools', 'tokenMeter', 'workingDirectory'];

const UNAVAILABLE = 'Æion Factory hook unavailable; action refused.';
const RESUME = 'Æion Factory: context compacted. Read your handover in work/handovers/ and continue the task.';
const ASK = 'This dsh profile lets only the user compact: ask them to type /compact now, then wait.';
// dsh's built-in tools under the names the shared guards know; glob only lists paths.
const TOOLS = { bash: 'Bash', read: 'Read', write: 'Write', edit: 'Edit', str_replace_editor: 'Edit', glob: 'Glob', grep: 'Grep' };

// A local file tool reads the project's own text; any other result may have come from outside.
const LOCAL = new Set(['Read', 'Grep', 'Glob', 'LS', 'Edit', 'Write', 'MultiEdit', 'NotebookEdit']);
// The hook refuses a payload over 2 MB; a larger result is not forwarded rather than truncated mid-text.
const MAX_RESULT = 256 * 1024;

// A session may work in a subfolder (demo/), so the hooks live in the nearest folder above that has them;
// a session outside any Æion Factory project has none, and the plugin leaves it alone.
function projectRoot(directory) {
  for (let folder = resolve(directory); ; folder = dirname(folder)) {
    if (existsSync(resolve(folder, 'tools/agents/hook.py'))) return folder;
    if (dirname(folder) === folder) return undefined;
  }
}

function invoke(root, event) {
  const result = spawnSync('python3', [resolve(root, 'tools/agents/hook.py'), 'dsh'], {
    cwd: root, input: JSON.stringify(event), encoding: 'utf8', timeout: 15000, maxBuffer: 128 * 1024,
  });
  if (result.error || result.status !== 0) throw new Error(UNAVAILABLE);
  const output = JSON.parse(result.stdout);
  const reason = output.stopReason || (output.decision === 'block' && output.reason)
    || (output.hookSpecificOutput?.permissionDecision === 'deny' && output.hookSpecificOutput.permissionDecisionReason);
  return { output, reason };
}

function toolName(exec) {
  const input = exec.arguments || {};
  // str_replace_editor's view command only reads; an unknown tool with a command string is a shell call.
  if (exec.name === 'str_replace_editor' && input.command === 'view') return 'Read';
  if (!(exec.name in TOOLS) && typeof input.command === 'string') return 'Bash';
  return TOOLS[exec.name] || exec.name;
}

export function apply(ctx) {
  // Each session's own directory, not the launch folder: one dsh web server serves many projects.
  const rootOf = (agent) => projectRoot(ctx.workingDirectory.get(agent.session));
  // Sessions given the factory's start context; a compaction removes one, so its next call is told again.
  const started = new Set();
  const compacted = new Set();
  // Agents whose verified handover asked for a compaction; it runs before their next model step.
  const due = new Set();

  // The last measure per session: a fall to under half means the user compacted (/compact), so its next call
  // is told the start context again as after a compaction.
  const last = new Map();

  const tokens = (agent) => ctx.tokenMeter.measure(agent.session).totalTokens;

  function observe(agent) {
    const session = agent.session.id;
    const now = tokens(agent);
    if (last.get(session) > 2 * now && started.has(session)) {
      started.delete(session);
      compacted.add(session);
    }
    last.set(session, now);
  }

  // The factory's start context reaches the model as steering: dsh has no hook that adds it to the prompt.
  const say = (agent, text) => agent.steer({ id: globalThis.crypto.randomUUID(), content: [{ type: 'text', text }], source: { kind: 'aeion-factory' } });

  function start(root, agent) {
    const session = agent.session.id;
    if (started.has(session)) return;
    const source = compacted.has(session) ? 'compact' : 'startup';
    const { output, reason } = invoke(root, { session_id: session, hook_event_name: 'SessionStart', source });
    if (reason) throw new Error(reason);
    started.add(session);
    compacted.delete(session);
    const context = output.hookSpecificOutput?.additionalContext;
    if (context) say(agent, context);
  }

  function toolEvent(exec, name, result) {
    const tool = toolName(exec);
    const event = {
      session_id: exec.agent.session.id, hook_event_name: name, tool_use_id: exec.callId,
      tool_name: tool, tool_input: exec.arguments,
      // dsh's own replay-based measure feeds the shared 250k/300k rule.
      observed_tokens: tokens(exec.agent),
    };
    // Any result a local file tool did not produce is forwarded; the adapter decides what reads outside.
    if (result !== undefined && !LOCAL.has(tool)) {
      try {
        if (JSON.stringify(result).length <= MAX_RESULT) event.tool_response = result;
      } catch { /* a result that cannot be serialized carries no text to scan */ }
    }
    return event;
  }

  // A synchronous guard runs after every other pre-execute policy, and nothing later can undo its denial.
  ctx.tools.guard((exec) => {
    // A call without an agent has no session to account it to, so it is refused.
    if (!exec.agent) return UNAVAILABLE;
    try {
      const root = rootOf(exec.agent);
      if (!root) return undefined;
      observe(exec.agent);
      start(root, exec.agent);
      return invoke(root, toolEvent(exec, 'PreToolUse')).reason || undefined;
    } catch (error) {
      return error.message || UNAVAILABLE;
    }
  });

  ctx.on('tools/post-execute', async (exec, result, next) => {
    const downstream = await next();
    if (!exec.agent || result?.isError) return downstream;
    try {
      const root = rootOf(exec.agent);
      if (!root) return downstream;
      const { output } = invoke(root, toolEvent(exec, 'PostToolUse', result));
      if (output.aeion?.compact) due.add(exec.agent);
      // A PostToolUse warning (token feedback, prompt defense) reaches the model as a system note.
      const context = output.hookSpecificOutput?.additionalContext;
      if (context) say(exec.agent, context);
    } catch (error) {
      ctx.logger?.warn?.(`aeion-factory: ${error.message || UNAVAILABLE}`);
    }
    return downstream;
  });

  // The turn's close is the factory's Stop: a sign-off finding steers one more step; the hook shows each
  // finding once per session, so a second close passes. `continue: false` is the hook's terminal stop, and
  // steering it would start another turn that closes the same way.
  ctx.on('agent/turn-stopping', async ({ agent }) => {
    try {
      const root = rootOf(agent);
      if (!root) return;
      const { output, reason } = invoke(root, { session_id: agent.session.id, hook_event_name: 'Stop' });
      if (reason && output.continue !== false) say(agent, reason);
    } catch (error) {
      ctx.logger?.warn?.(`aeion-factory: ${error.message || UNAVAILABLE}`);
    }
  });

  // A verified handover past 250k compacts now, not at dsh's own threshold near the model window.
  ctx.on('agent/pre-step', async ({ agent, signal }, next) => {
    if (!due.has(agent) || signal.aborted) return next();
    due.delete(agent);
    const session = agent.session.id;
    try {
      const root = rootOf(agent);
      // The shared rule refuses the compaction unless the checkpoint is verified, and allows it at 300k with the
      // closure owed; its own words say which, so they reach the user instead of a fixed "verified" claim.
      const { output, reason } = invoke(root, { session_id: session, hook_event_name: 'PreCompact' });
      if (reason) return next();
      // The web profile keeps compaction inside each agent preset, out of a plugin's reach: the user compacts.
      if (!seam.compaction) {
        say(agent, `${output.systemMessage || 'Æion Factory: closure pending.'} ${ASK}`);
        return next();
      }
      // dsh's overflow path compacts now whatever its own threshold; it is the step-time compaction dsh exposes.
      await seam.compaction.compactIfNeeded(agent, 'context-overflow', signal);
      started.delete(session);
      compacted.add(session);
      say(agent, RESUME);
    } catch (error) {
      ctx.logger?.warn?.(`aeion-factory: compaction failed: ${error.message}`);
    }
    return next();
  });
}
