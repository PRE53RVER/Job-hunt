"""Entry point for every job-hunt script: makes sure the skill's private virtualenv exists, then runs the script in it.

  python run.py --setup-only            -> create/refresh the venv and exit
  python run.py <script.py> [args...]   -> run scripts/<script.py> with the venv's Python

Uses only the standard library so it works with any system Python 3.9+.
The venv lives at <skill>/.venv and is rebuilt only when requirements.txt changes.
"""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
VENV = SKILL / ".venv"
REQ = SKILL / "requirements.txt"
MARK = VENV / ".requirements.sha256"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_env() -> Path:
    want = hashlib.sha256(REQ.read_bytes()).hexdigest()
    py = venv_python()
    if py.exists() and MARK.exists() and MARK.read_text().strip() == want:
        return py

    print(f"[job-hunt] setting up Python environment in {VENV} (first run only)...", file=sys.stderr)
    uv = shutil.which("uv")
    if not py.exists():
        if uv:
            subprocess.run([uv, "venv", str(VENV), "--python", ">=3.10"], check=True)
        else:
            if sys.version_info < (3, 10):
                sys.exit("[job-hunt] Python 3.10+ is required (or install `uv` so it can fetch one).")
            subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    if uv:
        subprocess.run([uv, "pip", "install", "-q", "-r", str(REQ), "--python", str(py)], check=True)
    else:
        subprocess.run([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", str(REQ)], check=True)
    MARK.write_text(want)
    print("[job-hunt] environment ready.", file=sys.stderr)
    return py


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    py = ensure_env()
    if sys.argv[1] == "--setup-only":
        print(py)
        return
    script = SCRIPTS / sys.argv[1]
    if not script.exists():
        sys.exit(f"[job-hunt] no such script: {script}")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    sys.exit(subprocess.run([str(py), str(script), *sys.argv[2:]], env=env).returncode)


if __name__ == "__main__":
    main()
