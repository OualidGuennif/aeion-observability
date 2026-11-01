// Spec: knowledge/operations/agent-compatibility.md
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const UNAVAILABLE = 'Æion Factory hook unavailable; action refused.';
const RESUME = 'Æion Factory: context compacted. Read your handover in work/handovers/ and continue the task.';
// A local file tool reads the project's own text; any other result may have come from outside.
const LOCAL = new Set(['Read', 'Grep', 'Glob', 'LS', 'Edit', 'Write', 'MultiEdit', 'NotebookEdit']);
// The hook refuses a payload over 2 MB; a larger result is not forwarded rather than truncated mid-text.
const MAX_RESULT = 256 * 1024;

// A closure refusal at settlement asks for a few more requests, then settles instead of looping on one alert.
const SETTLE_LIMIT = 3;
// Pi's built-in tools under the names the shared guards know; find and ls only list paths.
const TOOLS = { bash: 'Bash', powershell: 'Bash', read: 'Read', edit: 'Edit', write: 'Write', grep: 'Grep', find: 'Glob', ls: 'LS' };

// Pi may start in a subfolder (demo/), so the hooks live in the nearest folder above that has them.
function projectRoot(directory) {
  for (let folder = resolve(directory); ; folder = dirname(folder)) {
    if (existsSync(resolve(folder, 'tools/agents/hook.py'))) return folder;
    if (dirname(folder) === folder) return directory;
  }
}

function invoke(root, event) {
  const result = spawnSync('python3', [resolve(root, 'tools/agents/hook.py'), 'pi'], {
    cwd: root, input: JSON.stringify(event), encoding: 'utf8', timeout: 15000, maxBuffer: 128 * 1024,
  });
  if (result.error || result.status !== 0) throw new Error(UNAVAILABLE);
  const output = JSON.parse(result.stdout);
  const reason = output.stopReason || (output.decision === 'block' && output.reason)
    || (output.hookSpecificOutput?.permissionDecision === 'deny' && output.hookSpecificOutput.permissionDecisionReason);
  return { output, reason };
}

function toolEvent(event, ctx, name, result) {
  // An unknown tool that carries a command string is a shell call until proven otherwise.
  const shell = !(event.toolName in TOOLS) && typeof event.input?.command === 'string';
  const tool = shell ? 'Bash' : TOOLS[event.toolName] || event.toolName;
  const payload = {
    session_id: ctx.sessionManager.getSessionId(), hook_event_name: name, tool_use_id: event.toolCallId,
    tool_name: tool, tool_input: event.input,
    // Pi's own context measure feeds the shared 250k/300k rule; null right after a compaction.
    observed_tokens: ctx.getContextUsage?.()?.tokens ?? null,
  };
  // Any result a local file tool did not produce is forwarded; the adapter decides what reads outside.
  if (result !== undefined && !LOCAL.has(tool)) {
    try {
      if (JSON.stringify(result).length <= MAX_RESULT) payload.tool_response = result;
    } catch { /* a result that cannot be serialized carries no text to scan */ }
  }
  return payload;
}

export default function (pi) {
  // Sessions given the factory's start context; a compaction removes one, so its next run is told again.
  const started = new Set();
  const compacted = new Set();
  const settles = new Map();

  pi.on('before_agent_start', async (event, ctx) => {
    const session = ctx.sessionManager.getSessionId();
    if (started.has(session)) return undefined;
    const source = compacted.has(session) ? 'compact' : 'startup';
    const { output, reason } = invoke(projectRoot(ctx.cwd), { session_id: session, hook_event_name: 'SessionStart', source });
    if (reason) throw new Error(reason);
    started.add(session);
    compacted.delete(session);
    const content = output.hookSpecificOutput?.additionalContext;
    return content ? { message: { customType: 'aeion-factory', content, display: false } } : undefined;
  });

  pi.on('tool_call', async (event, ctx) => {
    try {
      const { reason } = invoke(projectRoot(ctx.cwd), toolEvent(event, ctx, 'PreToolUse'));
      return reason ? { block: true, reason } : undefined;
    } catch (error) {
      return { block: true, reason: error.message || UNAVAILABLE };
    }
  });

  pi.on('tool_result', async (event, ctx) => {
    if (event.isError) return undefined;
    const { reason, output } = invoke(projectRoot(ctx.cwd), toolEvent(event, ctx, 'PostToolUse', { content: event.content }));
    // A verified handover past 250k compacts now, not at Pi's own threshold near the model window.
    // Compacting aborts the running turn, so the session is told to resume from its handover once it is done.
    if (output.aeion?.compact) {
      ctx.compact({
        onComplete: () => pi.sendUserMessage(RESUME),
        onError: (error) => ctx.ui.notify(error.message || UNAVAILABLE, 'error'),
      });
    }
    const message = reason || output.hookSpecificOutput?.additionalContext;
    if (!message) return undefined;
    return { content: [...event.content, { type: 'text', text: `Æion Factory feedback: ${message}` }], structuredContent: event.structuredContent };
  });

  // The run's settlement is the factory's Stop: a sign-off finding asks for one more model request. The hook
  // shows each finding once per session, so the next settlement passes. A closure refusal is different: it
  // repeats until the checkpoint runs, so it asks a bounded number of times and then settles with the reason.
  pi.on('agent_before_settle', async (event, ctx) => {
    const session = ctx.sessionManager.getSessionId();
    try {
      const { output, reason } = invoke(projectRoot(ctx.cwd), { session_id: session, hook_event_name: 'Stop' });
      // A verified checkpoint past 250k compacts at settlement instead of spinning on continuation.
      if (output.aeion?.compact) {
        settles.delete(session);
        ctx.compact({
          onComplete: () => pi.sendUserMessage(RESUME),
          onError: (error) => ctx.ui.notify(error.message || UNAVAILABLE, 'error'),
        });
        return undefined;
      }
      if (!reason) {
        settles.delete(session);
        return undefined;
      }
      // Only the closure alert repeats until the checkpoint, bounded; a sign-off finding is already shown once
      // per session. The closure alert is a terminal stop too, and it is the one that earns a few more requests.
      if (!reason.includes('250k alert') && !reason.includes('300k')) {
        // Any other terminal stop ends the run here; continuing would ask for a request that settles the same way.
        if (output.continue === false) {
          settles.delete(session);
          ctx.ui.notify(reason, 'error');
          return undefined;
        }
        return { entries: [{ type: 'custom_message', customType: 'aeion-factory', content: reason, display: true }], continue: true };
      }
      const count = (settles.get(session) || 0) + 1;
      settles.set(session, count);
      if (count > SETTLE_LIMIT) {
        settles.delete(session);
        ctx.ui.notify(reason, 'error');
        return undefined;
      }
      return { entries: [{ type: 'custom_message', customType: 'aeion-factory', content: reason, display: true }], continue: true };
    } catch (error) {
      ctx.ui.notify(error.message || UNAVAILABLE, 'error');
      return undefined;
    }
  });

  pi.on('session_before_compact', async (event, ctx) => {
    const session = ctx.sessionManager.getSessionId();
    let reason;
    try {
      // `native` tells the shared rule this is Pi's own compaction at its window, not one the factory asked for:
      // refusing it would trap the session past the window, so it runs and the closure is owed after it.
      ({ reason } = invoke(projectRoot(ctx.cwd), { session_id: session, hook_event_name: 'PreCompact', native: true }));
    } catch (error) {
      // An unavailable hook is a broken guard, not a policy refusal: closing the only exit would lose the session.
      ctx.ui.notify(error.message || UNAVAILABLE, 'error');
      return undefined;
    }
    if (!reason) return undefined;
    // A policy refusal still lets the compaction through: the session must never be held at the model window.
    ctx.ui.notify(reason, 'warning');
    return undefined;
  });

  pi.on('session_compact', async (event, ctx) => {
    const session = ctx.sessionManager.getSessionId();
    started.delete(session);
    compacted.add(session);
    settles.delete(session);
  });
}
