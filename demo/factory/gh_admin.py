"""Explicit administrative actions on the factory's own pull requests.

Kept separate from the read-only probe so a mutation is always a deliberate command.
The token is loaded from the owner's environment file and never printed.
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from factory.gh_probe import KEY, call, load_secret


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="OualidGuennif/aeion-autonomous-forum")
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--title")
    parser.add_argument("--body")
    args = parser.parse_args()
    load_secret(KEY)
    token = os.environ.get(KEY)
    if not token:
        print(json.dumps({"ok": False, "reason": "token_missing"}))
        return 2
    payload = {}
    if args.title:
        payload["title"] = args.title
    if args.body:
        payload["body"] = args.body
    if not payload:
        print(json.dumps({"ok": False, "reason": "nothing_to_change"}))
        return 2
    import ssl
    import certifi
    request = urllib.request.Request(
        f"https://api.github.com/repos/{args.repo}/pulls/{args.pr}",
        data=json.dumps(payload).encode(), method="PATCH")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("User-Agent", "aeion-factory")
    with urllib.request.urlopen(request, timeout=30,
                                context=ssl.create_default_context(cafile=certifi.where())) as response:
        body = json.loads(response.read().decode())
    print(json.dumps({"ok": True, "number": body.get("number"), "title": body.get("title"),
                      "html_url": body.get("html_url")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
