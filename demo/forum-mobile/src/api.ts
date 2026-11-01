/**
 * The Agora forum's API client, and the only place that knows about the session cookie.
 *
 * The forum authenticates browsers with an HttpOnly cookie. React Native's `fetch` does not expose
 * `Set-Cookie` on every platform, so the client reads the login response header explicitly, keeps
 * the signed value in memory, and sends it back as a `Cookie` header. Nothing is persisted: a
 * fifteen-minute session that survives a process restart is a session nobody asked for, and
 * persisting a bearer value on a phone is how a demo becomes a finding.
 */

export type Account = {
  id: string;
  username: string;
  role: string;
};

export type Session = {
  account: Account;
  expiresNs: number;
  cookie: string;
  /** The double-submit half of the cookie: required on every mutation (feature 006). */
  csrf: string;
};

export type Thread = {
  id: string;
  title: string;
  body: string;
  author_id: string;
  created_ns: number;
};

export type Setting = {
  name: string;
  value: string;
  updated_ns: number;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string) {
    super(`${status} ${code}`);
    this.status = status;
    this.code = code;
  }
}

const DEFAULT_BASE = 'http://127.0.0.1:8081';

/**
 * In a browser the cookie jar owns the session and `Cookie`/`Set-Cookie` are unreadable or
 * forbidden headers, so the client sends no cookie of its own and keeps only the CSRF token.
 * On a device the same code speaks to the same API with its own header.
 */
const browser = typeof document !== 'undefined';

/** The base URL: `EXPO_PUBLIC_AGORA_API` when set, loopback otherwise. */
export function baseUrl(): string {
  const configured = process.env.EXPO_PUBLIC_AGORA_API;
  return configured && configured.startsWith('http') ? configured.replace(/\/$/, '') : DEFAULT_BASE;
}

function cookieValue(header: string | null): string {
  if (!header) {
    return '';
  }
  const match = /agora_session=([^;]+)/.exec(header);
  return match ? match[1] : '';
}

type Auth = { cookie: string; csrf: string };

async function request<T>(path: string, init: RequestInit = {}, auth?: Auth): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(init.body ? { 'Content-Type': 'application/json' } : {}),
    ...(auth && auth.cookie && !browser ? { Cookie: `agora_session=${auth.cookie}` } : {}),
    // A mutation carrying a session cookie must carry its token, or the forum answers 403.
    ...(auth && init.method && init.method !== 'GET' ? { 'X-CSRF-Token': auth.csrf } : {}),
  };
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, { ...init, headers, credentials: 'include' });
  } catch (cause) {
    throw new ApiError(0, 'network_unreachable');
  }
  const text = await response.text();
  const body = text ? JSON.parse(text) : undefined;
  if (!response.ok) {
    throw new ApiError(response.status, (body && body.error) || 'request_failed');
  }
  return { body, headers: response.headers } as unknown as T;
}

export async function health(): Promise<{ status: string; release: string; runtime: string }> {
  const result = await request<{ body: { status: string; release: string; runtime: string } }>(
    '/healthz',
  );
  return result.body;
}

export async function listThreads(limit = 20): Promise<Thread[]> {
  const result = await request<{ body: { threads: Thread[] } }>(`/api/threads?limit=${limit}`);
  return result.body.threads;
}

export async function getThread(id: string): Promise<Thread> {
  const result = await request<{ body: Thread }>(`/api/threads/${encodeURIComponent(id)}`);
  return result.body;
}

export async function getSetting(name: string): Promise<Setting> {
  const result = await request<{ body: Setting }>(`/api/settings/${encodeURIComponent(name)}`);
  return result.body;
}

export async function register(username: string, password: string): Promise<Account> {
  const result = await request<{ body: Account }>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  return result.body;
}

export async function login(username: string, password: string): Promise<Session> {
  const response = await fetch(`${baseUrl()}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ username, password }),
    credentials: 'include',
  });
  const text = await response.text();
  const body = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new ApiError(response.status, body.error || 'login_failed');
  }
  // The browser stores the cookie itself and hides it from JavaScript; a device reads it here.
  const cookie = browser ? '' : cookieValue(response.headers.get('set-cookie'));
  if (!cookie && !browser) {
    throw new ApiError(500, 'session_cookie_missing');
  }
  if (!body.csrf) {
    throw new ApiError(500, 'csrf_token_missing');
  }
  return { account: body as Account, expiresNs: body.expires_ns, cookie, csrf: body.csrf };
}

export async function logout(session: Session | null): Promise<boolean> {
  if (!session) {
    return false;
  }
  const result = await request<{ body: { revoked: boolean } }>(
    '/api/auth/logout',
    { method: 'POST' },
    session,
  );
  return result.body.revoked;
}

export async function createThread(
  session: Session | null,
  title: string,
  body: string,
): Promise<Thread> {
  if (!session) {
    throw new ApiError(401, 'unauthorized');
  }
  const result = await request<{ body: Thread }>(
    '/api/threads',
    { method: 'POST', body: JSON.stringify({ title, body }) },
    session,
  );
  return result.body;
}
