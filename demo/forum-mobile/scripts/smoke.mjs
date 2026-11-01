/**
 * Smoke test for the API layer the app uses, run against a live forum.
 *
 * `src/api.ts` has no React Native imports on purpose: it is plain TypeScript over `fetch`, so it
 * can be compiled and executed by Node. That is how the client is verified without a simulator —
 * the screens are proven by the Metro bundle, the network contract by this script.
 *
 *   npx tsc src/api.ts --outDir build --module esnext --target es2022 --moduleResolution bundler
 *   node scripts/smoke.mjs http://127.0.0.1:8081
 */
import assert from 'node:assert/strict';
import * as api from '../build/api.js';

const base = process.argv[2] ?? 'http://127.0.0.1:8081';
process.env.EXPO_PUBLIC_AGORA_API = base;

const suffix = Date.now().toString(36);
const username = `smoke-${suffix}`;
const password = 'correct-horse-battery';

const steps = [];
function step(name, detail) {
  steps.push({ name, detail });
  console.log(`ok  ${name}${detail ? ` — ${detail}` : ''}`);
}

const health = await api.health();
assert.equal(health.status, 'ok');
step('healthz', `release ${health.release}, runtime ${health.runtime}`);

const before = await api.listThreads(5);
assert.ok(Array.isArray(before));
step('list threads as a guest', `${before.length} visible`);

const account = await api.register(username, password);
assert.equal(account.username, username);
step('register', `role ${account.role}`);

const session = await api.login(username, password);
assert.ok(session.cookie.length > 20, 'a signed cookie is returned');
assert.ok(session.expiresNs > Date.now() * 1e6);
assert.ok(session.csrf.length > 20, 'a CSRF token is returned with the session');
step('login', `cookie ${session.cookie.length} chars, csrf ${session.csrf.length} chars`);

const thread = await api.createThread(session, `Smoke thread ${suffix}`, 'Posted by the app client.');
assert.equal(thread.title, `Smoke thread ${suffix}`);
step('create thread', thread.id);

const fetched = await api.getThread(thread.id);
assert.equal(fetched.id, thread.id);
step('read it back');

const after = await api.listThreads(5);
assert.ok(after.some((item) => item.id === thread.id), 'the new thread is listed');
step('list contains the new thread', `${after.length} visible`);

await assert.rejects(
  () => api.createThread(null, 'No session', 'should be refused'),
  (error) => error.status === 401,
);
step('refuses to post without a session', '401');

await assert.rejects(
  () => api.login(username, 'wrong-password-here'),
  (error) => error.status === 401,
);
step('refuses a wrong password', '401');

// The double-submit half: a live session with the wrong token is refused before any write.
await assert.rejects(
  () => api.createThread({ ...session, csrf: 'not-the-token' }, 'No token', 'refused'),
  (error) => error.status === 403,
);
step('refuses a mutation without its CSRF token', '403');

const revoked = await api.logout(session);
assert.equal(revoked, true);
step('logout', 'revoked');
await assert.rejects(
  () => api.createThread(session, 'After logout', 'the cookie is revoked'),
  (error) => error.status === 401,
);
step('refuses the revoked session', '401');


console.log(`\n${steps.length} steps passed against ${base}`);
