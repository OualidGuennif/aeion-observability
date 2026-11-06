import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../app/factory.js', import.meta.url), 'utf8');
function client() {
  const context = vm.createContext({ crypto: { randomUUID: () => 'fixture-id' } });
  vm.runInContext(source, context);
  context.document = { getElementById: (id) => ({ value: id === 'feature-search' ? '' : '' }) };
  return { context, run: (code) => vm.runInContext(code, context) };
}
const features = [
  { id: '001', title: 'Skeleton', phase: 'P0', availability: { state: 'implemented', selectable: false } },
  { id: '017', title: 'Strict request validation', phase: 'P0', availability: { state: 'ready', selectable: true } },
  { id: '020', title: 'Membership', phase: 'P1', availability: { state: 'blocked', selectable: false } },
];

test('ready view contains only admitted selectable work', () => {
  const { context, run } = client(); context.fixture = features;
  run('state.catalog = fixture; state.filter = "ready"');
  assert.equal(run('visibleFeatures().map(f => f.id).join()'), '017');
});

test('initial catalog shows all specifications even while the factory is paused', () => {
  const { context, run } = client(); context.fixture = features;
  run('state.catalog = fixture');
  assert.equal(run('visibleFeatures().length'), 3);
  assert.equal(run('visibleFeatures().filter(f => availability(f).selectable).length'), 1);
});

test('catalog follows prerequisite sequence while preserving stable feature IDs', () => {
  const { context, run } = client();
  context.fixture = [
    { id: '019', title: 'Channels', phase: 'P1', sequence: 21 },
    { id: '041', title: 'Rules', phase: 'P0', sequence: 19 },
    { id: '043', title: 'Permissions', phase: 'P0', sequence: 20 },
  ];
  run('state.catalog = fixture; state.filter = "all"');
  assert.equal(run('visibleFeatures().map(f => f.id).join()'), '041,043,019');
  assert.equal(run('state.catalog[0].id'), '019'); // rendering must not mutate server data
});

test('completed view keeps finished work visible without making it selectable', () => {
  const { context, run } = client(); context.fixture = features;
  run('state.catalog = fixture; state.filter = "completed"');
  assert.equal(run('visibleFeatures().map(f => f.id).join()'), '001');
  assert.equal(run('visibleFeatures()[0].availability.selectable'), false);
});

test('refresh removes a stale selection once a feature finishes', () => {
  const { context, run } = client(); context.fixture = features;
  run('state.catalog = fixture; state.selected.add("001"); state.selected.add("017"); cleanSelection()');
  assert.equal(run('[...state.selected].join()'), '017');
});

test('search and phase combine with status rather than bypassing it', () => {
  const { context, run } = client(); context.fixture = features;
  context.document = { getElementById: (id) => ({ value: id === 'feature-search' ? 'strict' : 'P1' }) };
  run('state.catalog = fixture; state.filter = "all"');
  assert.equal(run('visibleFeatures().length'), 0);
});

test('unknown availability fails closed', () => {
  const { run } = client();
  assert.equal(run('availability({id:"999"}).selectable'), false);
});

test('trace links validate identity and escape receipt fields', () => {
  const { context, run } = client();
  context.receipt = JSON.stringify({ build_id: '<img src=x>', telemetry: { trace_id: 'a'.repeat(32), status: 'confirmed' } });
  const rendered = run('receiptSummary(receipt)');
  assert.ok(rendered.includes('trace confirmed'));
  assert.ok(rendered.includes('/project/aeion-demo/traces/' + 'a'.repeat(32)));
  assert.ok(rendered.includes('&lt;img src=x&gt;'));
  assert.ok(!rendered.includes('<img src=x>'));
  context.receipt = JSON.stringify({ telemetry: { trace_id: 'javascript:alert(1)' } });
  assert.ok(!run('receiptSummary(receipt)').includes('href='));
});

test('compiler and test failures are readable and escaped without a raw log', () => {
  const { context, run } = client();
  context.receipt = JSON.stringify({ gate: { status: 'failed', results: { gradle_test: { detail: {
    failure_kind: 'java_compilation_failed',
    compiler_errors: [{ file: 'Filter.java', line: 82, symbol: '<img src=x>' }],
    failed_tests: ['Contract > refusesUnknownField FAILED'],
  } } } } });
  const rendered = run('receiptSummary(receipt)');
  assert.ok(rendered.includes('Filter.java:82'));
  assert.ok(rendered.includes('&lt;img src=x&gt;'));
  assert.ok(rendered.includes('refusesUnknownField'));
  assert.ok(!rendered.includes('<img src=x>'));
});

test('dependency hold without missing IDs never prints a broken prerequisite sentence', () => {
  const { run } = client();
  const text = run('reasonText({reason:"dependency_missing",missing_dependencies:[]})');
  assert.ok(!text.includes('feature .'));
  assert.ok(text.includes('earlier request'));
  assert.doesNotThrow(() => run('reasonText({reason:"dependency_missing"})'));
});

test('engine hold is explained globally and on cards without asking for per-feature setup', () => {
  const { run } = client();
  assert.equal(run('featureLabel({state:"blocked",reason:"flue_factory_unqualified"})'), 'Factory paused');
  assert.ok(run('executionNotice({hold_reason:"flue_factory_unqualified"},0).includes("Flue/Pi")'));
  assert.ok(!run('executionNotice({hold_reason:"flue_factory_unqualified"},0).includes("configure each feature")'));
  assert.equal(run('featureLabel({state:"blocked",reason:"dependency_missing"})'), 'Waiting for prerequisites');
});

test('progress and routing evidence are bounded and escaped in the activity view', () => {
  const { context, run } = client();
  context.receipt = JSON.stringify({progress:{phase:'checking',detail:{model:'<img src=x>'}},
    routing:{basis:'measured_cost_latency',model:'qwen-3.8-flash',samples:{'qwen-3.8-flash':3}}});
  const html = run('receiptSummary(receipt)');
  assert.ok(html.includes('Checking'));
  assert.ok(html.includes('measured_cost_latency'));
  assert.ok(!html.includes('<img src=x>'));
});

test('publication shows a confined PR link, CI reason and confirmed main evidence', () => {
  const { context, run } = client();
  context.receipt = JSON.stringify({publisher:{status:'pending',reason:'ci_pending',
    pr:{pr_number:17,url:'https://attacker.invalid/steal'}},main_sha:'a'.repeat(40)});
  const html = run('receiptSummary(receipt)');
  assert.ok(html.includes('https://github.com/OualidGuennif/aeion-autonomous-forum/pull/17'));
  assert.ok(html.includes('required checks'));
  assert.ok(!html.includes('attacker.invalid'));
});

test('a publication hold and changed specification explain the next safe action', () => {
  const { run } = client();
  assert.ok(run('reasonText({reason:"catalog_changed"})').includes('specification changed'));
  assert.ok(run('reasonText({reason:"protection_unreadable"})').includes('read access'));
  assert.ok(run('reasonText({reason:"publication_blocked"})').includes('publication evidence'));
});

test('simulator and offline notices never promise real implementation or publication', () => {
  const { run } = client();
  assert.match(run('executionNotice({mode:"simulator"},1)'), /Simulation only/);
  assert.match(run('executionNotice({mode:"simulator"},0)'), /no paid model calls, PR or main merge/i);
  assert.match(run('executionNotice({mode:"offline"},1)'), /scripted/i);
  assert.ok(!run('executionNotice({mode:"simulator"},1).includes("runs preparation, isolated implementation")'));
});

test('activity distinguishes a recorded queue request, worker and durable publication wait', () => {
  const { context, run } = client();
  context.fixture = ['queued','dispatched','pr_open','gated','cancelled','merged'].map(status => ({status}));
  assert.equal(run('activitySummary(fixture)'), '1 queued · 1 running · 2 publishing');
});

test('activity refresh keeps evidence open and restores focus only in its own list', () => {
  const { context, run } = client();
  let replacements = 0, focuses = 0;
  const detail = { open: false };
  const card = { dataset: { buildId: 'attempt-a' }, querySelector: (selector) =>
    selector === 'details' ? detail : { focus: () => { focuses++; } } };
  const active = { closest: () => card, matches: (selector) => selector === 'summary' };
  const list = { contains: (node) => node === active,
    querySelectorAll: (selector) => selector === '[data-build-id] details[open]' ? [{ closest: () => card }]
      : selector === '[data-build-id]' ? [card] : [],
    set innerHTML(value) { replacements++; detail.open = false; } };
  context.document = { getElementById: () => list, activeElement: active };
  run('updateBuildList("builds", "changed evidence")');
  assert.equal(detail.open, true); assert.equal(focuses, 1);
  run('updateBuildList("builds", "changed evidence")');
  assert.equal(replacements, 1); assert.equal(focuses, 1);
});

test('old successful contracts stay historical and cannot imply current implementation', () => {
  const { context, run } = client(); context.fixture = features;
  run('state.catalog = fixture');
  assert.equal(run('obsoleteProof({feature_id:"017",status:"baseline"})'), true);
  assert.equal(run('obsoleteProof({feature_id:"001",status:"baseline"})'), false);
  context.build = { feature_id:'017', build_id:'a'.repeat(32), status:'baseline' };
  assert.match(run('buildCard(build)'), /Earlier contract/);
  assert.match(run('buildCard(build)'), /does not certify the current MD/);
});

test('external product results and registered no-model preparation are visible', () => {
  const { context, run } = client();
  context.receipt = JSON.stringify({preparation:{preparation_kind:'registered_static_acceptance',
    preparer_model:null,negative_control:'registered_foundation_startup_rejection'},
    gate:{status:'failed',results:{prepared_product:{detail:{reason:'valid_database_less_startup_rejected'}}}}});
  const html=run('receiptSummary(receipt)');
  assert.match(html,/no model request/); assert.match(html,/registered startup contract/);
  assert.match(html,/valid_database_less_startup_rejected/);
});

test('active work shows a stable stage without certifying draft checks as the final gate', () => {
  const { context, run } = client();
  context.build={status:'dispatched',receipt:JSON.stringify({preparation:{preparation_kind:'registered_static_acceptance'},
    progress:{phase:'protected_check.started',detail:{model:'glm-5.3-flash'}}})};
  assert.equal(run('buildStage(build)'),'building');
  assert.match(run('stageProgress(build)'),/aria-current="step">Build/);
  assert.match(run('stageProgress(build)'),/glm-5.3-flash/);
  context.build.receipt=JSON.stringify({progress:{phase:'checking'}});
  assert.equal(run('buildStage(build)'),'checking');
  context.build.status='merged';
  assert.equal(run('buildStage(build)'),'main');
});

test('no ready selection during active work explains progress rather than a global setup failure', () => {
  const { run } = client();
  run('state.builds=[{status:"dispatched"}]');
  assert.match(run('executionNotice({mode:"live"},0)'),/A build is in progress/);
  run('state.builds=[]');
  assert.match(run('executionNotice({mode:"live"},0)'),/No new implementation can start/);
});


test('an interrupted worker still exposes its checked draft cause and preserved files', () => {
  const {context,run}=client();
  context.receipt=JSON.stringify({execution:{failure:'AGENT_TIMEOUT',retained_files_count:11,
    check:{status:'failed',reason:'missing_secret_accepted'}}});
  const html=run('receiptSummary(receipt)');
  assert.match(html,/missing_secret_accepted/);
  assert.match(html,/Retained draft files/);
  assert.match(html,/>11</);
});

test('the next step names one plain owner action and never presents a simulation as real work', () => {
  const { context, run } = client(); context.fixture = features;
  run('state.catalog = fixture');
  assert.match(run('nextStep({mode:"simulator"}, fixture, []).title'), /Nothing real/);
  assert.match(run('nextStep({mode:"live"}, fixture, []).title'), /Ready to launch: 017/);
  const held = { feature_id: '001', status: 'held', hold_reason: 'owner_review_required',
    receipt: JSON.stringify({ circuit: { reason: 'reviewer_failed' } }), created_ns: 2 };
  context.held = held;
  const step = run('nextStep({mode:"live"}, fixture, [held])');
  assert.match(step.title, /Feature 001 is on hold/);
  assert.match(step.detail, /could not finish its vote/);
  assert.match(step.detail, /rerun the votes once without rerunning the author/);
  assert.match(step.detail, /cancel and launch the feature again/);
  context.rejected = { ...held, receipt: JSON.stringify({ circuit: { reason: 'reviewer_rejected' } }) };
  assert.match(run('nextStep({mode:"live"}, fixture, [rejected]).detail'), /automatic attempts and correction rounds[^]*relaunch unchanged will likely be rejected again/);
  assert.match(run('failedText({correction:{attempt:1, round:0, trigger:"ci_failed"}})'), /Required CI failed on the open pull request[^]*correction round 1 of 2[^]*was not merged/);
  assert.match(run('failedText({correction:{attempt:1, round:1, trigger:"gate_failed"}})'), /correction round 2 of 2 with the same model/);
  assert.match(run('holdReason({status:"held", hold_reason:"publication_blocked", receipt:JSON.stringify({publisher:{reason:"ci_failed"}, correction:{exhausted:true}})})'), /^ci_failed$/);
  assert.match(run('ciCheckText({failed_checks:[{name:"Product artifacts", conclusion:"failure"}]})'), /Product artifacts \(failure\)/);
  assert.match(run('failedText({correction:{attempt:1, round:2, trigger:"reviewer_rejected"}})'), /attempt 2 of 3 on another model/);
  assert.match(run('failedText({correction:{attempt:2, round:0, trigger:"crash", crash:{failure:"CLI_FAILED"}}})'), /author agent stopped early[^]*attempt 3 of 3/);
  assert.doesNotMatch(run('failedText({error:"CLI_FAILED", correction:{attempt:3, round:0, trigger:"crash"}})'), /queued/);
  assert.equal(run('feedbackText({author:"RAS", reviewers:[{model:"glm-5.3-flash", text:"<b>ok</b>"}]})'), 'author: RAS · glm-5.3-flash: <b>ok</b>');
  assert.equal(run('feedbackText(null)'), '');
  context.running = { feature_id: '001', status: 'dispatched', receipt: '{}', created_ns: 3 };
  assert.match(run('nextStep({mode:"live"}, fixture, [running]).title'), /being built/);
  assert.match(run('nextStep({mode:"live", hold_reason:"budget_config_invalid"}, fixture, []).detail'), /Fix demo\/budget.conf/);
  assert.match(run('nextStep({mode:"live"}, [fixture[0], fixture[2]], []).title'), /Nothing can start yet/);
});

test('the cockpit markup no longer offers the synthetic canary drill or a fake environment link', () => {
  const html = readFileSync(new URL('../app/factory.html', import.meta.url), 'utf8');
  assert.ok(!/canary drill|staging-link|release-panel/i.test(html));
  assert.match(html, /Staging<\/dt><dd>Not deployed yet/);
  assert.match(html, /Production<\/dt><dd>Not deployed yet/);
});

test('an agent self-test on its draft is never labelled as the final check', () => {
  const { run } = client();
  const draft = run(`receiptSummary(JSON.stringify({draft_check:{status:"failed",reason:"explicit_database_less_startup_rejected"}}))`);
  assert.match(draft, /Agent self-test \(draft\)/);
  assert.match(draft, /not the final verdict/);
  assert.ok(!draft.includes('<dt>Check</dt>'));
  const gate = run(`receiptSummary(JSON.stringify({gate:{status:"failed"},draft_check:{status:"failed",reason:"x_y"}}))`);
  assert.match(gate, /<dt>Check<\/dt><dd>failed<\/dd>/);
});

test('agent clock shows elapsed time, silence and a stall warning without private data', () => {
  const { run } = client();
  const start = 1_000_000;
  const quiet = run(`clockText(${start}, ${start + 60000}, 10800, 0, ${start + 5 * 60000})`);
  assert.equal(quiet.attention, false);
  assert.match(quiet.text, /Agent time 5 of 180 min · last activity 4 min ago/);
  const stalled = run(`clockText(${start}, ${start + 60000}, 1800, 1, ${start + 15 * 60000})`);
  assert.equal(stalled.attention, true);
  assert.match(stalled.text, /No agent activity for 14 min/);
  assert.match(stalled.text, /draft self-test failed 1×/);
  const looping = run(`clockText(${start}, ${start}, 0, 3, ${start + 30000})`);
  assert.equal(looping.attention, true);
  assert.match(looping.text, /Agent time 0 min · last activity under a minute ago/);
  assert.match(looping.text, /keeps failing/);
});

test('agent clock appears only while the author runs', () => {
  const { context, run } = client();
  context.receipt = { author_started_ns: 1e15, last_tool_ns: 2e15, draft_failures: 2, progress: { phase: 'tool.finished', time_ns: 3e15 } };
  assert.match(run('agentClock({status:"dispatched"}, receipt, 10800)'), /data-start="1000000000" data-last="3000000000" data-window="10800" data-failures="2"/);
  assert.equal(run('agentClock({status:"failed"}, receipt, 10800)'), '');
  context.receipt.progress.phase = 'process.retired';
  assert.equal(run('agentClock({status:"dispatched"}, receipt, 10800)'), '');
  assert.equal(run('agentClock({status:"dispatched"}, {progress:{phase:"building"}}, 10800)'), '');
});

test('a failed review vote names the provider status and the retries it already used', () => {
  const { run } = client();
  const text = run(`voteText({model: "deepseek-4.1-flash", verdict: "error",
    execution: {failure: "PROVIDER_REJECTED", provider_http_status: 503, provider_retries: 2}})`);
  assert.equal(text, 'deepseek-4.1-flash error · PROVIDER_REJECTED · provider HTTP 503 · 2 provider retries');
  assert.equal(run('voteText({model: "qwen-3.8-flash", verdict: "approve", execution: {provider_retries: 0}})'),
    'qwen-3.8-flash approve');
  const html = run(`receiptSummary(JSON.stringify({circuit: {votes: [{model: "<b>", verdict: "error",
    execution: {provider_http_status: "503"}}]}}))`);
  assert.match(html, /&lt;b&gt; error/);
  assert.doesNotMatch(html, /provider HTTP/);
  const substituted = run(`receiptSummary(JSON.stringify({circuit: {status: "approved",
    votes: [{model: "qwen-3.8-flash", verdict: "approve"}, {model: "claude-haiku-5.5", verdict: "approve"}],
    unavailable_reviewers: [{model: "deepseek-4.1-flash", verdict: "error",
      execution: {failure: "PROVIDER_RATE_LIMITED", provider_http_status: 429, provider_retries: 2}}]}}))`);
  assert.match(substituted, /Busy reviewer replaced/);
  assert.match(substituted, /deepseek-4\.1-flash error · PROVIDER_RATE_LIMITED · provider HTTP 429 · 2 provider retries/);
});
