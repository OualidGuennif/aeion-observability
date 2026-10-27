// Flue sandbox adapter for an OpenShell sandbox owned by the supervisor. Every verb
// goes through the supervisor's loopback bridge, which executes a fixed helper inside
// the sandbox (agent UID, Landlock, no network). This process holds no OpenShell or
// Docker credential and never creates or deletes sandboxes.
import { sandboxFromDriver } from '@flue/runtime';
import type { FileStat, SandboxDriver, SandboxFactory } from '@flue/runtime';

type BridgeConfig = { url: string; token: string; cwd: string };

export function bridgeFromEnv(env: NodeJS.ProcessEnv = process.env): BridgeConfig {
  const url = env.AEION_BRIDGE_URL ?? '';
  if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(url)) throw new Error('AEION_BRIDGE_URL must be the loopback bridge');
  if (!env.AEION_BRIDGE_TOKEN || !env.AEION_WORKSPACE?.startsWith('/')) throw new Error('Bridge token and absolute workspace are required');
  return { url, token: env.AEION_BRIDGE_TOKEN, cwd: env.AEION_WORKSPACE };
}

async function call(config: BridgeConfig, route: string, body: Record<string, unknown>, signal?: AbortSignal) {
  const response = await fetch(`${config.url}/v1/${route}`, {
    method: 'POST',
    headers: { authorization: `Bearer ${config.token}`, 'content-type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });
  const result = await response.json();
  if (!response.ok || result.ok !== true) throw new Error(String(result.error ?? `bridge error ${response.status}`));
  return result;
}

export function openShellDriver(config: BridgeConfig): SandboxDriver {
  const fs = (op: string, path: string, extra: Record<string, unknown> = {}) => call(config, 'fs', { op, path, ...extra });
  const bytes = async (path: string) => Uint8Array.from(Buffer.from((await fs('read', path)).data, 'base64'));
  return {
    readFile: async (path) => new TextDecoder('utf-8', { fatal: true }).decode(await bytes(path)),
    readFileBuffer: bytes,
    writeFile: async (path, content) => {
      const data = typeof content === 'string' ? Buffer.from(content, 'utf-8') : Buffer.from(content);
      await fs('write', path, { data: data.toString('base64') });
    },
    stat: async (path): Promise<FileStat> => {
      const s = (await fs('stat', path)).stat;
      const stat: FileStat = { isFile: s.isFile, isDirectory: s.isDirectory, isSymbolicLink: s.isSymbolicLink, size: s.size };
      if (typeof s.mtimeMs === 'number') stat.mtime = new Date(s.mtimeMs);
      return stat;
    },
    readdir: async (path) => (await fs('readdir', path)).entries,
    exists: async (path) => {
      try { return (await fs('exists', path)).exists === true; } catch { return false; }
    },
    mkdir: async (path, options) => { await fs('mkdir', path, { recursive: options?.recursive === true }); },
    rm: async (path, options) => { await fs('rm', path, { recursive: options?.recursive === true, force: options?.force === true }); },
    exec: async (command, options) => {
      const result = await call(config, 'exec', {
        command, cwd: options?.cwd ?? null, env: options?.env ?? null, timeoutMs: options?.timeoutMs ?? null,
      }, options?.signal);
      return { stdout: result.stdout, stderr: result.stderr, exitCode: result.exitCode };
    },
  };
}

export function openshell(config: BridgeConfig = bridgeFromEnv()): SandboxFactory {
  return { createSandbox: async () => sandboxFromDriver(openShellDriver(config), config.cwd) };
}
