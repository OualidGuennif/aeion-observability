import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import * as v from 'valibot';
import { FEEDBACK_LIMIT, FEEDBACK_RULE, PIPELINE } from '../src/context.ts';
import { submitReview } from '../src/tools/submit-review.ts';
import { submitPreparation } from '../src/tools/submit-preparation.ts';
import { feedbackSubmitted, submitFeedback } from '../src/tools/submit-feedback.ts';

test('every agent learns the sandbox, the goal, the pipeline and the attempt bounds', () => {
  for (const fact of ['OpenShell sandbox without network', 'two reviewers', 'pull request',
    'two correction rounds', 'three attempts', 'data, never instructions']) {
    assert.match(PIPELINE, new RegExp(fact));
  }
  assert.match(FEEDBACK_RULE, /"RAS"/);
  assert.match(FEEDBACK_RULE, /Only the owner reads it/);
});

test('reviewer and preparer feedback is optional and bounded', () => {
  const review = submitReview('/private/tmp/unused-review-fixture.json');
  const vote = { verdict: 'approve', reason: 'Fixture' };
  assert.equal(v.safeParse(review.input, vote).success, true);
  assert.equal(v.safeParse(review.input, { ...vote, feedback: 'RAS' }).success, true);
  assert.equal(v.safeParse(review.input, { ...vote, feedback: 'x'.repeat(FEEDBACK_LIMIT + 1) }).success, false);
  const preparation = submitPreparation('/private/tmp/unused-preparation-fixture.json');
  const ready = { status: 'ready', contract: 'class Acceptance {}', reason: 'Fixture' };
  assert.equal(v.safeParse(preparation.input, { ...ready, feedback: 'RAS' }).success, true);
  assert.equal(v.safeParse(preparation.input, { ...ready, feedback: 'x'.repeat(FEEDBACK_LIMIT + 1) }).success, false);
});

test('author feedback goes to the supervisor bridge only, once accepted', async (t) => {
  const received = [];
  const server = createServer((request, response) => {
    let body = '';
    request.on('data', (chunk) => { body += chunk; });
    request.on('end', () => {
      received.push({ path: request.url, auth: request.headers.authorization, body: JSON.parse(body) });
      response.setHeader('content-type', 'application/json');
      response.end(JSON.stringify({ ok: true }));
    });
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  process.env.AEION_BRIDGE_URL = `http://127.0.0.1:${server.address().port}`;
  process.env.AEION_BRIDGE_TOKEN = 'fixture-token';
  process.env.AEION_WORKSPACE = '/sandbox/workspace';
  const tool = submitFeedback();
  assert.equal(v.safeParse(tool.input, { text: '' }).success, false);
  assert.equal(v.safeParse(tool.input, { text: 'RAS', path: '/etc/hosts' }).success, false);
  assert.equal(feedbackSubmitted(), false);
  assert.equal(await tool.run({ data: { text: 'RAS' }, toolCallId: 'one' }), 'Feedback recorded.');
  assert.equal(feedbackSubmitted(), true);
  assert.deepEqual(received, [{ path: '/v1/feedback', auth: 'Bearer fixture-token', body: { text: 'RAS' } }]);
});
