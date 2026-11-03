"""Generate the synthetic demo CSV with a fixed seed, plus its expected results.

Expected results come from the injection plan below, NOT from running csvclean,
so the test that compares them is an independent check.

Usage: python scripts/generate_data.py
Writes: data/demo_customers.csv, data/demo_rules.json, data/expected/demo_expected.json
"""
from __future__ import annotations

import csv
import io
import json
import random
from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
HEADER = ["customer_id", "name", "email", "phone", "signup_date", "city", "notes"]
RULES = {
    "trim_columns": ["name", "email", "city"],
    "required_columns": ["customer_id", "name", "email"],
    "email_columns": ["email"],
    "dedupe_keys": ["email"],
    "dedupe_keep": "first",
}
FIRST = ["Alice", "Bob", "Carmen", "David", "Elena", "Farid", "Grace", "Hiro", "Ines", "Jamal",
         "Kofi", "Lena", "Mateo", "Nora", "Omar", "Priya", "Quinn", "Rosa", "Sven", "Tara"]
LAST = ["Smith", "Garcia", "Chen", "Muller", "Rossi", "Kim", "Okafor", "Silva", "Novak", "Haddad"]
CN = ["张伟", "王芳", "李娜", "刘洋", "陈静", "杨磊", "赵敏", "黄婷"]
CITIES = ["Berlin", "Lisbon", "Toronto", "Austin", "Osaka", "São Paulo", "Zürich", "上海", "Nairobi"]
DOMAINS = ["example.com", "example.org", "example.net"]  # reserved demo domains
DATES = ["2025-04-03", "03/04/2025", "4 Mar 2025", "2025/03/04", "20250304", ""]
NOTES = ["", "", "", "VIP", 'Said "call after 5pm"', "Prefers email, not phone",
         "Line one\nLine two", "Café owner ☕", "备注：老客户", "N/A"]
BAD_EMAILS = ["user@", "@example.com", "two words@example.com", "a@@example.com",
              "no-at-sign.example.com", "user@example", "user@exa mple.com"]


def build():
    rnd = random.Random(SEED)
    base = []
    for i in range(1, 181):
        if i % 9 == 0:
            name = rnd.choice(CN)
        else:
            name = f"{rnd.choice(FIRST)} {rnd.choice(LAST)}"
        if i == 17:
            name = "Seán O'Brien, Jr."
        email = f"customer{i:03d}@{rnd.choice(DOMAINS)}"
        phone = rnd.choice(["+1 555 01{:02d}".format(i % 100), "0{:03d} 555 {:03d}".format(i, i),
                            "N/A", ""])
        base.append({
            "customer_id": f"C{i:04d}", "name": name, "email": email, "phone": phone,
            "signup_date": rnd.choice(DATES), "city": rnd.choice(CITIES),
            "notes": rnd.choice(NOTES),
        })

    plan = {}  # id(row) -> dict(kind, reasons)
    rows = [dict(r) for r in base]
    for r in rows:
        plan[id(r)] = {"kind": "clean", "reasons": []}
    pool = list(range(len(rows)))
    rnd.shuffle(pool)

    def take(n):
        return [pool.pop() for _ in range(n)]

    for p in take(5):  # missing required name (empty or spaces)
        rows[p]["name"] = rnd.choice(["", "   "])
        plan[id(rows[p])] = {"kind": "invalid", "reasons": ["missing_required:name"]}
    for p, bad in zip(take(7), BAD_EMAILS):  # invalid email format
        rows[p]["email"] = bad
        plan[id(rows[p])] = {"kind": "invalid", "reasons": ["invalid_email:email"]}
    for p in take(2):  # missing name AND invalid email
        rows[p]["name"] = ""
        rows[p]["email"] = "broken@"
        plan[id(rows[p])] = {"kind": "invalid",
                             "reasons": ["missing_required:name", "invalid_email:email"]}
    for p in take(2):  # missing email (required)
        rows[p]["email"] = "  "
        plan[id(rows[p])] = {"kind": "invalid", "reasons": ["missing_required:email"]}

    trim_targets = take(14)  # stray spaces on otherwise clean rows
    for p in trim_targets:
        col = rnd.choice(["name", "email", "city"])
        rows[p][col] = rnd.choice([" ", "  ", "\t"]) + rows[p][col] + rnd.choice(["", " "])

    dup_sources = take(8)  # duplicates of clean rows, inserted after their originals
    extra = []
    for k, p in enumerate(dup_sources):
        d = dict(rows[p])
        d["customer_id"] = f"C{900 + k:04d}"
        d["email"] = d["email"].strip()
        if k % 2 == 0:
            d["email"] = " " + d["email"] + " "  # identical only after trim
        plan[id(d)] = {"kind": "duplicate", "of": rows[p], "reasons": []}
        extra.append((rows[p], d))

    case_src = take(1)[0]  # same email, different case: NOT a duplicate (exact match)
    case_row = dict(rows[case_src])
    case_row["customer_id"] = "C0950"
    case_row["email"] = case_row["email"].strip().upper()
    plan[id(case_row)] = {"kind": "clean", "reasons": []}
    extra.append((rows[case_src], case_row))

    final = list(rows)
    for orig, d in extra:
        lo = final.index(orig) + 1
        final.insert(rnd.randint(lo, len(final)), d)

    mismatch = [["C0990", "Extra Field", "x990@example.com", "", "", "Berlin", "", "EXTRA"],
                ["C0991", "Short Row", "x991@example.com"]]
    for m in mismatch:
        plan[id(m)] = {"kind": "mismatch", "reasons": ["field_count_mismatch"]}
        final.insert(rnd.randint(1, len(final)), m)
    return final, plan


def to_csv(final) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(HEADER)
    for r in final:
        w.writerow(r if isinstance(r, list) else [r[h] for h in HEADER])
    return buf.getvalue().encode("utf-8")


def expected(final, plan) -> dict:
    pos = {id(r): i for i, r in enumerate(final, start=1)}
    issues, changed = {}, 0
    for i, r in enumerate(final, start=1):
        p = plan[id(r)]
        if p["kind"] != "mismatch":
            changed += sum(r[c] != r[c].strip() for c in RULES["trim_columns"])
        if p["kind"] in ("invalid", "mismatch"):
            issues[i] = ";".join(p["reasons"])
        elif p["kind"] == "duplicate":
            issues[i] = f"duplicate_of:{pos[id(p['of'])]}"
    reason_counts: dict[str, int] = {}
    for reasons in issues.values():
        for rsn in reasons.split(";"):
            key = "duplicate" if rsn.startswith("duplicate_of:") else rsn
            reason_counts[key] = reason_counts.get(key, 0) + 1
    kinds = [plan[id(r)]["kind"] for r in final]
    return {
        "seed": SEED,
        "counts": {
            "input_rows": len(final),
            "clean_rows": kinds.count("clean"),
            "issue_rows": len(issues),
            "field_count_mismatch_rows": kinds.count("mismatch"),
            "invalid_rows": kinds.count("invalid"),
            "duplicate_rows": kinds.count("duplicate"),
            "changed_cells": changed,
        },
        "reason_counts": dict(sorted(reason_counts.items())),
        "issues": {str(k): v for k, v in sorted(issues.items())},
    }


def main() -> None:
    final, plan = build()
    (ROOT / "data" / "expected").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "demo_customers.csv").write_bytes(to_csv(final))
    (ROOT / "data" / "demo_rules.json").write_text(
        json.dumps(RULES, indent=2) + "\n", encoding="utf-8")
    exp = expected(final, plan)
    (ROOT / "data" / "expected" / "demo_expected.json").write_text(
        json.dumps(exp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(exp["counts"]))


if __name__ == "__main__":
    main()
