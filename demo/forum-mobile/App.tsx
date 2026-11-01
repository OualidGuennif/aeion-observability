import React, { useCallback, useEffect, useState } from 'react';
import { Pressable, StatusBar, StyleSheet, Text, View } from 'react-native';
import * as api from './src/api';
import type { Session, Thread } from './src/api';
import { ComposeScreen } from './src/screens/ComposeScreen';
import { SessionScreen } from './src/screens/SessionScreen';
import { ThreadsScreen } from './src/screens/ThreadsScreen';

type Route = 'threads' | 'session' | 'compose';

/**
 * Agora, on React Native: read the forum without an account, write with one.
 *
 * Navigation is a single piece of state on purpose — three screens do not justify a navigation
 * library, and a hand-rolled route keeps the demo readable. The API base comes from
 * `EXPO_PUBLIC_AGORA_API` so a phone can reach a forum running anywhere.
 */
export default function App(): React.ReactElement {
  const [route, setRoute] = useState<Route>('threads');
  const [threads, setThreads] = useState<Thread[]>([]);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('connecting');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [health, list] = await Promise.all([api.health(), api.listThreads(30)]);
      setStatus(`release ${health.release} · runtime ${health.runtime}`);
      setThreads(list);
    } catch (failure) {
      setStatus('offline');
      setError(describe(failure));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh().catch(() => undefined);
  }, [refresh]);

  const signIn = async (username: string, password: string) => {
    setBusy(true);
    setError('');
    try {
      setSession(await api.login(username, password));
      setRoute('threads');
    } catch (failure) {
      setError(describe(failure));
    } finally {
      setBusy(false);
    }
  };

  const createAccount = async (username: string, password: string) => {
    setBusy(true);
    setError('');
    try {
      await api.register(username, password);
      setSession(await api.login(username, password));
      setRoute('threads');
    } catch (failure) {
      setError(describe(failure));
    } finally {
      setBusy(false);
    }
  };

  const signOut = async () => {
    setBusy(true);
    try {
      await api.logout(session);
    } catch (failure) {
      setError(describe(failure));
    } finally {
      setSession(null);
      setBusy(false);
      setRoute('threads');
    }
  };

  const publish = async (title: string, body: string) => {
    setBusy(true);
    setError('');
    try {
      await api.createThread(session, title, body);
      setRoute('threads');
      await refresh();
    } catch (failure) {
      setError(describe(failure));
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      {route === 'threads' ? (
        <>
          <ThreadsScreen
            threads={threads}
            loading={loading}
            error={error}
            signedInAs={session ? session.account.username : null}
            onRefresh={() => refresh().catch(() => undefined)}
            onCompose={() => setRoute(session ? 'compose' : 'session')}
            onOpen={() => undefined}
          />
          <View style={styles.footer}>
            <Text style={styles.footerText}>{status}</Text>
            <Pressable style={styles.footerButton} onPress={() => setRoute('session')}>
              <Text style={styles.footerButtonText}>
                {session ? 'Account' : 'Sign in'}
              </Text>
            </Pressable>
          </View>
        </>
      ) : null}
      {route === 'session' ? (
        <SessionScreen
          session={session}
          error={error}
          busy={busy}
          onLogin={(username, password) => signIn(username, password).catch(() => undefined)}
          onRegister={(username, password) => createAccount(username, password).catch(() => undefined)}
          onLogout={() => signOut().catch(() => undefined)}
          onBack={() => setRoute('threads')}
        />
      ) : null}
      {route === 'compose' ? (
        <ComposeScreen
          signedIn={session !== null}
          error={error}
          busy={busy}
          onSubmit={(title, body) => publish(title, body).catch(() => undefined)}
          onCancel={() => setRoute('threads')}
        />
      ) : null}
    </View>
  );
}

function describe(failure: unknown): string {
  if (failure instanceof api.ApiError) {
    return failure.status === 0
      ? `cannot reach ${api.baseUrl()}`
      : `${failure.status}: ${failure.code}`;
  }
  return failure instanceof Error ? failure.message : 'unexpected_error';
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#0b0d10' },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#1f2833',
  },
  footerText: { color: '#5f6b79', fontSize: 12 },
  footerButton: { paddingVertical: 6, paddingHorizontal: 12 },
  footerButtonText: { color: '#8fb4ff', fontWeight: '600' },
});
