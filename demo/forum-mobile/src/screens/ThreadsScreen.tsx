import React from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { Thread } from '../api';

type Props = {
  threads: Thread[];
  loading: boolean;
  error: string;
  onOpen: (thread: Thread) => void;
  onCompose: () => void;
  onRefresh: () => void;
  signedInAs: string | null;
};

/** The first screen a reader sees: what the forum holds, newest first, readable without an account. */
export function ThreadsScreen(props: Props): React.ReactElement {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Agora</Text>
        <Text style={styles.subtitle}>
          {props.signedInAs ? `signed in as ${props.signedInAs}` : 'reading as a guest'}
        </Text>
      </View>
      <View style={styles.actions}>
        <Pressable style={styles.button} onPress={props.onRefresh}>
          <Text style={styles.buttonText}>Refresh</Text>
        </Pressable>
        <Pressable style={[styles.button, styles.primary]} onPress={props.onCompose}>
          <Text style={[styles.buttonText, styles.primaryText]}>New thread</Text>
        </Pressable>
      </View>
      {props.loading ? <ActivityIndicator /> : null}
      {props.error ? <Text style={styles.error}>{props.error}</Text> : null}
      <ScrollView style={styles.list}>
        {props.threads.length === 0 && !props.loading ? (
          <Text style={styles.empty}>No thread yet. The first one is worth writing.</Text>
        ) : null}
        {props.threads.map((thread) => (
          <Pressable key={thread.id} style={styles.card} onPress={() => props.onOpen(thread)}>
            <Text style={styles.cardTitle}>{thread.title}</Text>
            <Text style={styles.cardBody} numberOfLines={3}>
              {thread.body}
            </Text>
            <Text style={styles.cardMeta}>{new Date(thread.created_ns / 1e6).toISOString()}</Text>
          </Pressable>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 64, paddingHorizontal: 16, backgroundColor: '#0b0d10' },
  header: { marginBottom: 16 },
  title: { color: '#f5f7fa', fontSize: 32, fontWeight: '700' },
  subtitle: { color: '#8b97a6', marginTop: 4 },
  actions: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  button: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2c3540',
  },
  primary: { backgroundColor: '#2f6feb', borderColor: '#2f6feb' },
  buttonText: { color: '#c8d2de', fontWeight: '600' },
  primaryText: { color: '#ffffff' },
  list: { flex: 1 },
  card: {
    padding: 14,
    marginBottom: 10,
    borderRadius: 10,
    backgroundColor: '#131820',
    borderWidth: 1,
    borderColor: '#1f2833',
  },
  cardTitle: { color: '#e9eef5', fontSize: 17, fontWeight: '600' },
  cardBody: { color: '#9aa7b6', marginTop: 6 },
  cardMeta: { color: '#5f6b79', marginTop: 8, fontSize: 12 },
  empty: { color: '#8b97a6', marginTop: 24, textAlign: 'center' },
  error: { color: '#ff8a8a', marginBottom: 12 },
});
