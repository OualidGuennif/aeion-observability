import test from 'node:test';
import assert from 'node:assert/strict';
import { finishReminder, initialCheck, MAX_FINISH_REMINDERS, unavailableCheck } from '../src/tools/factory-checks.ts';

test('a passed check lets the author stop', () => {
  assert.equal(finishReminder({ status: 'passed' }), null);
});

test('an author that never ran the check is told to run it before stopping', () => {
  assert.match(finishReminder(null), /You have not run run_protected_checks/);
});

test('a failed check names its failing tests and forbids stopping', () => {
  const text = finishReminder({ status: 'failed', reason: 'product_unit_tests_failed',
    failed_tests: ['DatabaseLessBootTest > livenessAnswersWithoutADatabase() FAILED'], compiler_errors: [] });
  assert.match(text, /product_unit_tests_failed/);
  assert.match(text, /livenessAnswersWithoutADatabase/);
  assert.match(text, /Do not stop/);
});

test('a refused protected check returns its reason token', () => {
  assert.deepEqual(unavailableCheck(false, { ok: false, error: 'SANDBOX_EXEC_FAILED' }),
    { status: 'failed', reason: 'SANDBOX_EXEC_FAILED' });
  assert.deepEqual(unavailableCheck(true, { ok: false, error: 'secret log line' }),
    { status: 'failed', reason: 'check_unavailable' });
  assert.equal(unavailableCheck(true, { ok: true, result: { status: 'passed' } }), null);
});

test('reminder data stays bounded and typed', () => {
  const text = finishReminder({ status: 'failed', reason: 7, failed_tests: [...Array(50)].map((_, i) => 'T' + i + 'x'.repeat(500)) });
  assert.match(text, /check_failed/);
  assert.ok(text.length < 3000);
  assert.equal(MAX_FINISH_REMINDERS, 3);
});

test('handover check environment initializes check state', () => {
  process.env.AEION_HANDOVER_CHECK = JSON.stringify({ status: 'passed', reason: 'passed' });
  const restored = initialCheck();
  assert.equal(restored?.status, 'passed');
  delete process.env.AEION_HANDOVER_CHECK;
});
