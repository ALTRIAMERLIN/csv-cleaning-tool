"""Run pytest and save results to test-results/ with local paths and host name removed.

Usage: python scripts/run_tests.py
"""
from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "test-results"


def scrub(text: str) -> str:
    for p in {str(ROOT), str(ROOT).replace("\\", "/"), str(Path.home()), sys.prefix,
              tempfile.gettempdir(), os.environ.get("KIROCREW_SCRATCH", "") or "\0"}:
        text = re.sub(re.escape(p), "<local>", text, flags=re.IGNORECASE)
    return re.sub(r'hostname="[^"]*"', 'hostname="<host>"', text).replace(platform.node(), "<host>")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    junit = OUT / "junit.xml"
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider",
             "--basetemp", str(Path(tmp) / "pt"), f"--junitxml={junit}"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        )
    (OUT / "pytest_output.txt").write_text(scrub(proc.stdout + proc.stderr), encoding="utf-8")
    junit.write_text(scrub(junit.read_text(encoding="utf-8")), encoding="utf-8")
    print(proc.stdout.strip().splitlines()[-1])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
