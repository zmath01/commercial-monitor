"""Atomic artifact writes; a failed request must not publish a partial file."""
from pathlib import Path
import os
import tempfile


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        binary = isinstance(text, bytes)
        options = {} if binary else {"encoding": "utf-8", "newline": ""}
        with os.fdopen(fd, "wb" if binary else "w", **options) as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
