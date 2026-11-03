"""Record one real demo run of the local Streamlit page and write demo/demo_manifest.json.

The page is driven by Playwright in Microsoft Edge (headless) at 1920x1080:
upload the synthetic CSV -> preview -> set rules -> run -> view clean data, issues, change log
and summary -> download the four files. The downloads are then checked against the core
output and against a separate CLI run. Every number in the manifest comes from this run.

Recording: every frame Edge paints is captured with the DevTools screencast (JPEG, quality 92)
together with its timestamp, then ffmpeg encodes the frames at their real timing into one
uncut 30 fps H.264 file. No cuts and no speed changes.

A small cursor marker is injected into the page so viewers can see where the script points
and clicks. It is hidden while screenshots are taken. Nothing else on the page is changed.

Usage: python scripts/record_demo.py [--force]   (needs ffmpeg on PATH)
Writes: demo/recording/raw_recording.mp4, demo/screens/*.png,
        demo/outputs/* (downloaded files), demo/demo_manifest.json
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from csvclean import __version__  # noqa: E402
from csvclean.core import Rules, process, render_outputs  # noqa: E402
from ui_check import CSV, LABELS, RULES, local_app  # noqa: E402

DEMO = ROOT / "demo"
EXPECTED = ROOT / "data" / "expected" / "demo_expected.json"
NAMES = ["clean.csv", "issues.csv", "changes.csv", "summary.json"]
SIZE = {"width": 1920, "height": 1080}

CURSOR_JS = """
(() => {
  const install = () => {
    if (document.getElementById('__demo_cursor')) return;
    const c = document.createElement('div');
    c.id = '__demo_cursor';
    Object.assign(c.style, {position: 'fixed', left: '-100px', top: '-100px', width: '26px',
      height: '26px', marginLeft: '-13px', marginTop: '-13px', borderRadius: '50%',
      background: 'rgba(37, 99, 235, 0.25)', border: '3px solid rgba(37, 99, 235, 0.9)',
      pointerEvents: 'none', zIndex: '2147483647', transition: 'transform 90ms ease-out'});
    document.body.appendChild(c);
    const move = e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; };
    document.addEventListener('mousemove', move, true);
    document.addEventListener('mousedown', () => { c.style.transform = 'scale(0.7)'; }, true);
    document.addEventListener('mouseup', () => { c.style.transform = 'scale(1)'; }, true);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install);
  else install();
})();
"""


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()


class Screencast:
    """Save every painted frame with its browser timestamp (seconds since the epoch)."""

    def __init__(self, page: Page, folder: Path):
        self.folder = folder
        self.frames: list[tuple[float, str]] = []
        self.cdp = page.context.new_cdp_session(page)
        self.cdp.on("Page.screencastFrame", self._on_frame)

    def start(self) -> None:
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92,
                                               "maxWidth": SIZE["width"],
                                               "maxHeight": SIZE["height"], "everyNthFrame": 1})

    def _on_frame(self, params: dict) -> None:
        name = f"f{len(self.frames):06d}.jpg"
        (self.folder / name).write_bytes(base64.b64decode(params["data"]))
        ts = params.get("metadata", {}).get("timestamp") or time.time()
        self.frames.append((float(ts), name))
        self.cdp.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})

    def stop(self) -> None:
        self.cdp.send("Page.stopScreencast")


def encode(frames: list[tuple[float, str]], folder: Path, end: float, out: Path) -> None:
    """Encode frames at their real timing (variable gaps) into constant 30 fps H.264."""
    lines = ["ffconcat version 1.0"]
    for i, (ts, name) in enumerate(frames):
        nxt = frames[i + 1][0] if i + 1 < len(frames) else max(end, ts + 1 / 30)
        lines += [f"file '{name}'", f"duration {max(nxt - ts, 0.001):.6f}"]
    lines.append(f"file '{frames[-1][1]}'")  # concat demuxer needs the last entry repeated
    (folder / "frames.ffconcat").write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", "frames.ffconcat", "-vf",
         "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
         "-fps_mode", "cfr", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-pix_fmt", "yuv420p", "-threads", "4", "-movflags", "+faststart", "-an", str(out)],
        cwd=folder, check=True)


class Demo:
    def __init__(self, page: Page):
        self.page = page
        self.timeline: list[dict] = []
        self.screens: list[str] = []

    def mark(self, event: str) -> None:
        self.timeline.append({"epoch": time.time(), "event": event})

    def pause(self, ms: int) -> None:
        self.page.wait_for_timeout(ms)

    def glide(self, loc: Locator) -> None:
        loc.scroll_into_view_if_needed()
        box = loc.bounding_box()
        self.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=28)
        self.pause(250)

    def click(self, loc: Locator) -> None:
        self.glide(loc)
        loc.click()

    def scroll_to(self, loc: Locator, block: str = "start") -> None:
        loc.evaluate("(el, b) => el.scrollIntoView({behavior: 'smooth', block: b})", block)
        self.pause(1100)

    def wheel_over(self, loc: Locator, steps: int, dy: int = 120) -> None:
        self.glide(loc)
        for _ in range(steps):
            self.page.mouse.wheel(0, dy)
            self.pause(260)

    def shot(self, name: str) -> None:
        path = DEMO / "screens" / name
        self.page.evaluate("document.getElementById('__demo_cursor').style.display = 'none'")
        self.page.screenshot(path=str(path))
        self.page.evaluate("document.getElementById('__demo_cursor').style.display = 'block'")
        self.screens.append(path.relative_to(ROOT).as_posix())
        self.mark(f"screenshot {name}")

    def pick(self, label: str, values: list[str]) -> None:
        box = self.page.locator('[data-testid="stMultiSelect"]').filter(has_text=label)
        inp = box.locator("input")
        self.click(inp)
        for v in values:
            inp.press_sequentially(v, delay=85)
            self.pause(350)
            inp.press("Enter")
            self.pause(450)
        self.page.keyboard.press("Escape")
        missing = [v for v in values if v not in box.inner_text()]
        if missing:
            raise RuntimeError(f"{label}: not selected {missing}")
        self.mark(f"rule set: {label} = {', '.join(values)}")
        self.pause(500)


def run_demo(url: str, frames_dir: Path, downloads: Path) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(viewport=SIZE, accept_downloads=True)
        ctx.add_init_script(CURSOR_JS)
        page = ctx.new_page()
        cast = Screencast(page, frames_dir)
        cast.start()
        d = Demo(page)
        page.goto(url)
        page.get_by_text("Upload a CSV file to begin").wait_for(timeout=30000)
        page.mouse.move(960, 700)
        d.mark("page ready (empty, waiting for upload)")
        d.pause(2000)

        with page.expect_file_chooser() as fc:
            d.click(page.locator('[data-testid="stFileUploader"] button').first)
        d.mark("upload: Upload button clicked, file chosen")
        fc.value.set_files(str(CSV))
        page.get_by_text("Data rows").wait_for()
        d.mark("preview shown")
        d.pause(1200)
        d.scroll_to(page.locator("h2", has_text="2. Preview"))
        d.pause(2500)
        d.shot("01_preview.png")
        d.wheel_over(page.locator('[data-testid="stDataFrame"]').first, 3)
        d.mark("preview table scrolled")
        d.pause(1200)

        d.scroll_to(page.locator("h2", has_text="3. Rules"))
        d.mark("rules section")
        d.pause(800)
        for key, label in LABELS.items():
            d.pick(label, RULES[key])
        d.glide(page.get_by_text("first occurrence"))
        d.mark(f"keep = {RULES['dedupe_keep']} occurrence (default, left unchanged)")
        d.pause(1000)
        d.shot("02_rules.png")

        d.click(page.get_by_role("button", name="Run cleaning"))
        d.mark("run clicked")
        page.get_by_text("Clean rows").wait_for()
        d.mark("results shown")
        d.pause(600)
        d.scroll_to(page.locator("h2", has_text="4. Results"))
        d.pause(2500)
        d.shot("03_results.png")

        for tab, event in (("Clean data", "tab: clean data"), ("Issues", "tab: issues"),
                           ("Change log", "tab: change log"), ("Summary", "tab: summary")):
            d.click(page.get_by_role("tab", name=tab))
            d.mark(event)
            d.pause(1800)
            if tab == "Issues":
                d.shot("04_issues.png")
                # get_by_role skips hidden elements, so this is the open tab's panel only
                d.wheel_over(page.get_by_role("tabpanel").locator(
                    '[data-testid="stDataFrame"]').first, 4)
                d.pause(900)
            elif tab == "Change log":
                d.shot("05_change_log.png")
                d.pause(800)
            elif tab == "Summary":
                d.wheel_over(page.locator('[data-testid="stJson"]'), 3)
                d.pause(900)

        d.scroll_to(page.locator("h2", has_text="5. Download"))
        d.mark("download section")
        d.pause(1500)
        for name in NAMES:
            with page.expect_download() as dl:
                d.click(page.get_by_role("button", name=f"⬇ {name}"))
            dl.value.save_as(str(downloads / name))
            d.mark(f"downloaded {name}")
            d.pause(900)
        d.glide(page.locator('[data-testid="stDataFrame"]').last)
        d.mark("SHA-256 table")
        d.pause(1000)
        d.shot("06_downloads.png")
        d.pause(2500)
        d.mark("end")
        end = time.time()
        d.pause(300)
        cast.stop()
        browser_version = browser.version
        ctx.close()
        browser.close()
    if not cast.frames:
        raise RuntimeError("the screencast produced no frames")
    raw = DEMO / "recording" / "raw_recording.mp4"
    encode(cast.frames, frames_dir, end, raw)
    start = cast.frames[0][0]
    timeline = [{"t": round(e["epoch"] - start, 2), "event": e["event"]} for e in d.timeline]
    return {"timeline": timeline, "screens": d.screens, "browser": browser_version, "raw": raw,
            "frames": len(cast.frames), "span_s": round(end - start, 2)}


def probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,avg_frame_rate,nb_frames:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True)
    j = json.loads(out.stdout)
    s = j["streams"][0]
    return {"width": s["width"], "height": s["height"], "fps": s["avg_frame_rate"],
            "frames": int(s.get("nb_frames", 0)), "duration_s": round(float(j["format"]["duration"]), 2)}


def main() -> int:
    if DEMO.exists() and "--force" not in sys.argv:
        print("demo/ already exists; pass --force to record again", file=sys.stderr)
        return 2
    commit, dirty = git("rev-parse", "HEAD"), git("status", "--porcelain") != ""
    if dirty:
        print("refusing to record: commit your changes first, so the manifest names the "
              "exact program version", file=sys.stderr)
        return 2
    for sub in ("recording", "screens", "outputs"):
        shutil.rmtree(DEMO / sub, ignore_errors=True)
        (DEMO / sub).mkdir(parents=True)

    recorded = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with tempfile.TemporaryDirectory() as tmp, local_app() as url:
        (Path(tmp) / "frames").mkdir()
        info = run_demo(url, Path(tmp) / "frames", DEMO / "outputs")

        cli_dir = Path(tmp) / "cli"
        cli = subprocess.run([sys.executable, "-m", "csvclean", str(CSV), "--out", str(cli_dir),
                              "--rules", str(ROOT / "data" / "demo_rules.json")],
                             cwd=ROOT, capture_output=True, text=True)
        cli_files = {n: (cli_dir / n).read_bytes() for n in NAMES} if cli.returncode == 0 else {}

    got = {n: (DEMO / "outputs" / n).read_bytes() for n in NAMES}
    core = render_outputs(process(CSV.read_bytes(), Rules.from_dict(RULES), CSV.name))
    summary = json.loads(got["summary.json"])
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    rows = {n: len(list(csv.reader(io.StringIO(got[n].decode("utf-8-sig"), newline="")))) - 1
            for n in NAMES[:3]}  # data rows, header excluded; quoted line breaks stay in one row
    raw = info["raw"]
    checks = {
        "downloads_match_core_output": all(got[n] == core[n] for n in NAMES),
        "downloads_match_cli_output": bool(cli_files) and all(got[n] == cli_files[n]
                                                              for n in NAMES),
        "counts_match_expected": summary["counts"] == expected["counts"],
        "reason_counts_match_expected": summary["reason_counts"] == expected["reason_counts"],
        "accounting_ok": summary["accounting_ok"],
        "input_sha256_matches_file": summary["input_sha256"] == sha256(CSV.read_bytes()),
    }
    manifest = {
        "project": "CSV Data Cleaning & Validation Tool",
        "label": "Personal demo, synthetic data",
        "recorded_utc": recorded,
        "program": {
            "csvclean_version": __version__, "git_commit": commit, "working_tree_clean": True,
            "python": platform.python_version(), "streamlit": version("streamlit"),
            "playwright": version("playwright"), "browser": f"Microsoft Edge {info['browser']} "
            "(headless)", "os": f"{platform.system()} {platform.release()}",
        },
        "input": {
            "file": CSV.relative_to(ROOT).as_posix(), "bytes": len(CSV.read_bytes()),
            "sha256": sha256(CSV.read_bytes()), "generator": "scripts/generate_data.py",
            "seed": expected["seed"],
        },
        "rules": RULES,
        "recording": {
            "raw_file": raw.relative_to(ROOT).as_posix(), "bytes": raw.stat().st_size,
            "sha256": sha256(raw.read_bytes()), **probe(raw), "codec": "H.264, no audio",
            "captured_frames": info["frames"], "captured_span_s": info["span_s"],
            "how": "Real local Streamlit page (127.0.0.1) in Microsoft Edge, driven by "
                   "scripts/record_demo.py with Playwright. Every painted frame was captured "
                   "with the DevTools screencast (JPEG quality 92) and encoded by ffmpeg at "
                   "its real timestamp. Complete run: no cuts, no speed changes.",
            "page_changes": "A cursor marker was injected to show where the script points "
                            "and clicks. It is hidden while screenshots are taken, so it "
                            "blinks off briefly in the video. Nothing else changed.",
            "timeline_note": "t = seconds from the first recorded frame",
            "timeline": info["timeline"],
        },
        "screenshots": info["screens"],
        "outputs": {n: {"file": f"demo/outputs/{n}", "bytes": len(got[n]),
                        "sha256": sha256(got[n]), **({"rows": rows[n]} if n in rows else {})}
                    for n in NAMES},
        "counts": summary["counts"],
        "reason_counts": summary["reason_counts"],
        "trailing_blank_lines_ignored": summary["trailing_blank_lines_ignored"],
        "checks": checks,
    }
    (DEMO / "demo_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "counts": summary["counts"],
                      "duration_s": manifest["recording"]["duration_s"],
                      "events": len(info["timeline"])}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
