#!/usr/bin/env python3
# Spec: knowledge/policies/bounded-intake.md
"""PostToolUse/Stop hook: one-line feedback on tokens spent for nothing; it never blocks.

Narration: visible prose or JSON notes before or between tool calls. Tolerated are one required
status line of at most 100 characters per turn (some harnesses ask for one) and the final
answer after the last tool. PostToolUse warns once per turn; Stop records the turn's total in
.aeion/context/narration-<session>.json. Rewrite: a Write that replaced an existing file with
200+ lines, where Edit would have sent only the change.

The transcript is read in Claude Code's and Codex's JSONL shapes; any other shape, or any error,
means silence. Exit 0 always: feedback must never stop work."""
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_TAIL = 4 * 1024 * 1024
STATUS_LIMIT = 100
REWRITE_LINES = 200
SESSION = re.compile(r"[A-Za-z0-9_-]{1,100}")


def tail_records(path):
    """Parsed JSONL records from the transcript's bounded tail; unparsable lines are skipped."""
    transcript = Path(path)
    if transcript.is_symlink() or not transcript.is_file():
        return []
    with transcript.open("rb") as stream:
        size = stream.seek(0, 2)
        stream.seek(max(0, size - MAX_TAIL))
        if size > MAX_TAIL:
            stream.readline()
        lines = stream.read().splitlines()
    records = []
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            records.append((line, record))
    return records


def is_prompt_text(text):
    # Injected context (system reminders, environment blocks) is tagged; a person's prompt is not.
    return isinstance(text, str) and bool(text.strip()) and not text.lstrip().startswith("<")


def events(record):
    """('turn',) for a new user prompt, ('text', s) for assistant text, ('tool',) for a tool call."""
    # Claude Code: one record per message, content blocks inside.
    if record.get("subtype") == "compact_boundary":
        return [("turn",)]
    message = record.get("message")
    if record.get("type") in {"user", "assistant"} and isinstance(message, dict):
        content = message.get("content")
        if record["type"] == "user":
            if record.get("isMeta") or record.get("toolUseResult") is not None:
                return []
            parts = [content] if isinstance(content, str) else [p.get("text") for p in content or []
                                                               if isinstance(p, dict) and p.get("type") == "text"]
            tool_results = isinstance(content, list) and any(isinstance(p, dict) and p.get("type") == "tool_result"
                                                             for p in content)
            return [("turn",)] if not tool_results and any(is_prompt_text(p) for p in parts) else []
        found = []
        for part in content if isinstance(content, list) else []:
            if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                found.append(("text", part["text"]))
            elif isinstance(part, dict) and part.get("type") == "tool_use":
                found.append(("tool",))
        return found
    # Codex: response items with a payload.
    payload = record.get("payload")
    if record.get("type") == "response_item" and isinstance(payload, dict):
        kind = payload.get("type")
        if kind in {"function_call", "custom_tool_call", "local_shell_call"}:
            return [("tool",)]
        if kind == "message" and isinstance(payload.get("content"), list):
            texts = [p.get("text") for p in payload["content"] if isinstance(p, dict)]
            if payload.get("role") == "user":
                return [("turn",)] if any(is_prompt_text(t) for t in texts) else []
            if payload.get("role") == "assistant":
                return [("text", t) for t in texts if isinstance(t, str)]
    return []


def current_turn(records):
    """The turn key (hash of its prompt record) and its ordered text/tool events."""
    key, turn = None, []
    for line, record in records:
        for event in events(record):
            if event[0] == "turn":
                key, turn = hashlib.sha256(line).hexdigest()[:16], []
            else:
                turn.append(event)
    return key, turn


def narration(texts):
    """Visible narration, excluding only the turn's one short non-JSON status line."""
    total, status_used = 0, False
    for raw in texts:
        text = raw.strip()
        if not text:
            continue
        if not status_used and not text.startswith(("{", "[")) and "\n" not in text and len(text) <= STATUS_LIMIT:
            status_used = True
            continue
        total += len(text)
    return total


def between_tools(turn):
    """Texts written before the turn's last tool call: the answer after it is not narration."""
    last = max((i for i, event in enumerate(turn) if event[0] == "tool"), default=-1)
    return [event[1] for event in turn[:last] if event[0] == "text"]


def rewrite_note(event):
    data, response = event.get("tool_input"), event.get("tool_response")
    if event.get("tool_name") != "Write" or not isinstance(data, dict) or not isinstance(response, dict):
        return None
    content = data.get("content")
    if response.get("type") != "update" or not isinstance(content, str):
        return None
    lines = content.count("\n") + 1
    if lines < REWRITE_LINES:
        return None
    return f"rewrite: Write resent {lines} lines of an existing file; Edit sends only the change."


def post_tool_use(event, session):
    notes = []
    rewrite = rewrite_note(event)
    if rewrite:
        notes.append(rewrite)
    key, turn = current_turn(tail_records(event.get("transcript_path") or ""))
    # After a tool ran, everything the turn has written so far came before a tool call.
    chars = narration(event[1] for event in turn if event[0] == "text")
    # Once per turn: the reminder is the cost we accept, a stream of them is not.
    state = Path(tempfile.gettempdir()) / f"aeion-narration-{session}"
    if key and chars and not state.is_symlink() and (not state.exists() or state.read_text().strip() != key):
        state.write_text(key + "\n")
        notes.append(f"narration: {chars} chars of visible narration between tools this turn; "
                     "keep reasoning private; omit optional progress and JSON notes. "
                     "Use tools directly until a necessary user decision or the final result.")
    if notes:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                 "additionalContext": "\n".join(notes)}}))


def stop(event, session):
    key, turn = current_turn(tail_records(event.get("transcript_path") or ""))
    if not key or not any(kind == "tool" for kind, *_ in turn):
        return
    chars = narration(between_tools(turn))
    record = ROOT / ".aeion/context" / f"narration-{session}.json"
    if record.is_symlink():
        return
    totals = json.loads(record.read_text()) if record.is_file() and not record.is_symlink() else {}
    turns = totals.get("turns", {})
    # A Stop that a sign-off reminder sent back fires again for the same turn: replace, never add twice.
    turns[key] = chars
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps({"turns": turns, "chars": sum(turns.values()),
                                  "turns_with_narration": sum(1 for c in turns.values() if c)},
                                 sort_keys=True) + "\n")


def main():
    try:
        event = json.loads(sys.stdin.read(2 * 1024 * 1024))
        session = event.get("session_id") if isinstance(event, dict) else None
        if not isinstance(session, str) or not SESSION.fullmatch(session):
            return 0
        if event.get("hook_event_name") == "Stop":
            stop(event, session)
        else:
            post_tool_use(event, session)
    except Exception:  # noqa: BLE001 - advisory feedback must never fail a tool call or a stop.
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
