"""Loopback bridge from the Flue sandbox adapter to one supervisor-owned OpenShell sandbox.

Only fixed argv commands run inside the sandbox; nothing executes on the host. Request
contents are never logged. The harness receives this token, never OpenShell credentials.
"""
import base64
import binascii
import hmac
import json
import math
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from json_input import loads

HELPER = "/opt/demo/fs-helper.py"
OPERATIONS = {"read", "write", "stat", "readdir", "exists", "mkdir", "rm"}
MAX_BODY = 1572864 * 2
MAX_FILE = 1048576
MAX_OUTPUT = 1048576
DEFAULT_EXEC_SECONDS = 120
MAX_EXEC_SECONDS = 300
ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}")


def text(value):
    data = value if isinstance(value, bytes) else str(value or "").encode()
    clipped = data[:MAX_OUTPUT]
    suffix = "\n[aeion: output truncated at 1 MiB]" if len(data) > MAX_OUTPUT else ""
    return clipped.decode("utf-8", errors="replace") + suffix


def absolute(path):
    if not isinstance(path, str) or not path.startswith("/") or "\0" in path or len(path) > 4096:
        raise ValueError("path must be an absolute POSIX path")
    return path


class SandboxBridge:
    def __init__(self, sandbox, *, bind=("127.0.0.1", 0)):
        self.sandbox = sandbox
        self.token = secrets.token_urlsafe(32)
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def reply(self, status, value):
                data = json.dumps(value).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + bridge.token):
                    return self.reply(403, {"ok": False, "error": "BRIDGE_DENIED"})
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= MAX_BODY:
                        raise ValueError("request too large")
                    request = loads(self.rfile.read(length))
                    if not isinstance(request, dict):
                        raise ValueError("request must be an object")
                    if self.path == "/v1/fs":
                        return self.reply(200, bridge.fs(request))
                    if self.path == "/v1/exec":
                        return self.reply(200, bridge.exec(request))
                    return self.reply(404, {"ok": False, "error": "not_found"})
                except (ValueError, TypeError, binascii.Error) as error:
                    return self.reply(400, {"ok": False, "error": str(error)[:200]})
                except Exception:
                    # Never echo sandbox/runtime exception text to the model.
                    return self.reply(502, {"ok": False, "error": "SANDBOX_EXEC_FAILED"})

        self.server = ThreadingHTTPServer(bind, Handler)
        self.server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def fs(self, request):
        op, path = request.get("op"), absolute(request.get("path"))
        if op not in OPERATIONS:
            raise ValueError("unsupported operation")
        argv = ["python3", "-I", HELPER, op, path]
        argv += ["--recursive"] if request.get("recursive") is True else []
        argv += ["--force"] if request.get("force") is True else []
        stdin = None
        if op == "write":
            if not isinstance(request.get("data"), str):
                raise ValueError("write requires base64 data")
            stdin = base64.b64decode(request["data"], validate=True)
            if len(stdin) > MAX_FILE:
                raise ValueError("content larger than 1 MiB")
        result = self.sandbox.exec(argv, stdin=stdin, timeout=15)
        output = result.stdout if isinstance(result.stdout, bytes) else str(result.stdout or "").encode()
        if result.exit_code != 0 or len(output) > MAX_BODY:
            raise RuntimeError("FS_HELPER_FAILED")
        value = json.loads(output)
        if not isinstance(value, dict) or not isinstance(value.get("ok"), bool):
            raise RuntimeError("FS_HELPER_PROTOCOL")
        return value

    def exec(self, request):
        command, cwd, env, timeout_ms = (request.get(k) for k in ("command", "cwd", "env", "timeoutMs"))
        if not isinstance(command, str) or not command or len(command) > 65536 or "\0" in command:
            raise ValueError("command must be a non-empty string")
        if cwd is not None:
            absolute(cwd)
        if env is not None and (not isinstance(env, dict) or len(env) > 64 or any(
                not isinstance(k, str) or not ENV_NAME.fullmatch(k) or not isinstance(v, str) or len(v) > 4096
                for k, v in env.items())):
            raise ValueError("env must map simple names to strings")
        if timeout_ms is None:
            seconds = DEFAULT_EXEC_SECONDS
        elif type(timeout_ms) is int and timeout_ms > 0:
            seconds = min(MAX_EXEC_SECONDS, math.ceil(timeout_ms / 1000))
        else:
            raise ValueError("timeoutMs must be a positive integer")
        result = self.sandbox.exec(["/bin/bash", "-c", command], env=env, workdir=cwd, timeout=seconds)
        return {"ok": True, "stdout": text(result.stdout), "stderr": text(result.stderr), "exitCode": int(result.exit_code)}

    def start(self):
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
