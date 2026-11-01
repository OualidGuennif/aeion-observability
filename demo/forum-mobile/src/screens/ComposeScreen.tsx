import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

type Props = {
  signedIn: boolean;
  error: string;
  busy: boolean;
  onSubmit: (title: string, body: string) => void;
  onCancel: () => void;
};

/** Compose a thread. A guest is sent to the session screen instead of being told to try again. */
export function ComposeScreen(props: Props): React.ReactElement {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');

  if (!props.signedIn) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Sign in first</Text>
        <Text style={styles.meta}>Writing a thread needs a forum account; reading does not.</Text>
        <Pressable style={styles.button} onPress={props.onCancel}>
          <Text style={styles.buttonText}>Back</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>New thread</Text>
      <TextInput
        style={styles.input}
        placeholder="title"
        placeholderTextColor="#5f6b79"
        value={title}
        onChangeText={setTitle}
      />
      <TextInput
        style={[styles.input, styles.multiline]}
        placeholder="what do you want to say?"
        placeholderTextColor="#5f6b79"
        multiline
        value={body}
        onChangeText={setBody}
      />
      {props.error ? <Text style={styles.error}>{props.error}</Text> : null}
      <Pressable
        style={[styles.button, styles.primary]}
        disabled={props.busy}
        onPress={() => props.onSubmit(title, body)}
      >
        <Text style={[styles.buttonText, styles.primaryText]}>
          {props.busy ? 'Publishing...' : 'Publish'}
        </Text>
      </Pressable>
      <Pressable style={styles.button} onPress={props.onCancel}>
        <Text style={styles.buttonText}>Cancel</Text>
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
  multiline: { minHeight: 160, textAlignVertical: 'top' },
  button: {
    paddingVertical: 12,
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
