import test from 'node:test';
import assert from 'node:assert/strict';

test('served application runs on a migrated PostgreSQL database', async () => {
  const health = await fetch('http://127.0.0.1:8080/healthz', {
    signal: AbortSignal.timeout(3000),
  });
  assert.equal(health.status, 200);
  const schema = await fetch('http://127.0.0.1:8080/api/schema', {
    signal: AbortSignal.timeout(3000),
  });
  assert.equal(schema.status, 200);
  const body = await schema.json();
  assert.ok(Array.isArray(body.applied) && body.applied.length > 0);
  assert.equal(body.pending, 0);
});
