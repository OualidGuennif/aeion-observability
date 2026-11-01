"""A Redis cache with a file fallback that behaves the same way.

The playground must be testable on a laptop with no daemon and usable with a real Redis in front of
the forum. Both backends implement the same four operations, and every response says which one
answered, so a drill can never be mistaken for a Redis measurement.

The Redis client is a minimal RESP reader/writer: no dependency, no connection pool, one socket per
call with a timeout. It is deliberately not a general-purpose client.
"""
import json
import os
import socket
import time
from pathlib import Path

DEFAULT_TTL = 60
TIMEOUT = 1.0


class CacheError(ValueError):
    """A cache call that could not be completed; callers fail closed to the origin."""


def parse_url(url):
    """`redis://host:port` or `redis://:password@host:port/db` into connection keywords."""
    if not isinstance(url, str) or not url.startswith("redis://"):
        raise CacheError("unsupported_cache_url")
    rest = url[len("redis://"):]
    auth, _, location = rest.rpartition("@")
    database = 0
    if "/" in location:
        location, _, tail = location.partition("/")
        database = int(tail or 0)
    password = auth.partition(":")[2] if auth else None
    host, _, port = location.partition(":")
    return {"host": host or "127.0.0.1", "port": int(port or 6379),
            "password": password or None, "database": database}


class RedisCache:
    backend = "redis"

    def __init__(self, url, ttl=DEFAULT_TTL):
        self.options = parse_url(url)
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self.errors = 0

    def _command(self, *parts):
        payload = [f"*{len(parts)}\r\n".encode()]
        for part in parts:
            data = part if isinstance(part, bytes) else str(part).encode()
            payload.append(f"${len(data)}\r\n".encode() + data + b"\r\n")
        with socket.create_connection((self.options["host"], self.options["port"]),
                                      timeout=TIMEOUT) as connection:
            connection.settimeout(TIMEOUT)
            connection.sendall(b"".join(payload))
            return self._read(connection)

    @staticmethod
    def _read(connection):
        stream = connection.makefile("rb")
        line = stream.readline()
        if not line:
            raise CacheError("empty_reply")
        kind, body = line[:1], line[1:].strip()
        if kind == b"+":
            return body.decode()
        if kind == b"-":
            raise CacheError("redis_error:" + body.decode()[:80])
        if kind == b":":
            return int(body)
        if kind == b"$":
            length = int(body)
            if length < 0:
                return None
            return stream.read(length + 2)[:-2]
        if kind == b"*":
            count = int(body)
            return [RedisCache._read(connection) for _ in range(max(0, count))]
        raise CacheError("unknown_reply")

    def get(self, key):
        try:
            value = self._command("GET", key)
        except (OSError, CacheError):
            self.errors += 1
            raise
        if value is None:
            self.misses += 1
            return None
        self.hits += 1
        return value

    def set(self, key, value, ttl=None):
        ttl = self.ttl if ttl is None else int(ttl)
        try:
            if ttl > 0:
                return self._command("SET", key, value, "EX", ttl) == "OK"
            return self._command("SET", key, value) == "OK"
        except (OSError, CacheError):
            self.errors += 1
            raise

    def incr(self, key):
        try:
            return int(self._command("INCR", key))
        except (OSError, CacheError):
            self.errors += 1
            raise

    def ping(self):
        try:
            return self._command("PING") == "PONG"
        except (OSError, CacheError):
            return False

    def stats(self):
        return {"backend": self.backend, "hits": self.hits, "misses": self.misses,
                "errors": self.errors}


class FileCache:
    """Same semantics, one file per key, mtime-based expiry; used when no Redis answers."""

    backend = "file"

    def __init__(self, folder, ttl=DEFAULT_TTL):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        os.chmod(self.folder, 0o700)
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self.errors = 0

    def _path(self, key):
        safe = "".join(character if character.isalnum() else "-" for character in str(key))[:120]
        return self.folder / (safe + ".cache")

    def get(self, key):
        path = self._path(key)
        try:
            stat = path.stat()
        except OSError:
            self.misses += 1
            return None
        if time.time() - stat.st_mtime > self.ttl:
            path.unlink(missing_ok=True)
            self.misses += 1
            return None
        self.hits += 1
        return path.read_bytes()

    def set(self, key, value, ttl=None):
        path = self._path(key)
        data = value if isinstance(value, bytes) else str(value).encode()
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, path)
        return True

    def incr(self, key):
        path = self._path(key)
        try:
            value = int(path.read_text() or 0)
        except (OSError, ValueError):
            value = 0
        value += 1
        path.write_text(str(value))
        return value

    def ping(self):
        return True

    def stats(self):
        return {"backend": self.backend, "hits": self.hits, "misses": self.misses,
                "errors": self.errors}


def connect(url=None, fallback_dir=None, ttl=DEFAULT_TTL):
    """The real Redis when it answers, the file cache otherwise; the caller learns which."""
    if url:
        cache = RedisCache(url, ttl=ttl)
        if cache.ping():
            return cache, None
        reason = "redis_unreachable"
    else:
        reason = "redis_not_configured"
    return FileCache(fallback_dir or "/tmp/aeion-cache", ttl=ttl), reason


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
