"""Build src/demo-data.json for the video from the real recorded run.

Every number and example row in the video comes from this file, and this file comes only from
demo/demo_manifest.json, demo/outputs/* (the files downloaded during the recording),
data/demo_customers.csv (the uploaded input) and test-results/run_info.json.

Usage (from video/): python scripts/make_data.py
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "demo"
OUT = Path(__file__).resolve().parents[1] / "src" / "demo-data.json"
SHOW = ["customer_id", "name", "email", "city"]
CJK = re.compile(r"[\u4e00-\u9fff]")


def rows_of(path: Path) -> list[list[str]]:
    return list(csv.reader(io.StringIO(path.read_bytes().decode("utf-8-sig"), newline="")))


def dicts_of(path: Path) -> dict[int, dict]:
    head, *body = rows_of(path)
    return {int(r[0]): dict(zip(head, r)) for r in body}


def main() -> None:
    manifest_bytes = (DEMO / "demo_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    head, *body = rows_of(ROOT / "data" / "demo_customers.csv")
    clean = dicts_of(DEMO / "outputs" / "clean.csv")
    issues = dicts_of(DEMO / "outputs" / "issues.csv")
    changes = list(csv.DictReader(io.StringIO(
        (DEMO / "outputs" / "changes.csv").read_bytes().decode("utf-8-sig"), newline="")))
    changed_rows = {int(c["source_row"]) for c in changes}

    def first(cond) -> int:
        return min(n for n in range(1, len(body) + 1) if cond(n))

    picks = {
        "trimmed": first(lambda n: n in clean and any(
            int(c["source_row"]) == n and c["column"] in ("name", "email") for c in changes)),
        "unchanged": first(lambda n: n in clean and n not in changed_rows
                           and CJK.search(clean[n]["name"])),
        "missing": first(lambda n: n in issues and issues[n]["reasons"] == "missing_required:name"),
        "bad_email": first(lambda n: n in issues and issues[n]["reasons"] == "invalid_email:email"),
        "duplicate": first(lambda n: n in issues and issues[n]["reasons"].startswith("duplicate_of:")),
        "broken": first(lambda n: n in issues and issues[n]["reasons"] == "field_count_mismatch"),
    }
    examples = []
    for kind, n in sorted(picks.items(), key=lambda kv: kv[1]):
        fields = body[n - 1]
        ex = {"kind": kind, "source_row": n,
              "input": dict(zip(head, fields)) if len(fields) == len(head) else None,
              "raw_record": issues[n]["raw_record"] if kind == "broken" else None}
        if ex["input"] is not None:
            ex["input"] = {k: ex["input"][k] for k in SHOW}
        if n in clean:
            ex.update(dest="clean.csv", after={k: clean[n][k] for k in SHOW}, reason=None)
        else:
            ex.update(dest="issues.csv", after=None, reason=issues[n]["reasons"])
        examples.append(ex)

    run_info = json.loads((ROOT / "test-results" / "run_info.json").read_text(encoding="utf-8"))
    data = {
        "source": {"manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                   "recorded_utc": manifest["recorded_utc"],
                   "program_commit": manifest["program"]["git_commit"][:7],
                   "csvclean_version": manifest["program"]["csvclean_version"],
                   "browser": manifest["program"]["browser"]},
        "input": {"file": Path(manifest["input"]["file"]).name,
                  "rows": manifest["counts"]["input_rows"], "columns": len(head)},
        "rules": manifest["rules"],
        "counts": manifest["counts"],
        "reason_counts": manifest["reason_counts"],
        "outputs": manifest["outputs"],
        "checks": manifest["checks"],
        "recording": {k: manifest["recording"][k] for k in
                      ("raw_file", "duration_s", "width", "height", "timeline")},
        "tests": run_info["result"],
        "examples": examples,
        "shown_columns": SHOW,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}: {len(examples)} examples, rows {[e['source_row'] for e in examples]}")


if __name__ == "__main__":
    main()
