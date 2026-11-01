"""Read-only GitHub access probe for the factory publisher.

The token is loaded from the owner's environment file into this process only. It is never
printed, logged, hashed into output or written anywhere; every line this script emits is
non-secret metadata. Only GET requests are made.
"""
import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "demo") not in sys.path:
    sys.path.insert(0, str(ROOT / "demo"))
CANDIDATES = (ROOT / ".env", Path(__file__).resolve().parents[1] / ".local" / "stack.env")
KEY = "GH_API_KEY"


def tls_context():
    """The demo venv has no system trust store; prefer certifi when it is present."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError):
        return ssl.create_default_context()


def load_secret(name):
    """Populate the requested variable from the owner's files without ever echoing it."""
    if os.environ.get(name):
        return "process-environment"
    for path in CANDIDATES:
        if not path.is_file():
            continue
        try:
            lines = path.read_text().splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip().removeprefix("export ").strip() == name:
                os.environ[name] = value.strip().strip("'\"")
                return str(path)
    return None


def call(method, path, token):
    request = urllib.request.Request("https://api.github.com" + path, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("User-Agent", "aeion-factory-probe")
    try:
        with urllib.request.urlopen(request, timeout=30, context=tls_context()) as response:
            body = response.read().decode("utf-8")
            return response.status, (json.loads(body) if body else {}), dict(response.headers)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except ValueError:
            parsed = {"message": body[:200]}
        return exc.code, parsed, dict(exc.headers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", default="publish", choices=["build", "publish", "release"],
                        help="which credential of the .env.example table to probe")
    parser.add_argument("--repo", default="OualidGuennif/aeion-autonomous-forum")
    parser.add_argument("--base", default="develop")
    parser.add_argument("--pr", type=int, help="Inspect one pull request instead of probing access")
    parser.add_argument("--tree", help="List one repository directory instead of probing access")
    args = parser.parse_args()
    from factory.keys import names_for

    key = names_for(args.role)[0]
    source = load_secret(key)
    token = os.environ.get(key)
    if not token:
        print(json.dumps({"ok": False, "reason": "token_missing", "role": args.role,
                          "key": key, "looked_in": [str(p) for p in CANDIDATES]}))
        return 2
    out = {"ok": False, "role": args.role, "key": key, "token_source": source,
           "repo": args.repo, "base": args.base}
    if args.tree is not None:
        path = f"/repos/{args.repo}/contents/{args.tree}" if args.tree else f"/repos/{args.repo}/contents/"
        status, listing, _ = call("GET", path, token)
        out["tree_status"] = status
        if status == 200 and isinstance(listing, list):
            out["entries"] = sorted((e.get("name"), e.get("type")) for e in listing)
            out["ok"] = True
        else:
            out["tree_error"] = listing.get("message") if isinstance(listing, dict) else None
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0 if out["ok"] else 1
    if args.pr:
        status, pr, _ = call("GET", f"/repos/{args.repo}/pulls/{args.pr}", token)
        out["pr_status"] = status
        if status == 200:
            status, files, _ = call("GET", f"/repos/{args.repo}/pulls/{args.pr}/files", token)
            out.update(number=pr.get("number"), state=pr.get("state"), title=pr.get("title"),
                       head=(pr.get("head") or {}).get("ref"), base_ref=(pr.get("base") or {}).get("ref"),
                       mergeable=pr.get("mergeable"), html_url=pr.get("html_url"),
                       files=[(f.get("filename"), f.get("status")) for f in files] if isinstance(files, list) else None)
            out["ok"] = True
        else:
            out["pr_error"] = pr.get("message")
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0 if out["ok"] else 1
    status, body, _ = call("GET", f"/repos/{args.repo}", token)
    out["repo_status"] = status
    if status == 200:
        out["full_name"] = body.get("full_name")
        out["default_branch"] = body.get("default_branch")
        out["private"] = body.get("private")
        out["permissions"] = sorted(k for k, v in (body.get("permissions") or {}).items() if v)
    else:
        out["repo_error"] = body.get("message")
        print(json.dumps(out, indent=2))
        return 1
    status, body, _ = call("GET", f"/repos/{args.repo}/branches/{args.base}", token)
    out["base_status"] = status
    out["base_present"] = status == 200
    if status == 200:
        out["base_sha"] = (body.get("commit") or {}).get("sha", "")[:12]
    status, branches, _ = call("GET", f"/repos/{args.repo}/branches?per_page=100", token)
    if status == 200 and isinstance(branches, list):
        out["branches"] = [b.get("name") for b in branches]
    status, body, headers = call("GET", "/rate_limit", token)
    out["rate_remaining"] = body.get("rate", {}).get("remaining") if status == 200 else None
    scopes = headers.get("X-OAuth-Scopes")
    out["token_scopes"] = scopes.split(", ") if scopes else None
    out["ok"] = bool(out["base_present"])
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
