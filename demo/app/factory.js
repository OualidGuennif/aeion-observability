/* Spec: knowledge/components/operator-cockpit.md */
"use strict";
const TERMINAL = ["merged", "failed", "cancelled", "simulated_complete", "live_complete", "baseline"];
const LANGFUSE_UI = "http://127.0.0.1:3300";
const LANGFUSE_PROJECT = "aeion-demo"; // The project initialized by demo/compose.yaml.
const state = { csrf: null, selected: new Set(), catalog: [], builds: [], events: [], lastSeq: 0,
  execution: {}, filter: "all", refreshing: false, submitting: false, stream: null, requestKey: null, specRequest: 0, buildMarkup: {} };
const $ = (id) => document.getElementById(id);
const LABELS = { ready: "Ready", implemented: "Implemented", built: "Built · awaiting integration",
  in_progress: "In progress", blocked: "Waiting", live_complete: "Built", baseline: "Verified baseline",
  merged: "Integrated", queued: "Queued", dispatched: "Running", held: "On hold", failed: "Failed",
  cancelled: "Cancelled", simulated_complete: "Simulation", approved: "Approved", gated: "Publication queued", pr_open: "Waiting for CI" };
function esc(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function uid() { return crypto.randomUUID(); }
function availability(feature) {
  return feature.availability || { state: "blocked", selectable: false, reason: "availability_unavailable" };
}
function reasonText(info) {
  const reason = info.reason || "";
  if (!reason && state.execution.mode === "simulator") return "Ready for a scripted queue simulation.";
  if (!reason && state.execution.mode === "offline") return "Ready for isolated qualification with scripted agent output.";
  if (reason === "dependency_missing") {
    const missing = Array.isArray(info.missing_dependencies) ? info.missing_dependencies : [];
    return missing.length ? `Waiting for feature${missing.length > 1 ? "s" : ""} ${missing.join(", ")} to be integrated.`
      : "The prerequisites of this earlier request are now satisfied. Its hold must be reconciled before dispatch.";
  }
  return ({ already_implemented: "Implemented and locked against another launch.",
    awaiting_integration: "Implementation built. Integration is a separate step; relaunch is locked.",
    feature_in_progress: "Already queued or running. Follow it in Build activity.",
    target_unavailable: "Automatic task preparation is not connected for this feature yet. This is factory work, not configuration for you to supply.",
    flue_factory_unqualified: "Flue/Pi worker or checker qualification is missing, expired or changed. The factory must verify its execution tools; there is no individual MD setup for you to supply.",
    provider_unconfigured: "The model provider is not configured.",
    execution_unavailable: "The product repository or task preparation adapter is unavailable to the factory.",
    sandbox_unqualified: "The isolated checker needs qualification.",
    budget_unavailable: "The daily budget is unavailable or exhausted.",
    budget_config_invalid: "demo/budget.conf is invalid or above its ceiling ($15/day, $5 per author execution, $1 per review vote). No paid work starts until it is fixed.",
    STEP_LIMIT: "The worker reached its allowed model-step limit. This attempt is preserved; the feature has not been implemented.",
    CLI_STARTUP_FAILED: "The agent CLI stopped before its first model request. The factory must repair its launcher; no implementation was started.",
    builder_error: "Implementation stopped. Open Build evidence for the exact agent failure and the full Langfuse session.",
    availability_unavailable: "Refresh after the controller update to load availability.",
    qualification_missing: "The independent acceptance check is missing or unqualified. The factory must prepare and verify it before implementation.",
    target_feature_mismatch: "This feature does not match the configured execution target.",
    owner_review_required: "Owner review is required before proceeding.",
    reviewer_failed: "A reviewer could not finish its vote (timeout, provider refusal or no typed verdict). Nothing was published; Review votes shows which one and why.",
    reviewer_rejected: "An independent reviewer rejected the change after the automatic attempts and correction rounds. Nothing was published; the reasons are in Build evidence.",
    correction_unchanged: "A correction round returned the refused candidate unchanged, so it was not checked or reviewed again. Nothing was published.",
    worker_error: "The worker stopped unexpectedly. The request is held for review; no automatic paid retry.",
    reconciliation_needed: "An interrupted attempt or remote action needs reconciliation. Another launch stays locked while its effects are unknown.",
    catalog_changed: "The specification changed after this request. Refresh and read the current MD. A new selection replaces only an obsolete request that never started; uncertain attempts stay locked.",
    publication_blocked: "Publication stopped safely. Open the publication evidence below for the precise blocker.",
    publication_unavailable: "The isolated publisher is not connected. The checked artifact is preserved; no PR or main merge is claimed.",
    preparation_unavailable: "Task preparation stopped before implementation. Open the evidence for the exact checker, repository or acceptance blocker.",
    preparation_model_declined: "The preparer could not turn this MD into a valid acceptance contract. Its proposal is preserved for diagnosis; no builder started.",
    preparation_acceptance_runtime_mismatch: "The preparer returned a different test format from the protected Node checker. No builder started.",
    preparation_acceptance_size_invalid: "The proposed acceptance is empty, too large or contains invalid data. No builder started.",
    preparation_acceptance_assertions_missing: "The proposed acceptance has no executable test assertions. No builder started.",
    preparation_acceptance_skips_forbidden: "The proposed acceptance skips or excludes tests; the protected checker refuses it.",
    preparation_budget_stop: "Acceptance preparation reached its per-attempt budget. No builder or publication started; the measured cost and failed attempt are preserved.",
    preparation_agent_timeout: "Acceptance preparation exceeded its deadline. The attempt is preserved; no builder or publication started.",
    preparation_cli_failed: "The preparation harness stopped without a completed submission. No implementation or publication was started.",
    preparation_profile_unavailable: "This specification requires the shared React/web checker, which has not been qualified yet. This is factory infrastructure work.",
    preparation_transition_checker_unqualified: "The shared PostgreSQL transition checker has not been qualified. No builder was started for this request.",
    preparation_checker_unqualified: "The protected check boundary could not be qualified. No implementation was started.",
    product_base_not_integrated: "The product main branch still lacks the baseline application. A checked bootstrap PR must integrate it before a feature can start.",
    preparation_base_unavailable: "The factory cannot resolve the product's pinned main commit. Repository synchronization must be repaired before implementation.",
    preparation_negative_control_missing: "The proposed acceptance did not produce a genuine failing case on the untouched baseline. It cannot certify a new implementation.",
    preparation_contract_unavailable: "The preparer could not produce a usable protected acceptance contract. The request is preserved without starting a builder.",
    protection_unreadable: "The release role needs read access to main branch protection before it can verify a safe merge.",
    protection_unqualified: "Main branch protection does not satisfy the factory policy. No merge was requested.",
    ci_pending: "Waiting for all required checks on this exact PR commit. No new implementation is needed.",
    ci_failed: "A required CI check failed. The pull request was not merged. Automatic correction rounds are finished, so this feature stays on hold.",
    stale_base: "Main changed after the task was frozen. Rebase, checks and independent reviews must be repeated before publication.",
    stale_head: "The PR head changed after review. Publication is held until the exact artifact is verified again.",
    merge_not_confirmed: "A merge could not be confirmed on main. Keep this feature locked while the factory reconciles the remote result.",
    profile_expired: "The model profile needs requalification." })[reason] || (reason ? `Waiting: ${reason}. Inspect the request evidence.` : "Ready for automatic preparation and build.");
}
const OWNER_ACTIONS = {
  reviewer_failed: "The operator may rerun the votes once without rerunning the author (review_context --retry-failed-review); otherwise cancel and launch the feature again.",
  reviewer_rejected: "The factory already ran its automatic attempts and correction rounds. Read the reviewer reasons in Build evidence, then cancel this request; a relaunch unchanged will likely be rejected again.",
  worker_error: "Cancel this request, then launch the feature again.",
  catalog_changed: "Cancel this request, then launch the feature again with the current MD.",
  reconciliation_needed: "Do not relaunch. Ask the agent to reconcile this attempt first.",
  dependency_missing: "Nothing to do: it starts after its prerequisites reach main.",
  budget_unavailable: "Wait for tomorrow's budget or raise DAILY_LIMIT_USD in demo/budget.conf (max $15).",
  budget_config_invalid: "Fix demo/budget.conf, then restart the controller.",
  ci_failed: "Read the failing check names in Build evidence, then cancel this request to free the feature. A relaunch starts a new author; it does not resume these rounds.",
};
function publicationDetail(receipt) {
  const reason = (receipt.publisher || {}).reason;
  if (!reason) return "";
  if (reason === "ci_failed" && receipt.correction?.exhausted !== true)
    return "A required CI check failed. The pull request was not merged.";
  return reasonText({reason});
}
function holdReason(build) {
  const receipt = parseReceipt(build.receipt);
  if (receipt.reason === "correction_unchanged") return receipt.reason;
  if ((receipt.publisher || {}).reason === "ci_failed" && receipt.correction?.exhausted === true) return "ci_failed";
  const circuit = receipt.circuit || {};
  return ["reviewer_failed", "reviewer_rejected"].includes(circuit.reason) ? circuit.reason : build.hold_reason;
}
function failedText(r) {
  const c = r.correction || {};
  const attempt = Number.isInteger(c.attempt) ? c.attempt : 1;
  if (c.exhausted !== true && Number.isInteger(c.round) && ["reviewer_rejected", "gate_failed", "ci_failed", "crash"].includes(c.trigger)) {
    const cause = { reviewer_rejected: "A reviewer rejected this build", gate_failed: "A protected check refused this build", ci_failed: "Required CI failed on the open pull request", crash: "The author agent stopped early" }[c.trigger];
    const tail = c.trigger === "ci_failed" ? "The pull request was not merged." : "Nothing was published.";
    if (c.trigger !== "crash" && c.round < 2)
      return `${cause}; the factory queued correction round ${c.round + 1} of 2 with the same model and that feedback. ${tail}`;
    if (attempt < 3)
      return `${cause}; the factory queued attempt ${attempt + 1} of 3 on another model, starting from the validated files. ${tail}`;
  }
  return reasonText({reason:r.error || r.reason || "builder_error"});
}
function feedbackText(f) {
  if (!f || typeof f !== "object") return "";
  const parts = [];
  if (typeof f.author === "string") parts.push(`author: ${f.author}`);
  if (typeof f.preparer === "string") parts.push(`preparer: ${f.preparer}`);
  if (Array.isArray(f.reviewers)) for (const v of f.reviewers)
    if (v && typeof v.text === "string") parts.push(`${typeof v.model === "string" ? v.model : "reviewer"}: ${v.text}`);
  return parts.join(" · ");
}
function ownerAction(reason) {
  return OWNER_ACTIONS[reason] || "Open Build evidence below. Cancel the request to free the feature, or ask the agent if the reason is unclear.";
}
function featureLabel(info) {
  if (info.state !== "blocked") return LABELS[info.state] || info.state;
  if (info.reason === "dependency_missing") return "Waiting for prerequisites";
  if (info.reason === "flue_factory_unqualified") return "Factory paused";
  if (info.reason === "target_unavailable") return "Preparation pending";
  if (info.reason === "owner_review_required") return "Review required";
  return "On hold";
}
function executionNotice(execution, ready) {
  if (execution.mode === "simulator") return "<strong>Simulation only.</strong>Scripted queue behavior: no paid model calls, PR or main merge. A simulation does not implement a feature.";
  if (execution.mode === "offline") return "<strong>Offline qualification.</strong>Isolated checks use scripted agent output. No paid model call or real PR/main publication occurs.";
  const hold = execution.hold_reason || execution.live_hold_reason;
  if (hold && execution.mode !== "simulator" && execution.mode !== "offline") {
    return `<strong>Factory paused.</strong>${esc(reasonText({reason: hold}))} The factory owns repository, isolation, checks and publication preparation. Your step is to choose a specification when execution is available.`;
  }
  if (ready) return `<strong>${ready} feature${ready === 1 ? " is" : "s are"} ready.</strong>Select up to ten specifications. The factory runs preparation, isolated implementation, checks and review in order.`;
  if (state.builds.some((build) => ["dispatched", "built", "gated", "pr_open", "approved"].includes(build.status)))
    return "<strong>A build is in progress.</strong>Follow its current stage in Build activity. Features unlock after their prerequisites are integrated on main.";
  return "<strong>No new implementation can start yet.</strong>Read the specifications and their prerequisite order below. The waiting states explain the exact factory or dependency blocker.";
}
const PHASE_LABELS = {preparing:"Preparing task",building:"Building in OpenShell",checking:"Checking",
  reviewing:"Independent review",publishing:"Opening pull request",waiting_ci:"Waiting for CI",merging:"Merging",
  "model.step.started":"Agent working","tool.finished":"Tool completed","gen_ai.request":"Model response received",
  "protected_check.started":"Checking","protected_check.finished":"Check completed",
  "process.started":"Agent started","process.retired":"Agent stopped","gate.closed":"Session checkpoint"};
function visibleFeatures() {
  const query = $("feature-search").value.trim().toLowerCase();
  const phase = $("phase-filter").value;
  return state.catalog.filter((f) => {
    const a = availability(f);
    const statusMatch = state.filter === "all" || a.state === state.filter
      || (state.filter === "completed" && ["implemented", "built"].includes(a.state));
    return statusMatch && (!phase || f.phase === phase)
      && (!query || `${f.id} ${f.title}`.toLowerCase().includes(query));
  }).sort((a, b) => (a.sequence ?? Number.MAX_SAFE_INTEGER) - (b.sequence ?? Number.MAX_SAFE_INTEGER)
    || a.id.localeCompare(b.id));
}
function cleanSelection() {
  for (const id of state.selected) {
    if (!state.catalog.some((f) => f.id === id && availability(f).selectable)) state.selected.delete(id);
  }
}
async function api(path, options) {
  const response = await fetch(path, { credentials: "same-origin", ...options });
  return { ok: response.ok, status: response.status, body: await response.json().catch(() => ({})) };
}
function setConnection(connected, label) {
  $("system-dot").classList.toggle("connected", connected);
  $("system-status").textContent = label;
}
function showLogin() {
  $("login").hidden = false; $("app").hidden = true;
  state.csrf = null; state.selected.clear();
  if (state.stream) { state.stream.close(); state.stream = null; }
  setConnection(false, "Sign in required");
  const dialog = $("spec-dialog");
  if (dialog?.open) dialog.close();
  state.specRequest++;
}
const RUNNING = ["queued", "dispatched", "built", "gated", "pr_open", "approved"];
function nextStep(execution, catalog, current) {
  const title = (f) => `${f.id} · ${f.title}`;
  if (execution.mode === "simulator" || execution.mode === "offline")
    return { title: "Nothing real can be built in this mode.", detail: "The controller runs without live execution. Restart it with AEION_FACTORY_EXECUTION=live; no paid model call, PR or merge happens until then." };
  const hold = execution.hold_reason || execution.live_hold_reason;
  if (hold) return { title: "The factory is paused.", detail: `${reasonText({ reason: hold })} ${ownerAction(hold)}` };
  const held = current.find((b) => b.status === "held");
  if (held) {
    const reason = holdReason(held);
    return { title: `Feature ${held.feature_id} is on hold.`, detail: `${reasonText({ reason })} ${ownerAction(reason)}` };
  }
  const running = current.find((b) => RUNNING.includes(b.status));
  if (running) return { title: `Feature ${running.feature_id} is being built.`, detail: "Nothing to do. Follow its stage in Build activity; the next feature unlocks once it reaches main." };
  const ready = catalog.filter((f) => availability(f).selectable);
  if (ready.length) return { title: `Ready to launch: ${ready.slice(0, 3).map(title).join(", ")}${ready.length > 3 ? "…" : ""}`, detail: "Tick it in the catalog below, then click Build selected." };
  return { title: "Nothing can start yet.", detail: "Every remaining feature waits for an earlier one to reach main. The catalog shows what each one waits for." };
}
function renderOverview() {
  const count = (predicate) => state.catalog.filter((f) => predicate(availability(f))).length;
  const ready = count((a) => a.selectable);
  $("catalog-summary").textContent = `${ready} ready · ${count((a) => a.state === "in_progress")} in progress · ` +
    `${count((a) => ["implemented", "built"].includes(a.state))} completed · ${count((a) => a.state === "blocked")} waiting`;
  const e = state.execution;
  const mode = ({ live: "Live", offline: "Offline qualification", simulator: "Simulation only" })[e.mode] || "Unavailable";
  $("execution-mode").textContent = `${mode}${e.hold_reason ? " · Paused" : ""}`;
  $("execution-notice").innerHTML = e.mode === "live" && !(e.hold_reason || e.live_hold_reason)
    ? "Real model calls, isolated build, protected checks, two independent reviews, then a PR to main. One build at a time."
    : executionNotice(e, ready);
  const step = nextStep(e, state.catalog, splitBuilds(state.builds).current);
  $("next-title").textContent = step.title; $("next-detail").textContent = step.detail;
  $("next-step").classList.toggle("attention", /on hold|paused|Nothing real/.test(step.title));
}
function renderCards() {
  cleanSelection();
  const features = visibleFeatures();
  $("catalog-count").textContent = `${features.length} of ${state.catalog.length}`;
  $("cards").innerHTML = features.length ? features.map((f) => {
    const a = availability(f);
    const checked = state.selected.has(f.id);
    const disabled = !a.selectable || state.submitting || (!checked && state.selected.size >= 10);
    return `<article class="feature-row ${disabled ? "locked" : ""} ${checked ? "selected" : ""}">` +
      `<input type="checkbox" id="feature-${esc(f.id)}" data-id="${esc(f.id)}" aria-label="Select feature ${esc(f.id)}" ${checked ? "checked" : ""} ${disabled ? "disabled" : ""}>` +
      `<div class="feature-copy"><div class="feature-top"><span class="feature-number">${f.sequence ? `Step ${esc(f.sequence)} · ` : ""}${esc(f.id)} · ${esc(f.phase)}</span>` +
      `<span class="badge ${esc(a.state)}">${esc(featureLabel(a))}</span></div><label class="feature-title" for="feature-${esc(f.id)}">${esc(f.title)}</label>` +
      `<p class="feature-reason">${esc(reasonText(a))}</p><button class="text-button spec-button" data-spec="${esc(f.id)}" type="button">Read MD →</button></div></article>`;
  }).join("") : `<div class="empty-state"><div class="empty-icon">◇</div><h3>${state.filter === "ready" ? "Nothing ready to launch yet" : "No matching features"}</h3>` +
    `<p>${state.filter === "ready" ? "Browse the catalog to read the specifications and see the exact waiting states. Completed work stays locked." : "Try another search or status filter."}</p><button class="text-button" id="view-all">View all features →</button></div>`;
  $("cards").querySelectorAll("[data-id]").forEach((input) => input.addEventListener("change", () => {
    if (input.checked && state.selected.size < 10) state.selected.add(input.dataset.id);
    else state.selected.delete(input.dataset.id);
    state.requestKey = null;
    renderCards();
  }));
  if ($("view-all")) $("view-all").addEventListener("click", () => setFilter("all"));
  $("cards").querySelectorAll("[data-spec]").forEach((button) => button.addEventListener("click", () => openSpec(button.dataset.spec)));
  $("selection-count").textContent = state.selected.size ? `${state.selected.size} / 10 selected` : "No features selected";
  $("build-one").disabled = !state.selected.size || !state.csrf || state.submitting;
  $("build-one").innerHTML = `${state.submitting ? "Submitting…" : "Build selected"} <span>→</span>`;
}
async function openSpec(id) {
  const request = ++state.specRequest;
  const dialog = $("spec-dialog");
  $("spec-title").textContent = `Feature ${id}`;
  $("spec-body").textContent = "Loading specification…";
  $("spec-digest").textContent = "";
  if (!dialog.open) dialog.showModal();
  try {
    const result = await api(`/api/factory/spec/${encodeURIComponent(id)}`);
    if (request !== state.specRequest || !dialog.open) return;
    if (result.status === 401) { showLogin(); return; }
    if (!result.ok) throw new Error("unavailable");
    $("spec-title").textContent = `${result.body.id} · ${result.body.title}`;
    $("spec-body").textContent = result.body.markdown;
    $("spec-digest").textContent = `Specification SHA-256: ${result.body.sha256}`;
  } catch {
    if (request === state.specRequest) $("spec-body").textContent = "The specification could not be loaded. Close this view and try again.";
  }
}
function setFilter(filter) {
  state.filter = filter;
  $("status-filters").querySelectorAll("[data-filter]").forEach((button) => {
    const selected = button.dataset.filter === filter;
    button.classList.toggle("selected", selected); button.setAttribute("aria-pressed", String(selected));
  });
  renderCards();
}
function voteText(vote) {
  const execution = vote?.execution || {};
  const parts = [`${vote?.model || "unknown"} ${vote?.verdict || "unknown"}`];
  if (execution.failure) parts.push(String(execution.failure));
  if (Number.isInteger(execution.provider_http_status)) parts.push(`provider HTTP ${execution.provider_http_status}`);
  if (Number.isInteger(execution.provider_retries) && execution.provider_retries > 0)
    parts.push(`${execution.provider_retries} provider retr${execution.provider_retries === 1 ? "y" : "ies"}`);
  return parts.join(" · ");
}
function parseReceipt(raw) {
  try { return raw ? JSON.parse(raw) : {}; } catch { return {}; }
}
function ciCheckText(publication) {
  const items = Array.isArray(publication.failed_checks) ? publication.failed_checks.slice(0, 8) : [];
  const text = items.map((item) => {
    const name = typeof item?.name === "string" ? item.name.slice(0, 80) : "";
    const conclusion = typeof item?.conclusion === "string" ? item.conclusion.slice(0, 32) : "";
    return name && conclusion ? `${name} (${conclusion})` : "";
  }).filter(Boolean).join("; ");
  return text ? esc(text) : "";
}
function receiptSummary(raw) {
  const r = parseReceipt(raw);
  const check = r.gate?.results?.prepared_product?.detail || r.gate?.results?.prepared_gradle?.detail || r.gate?.results?.gradle_test?.detail || r.execution?.check || r.draft_check || r.check || {};
  // Before the protected gate runs, the only check is the agent's own self-test of its draft.
  const draft = !r.gate?.status && check === r.draft_check;
  const telemetry = r.telemetry || {};
  const trace = telemetry.trace_id;
  const status = telemetry.status || "unknown";
  const traceLabel = status === "confirmed" ? "trace confirmed" : `trace ${status}`;
  const link = trace && /^[a-f0-9]{32}$/i.test(trace)
    ? `<a href="${LANGFUSE_UI}/project/${LANGFUSE_PROJECT}/traces/${encodeURIComponent(trace)}" target="_blank" rel="noreferrer">${esc(traceLabel)} ↗</a>` : "";
  const sessionLink = /^[a-f0-9]{32}$/.test(r.build_id || "")
    ? `<a href="${LANGFUSE_UI}/project/${LANGFUSE_PROJECT}/sessions/${encodeURIComponent("factory:" + r.build_id)}" target="_blank" rel="noreferrer">Full build session ↗</a>` : "";
  const publication = r.publisher || {};
  const number = publication.pr?.pr_number;
  const prLink = Number.isSafeInteger(number) && number > 0
    ? `<a href="https://github.com/OualidGuennif/aeion-autonomous-forum/pull/${number}" target="_blank" rel="noreferrer">Pull request #${number} ↗</a>` : "";
  const evidence = [
    ["Progress", r.progress?.phase && esc(PHASE_LABELS[r.progress.phase] || "Working")],
    ["Routing", r.routing?.basis && esc(`${r.routing.basis} · ${r.routing.model || "unknown"}`)],
    ["Reason", r.reason && esc(reasonText({reason:String(r.reason)}))],
    ["Error", r.error && esc(String(r.error))],
    ["Build", r.build_id && esc(String(r.build_id))],
    ["Attempt", r.attempt_id && esc(String(r.attempt_id))],
    ["Artifact", r.artifact_digest && esc(String(r.artifact_digest))],
    ["Base", r.base_sha && esc(String(r.base_sha))],
    ["Model", r.author_model && esc(String(r.author_model))],
    ["Agent failure", r.execution?.failure && esc(String(r.execution.failure))],
    ["Error class", r.execution?.error_class && esc(String(r.execution.error_class))],
    ["Attempt and round", Number.isInteger(r.correction?.round) && esc(`attempt ${Number.isInteger(r.correction.attempt) ? r.correction.attempt : 1} of 3 · round ${r.correction.round} of 2${r.correction.crash?.failure ? " · after crash " + r.correction.crash.failure : ""}`)],
    ["Agent feedback (owner only)", esc(feedbackText(r.feedback))],
    ["Review votes", Array.isArray(r.circuit?.votes) && r.circuit.votes.length && esc(r.circuit.votes.map(voteText).join("; "))],
    ["Busy reviewer replaced", Array.isArray(r.circuit?.unavailable_reviewers) && r.circuit.unavailable_reviewers.length && esc(r.circuit.unavailable_reviewers.map(voteText).join("; "))],
    ["CLI exit", Number.isInteger(r.execution?.process_exit_code) && String(r.execution.process_exit_code)],
    ["Model requests", Number.isInteger(r.execution?.forwarded_count) && String(r.execution.forwarded_count)],
    ["Retained draft files", Number.isInteger(r.execution?.retained_files_count) && String(r.execution.retained_files_count)],
    ["Candidate recovery", r.execution?.candidate_recovered === true && "Agent bound reached; candidate sent to independent checks"],
    ["Preparer", r.preparation?.preparation_kind === "registered_static_acceptance" ? "Registered contract · no model request" : r.preparation?.preparer_model && esc(r.preparation.preparer_model)],
    ["Acceptance baseline", r.preparation?.negative_control === "registered_foundation_startup_rejection" ? "Untouched baseline refused the registered startup contract" : r.preparation?.negative_control === "registered_transition_source_missing" ? "Untouched baseline lacks the registered migration operator or browser source" : r.preparation?.negative_control === "failed_contract_assertion" && "Independent contract failed on the untouched baseline"],
    ["Working memory", r.execution?.memory?.claude_mem?.status && esc(r.execution.memory.claude_mem.status)],
    ["Hindsight", r.execution?.memory?.hindsight?.status && esc(r.execution.memory.hindsight.status)],
    [draft ? "Agent self-test (draft)" : "Check", r.gate?.status ? esc(String(r.gate.status)) : check.status ? esc(String(check.status)) + (draft && check.status !== "passed" ? " · the agent is still fixing its draft; not the final verdict" : "") : check.returncode === 0 ? "passed" : null],
    ["Failure", check.failure_kind && esc(String(check.failure_kind))],
    [draft ? "Self-test detail" : "Check detail", check.reason && esc(String(check.reason))],
    ["Compiler", Array.isArray(check.compiler_errors) && check.compiler_errors.length &&
      esc(check.compiler_errors.map((e) => `${e.file}:${e.line}${e.symbol ? " · " + e.symbol : ""}`).join("; "))],
    ["Failed tests", Array.isArray(check.failed_tests) && check.failed_tests.length && esc(check.failed_tests.join("; "))],
    ["Review", r.circuit?.status && esc(String(r.circuit.status))],
    ["Publication", publication.status && esc(String(publication.status))],
    ["Publication detail", publication.reason && esc(publicationDetail(r))],
    ["CI checks", ciCheckText(publication)],
    ["Merged commit", publication.confirmed_main === true && /^[a-f0-9]{40}$/.test(publication.merge_sha) && esc(publication.merge_sha)],
    ["Confirmed main", publication.confirmed_main === true && /^[a-f0-9]{40}$/.test(publication.main_sha) && esc(publication.main_sha)],
  ].filter(([, value]) => value);
  return `${link || prLink || sessionLink ? `<div class="build-actions">${link}${sessionLink}${prLink}</div>` : ""}` + (evidence.length
    ? `<details class="evidence"><summary>Build evidence</summary><dl>${evidence.map(([key, value]) => `<dt>${key}</dt><dd>${value}</dd>`).join("")}</dl></details>` : "");
}
function obsoleteProof(build) {
  if (!["baseline", "merged", "live_complete"].includes(build.status)) return false;
  const feature = state.catalog.find((f) => f.id === build.feature_id);
  return !["implemented", "built"].includes(availability(feature || {}).state);
}
function buildStage(build) {
  const receipt = parseReceipt(build.receipt);
  if (build.status === "merged") return "main";
  if (["pr_open", "gated", "approved"].includes(build.status)) return "publication";
  const phase = receipt.progress?.phase;
  if (["preparing", "building", "checking", "reviewing"].includes(phase)) return phase;
  if (phase) return receipt.preparation ? "building" : "preparing";
  return null;
}
// Ten minutes with no tool result or model step: likely a long command or a stalled agent.
const STALL_SECONDS = 600;
function agentClock(build, receipt, windowSeconds) {
  const started = Number(receipt.author_started_ns);
  if (build.status !== "dispatched" || !Number.isFinite(started) || started <= 0) return "";
  if (["process.retired", "checking", "reviewing", "publishing"].includes(receipt.progress?.phase)) return "";
  const last = Math.max(started, Number(receipt.last_tool_ns) || 0, Number(receipt.progress?.time_ns) || 0);
  const failures = Number.isInteger(receipt.draft_failures) ? receipt.draft_failures : 0;
  const window = Number.isInteger(windowSeconds) && windowSeconds > 0 ? windowSeconds : 0;
  return `<p class="agent-clock" data-start="${started / 1e6}" data-last="${last / 1e6}" data-window="${window}" data-failures="${failures}"></p>`;
}
function clockText(startMs, lastMs, windowSeconds, failures, nowMs) {
  const minutes = (ms) => Math.max(0, Math.floor(ms / 60000));
  const elapsed = minutes(nowMs - startMs);
  const silent = Math.max(0, (nowMs - lastMs) / 1000);
  const parts = [windowSeconds ? `Agent time ${elapsed} of ${Math.round(windowSeconds / 60)} min` : `Agent time ${elapsed} min`,
    `last activity ${silent < 60 ? "under a minute" : minutes(silent * 1000) + " min"} ago`];
  if (failures) parts.push(`draft self-test failed ${failures}×`);
  const stalled = silent >= STALL_SECONDS;
  const note = stalled ? ` · No agent activity for ${minutes(silent * 1000)} min: a long command or a stalled agent. The time window and author budget still stop it.`
    : failures >= 3 ? " · The same draft keeps failing its self-test." : "";
  return { text: parts.join(" · ") + note, attention: stalled || failures >= 3 };
}
function tickClocks(nowMs = Date.now()) {
  if (typeof document === "undefined" || !document.querySelectorAll) return;
  for (const el of document.querySelectorAll(".agent-clock")) {
    const c = clockText(Number(el.dataset.start), Number(el.dataset.last), Number(el.dataset.window), Number(el.dataset.failures), nowMs);
    el.textContent = c.text; el.classList.toggle("attention", c.attention);
  }
}
function stageProgress(build) {
  const current = buildStage(build);
  if (!current || ["failed", "cancelled", "held"].includes(build.status)) return "";
  const labels = { preparing: "Prepare", building: "Build", checking: "Check", reviewing: "Review", publication: "PR / CI", main: "Main" };
  const receipt = parseReceipt(build.receipt);
  const model = receipt.progress?.detail?.model;
  return `<ol class="build-stages" aria-label="Implementation stages">${Object.entries(labels).map(([stage, label]) =>
    `<li${stage === current ? ' aria-current="step"' : ""}>${label}</li>`).join("")}</ol>` +
    `<p class="current-stage">${esc(PHASE_LABELS[receipt.progress?.phase] || labels[current])}${model ? " · " + esc(model) : ""}</p>` +
    agentClock(build, receipt, state.execution?.author_window_seconds);
}
function buildCard(build) {
  const feature = state.catalog.find((f) => f.id === build.feature_id);
  const r = parseReceipt(build.receipt);
  const simulation = r.simulated === true || build.status === "simulated_complete";
  const obsolete = obsoleteProof(build);
  const label = simulation ? "Simulation" : obsolete ? "Earlier contract" : (LABELS[build.status] || build.status);
  const time = build.updated_ns ? new Date(build.updated_ns / 1e6) : null;
  return `<article class="build-card" data-build-id="${esc(build.build_id)}"><div class="build-card-heading"><span class="feature-number">FEATURE ${esc(build.feature_id)}</span>` +
    `<span class="badge ${esc(build.status)}">${esc(label)}</span></div><h3>${esc(feature?.title || build.feature_id)}</h3>` +
    (obsolete ? "<p>This historical result does not certify the current MD.</p>" : build.status === "failed" ? `<p>${esc(failedText(r))}</p>` : build.hold_reason ? `<p>${esc(reasonText({ reason: holdReason(build), missing_dependencies: feature?.availability?.missing_dependencies || [] }))}</p><p class="owner-action">${esc(ownerAction(holdReason(build)))}</p>` :
      `<p>${build.status === "live_complete" ? "Checked implementation ready for integration." : build.status === "baseline" || build.status === "merged" ? "Implemented at a verified product base." : simulation ? "Historical fixture, separate from real implementation." : "Protected checks and review govern the next step."}</p>`) +
    stageProgress(build) + receiptSummary(build.receipt) + `<div class="build-actions">${time ? `<time datetime="${time.toISOString()}">${esc(time.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }))}</time>` : ""}` +
    (!TERMINAL.includes(build.status) ? `<button class="cancel" data-cancel="${esc(build.build_id)}">Cancel request</button>` : "") + "</div></article>";
}
function activitySummary(builds) {
  const count = (statuses) => builds.filter((b) => statuses.includes(b.status)).length;
  return `${count(["queued"])} queued · ${count(["dispatched", "built"])} running · ${count(["gated", "pr_open", "approved"])} publishing`;
}
function updateBuildList(id, html) {
  if (state.buildMarkup[id] === html) return;
  const list = $(id);
  const opened = new Set([...list.querySelectorAll("[data-build-id] details[open]")]
    .map((detail) => detail.closest("[data-build-id]").dataset.buildId));
  const active = document.activeElement;
  const focusedBuild = list.contains(active) && active.closest("[data-build-id]")?.dataset.buildId;
  const focusedSelector = active?.matches("summary") ? "summary" : active?.matches("[data-cancel]") ? "[data-cancel]" : null;
  list.innerHTML = html; state.buildMarkup[id] = html;
  for (const card of list.querySelectorAll("[data-build-id]")) {
    if (opened.has(card.dataset.buildId) && card.querySelector("details")) card.querySelector("details").open = true;
    if (focusedBuild === card.dataset.buildId && focusedSelector) card.querySelector(focusedSelector)?.focus({ preventScroll: true });
  }
  list.querySelectorAll("[data-cancel]").forEach((button) => button.addEventListener("click", () => cancelBuild(button.dataset.cancel)));
}
function splitBuilds(builds) {
  const sorted = [...builds].sort((a, b) => b.created_ns - a.created_ns);
  const seen = new Set(); const current = []; const history = [];
  for (const build of sorted) {
    const simulation = parseReceipt(build.receipt).simulated === true || build.status === "simulated_complete";
    const feature = state.catalog.find((f) => f.id === build.feature_id);
    const a = availability(feature || {});
    const completed = ["implemented", "built"].includes(a.state);
    const oldHold = build.status === "held" && (completed || a.reason === "target_unavailable");
    if (simulation || obsoleteProof(build) || oldHold || seen.has(build.feature_id)) history.push(build);
    else { seen.add(build.feature_id); current.push(build); }
  }
  return { current, history };
}
function renderBuilds() {
  const { current, history } = splitBuilds(state.builds);
  updateBuildList("builds", current.length ? current.slice(0, 8).map(buildCard).join("")
    : '<div class="empty-state"><h3>No real build yet</h3><p>Your next admitted feature will appear here.</p></div>');
  $("queue-count").textContent = activitySummary(state.builds);
  updateBuildList("history", history.map(buildCard).join(""));
  $("history-count").textContent = `(${history.length})`;
  $("history-panel").hidden = !history.length;
  tickClocks();
}
function renderBudgets(budget) {
  const scopes = budget?.scopes || {};
  const names = { "aeion-autonomous-forum": "Forum workers", "aeion-observability": "Observability" };
  $("budgets").innerHTML = budget?.status === "available" ? Object.entries(scopes).map(([scope, value]) => {
    const remaining = Number(value.remaining_usd), limit = Number(value.limit_usd);
    const percent = limit > 0 ? Math.max(0, Math.min(100, (1 - remaining / limit) * 100)) : 100;
    return `<div class="budget-row"><div><span>${esc(names[scope] || scope)}</span><strong>$${remaining.toFixed(2)}</strong></div>` +
      `<progress class="budget-track" max="100" value="${percent}" aria-label="Daily budget used"></progress><p>remaining of $${limit.toFixed(2)} · ${esc(value.day)}</p></div>`;
  }).join("") : '<p class="fineprint">Budget information is unavailable. Spending remains subject to the server guard.</p>';
}
function pushEvent(event) {
  state.events.unshift({ event, time: new Date().toLocaleTimeString() });
  state.events = state.events.slice(0, 20);
  $("events").innerHTML = state.events.map((e) => `<div class="event">${esc(e.time)} · ${esc(e.event.replaceAll("_", " "))}</div>`).join("");
}
async function refresh() {
  if (state.refreshing) return;
  state.refreshing = true;
  try {
    const [catalog, board] = await Promise.all([api("/api/factory/catalog"), api("/api/factory/board")]);
    if (catalog.status === 401 || board.status === 401) { showLogin(); return; }
    if (!catalog.ok || !board.ok) throw new Error("unavailable");
    $("login").hidden = true; $("app").hidden = false;
    state.catalog = catalog.body.features || []; state.execution = catalog.body.execution || {};
    state.builds = board.body.builds || []; state.csrf = board.body.csrf || state.csrf;
    const phase = $("phase-filter").value;
    const phases = [...new Set(state.catalog.map((f) => f.phase))].sort();
    $("phase-filter").innerHTML = '<option value="">All phases</option>' + phases.map((p) => `<option>${esc(p)}</option>`).join("");
    $("phase-filter").value = phases.includes(phase) ? phase : "";
    renderOverview(); renderCards(); renderBuilds(); renderBudgets(board.body.budget);
    setConnection(true, "Controller connected");
    if (!state.stream) connectSSE();
  } catch {
    setConnection(false, "Connection interrupted");
    $("queue-msg").textContent = "The controller is unavailable. Reconnecting; no new request was sent.";
  } finally { state.refreshing = false; }
}
async function queue() {
  const ids = [...state.selected];
  if (!ids.length || state.submitting) return;
  state.submitting = true; state.requestKey ||= uid(); renderCards();
  try {
    const result = await api("/api/factory/queue", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": state.csrf }, body: JSON.stringify({ ids, idempotency_key: state.requestKey }) });
    if (result.ok && ["admitted", "replayed"].includes(result.body.status)) {
      state.selected.clear(); state.requestKey = null;
      $("queue-msg").textContent = "Request recorded. Follow its progress in Build activity.";
      pushEvent("request_recorded");
    } else {
      const code = result.body.error || result.body.status || "request_refused";
      $("queue-msg").textContent = code.startsWith("feature_already_completed") ? "This feature is already completed and cannot be launched again."
        : code.startsWith("feature_in_progress") ? "This feature is already queued or running."
        : result.status === 403 ? "Your session needs refreshing. Sign in again if this persists."
        : "The request was not admitted. Review availability and the queue limit.";
    }
  } catch { $("queue-msg").textContent = "Connection lost. Retry to check the same request without creating a duplicate."; }
  finally { state.submitting = false; await refresh(); renderCards(); }
}
async function cancelBuild(buildId) {
  try {
    const result = await api("/api/factory/cancel", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": state.csrf }, body: JSON.stringify({ build_id: buildId }) });
    $("queue-msg").textContent = result.ok ? "Cancellation recorded." : "Cancellation could not be recorded. Refresh and retry.";
    await refresh();
  } catch { $("queue-msg").textContent = "Connection lost while requesting cancellation."; }
}
function connectSSE() {
  const es = new EventSource(`/api/factory/events?since=${state.lastSeq}`); state.stream = es;
  const onEvent = (event) => {
    if (event.lastEventId) state.lastSeq = parseInt(event.lastEventId, 10) || state.lastSeq;
    pushEvent(event.type); refresh();
  };
  ["build_updated", "build_progress", "admitted", "cancelled", "observed", "session_rotated"].forEach((name) => es.addEventListener(name, onEvent));
  es.addEventListener("reload", () => { es.close(); state.stream = null; refresh(); });
  es.onerror = () => setConnection(false, "Live updates reconnecting");
}
async function boot() {
  $("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = $("login-form").querySelector("button"); button.disabled = true;
    try {
      const result = await api("/api/factory/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token: $("token").value }) });
      if (!result.ok) { $("login-msg").textContent = result.status === 429 ? "Too many attempts. Wait a minute." : "Invalid or rotated token. Reopen the local token file."; return; }
      state.csrf = result.body.csrf; $("token").value = ""; await refresh();
    } catch { $("login-msg").textContent = "Cannot reach the local controller."; }
    finally { button.disabled = false; }
  });
  $("build-one").addEventListener("click", queue);
  $("spec-close").addEventListener("click", () => { state.specRequest++; $("spec-dialog").close(); });
  $("spec-dialog").addEventListener("cancel", () => { state.specRequest++; });
  $("feature-search").addEventListener("input", renderCards);
  $("phase-filter").addEventListener("change", renderCards);
  $("status-filters").querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => setFilter(button.dataset.filter)));
  await refresh();
  setInterval(() => { if (!$("app").hidden) refresh(); }, 10000);
  setInterval(() => tickClocks(), 15000);
}
if (typeof document !== "undefined") boot();
