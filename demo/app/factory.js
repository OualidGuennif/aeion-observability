/* Factory board client: admin login, catalog cards, queue, cancel and bounded SSE. */
"use strict";
const TERMINAL = ["merged", "failed", "cancelled", "simulated_complete"];
const LANGFUSE_UI = "http://localhost:3300";
const state = { csrf: null, selected: new Set(), catalog: [], builds: [], events: [], lastSeq: 0 };

const $ = (id) => document.getElementById(id);

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function uid() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  return "id-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

async function api(path, options) {
  const r = await fetch(path, { credentials: "same-origin", ...options });
  const body = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, body };
}

function pushEvent(event, data) {
  state.events.unshift({ event, data });
  state.events = state.events.slice(0, 20);
  renderEvents();
}

function renderEvents() {
  const list = $("events");
  list.innerHTML = state.events.length
    ? state.events.map((e) => `<div class="event"><b>${esc(e.event)}</b> ${e.data ? esc(JSON.stringify(e.data)).slice(0, 120) : ""}</div>`).join("")
    : '<p class="muted">Waiting for events.</p>';
}

function renderCards() {
  const phase = $("phase-filter").value;
  const area = $("area-filter").value;
  const grid = $("cards");
  grid.innerHTML = "";
  let count = 0;
  for (const f of state.catalog) {
    if (phase && f.phase !== phase) continue;
    if (area && f.area !== area) continue;
    count += 1;
    const checked = state.selected.has(f.id);
    const disabled = !checked && state.selected.size >= 10;
    const card = document.createElement("label");
    card.className = "card" + (checked ? " selected" : "");
    card.innerHTML = `<input type="checkbox" data-id="${esc(f.id)}" ${checked ? "checked" : ""} ${disabled ? "disabled" : ""}>` +
      `<div class="card-body"><div class="card-head"><strong>${esc(f.id)}</strong><span class="tag">${esc(f.phase)} · ${esc(f.area)}</span></div>` +
      `<h4>${esc(f.title)}</h4><div class="card-meta"><span>size ${esc(f.size)}</span><span>tier ${f.tier}</span>` +
      `${f.parallel ? '<span class="badge-parallel">parallel</span>' : ""}<span>${f.depends_on.length ? "needs " + f.depends_on.map(esc).join(", ") : "no deps"}</span></div></div>`;
    card.querySelector("input").addEventListener("change", (e) => toggleSelection(e.target, f.id));
    grid.appendChild(card);
  }
  $("catalog-count").textContent = `${count} features`;
  $("selection-count").textContent = `${state.selected.size} / 10 selected`;
  $("build-one").disabled = state.selected.size !== 1;
  $("queue-ten").disabled = state.selected.size < 1 || state.selected.size > 10;
}

function toggleSelection(input, id) {
  if (input.checked) {
    if (state.selected.size >= 10) { input.checked = false; return; }
    state.selected.add(id);
  } else {
    state.selected.delete(id);
  }
  renderCards();
}

function receiptSummary(raw) {
  if (!raw) return "";
  let r;
  try { r = JSON.parse(raw); } catch { return `<p class="fineprint">receipt: ${esc(String(raw).slice(0, 140))}</p>`; }
  const bits = [];
  if (r.simulated) bits.push("simulated");
  if (r.gate && r.gate.status) {
    const results = Object.entries(r.gate.results || {}).map(([k, v]) => `${k}:${v.status}`).join(", ");
    bits.push(`gate ${esc(r.gate.status)}${results ? " (" + esc(results) + ")" : ""}`);
  }
  if (r.publisher && r.publisher.decision) bits.push(`publisher ${esc(r.publisher.decision)}`);
  const pr = r.publisher && r.publisher.forge && r.publisher.forge.pr;
  if (pr && pr.pr_number) bits.push(`fake PR #${esc(pr.pr_number)}`);
  if (r.build_id) bits.push(`build ${esc(String(r.build_id).slice(0, 8))}`);
  if (r.attempt_id) bits.push(`attempt ${esc(String(r.attempt_id).slice(0, 8))}`);
  if (r.artifact_digest) bits.push(`artifact ${esc(String(r.artifact_digest).slice(0, 12))}`);
  if (r.frozen_digest) bits.push(`frozen ${esc(String(r.frozen_digest).slice(0, 12))}`);
  if (r.base_sha) bits.push(`base ${esc(String(r.base_sha).slice(0, 8))}`);
  const trace = r.telemetry && r.telemetry.trace_id;
  if (trace) bits.push(`<a href="${LANGFUSE_UI}/trace/${encodeURIComponent(trace)}" target="_blank" rel="noreferrer">trace ${esc(String(trace).slice(0, 8))}</a>`);
  return bits.length ? `<p class="fineprint">${bits.join(" · ")}</p>` : "";
}

function renderBuilds() {
  const list = $("builds");
  const nonterm = state.builds.filter((b) => !TERMINAL.includes(b.status)).length;
  $("queue-count").textContent = `${nonterm} nonterminal`;
  list.innerHTML = state.builds.length
    ? state.builds.map((b) => {
        const f = state.catalog.find((x) => x.id === b.feature_id);
        const cancel = !TERMINAL.includes(b.status)
          ? `<button class="quiet" data-cancel="${esc(b.build_id)}">Cancel</button>` : "";
        return `<div class="build-row ${esc(b.status)}"><div class="build-head"><strong>${esc(b.feature_id)}</strong>` +
          `<span class="tag">${esc(b.status)}</span>${cancel}</div><p>${f ? esc(f.title) : ""}${b.hold_reason ? " · held: " + esc(b.hold_reason) : ""}</p>${receiptSummary(b.receipt)}</div>`;
      }).join("")
    : '<p class="muted">No builds yet.</p>';
  list.querySelectorAll("[data-cancel]").forEach((btn) => btn.addEventListener("click", () => cancelBuild(btn.dataset.cancel)));
}

function fmt(seconds) {
  const s = Math.max(0, Math.round(seconds || 0));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h ? `${h}h ${m}m` : `${m}m ${s % 60}s`;
}

function renderReleases(view) {
  const rel = view && view.release;
  const state = $("release-state");
  const msg = $("release-msg");
  const staging = $("staging-link");
  const toggle = (id, on) => { $(id).disabled = !on; };
  if (!rel) {
    state.textContent = "no release";
    $("release-id").textContent = "—";
    $("release-features").textContent = "Nothing staged yet.";
    $("release-timeline").textContent = "—";
    $("release-traffic").textContent = "—";
    $("release-gate").textContent = "—";
    $("release-flags").textContent = "";
    staging.hidden = true;
    ["validate-release", "deploy-now", "advance-release", "rollback-release"].forEach((id) => toggle(id, false));
    return;
  }
  state.textContent = `${rel.state} · ${rel.percent}%`;
  $("release-id").textContent = rel.release_id;
  $("release-features").textContent = rel.features.map((f) => `${f.id} ${f.title}`).join(" · ");
  staging.hidden = false;
  staging.href = view.endpoints.staging;
  const step = rel.step_status || {};
  const plan = (rel.steps || []).map((s) => `${s.percent}%/${fmt(s.dwell_seconds)}`).join(" → ");
  $("release-timeline").textContent = `step ${rel.step + 1}/${rel.steps.length} · ${plan} · ` +
    (rel.state === "canary" ? `${fmt(step.elapsed_seconds)} elapsed, ${fmt(step.remaining_seconds)} left` : rel.state);
  const traffic = view.traffic || {};
  $("release-traffic").textContent = `${traffic.requests || 0} req · ${traffic.status_5xx || 0} 5xx · p95 ${traffic.p95_ms || 0} ms · cache ${traffic.cache_hits || 0}/${(traffic.cache_hits || 0) + (traffic.cache_misses || 0)} hits`;
  const gate = (rel.gate || {});
  $("release-gate").textContent = `gate ${gate.verdict || "?"} — ${gate.reason || ""} (${gate.samples || 0} samples)`;
  const flags = rel.flags || {};
  const names = Object.keys(flags);
  $("release-flags").innerHTML = names.length
    ? names.map((name) => {
        const flag = flags[name];
        return `<label class="flag-row"><input type="checkbox" data-flag="${esc(name)}" ${flag.enabled ? "checked" : ""}>` +
          `${esc(name)} · ${flag.rollout}%</label>`;
      }).join("")
    : '<span class="muted">No flags in this release.</span>';
  $("release-flags").querySelectorAll("[data-flag]").forEach((box) =>
    box.addEventListener("change", () => releaseAction("flag", { name: box.dataset.flag, enabled: box.checked })));
  toggle("validate-release", rel.state === "staged");
  toggle("deploy-now", ["staged", "canary", "held"].includes(rel.state));
  toggle("advance-release", rel.state === "canary" && step.due && gate.verdict === "continue");
  toggle("rollback-release", ["canary", "held"].includes(rel.state));
  msg.textContent = (rel.history || []).length ? "last: " + rel.history[rel.history.length - 1].event : "";
}

async function loadReleases() {
  const { ok, status, body } = await api("/api/factory/releases");
  if (!ok) { if (status === 401) showLogin(); return; }
  renderReleases(body);
}

async function releaseAction(action, extra) {
  const { ok, status, body } = await api("/api/factory/release", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": state.csrf },
    body: JSON.stringify({ action, ...(extra || {}) }),
  });
  if (!ok) { pushEvent("release_error", { status, ...body }); }
  await loadReleases();
}

async function refresh() {
  const { ok, body } = await api("/api/factory/board");
  if (!ok) { showLogin(); return; }
  state.builds = body.builds || [];
  state.lastSeq = body.earliest_seq || state.lastSeq;
  renderBuilds();
}

async function loadCatalog() {
  const { ok, body } = await api("/api/factory/catalog");
  if (!ok) { showLogin(); return; }
  state.catalog = body.features || [];
  const phases = [...new Set(state.catalog.map((f) => f.phase))].sort();
  const areas = [...new Set(state.catalog.map((f) => f.area))].sort();
  $("phase-filter").innerHTML = '<option value="">All phases</option>' + phases.map((p) => `<option>${esc(p)}</option>`).join("");
  $("area-filter").innerHTML = '<option value="">All areas</option>' + areas.map((a) => `<option>${esc(a)}</option>`).join("");
  renderCards();
}

function showLogin() {
  $("login").hidden = false;
  $("app").hidden = true;
}

function showApp() {
  $("login").hidden = true;
  $("app").hidden = false;
}

async function queue(ids) {
  const key = uid();
  const { ok, status, body } = await api("/api/factory/queue", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": state.csrf },
    body: JSON.stringify({ ids, idempotency_key: key }),
  });
  if (ok) { state.selected.clear(); renderCards(); await refresh(); }
  else { pushEvent("queue_error", { status, ...body }); }
}

async function cancelBuild(buildId) {
  const { ok, status, body } = await api("/api/factory/cancel", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": state.csrf },
    body: JSON.stringify({ build_id: buildId }),
  });
  if (!ok) pushEvent("cancel_error", { status, ...body });
  await refresh();
}

function connectSSE() {
  const es = new EventSource(`/api/factory/events?since=${state.lastSeq}`);
  const onEvent = (e) => {
    if (e.lastEventId) state.lastSeq = parseInt(e.lastEventId, 10) || state.lastSeq;
    if (e.type !== "reload") pushEvent(e.type, e.data ? safeParse(e.data) : null);
    refresh();
    if (e.type === "release_updated") loadReleases();
  };
  ["build_updated", "admitted", "cancelled", "observed", "session_rotated", "release_updated"]
    .forEach((n) => es.addEventListener(n, onEvent));
  es.addEventListener("reload", () => { es.close(); refresh(); });
  es.onerror = () => { /* EventSource auto-reconnects. */ };
}

function safeParse(text) {
  try { return JSON.parse(text); } catch { return text; }
}

async function boot() {
  $("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = $("login-msg");
    msg.textContent = "";
    const { ok, status, body } = await api("/api/factory/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: $("token").value }),
    });
    if (!ok) { msg.textContent = status === 429 ? "Too many attempts. Wait a minute." : "Invalid or rotated token."; return; }
    state.csrf = body.csrf;
    $("token").value = "";
    showApp();
    await loadCatalog();
    await refresh();
    await loadReleases();
    connectSSE();
  });
  $("build-one").addEventListener("click", () => queue([...state.selected]));
  $("queue-ten").addEventListener("click", () => queue([...state.selected]));
  $("validate-release").addEventListener("click", () => releaseAction("validate"));
  $("deploy-now").addEventListener("click", () => releaseAction("deploy_now"));
  $("advance-release").addEventListener("click", () => releaseAction("advance"));
  $("rollback-release").addEventListener("click", () => releaseAction("rollback", { reason: "operator" }));
  $("phase-filter").addEventListener("change", renderCards);
  $("area-filter").addEventListener("change", renderCards);

  if (await authed()) {
    showApp();
    await loadCatalog();
    await refresh();
    await loadReleases();
    connectSSE();
    setInterval(loadReleases, 15000);
  }
}

async function authed() {
  try { const r = await fetch("/api/factory/board", { credentials: "same-origin" }); return r.ok; }
  catch { return false; }
}

boot();
