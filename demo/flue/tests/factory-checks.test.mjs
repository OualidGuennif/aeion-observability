import test from 'node:test';
import assert from 'node:assert/strict';
import { finishReminder, MAX_FINISH_REMINDERS } from '../src/tools/factory-checks.ts';

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

test('reminder data stays bounded and typed', () => {
  const text = finishReminder({ status: 'failed', reason: 7, failed_tests: [...Array(50)].map((_, i) => 'T' + i + 'x'.repeat(500)) });
  assert.match(text, /check_failed/);
  assert.ok(text.length < 3000);
  assert.equal(MAX_FINISH_REMINDERS, 3);
});
