import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import type { Session } from '../api';

type Props = {
  session: Session | null;
  error: string;
  busy: boolean;
  onLogin: (username: string, password: string) => void;
  onRegister: (username: string, password: string) => void;
  onLogout: () => void;
  onBack: () => void;
};

/**
 * Sign in, or create the first account of an empty forum.
 *
 * The password is never echoed, stored or logged here; the field is `secureTextEntry` and the value
 * lives in component state only until the request completes.
 */
export function SessionScreen(props: Props): React.ReactElement {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  if (props.session) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Signed in</Text>
        <Text style={styles.meta}>
          {props.session.account.username} · {props.session.account.role}
        </Text>
        <Text style={styles.meta}>
          session ends {new Date(props.session.expiresNs / 1e6).toISOString()}
        </Text>
        <Pressable style={styles.button} onPress={props.onLogout}>
          <Text style={styles.buttonText}>Sign out</Text>
        </Pressable>
        <Pressable style={styles.button} onPress={props.onBack}>
          <Text style={styles.buttonText}>Back to the forum</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Sign in</Text>
      <Text style={styles.meta}>
        A forum account, never a worker key: the two planes are separate on purpose.
      </Text>
      <TextInput
        style={styles.input}
        placeholder="username"
        placeholderTextColor="#5f6b79"
        autoCapitalize="none"
        autoCorrect={false}
        value={username}
        onChangeText={setUsername}
      />
      <TextInput
        style={styles.input}
        placeholder="password (12 characters or more)"
        placeholderTextColor="#5f6b79"
        secureTextEntry
        autoCapitalize="none"
        value={password}
        onChangeText={setPassword}
      />
      {props.error ? <Text style={styles.error}>{props.error}</Text> : null}
      <Pressable
        style={[styles.button, styles.primary]}
        disabled={props.busy}
        onPress={() => props.onLogin(username, password)}
      >
        <Text style={[styles.buttonText, styles.primaryText]}>
          {props.busy ? 'Signing in...' : 'Sign in'}
        </Text>
      </Pressable>
      <Pressable
        style={styles.button}
        disabled={props.busy}
        onPress={() => props.onRegister(username, password)}
      >
        <Text style={styles.buttonText}>Create an account</Text>
      </Pressable>
      <Pressable style={styles.button} onPress={props.onBack}>
        <Text style={styles.buttonText}>Back to the forum</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 64, paddingHorizontal: 16, backgroundColor: '#0b0d10' },
  title: { color: '#f5f7fa', fontSize: 28, fontWeight: '700', marginBottom: 8 },
  meta: { color: '#8b97a6', marginBottom: 16 },
  input: {
    borderWidth: 1,
    borderColor: '#2c3540',
    borderRadius: 8,
    padding: 12,
    color: '#e9eef5',
    marginBottom: 10,
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2c3540',
    marginTop: 8,
  },
  primary: { backgroundColor: '#2f6feb', borderColor: '#2f6feb' },
  buttonText: { color: '#c8d2de', fontWeight: '600', textAlign: 'center' },
  primaryText: { color: '#ffffff' },
  error: { color: '#ff8a8a', marginBottom: 8 },
});
