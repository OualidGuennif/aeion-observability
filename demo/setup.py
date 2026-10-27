"""Generate private local credentials; copy only the explicitly authorized OpenCode key."""
import argparse
import base64
import os
from pathlib import Path
import re
import secrets


def read_key(path):
    if not path.is_file():
        return ""
    for line in path.read_text().splitlines():
        match = re.fullmatch(r"\s*(?:export\s+)?OPENCODE_API_KEY\s*=\s*(.*?)\s*", line)
        if not match:
            continue
        value = match[1]
        if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
            value = value[1:-1]
        if value and not re.fullmatch(r"[A-Za-z0-9._-]+", value):
            raise SystemExit("Unsupported OPENCODE_API_KEY format; use a dedicated simple dotenv entry.")
        return value
    return ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opencode-env", type=Path, help="Read OPENCODE_API_KEY only from this existing dotenv file")
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent / ".local"
    folder.mkdir(mode=0o700, exist_ok=True)
    path = folder / "stack.env"
    if path.exists():
        raise SystemExit("Local configuration already exists; preserving credentials and volumes.")
    os.umask(0o077)
    values = {key: secrets.token_hex(24) for key in (
        "POSTGRES_PASSWORD", "CLICKHOUSE_PASSWORD", "REDIS_PASSWORD", "MINIO_PASSWORD", "SALT", "NEXTAUTH_SECRET", "LANGFUSE_PASSWORD")}
    values.update(ENCRYPTION_KEY=secrets.token_hex(32), LANGFUSE_PUBLIC_KEY="pk-lf-" + secrets.token_hex(16),
                  LANGFUSE_SECRET_KEY="sk-lf-" + secrets.token_hex(24))
    values["LANGFUSE_AUTH"] = base64.b64encode((values["LANGFUSE_PUBLIC_KEY"] + ":" + values["LANGFUSE_SECRET_KEY"]).encode()).decode()
    values["OPENCODE_API_KEY"] = read_key(args.opencode_env) if args.opencode_env else ""
    with path.open("x") as output:
        output.write("".join(f"{key}={value}\n" for key, value in values.items()))
    print("Private demo configuration created. OpenCode key configured:", bool(values["OPENCODE_API_KEY"]))
    print("Langfuse login: demo@aeion.local; password is LANGFUSE_PASSWORD in demo/.local/stack.env.")
    print("Next: python3 demo/install.py && python3 demo/openshell/setup.py")
    print("Then: docker compose --env-file demo/.local/stack.env -f demo/compose.yaml up -d --build && python3 demo/run.py")


if __name__ == "__main__":
    main()
