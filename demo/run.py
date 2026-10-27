"""Start the host-native cockpit on 127.0.0.1:8088 with the controller venv and private stack configuration."""
import os
from pathlib import Path

DEMO = Path(__file__).resolve().parent
PYTHON = DEMO / ".local/venv/bin/python"

if not PYTHON.exists():
    raise SystemExit("Run python3 demo/install.py first")
os.chdir(DEMO / "app")
os.execv(str(PYTHON), [str(PYTHON), str(DEMO / "app/server.py")])
