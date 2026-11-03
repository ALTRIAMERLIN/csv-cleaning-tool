"""Drive the real Streamlit page in Edge: upload -> rules -> run -> download -> verify.

Usage: python scripts/ui_check.py OUT_DIR [--video] [--start-app]
  --start-app  start app.py on a free 127.0.0.1 port and stop it afterwards
  (without it, the app must already be running at http://127.0.0.1:8501)
Exit 0 only if every downloaded file is byte-identical to the core output.
"""
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from csvclean.core import Rules, process, render_outputs  # noqa: E402

URL = "http://127.0.0.1:8501"
CSV = ROOT / "data" / "demo_customers.csv"
RULES = json.loads((ROOT / "data" / "demo_rules.json").read_text(encoding="utf-8"))
LABELS = {
    "trim_columns": "Trim leading/trailing spaces",
    "required_columns": "Required",
    "email_columns": "Email format check",
    "dedupe_keys": "Remove duplicates by",
}


def pick(page: Page, label: str, values: list[str]) -> None:
    box = page.locator('[data-testid="stMultiSelect"]').filter(has_text=label)
    for v in values:
        inp = box.locator("input")
        inp.click()
        inp.press_sequentially(v, delay=40)
        page.wait_for_timeout(250)
        inp.press("Enter")
        page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    chosen = box.inner_text()
    missing = [v for v in values if v not in chosen]
    if missing:
        raise RuntimeError(f"{label}: not selected {missing}")


@contextmanager
def local_app():
    """Start app.py on a free localhost port, yield its URL, always stop this child afterwards."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
         "--server.address", "127.0.0.1", "--server.port", str(port),
         "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 60
        while True:
            if proc.poll() is not None:
                raise RuntimeError("Streamlit exited during startup")
            try:
                with urllib.request.urlopen(url + "/_stcore/health", timeout=2) as r:
                    if r.read() == b"ok":
                        break
            except OSError:
                pass
            if time.time() > deadline:
                raise RuntimeError("Streamlit did not start within 60 s")
            time.sleep(1)
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def main(out: Path, video: bool, url: str = URL) -> int:
    out.mkdir(parents=True, exist_ok=True)
    shots, dl = out / "screens", out / "downloads"
    shots.mkdir(exist_ok=True)
    dl.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(
            viewport={"width": 1600, "height": 900}, accept_downloads=True,
            record_video_dir=str(out / "video") if video else None,
            record_video_size={"width": 1600, "height": 900} if video else None)
        page = ctx.new_page()
        page.goto(url)
        page.get_by_text("Upload a CSV file to begin").wait_for(timeout=30000)
        page.locator('input[type="file"]').set_input_files(str(CSV))
        page.get_by_text("Data rows").wait_for()
        page.screenshot(path=str(shots / "1_preview.png"), full_page=True)
        for key, label in LABELS.items():
            pick(page, label, RULES[key])
        page.get_by_role("button", name="Run cleaning").click()
        page.get_by_text("Clean rows").wait_for()
        page.wait_for_timeout(1000)
        page.screenshot(path=str(shots / "2_results.png"), full_page=True)
        page.get_by_role("tab", name="Issues").click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(shots / "3_issues.png"), full_page=True)
        names = ["clean.csv", "issues.csv", "changes.csv", "summary.json"]
        for n in names:
            with page.expect_download() as d:
                page.get_by_role("button", name=f"⬇ {n}").click()
            d.value.save_as(str(dl / n))
        ctx.close()
        browser.close()

    expected = render_outputs(process(CSV.read_bytes(), Rules.from_dict(RULES), CSV.name))
    ok = True
    for n in names:
        got = (dl / n).read_bytes()
        same = got == expected[n]
        ok &= same
        print(f"{n}: {len(got)} bytes sha256={hashlib.sha256(got).hexdigest()[:16]} "
              f"{'MATCH' if same else 'DIFFERENT'}")
    print(json.loads(expected["summary.json"])["counts"])
    return 0 if ok else 1


if __name__ == "__main__":
    out_dir, record = Path(sys.argv[1]), "--video" in sys.argv
    if "--start-app" in sys.argv:
        with local_app() as app_url:
            code = main(out_dir, record, app_url)
    else:
        code = main(out_dir, record)
    raise SystemExit(code)
