"""Shared processing core. Used by both the CLI and the Streamlit UI.

Spec: docs/REQUIREMENTS.md. Pure functions except `write_outputs`.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
from collections import Counter
from dataclasses import asdict, dataclass, field

from csvclean import __version__

RESERVED_COLUMNS = ("source_row", "reasons", "raw_record")
OUTPUT_FILES = ("clean.csv", "issues.csv", "changes.csv", "summary.json")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CsvCleanError(Exception):
    """Base class for expected input/rule errors (CLI exit code 2)."""


class EmptyFileError(CsvCleanError):
    pass


class HeaderError(CsvCleanError):
    pass


class EncodingError(CsvCleanError):
    pass


class RuleError(CsvCleanError):
    pass


class OutputError(CsvCleanError):
    pass


@dataclass(frozen=True)
class Rules:
    trim_columns: list[str] = field(default_factory=list)
    required_columns: list[str] = field(default_factory=list)
    email_columns: list[str] = field(default_factory=list)
    dedupe_keys: list[str] = field(default_factory=list)
    dedupe_keep: str = "first"

    @classmethod
    def from_dict(cls, d: dict) -> "Rules":
        allowed = {f for f in cls.__dataclass_fields__}
        unknown = sorted(set(d) - allowed)
        if unknown:
            raise RuleError(f"Unknown rule keys: {', '.join(unknown)}")
        kwargs = {}
        for k, v in d.items():
            if k == "dedupe_keep":
                kwargs[k] = v
            elif not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                raise RuleError(f"Rule '{k}' must be a list of column names")
            else:
                kwargs[k] = list(v)
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Result:
    header: list[str]
    clean_rows: list[dict]
    issue_rows: list[dict]
    changes: list[dict]
    summary: dict


def is_missing(value: str) -> bool:
    return value.strip() == ""


def is_valid_email(value: str) -> bool:
    return EMAIL_RE.match(value) is not None


def _decode(data: bytes) -> str:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise EncodingError(
            f"File is not valid UTF-8 (byte {e.start}). Save it as UTF-8 and try again."
        ) from None
    if text.strip() == "":
        raise EmptyFileError("File is empty: it has no header row.")
    return text


def _check_header(header: list[str]) -> None:
    blanks = [i + 1 for i, h in enumerate(header) if h.strip() == ""]
    if blanks:
        raise HeaderError(f"Blank header name at column position(s): {blanks}")
    dups = sorted(h for h, n in Counter(header).items() if n > 1)
    if dups:
        raise HeaderError(f"Duplicate header names: {', '.join(dups)}")
    reserved = [h for h in header if h in RESERVED_COLUMNS]
    if reserved:
        raise HeaderError(f"Reserved column names used in input: {', '.join(reserved)}")


def _check_rules(rules: Rules, header: list[str]) -> None:
    if rules.dedupe_keep not in ("first", "last"):
        raise RuleError("dedupe_keep must be 'first' or 'last'")
    named = (
        rules.trim_columns + rules.required_columns + rules.email_columns + rules.dedupe_keys
    )
    missing = sorted({c for c in named if c not in header})
    if missing:
        raise RuleError(f"Rules name columns not in the file: {', '.join(missing)}")


def _raw_record(fields: list[str]) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow(fields)
    return buf.getvalue()


def process(data: bytes, rules: Rules, input_name: str) -> Result:
    """Run read -> structure check -> trim -> validate -> dedupe. No file I/O."""
    text = _decode(data)
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        records = list(reader)
    except csv.Error as e:
        raise HeaderError(f"CSV could not be parsed: {e}") from None
    header = records[0]
    _check_header(header)
    _check_rules(rules, header)

    trim_set = set(rules.trim_columns)
    req_cols = [c for c in header if c in set(rules.required_columns)]
    email_cols = [c for c in header if c in set(rules.email_columns)]

    issues: dict[int, dict] = {}
    changes: list[dict] = []
    valid: list[tuple[int, dict]] = []
    mismatch = invalid = 0
    reason_counts: Counter = Counter()

    for idx, fields in enumerate(records[1:], start=1):
        if len(fields) != len(header):
            mismatch += 1
            reason_counts["field_count_mismatch"] += 1
            row = {"source_row": idx, "reasons": "field_count_mismatch"}
            row.update({h: "" for h in header})
            row["raw_record"] = _raw_record(fields)
            issues[idx] = row
            continue

        values = dict(zip(header, fields))
        for col in header:
            if col in trim_set:
                new = values[col].strip()
                if new != values[col]:
                    changes.append(
                        {"source_row": idx, "column": col, "action": "trim",
                         "old_value": values[col], "new_value": new}
                    )
                    values[col] = new

        reasons = [f"missing_required:{c}" for c in req_cols if is_missing(values[c])]
        reasons += [
            f"invalid_email:{c}" for c in email_cols
            if not is_missing(values[c]) and not is_valid_email(values[c])
        ]
        if reasons:
            invalid += 1
            reason_counts.update(reasons)
            issues[idx] = {"source_row": idx, "reasons": ";".join(reasons), **values,
                           "raw_record": ""}
        else:
            valid.append((idx, values))

    duplicate = 0
    clean: list[dict] = []
    if rules.dedupe_keys:
        groups: dict[tuple, list[int]] = {}
        for pos, (idx, values) in enumerate(valid):
            key = tuple(values[k] for k in rules.dedupe_keys)
            groups.setdefault(key, []).append(pos)
        drop: dict[int, int] = {}
        for positions in groups.values():
            keep_pos = positions[0] if rules.dedupe_keep == "first" else positions[-1]
            for p in positions:
                if p != keep_pos:
                    drop[p] = valid[keep_pos][0]
        for pos, (idx, values) in enumerate(valid):
            if pos in drop:
                duplicate += 1
                reason = f"duplicate_of:{drop[pos]}"
                reason_counts["duplicate"] += 1
                issues[idx] = {"source_row": idx, "reasons": reason, **values,
                               "raw_record": ""}
            else:
                clean.append({"source_row": idx, **values})
    else:
        clean = [{"source_row": idx, **values} for idx, values in valid]

    input_rows = len(records) - 1
    issue_rows = [issues[k] for k in sorted(issues)]
    counts = {
        "input_rows": input_rows,
        "clean_rows": len(clean),
        "issue_rows": len(issue_rows),
        "field_count_mismatch_rows": mismatch,
        "invalid_rows": invalid,
        "duplicate_rows": duplicate,
        "changed_cells": len(changes),
    }
    accounted = sorted([r["source_row"] for r in clean] + [r["source_row"] for r in issue_rows])
    summary = {
        "tool": "csvclean",
        "version": __version__,
        "input_file": os.path.basename(input_name),
        "input_sha256": hashlib.sha256(data).hexdigest(),
        "input_bytes": len(data),
        "columns": header,
        "rules": rules.to_dict(),
        "counts": counts,
        "reason_counts": dict(sorted(reason_counts.items())),
        "accounting_ok": accounted == list(range(1, input_rows + 1))
        and input_rows == counts["clean_rows"] + counts["issue_rows"]
        and counts["issue_rows"] == mismatch + invalid + duplicate,
        "outputs": list(OUTPUT_FILES),
    }
    return Result(header, clean, issue_rows, changes, summary)


def _csv_bytes(columns: list[str], rows: list[dict]) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")


def render_outputs(result: Result) -> dict[str, bytes]:
    """Exact bytes of every output file. The UI downloads these; the CLI writes them."""
    h = result.header
    return {
        "clean.csv": _csv_bytes(["source_row", *h], result.clean_rows),
        "issues.csv": _csv_bytes(["source_row", "reasons", *h, "raw_record"], result.issue_rows),
        "changes.csv": _csv_bytes(
            ["source_row", "column", "action", "old_value", "new_value"], result.changes
        ),
        "summary.json": (
            json.dumps(result.summary, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8"),
    }


def write_outputs(result: Result, out_dir: str, force: bool = False,
                  input_path: str | None = None) -> list[str]:
    """Write all outputs into out_dir. Never overwrites the input or (without force) old outputs."""
    files = render_outputs(result)
    targets = {name: os.path.join(out_dir, name) for name in files}
    if input_path is not None:
        src = os.path.normcase(os.path.realpath(input_path))
        if os.path.normcase(os.path.realpath(out_dir)) == src or any(
            os.path.normcase(os.path.realpath(p)) == src for p in targets.values()
        ):
            raise OutputError("Output would overwrite the input file. Choose another folder.")
    existing = [n for n, p in targets.items() if os.path.exists(p)]
    if existing and not force:
        raise OutputError(
            f"Output files already exist: {', '.join(existing)}. Use --force to overwrite."
        )
    os.makedirs(out_dir, exist_ok=True)
    for name, path in targets.items():
        with open(path, "wb") as f:
            f.write(files[name])
    return list(files)
