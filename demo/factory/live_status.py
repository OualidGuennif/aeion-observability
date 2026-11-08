"""Read-only live factory status. Status names only: no receipts, prompts or credentials.

Replaces the one-off controller, feature, progress, CI-feedback and protection probes.
Spec: knowledge/components/operator-cockpit.md
"""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "demo/.local/factory/factory.db"
PHASE = re.compile(r"[A-Za-z0-9_.:-]{1,80}")
CHECK = re.compile(r"[A-Za-z0-9_ .,/:+-]{1,80}")
TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,40}")
CI_PREFIXES = ("Required CI failed", "Supervisor:")


def parse_procargs(data):
    """Argv plus whether the execution mode is live. Trailing pairs are not returned."""
    if len(data) < 4:
        return 0, [], False
    argc = int.from_bytes(data[:4], "little")
    rest = data[4:]
    end = rest.find(b"\0")
    rest = rest[end + 1:]
    index = 0
    while index < len(rest) and rest[index] == 0:
        index += 1
    rest = rest[index:]
    args = []
    for _ in range(max(0, argc)):
        end = rest.find(b"\0")
        if end < 0:
            break
        args.append(rest[:end].decode("utf-8", "replace"))
        rest = rest[end + 1:]
    mode_live = False
    while rest:
        end = rest.find(b"\0")
        if end <= 0:
            break
        if rest[:end] == b"AEION_FACTORY_EXECUTION=live":
            mode_live = True
        rest = rest[end + 1:]
    return argc, args, mode_live


def procargs(pid):
    import ctypes
    import ctypes.util
    libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    sysctl = libc.sysctl
    sysctl.argtypes = [
        ctypes.POINTER(ctypes.c_int), ctypes.c_uint, ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t]
    sysctl.restype = ctypes.c_int
    mib = (ctypes.c_int * 3)(1, 49, pid)
    size = ctypes.c_size_t(0)
    if sysctl(mib, 3, None, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno())
    buf = ctypes.create_string_buffer(size.value)
    if sysctl(mib, 3, buf, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno())
    return parse_procargs(buf.raw[:size.value])


def token(value):
    return value if isinstance(value, str) and TOKEN.fullmatch(value) else "-"


def phase_name(value):
    return value if isinstance(value, str) and PHASE.fullmatch(value) else "-"


def ci_lines(feedback):
    """Supervisor CI lines only. Reviewer and author prose stays out of the report."""
    if not isinstance(feedback, list):
        return [], 0
    kept = [line for line in feedback if isinstance(line, str) and line.startswith(CI_PREFIXES) and len(line) <= 400]
    return kept, len(feedback) - len(kept)


def protection_lines(result):
    """HTTP status and required check names from a forge protection result."""
    if not isinstance(result, dict):
        return ["protection_status=- http=- check_count=0"]
    status = token(result.get("status")) if result.get("status") != "qualified" else "qualified"
    reason = token(result.get("reason"))
    http = result.get("http_status")
    http_text = str(http) if isinstance(http, int) else ("200" if status == "qualified" else "-")
    checks = result.get("checks") if isinstance(result.get("checks"), list) else []
    names = [name for name in checks if isinstance(name, str) and CHECK.fullmatch(name)]
    lines = [f"protection_status={status} reason={reason} http={http_text} check_count={len(names)}"]
    if names:
        lines.append("checks=" + ",".join(names))
    return lines


def format_build(row, now_ns):
    build_id, status, hold, raw, updated_ns, lease_until = row
    receipt = json.loads(raw) if raw else {}
    if not isinstance(receipt, dict):
        receipt = {}
    progress = receipt.get("progress") if isinstance(receipt.get("progress"), dict) else {}
    publisher = receipt.get("publisher") if isinstance(receipt.get("publisher"), dict) else {}
    circuit = receipt.get("circuit") if isinstance(receipt.get("circuit"), dict) else {}
    correction = receipt.get("correction") if isinstance(receipt.get("correction"), dict) else {}
    age = max(0, int((now_ns - int(updated_ns)) / 1_000_000_000))
    lease = isinstance(lease_until, int) and lease_until > now_ns
    return (f"build={str(build_id)[:12]} status={token(status)} hold={token(hold) if hold else '-'} "
            f"progress={phase_name(progress.get('phase'))} publisher={token(publisher.get('reason'))} "
            f"circuit={token(circuit.get('reason'))} trigger={token(correction.get('trigger'))} "
            f"updated_age_s={age} lease_active={lease}")


def format_progress(raw, now_ns, event_ns):
    try:
        item = json.loads(raw) if raw else {}
    except (TypeError, ValueError):
        return None
    if not isinstance(item, dict):
        return None
    detail = item.get("detail") if isinstance(item.get("detail"), dict) else {}
    age = max(0, int((now_ns - int(event_ns)) / 1_000_000_000))
    step = detail.get("step") if isinstance(detail.get("step"), int) else "-"
    failed = detail.get("failed_count") if isinstance(detail.get("failed_count"), int) else "-"
    return (f"progress={phase_name(item.get('phase'))} status={token(detail.get('status'))} "
            f"reason={token(detail.get('reason'))} step={step} failed={failed} age_s={age}")


def feedback_lines(conn, build_id):
    from factory.dispatch import correction_feedback
    row = conn.execute(
        "SELECT detail FROM events WHERE build_id=? AND event='correction' ORDER BY seq LIMIT 1",
        (build_id,)).fetchone()
    if row is None:
        return ["feedback_linked=False"]
    try:
        link = json.loads(row[0])
    except (TypeError, ValueError):
        return ["feedback_linked=False"]
    if not isinstance(link, dict):
        return ["feedback_linked=False"]
    print_attempt = link.get("attempt") if isinstance(link.get("attempt"), int) else "-"
    print_round = link.get("round") if isinstance(link.get("round"), int) else "-"
    lines = [f"correction_attempt={print_attempt} correction_round={print_round} "
             f"linked={isinstance(link.get('previous_build_id'), str)}"]
    previous = conn.execute(
        "SELECT receipt FROM builds WHERE build_id=?", (link.get("previous_build_id"),)).fetchone()
    try:
        receipt = json.loads(previous[0]) if previous and previous[0] else {}
    except (TypeError, ValueError):
        receipt = {}
    if not isinstance(receipt, dict):
        receipt = {}
    publisher = receipt.get("publisher") if isinstance(receipt.get("publisher"), dict) else {}
    marker = receipt.get("correction") if isinstance(receipt.get("correction"), dict) else {}
    names = []
    for item in (publisher.get("failed_checks") or [])[:8]:
        if isinstance(item, dict) and CHECK.fullmatch(str(item.get("name") or "")) and TOKEN.fullmatch(str(item.get("conclusion") or "")):
            names.append(item["name"] + " (" + item["conclusion"] + ")")
    lines.append(f"previous_publisher={token(publisher.get('reason'))} "
                 f"previous_trigger={token(marker.get('trigger'))} named_checks={len(names)}")
    lines.extend("check=" + name for name in names)
    feedback = correction_feedback(receipt)
    kept, others = ci_lines(feedback)
    lines.append(f"ci_lines={len(kept)} other_feedback_lines={others}")
    lines.extend("line=" + line for line in kept)
    return lines


def feature_lines(conn, feature_id, now_ns, feedback=False):
    rows = conn.execute(
        "SELECT build_id, status, IFNULL(hold_reason, ''), receipt, updated_ns, lease_until_ns "
        "FROM builds WHERE feature_id=? ORDER BY updated_ns DESC LIMIT 3", (feature_id,)).fetchall()
    if not rows:
        return ["build_found=False"]
    lines = [format_build(row, now_ns) for row in rows]
    if feedback:
        lines.extend(feedback_lines(conn, rows[0][0]))
    events = conn.execute(
        "SELECT detail, time_ns FROM events WHERE build_id=? AND event='progress' "
        "ORDER BY seq DESC LIMIT 15", (rows[0][0],)).fetchall()
    rendered = [format_progress(raw, now_ns, stamp) for raw, stamp in reversed(events)]
    lines.extend(line for line in rendered if line)
    return lines


def hold_lines(conn):
    rows = conn.execute(
        "SELECT feature_id, status, IFNULL(hold_reason, '') FROM builds b "
        "WHERE feature_id IN ('002', '003', '013') AND updated_ns = ("
        "SELECT MAX(updated_ns) FROM builds WHERE feature_id = b.feature_id)").fetchall()
    return [f"feature={fid} status={token(status)} hold={token(hold) if hold else '-'}"
            for fid, status, hold in rows]


def listener_lines():
    """The cockpit listener, without printing its command or its pairs."""
    try:
        text = subprocess.check_output(
            ["lsof", "-nP", "-iTCP:8088", "-sTCP:LISTEN"], text=True)
    except (OSError, subprocess.CalledProcessError):
        return ["listen_ok=False"]
    pid = None
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) > 1 and parts[1].isdigit() and "127.0.0.1:8088" in line:
            pid = int(parts[1])
            break
    if pid is None:
        return ["listen_ok=False"]
    alive = True
    try:
        os.kill(pid, 0)
    except OSError:
        alive = False
    lines = [f"pid={pid} alive={alive} listen_ok=True"]
    if not alive:
        return lines
    try:
        argc, args, mode_live = procargs(pid)
    except OSError:
        argc, args, mode_live = 0, [], False
    server = len(args) >= 2 and str(args[-1]).endswith("demo/app/server.py")
    lines.append(f"argc={argc} server_ok={server} mode_live={mode_live}")
    return lines


def open_db():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature", default="001")
    parser.add_argument("--feedback", action="store_true",
                        help="print the supervisor CI lines of the latest correction")
    parser.add_argument("--protection", action="store_true",
                        help="print the release token's branch-protection status")
    parser.add_argument("--no-listener", action="store_true")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9]{3}", args.feature):
        print("feature_invalid=True")
        return 2
    lines = [] if args.no_listener else listener_lines()
    if DB.is_file():
        conn = open_db()
        try:
            now = time.time_ns()
            lines.extend(feature_lines(conn, args.feature, now, feedback=args.feedback))
            lines.extend(hold_lines(conn))
        finally:
            conn.close()
    else:
        lines.append("db_found=False")
    if args.protection:
        lines.extend(release_protection())
    print("\n".join(lines))
    return 0


def release_protection():
    from factory.gh_probe import load_secret
    from factory.github import GitHubError, GitHubForge
    from factory.keys import names_for
    key = names_for("release")[0]
    source = load_secret(key)
    token = os.environ.get(key)
    if not token:
        return [f"key={key} present=False loaded={source is not None}"]
    forge = GitHubForge("OualidGuennif/aeion-autonomous-forum", token=token, dry_run=True)
    try:
        result = forge.protection()
    except (GitHubError, OSError, TimeoutError) as exc:
        return [f"key={key} present=True error_class={type(exc).__name__}"]
    return [f"key={key} present=True loaded=True", *protection_lines(result)]


if __name__ == "__main__":
    sys.exit(main())
