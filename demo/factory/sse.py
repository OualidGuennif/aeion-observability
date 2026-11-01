"""Bounded server-sent-event hub for the factory board.

Events are metadata only: a monotonic sequence plus an event name and a JSON-safe
payload. A bounded ring buffer keeps a reconnect cursor window; a client that falls
behind the window is told to reload instead of receiving a partial history.
"""
import threading
from collections import deque


class SseHub:
    def __init__(self, max_events=200):
        self.max_events = max_events
        self._lock = threading.Lock()
        self._buffer = deque(maxlen=max_events)
        self._seq = 0

    def publish(self, event, data=None):
        with self._lock:
            self._seq += 1
            frame = {"seq": self._seq, "event": event, "data": data}
            self._buffer.append(frame)
            return dict(frame)

    def earliest_seq(self):
        with self._lock:
            if not self._buffer:
                return self._seq
            return self._buffer[0]["seq"]

    def replay(self, since=0):
        with self._lock:
            return [dict(f) for f in self._buffer if f["seq"] > since]
