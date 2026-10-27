"""Install the host-native controller: Python venv, pinned tokenizers and the pinned Flue harness."""
from pathlib import Path
import shutil
import subprocess
import sys

DEMO = Path(__file__).resolve().parent
LOCAL = DEMO / ".local"
VENV = LOCAL / "venv"


def main():
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11+ is required")
    node = shutil.which("node")
    version = subprocess.check_output([node, "--version"]).decode().strip().lstrip("v") if node else "0"
    if tuple(int(part) for part in version.split(".")[:2]) < (22, 19) or not shutil.which("npm"):
        raise SystemExit("Node.js 22.19+ and npm are required for the Flue harness")
    LOCAL.mkdir(mode=0o700, exist_ok=True)
    for folder, mode in ((LOCAL / "data", 0o700), (LOCAL / "work", 0o700), (LOCAL / "work/published", 0o755)):
        folder.mkdir(mode=mode, parents=True, exist_ok=True)
    if not (VENV / "bin/python").exists():
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    python = str(VENV / "bin/python")
    subprocess.run([python, "-m", "pip", "install", "--quiet", "-r", str(DEMO / "requirements.txt")], check=True)
    subprocess.run([python, str(DEMO / "fetch_tokenizers.py")], check=True)
    # Exact lockfile install; no lifecycle scripts beyond what the pinned packages declare.
    subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=DEMO / "flue", check=True)
    print("Controller installed. Start the cockpit with: python3 demo/run.py")


if __name__ == "__main__":
    main()
