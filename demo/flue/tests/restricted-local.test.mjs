import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, realpath, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { restrictedDriver, restrictedLocal, workspaceFromEnv } from '../src/sandboxes/restricted-local.ts';

async function workspace(t) {
  const base = await realpath(await mkdtemp(join(tmpdir(), 'aeion-local-')));
  t.after(() => rm(base, { recursive: true, force: true }));
  const root = join(base, 'workspace');
  await mkdir(join(root, 'src'), { recursive: true });
  await writeFile(join(root, 'src/pricing.js'), 'export function totalCents() {}\n');
  await writeFile(join(root, 'HANDOVER.md'), '# handover\n');
  await writeFile(join(base, 'secret.txt'), 'outside\n');
  return { base, root, driver: restrictedDriver(root) };
}

test('reads and writes stay inside the workspace, and writes inside src/', async (t) => {
  const { base, root, driver } = await workspace(t);
  assert.match(await driver.readFile(join(root, 'src/pricing.js')), /totalCents/);
  assert.equal(await driver.readFile(join(root, 'HANDOVER.md')), '# handover\n');
  await driver.writeFile(join(root, 'src/pricing.js'), 'export const ok = 1;\n');
  assert.equal(await readFile(join(root, 'src/pricing.js'), 'utf-8'), 'export const ok = 1;\n');
  assert.deepEqual(await driver.readdir(root), ['HANDOVER.md', 'src']);
  for (const path of [join(base, 'secret.txt'), join(root, '../secret.txt'), join(root, 'src/../../secret.txt'), '/etc/passwd', 'src/pricing.js'])
    await assert.rejects(driver.readFile(path), /outside the workspace/);
  for (const path of [join(root, 'HANDOVER.md'), join(root, 'src.js'), join(root, '.git/config')])
    await assert.rejects(driver.writeFile(path, 'x'), /Only src\/ is writable/);
  await assert.rejects(driver.rm(join(root, 'HANDOVER.md')), /Only src\/ is writable/);
  await assert.rejects(driver.mkdir(join(root, 'other')), /Only src\/ is writable/);
  assert.equal(await driver.exists(join(base, 'secret.txt')), false);
  assert.equal(await readFile(join(root, 'HANDOVER.md'), 'utf-8'), '# handover\n');
});

test('symbolic links are refused on every path component', async (t) => {
  const { base, root, driver } = await workspace(t);
  await symlink(base, join(root, 'src/up'));
  await symlink(join(base, 'secret.txt'), join(root, 'src/leak.js'));
  await assert.rejects(driver.readFile(join(root, 'src/up/secret.txt')), /Symbolic links are not allowed/);
  await assert.rejects(driver.readFile(join(root, 'src/leak.js')), /Symbolic links are not allowed/);
  await assert.rejects(driver.writeFile(join(root, 'src/leak.js'), 'x'), /Symbolic links are not allowed/);
  await assert.rejects(driver.writeFile(join(root, 'src/up/secret.txt'), 'x'), /Symbolic links are not allowed/);
  assert.equal(await readFile(join(base, 'secret.txt'), 'utf-8'), 'outside\n');
  assert.equal((await driver.stat(join(root, 'src'))).isSymbolicLink, false);
});

test('there is no shell and the model sees only read, write and edit', async (t) => {
  const { root, driver } = await workspace(t);
  await assert.rejects(driver.exec('cat /etc/passwd', {}), /Shell commands are not available/);
  const factory = restrictedLocal(root);
  const sandbox = await factory.createSandbox({ id: 'run-1' });
  assert.equal(sandbox.cwd, root);
  assert.deepEqual(factory.tools(sandbox).map((tool) => tool.name), ['read', 'write', 'edit']);
  // Flue's write wrapper creates missing parents through the same confined driver.
  await sandbox.writeFile('src/lib/new.js', 'export {};\n');
  assert.equal(await readFile(join(root, 'src/lib/new.js'), 'utf-8'), 'export {};\n');
  await assert.rejects(sandbox.writeFile('notes/new.md', 'x'), /Only src\/ is writable/);
});

test('oversized and non-UTF-8 files are refused', async (t) => {
  const { root, driver } = await workspace(t);
  await assert.rejects(driver.writeFile(join(root, 'src/big.js'), 'x'.repeat(1048577)), /larger than 1 MiB/);
  await writeFile(join(root, 'src/binary.js'), Buffer.from([0xff, 0xfe]));
  await assert.rejects(driver.readFile(join(root, 'src/binary.js')));
  await assert.rejects(driver.readFile(join(root, 'src')), /Not a regular file/);
});

test('the workspace must be an absolute path', () => {
  assert.throws(() => workspaceFromEnv({}), /AEION_WORKSPACE/);
  assert.throws(() => workspaceFromEnv({ AEION_WORKSPACE: 'relative' }), /AEION_WORKSPACE/);
  assert.equal(workspaceFromEnv({ AEION_WORKSPACE: '/work/run/workspace' }), '/work/run/workspace');
});
