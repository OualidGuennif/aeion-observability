// Tier 2: file tools on the host, confined to one workspace folder. This restricts the
// model-facing tools only; it is not OS isolation (the harness keeps the user's privileges).
// No shell: `exec` throws and only read/write/edit are offered. Writes stay under `src/`.
import { constants } from 'node:fs';
import { lstat, mkdir, open, readdir, realpath, rm } from 'node:fs/promises';
import { posix } from 'node:path';
import { createEditTool, createReadTool, createWriteTool, sandboxFromDriver } from '@flue/runtime';
import type { FileStat, SandboxDriver, SandboxFactory } from '@flue/runtime';

const LIMIT = 1048576;
const WRITABLE = 'src/';

function relative(root: string, path: string): string {
  const target = posix.normalize(path);
  const rel = posix.relative(root, target);
  if (!posix.isAbsolute(target) || rel === '..' || rel.startsWith('../') || posix.isAbsolute(rel))
    throw new Error(`Path is outside the workspace: ${path}`);
  return rel;
}

// Refuse a symlink anywhere on the path; components that do not exist yet are allowed.
async function resolve(root: string, path: string, scope: 'read' | 'write'): Promise<string> {
  const rel = relative(root, path);
  if (scope === 'write' && !rel.startsWith(WRITABLE)) throw new Error(`Only ${WRITABLE} is writable: ${path}`);
  let current = root;
  for (const part of rel ? rel.split('/') : []) {
    current = posix.join(current, part);
    try {
      if ((await lstat(current)).isSymbolicLink()) throw new Error(`Symbolic links are not allowed: ${path}`);
    } catch (error: any) {
      if (error?.code === 'ENOENT') break;
      throw error;
    }
  }
  return current === root ? root : posix.join(root, rel);
}

async function readBytes(root: string, path: string): Promise<Uint8Array> {
  const handle = await open(await resolve(root, path, 'read'), constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const info = await handle.stat();
    if (!info.isFile()) throw new Error(`Not a regular file: ${path}`);
    if (info.size > LIMIT) throw new Error(`File larger than 1 MiB: ${path}`);
    const buffer = Buffer.alloc(info.size);
    const { bytesRead } = await handle.read(buffer, 0, info.size, 0);
    return new Uint8Array(buffer.subarray(0, bytesRead));
  } finally {
    await handle.close();
  }
}

export function restrictedDriver(root: string): SandboxDriver {
  return {
    readFile: async (path) => new TextDecoder('utf-8', { fatal: true }).decode(await readBytes(root, path)),
    readFileBuffer: (path) => readBytes(root, path),
    writeFile: async (path, content) => {
      const data = typeof content === 'string' ? Buffer.from(content, 'utf-8') : Buffer.from(content);
      if (data.length > LIMIT) throw new Error(`Content larger than 1 MiB: ${path}`);
      const handle = await open(await resolve(root, path, 'write'),
                                constants.O_WRONLY | constants.O_CREAT | constants.O_TRUNC | constants.O_NOFOLLOW, 0o644);
      try {
        if (!(await handle.stat()).isFile()) throw new Error(`Not a regular file: ${path}`);
        await handle.writeFile(data);
      } finally {
        await handle.close();
      }
    },
    stat: async (path): Promise<FileStat> => {
      const info = await lstat(await resolve(root, path, 'read'));
      return { isFile: info.isFile(), isDirectory: info.isDirectory(), isSymbolicLink: false, size: info.size, mtime: info.mtime };
    },
    readdir: async (path) => (await readdir(await resolve(root, path, 'read'))).sort(),
    exists: async (path) => {
      try { await lstat(await resolve(root, path, 'read')); return true; } catch { return false; }
    },
    mkdir: async (path, options) => { await mkdir(await resolve(root, path, 'write'), { recursive: options?.recursive === true }); },
    rm: async (path, options) => {
      await rm(await resolve(root, path, 'write'), { recursive: options?.recursive === true, force: options?.force === true });
    },
    exec: async () => { throw new Error('Shell commands are not available in this workspace'); },
  };
}

export function workspaceFromEnv(env: NodeJS.ProcessEnv = process.env): string {
  if (!env.AEION_WORKSPACE?.startsWith('/')) throw new Error('AEION_WORKSPACE must be an absolute path');
  return env.AEION_WORKSPACE;
}

export function restrictedLocal(workspace: string = workspaceFromEnv()): SandboxFactory {
  return {
    createSandbox: async () => {
      const root = await realpath(workspace);
      return sandboxFromDriver(restrictedDriver(root), root);
    },
    // Replaces Flue's default six tools: no bash, grep or glob, which all need `exec`.
    tools: (sandbox) => [createReadTool(sandbox), createWriteTool(sandbox), createEditTool(sandbox)],
  };
}
