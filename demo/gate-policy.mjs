export function measure(tokens) {
  const values = [tokens?.input, tokens?.cache?.read, tokens?.cache?.write];
  if (values.some((v) => !Number.isSafeInteger(v) || v < 0)) {
    throw new Error("USAGE_UNKNOWN");
  }
  const context = values.reduce((a, b) => a + b, 0);
  if (!Number.isSafeInteger(context) || context === 0) throw new Error("USAGE_UNKNOWN");
  return context;
}

export function decision(messages, limit, metric = "active_context") {
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > 250000) throw new Error("INVALID_LIMIT");
  if (!["active_context", "cumulative_input"].includes(metric)) throw new Error("INVALID_METRIC");
  const seen = new Set();
  let active = 0;
  let cumulative = 0;
  for (const { info } of messages) {
    if (info.role !== "assistant" || seen.has(info.id)) continue;
    if (info.error || !info.finish || info.summary) throw new Error("USAGE_UNKNOWN");
    seen.add(info.id);
    active = measure(info.tokens);
    cumulative += active;
    if (!Number.isSafeInteger(cumulative)) throw new Error("USAGE_UNKNOWN");
  }
  const observed = metric === "active_context" ? active : cumulative;
  return { action: observed >= limit ? "handover" : "continue", observed, metric, limit };
}
