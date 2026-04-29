"""
Project launcher.

Running `python main.py` starts the Streamlit app with the same defaults used
by the container setup, while still allowing extra Streamlit CLI flags to be
passed through.

The app itself uses a Strategy + Factory LLM layer, so model selection happens
inside the Streamlit UI rather than in this launcher.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
APP_FILE = PROJECT_ROOT / "app.py"
DEFAULT_STREAMLIT_ARGS = [
    "--server.port=8501",
    "--server.address=0.0.0.0",
    "--server.headless=true",
]


def main() -> int:
    if not APP_FILE.exists():
        raise FileNotFoundError(f"Streamlit app entrypoint not found: {APP_FILE}")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_FILE),
        *DEFAULT_STREAMLIT_ARGS,
        *sys.argv[1:],
    ]
    return subprocess.call(command, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
