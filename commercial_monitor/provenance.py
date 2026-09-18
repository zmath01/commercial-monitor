from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path

def sha256_file(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def write_manifest(paths, output):
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": {str(p): sha256_file(p) for p in paths if Path(p).exists()},
    }
    Path(output).write_text(json.dumps(manifest,indent=2),encoding="utf-8")
