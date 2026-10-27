// Pinned to OpenCode 1.19.4. No prompts, tool payloads or source leave this hook.
import { writeFileSync, existsSync, readFileSync, renameSync } from "node:fs";

import { decision } from "./gate-policy.mjs";

export const ContextGate = async () => {
  let admitted = false;
  return {
  "chat.headers": async (input, output) => {
    // The provider receives only a deliberately invalid key without this hook.
    // Consume one admission ticket per main request; missing plugins fail closed.
    if (input.agent !== "build") throw new Error("AEION_GATE_CLOSED_AGENT");
    if (!admitted) throw new Error("AEION_GATE_CLOSED_TICKET");
    if (!process.env.AEION_OPENCODE_KEY) throw new Error("AEION_GATE_CLOSED_CREDENTIAL");
    admitted = false;
    output.headers.Authorization = `Bearer ${process.env.AEION_OPENCODE_KEY}`;
  },
  "chat.params": async (_input, output) => {
    output.maxOutputTokens = Math.min(output.maxOutputTokens ?? 4096, 4096);
  },
  "experimental.chat.messages.transform": async (_input, output) => {
    admitted = false;
    let result;
    try {
      result = decision(output.messages, Number(process.env.AEION_CONTEXT_LIMIT), process.env.AEION_CONTEXT_METRIC);
      const steps = output.messages.filter(({info}) => info.role === "assistant");
      if (result.action === "continue" && steps.length >= 12) result = {action:"stop",reason:"STEP_LIMIT"};
      const costs = steps.map(({info}) => info.cost);
      if (costs.some(value => typeof value !== "number" || !Number.isFinite(value) || value < 0)) throw new Error("COST_UNKNOWN");
      const budget = Number(process.env.AEION_MAX_COST_USD ?? "0.10");
      if (!Number.isFinite(budget) || budget < 0) throw new Error("COST_UNKNOWN");
      if (costs.reduce((a,b)=>a+b,0) > budget) result = {action:"stop",reason:"BUDGET_STOP"};
    } catch {
      result = { action: "stop", reason: "USAGE_UNKNOWN" };
    }
    if (result.observed >= Math.max(1, result.limit - 20000)) {
      const checkpoint = {id: crypto.randomUUID(), observed: result.observed, metric: result.metric, limit: result.limit};
      const temporary = process.env.AEION_CHECKPOINT_REQUEST + ".tmp";
      writeFileSync(temporary, JSON.stringify(checkpoint), {mode:0o600});
      renameSync(temporary, process.env.AEION_CHECKPOINT_REQUEST);
      let acknowledged = false;
      const deadline = Date.now() + 20000;
      while (Date.now() < deadline) {
        try {
          if (existsSync(process.env.AEION_CHECKPOINT_ACK)) {
            const ack = JSON.parse(readFileSync(process.env.AEION_CHECKPOINT_ACK, "utf8"));
            if (ack.id === checkpoint.id && ack.ready === true && /^[a-f0-9]{64}$/.test(ack.sha256)) {
              acknowledged = true; break;
            }
          }
        } catch { /* Atomic replacement may be in progress; never admit without an ack. */ }
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      if (!acknowledged) {
        writeFileSync(process.env.AEION_GATE_FILE, JSON.stringify({action:"stop",reason:"HANDOVER_NOT_READY"}), {mode:0o600});
        throw new Error("AEION_GATE_CLOSED");
      }
    }
    if (result.action !== "continue") {
      writeFileSync(process.env.AEION_GATE_FILE, JSON.stringify(result), { mode: 0o600 });
      // This hook precedes handle.process/provider dispatch in session/prompt.ts.
      throw new Error("AEION_GATE_CLOSED");
    }
    admitted = true;
  },
};
};
