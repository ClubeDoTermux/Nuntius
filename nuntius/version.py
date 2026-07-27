VERSION = "0.2.1"

import subprocess
from pathlib import Path


def get_local_commit() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=Path(__file__).parent,
        )
        return r.stdout.strip()[:12]
    except Exception:
        return ""


def get_local_branch() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=Path(__file__).parent,
        )
        return r.stdout.strip()
    except Exception:
        return "main"
