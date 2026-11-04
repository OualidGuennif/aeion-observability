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
