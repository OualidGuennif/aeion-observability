"""Build-time fetch of pinned public tokenizer files, never model weights."""
import hashlib
import json
from pathlib import Path
import urllib.request

root = Path(__file__).resolve().parent
for name, entry in json.loads((root / "tokenizers.json").read_text()).items():
    folder = root / "tokenizers" / name
    folder.mkdir(parents=True, exist_ok=True)
    for filename, expected in entry["files"].items():
        url = f"https://huggingface.co/{entry['repo']}/resolve/{entry['revision']}/{filename}"
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(30000001)
        if len(data) > 30000000 or hashlib.sha256(data).hexdigest() != expected:
            raise SystemExit("Tokenizer fingerprint mismatch")
        (folder / filename).write_bytes(data)
