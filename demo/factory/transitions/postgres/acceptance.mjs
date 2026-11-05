import test from 'node:test';
import assert from 'node:assert/strict';

test('database-less liveness exposes no host, build or configuration values', async () => {
  const response = await fetch('http://127.0.0.1:8080/healthz', {
    signal: AbortSignal.timeout(3000),
  });
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: 'ok' });
});
