"""Run pytest and save results to test-results/ with local paths and host name removed.

Also writes test-results/run_info.json with a SHA-256 digest of the tested sources, so saved
results can be checked against the current code.

Usage:
  python scripts/run_tests.py           run tests, save results
  python scripts/run_tests.py --check   exit 1 if saved results do not match current sources
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "test-results"
SOURCES = ["app.py", "pyproject.toml", "requirements.txt", "src", "tests", "scripts", "data"]


def source_digest() -> str:
    files: list[Path] = []
    for s in SOURCES:
        p = ROOT / s
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files += [q for q in p.rglob("*") if q.is_file() and "__pycache__" not in q.parts]
    h = hashlib.sha256()
    for f in sorted(files, key=lambda q: q.relative_to(ROOT).as_posix()):
        body = f.read_bytes().replace(b"\r\n", b"\n")  # same digest for CRLF and LF checkouts
        h.update(f.relative_to(ROOT).as_posix().encode() + b"\0" + body + b"\0")
    return h.hexdigest()


def scrub(text: str) -> str:
    for p in {str(ROOT), str(ROOT).replace("\\", "/"), str(Path.home()), sys.prefix,
              tempfile.gettempdir()}:
        text = re.sub(re.escape(p), "<local>", text, flags=re.IGNORECASE)
    return re.sub(r'hostname="[^"]*"', 'hostname="<host>"', text).replace(platform.node(), "<host>")


def check() -> int:
    info = json.loads((OUT / "run_info.json").read_text(encoding="utf-8"))
    fresh = info["source_sha256"] == source_digest()
    print("saved results match current sources" if fresh else
          "STALE: sources changed since the saved run; re-run scripts/run_tests.py")
    return 0 if fresh and info["exit_code"] == 0 else 1


def main() -> int:
    if "--check" in sys.argv:
        return check()
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
    result = proc.stdout.strip().splitlines()[-1].strip("= ")
    sys.path.insert(0, str(ROOT / "src"))
    from csvclean import __version__

    info = {
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "csvclean_version": __version__,
        "python": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "result": result,
        "exit_code": proc.returncode,
        "source_sha256": source_digest(),
        "source_paths": SOURCES,
    }
    (OUT / "run_info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(result)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
