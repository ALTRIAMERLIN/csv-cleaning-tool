"""Command-line entry. Thin wrapper over csvclean.core."""
from __future__ import annotations

import argparse
import json
import sys

from csvclean import __version__
from csvclean.core import CsvCleanError, RuleError, Rules, process, write_outputs


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="csvclean", description="Clean and validate a CSV file.")
    p.add_argument("input", help="input CSV (UTF-8); never modified")
    p.add_argument("--out", required=True, help="output folder")
    p.add_argument("--rules", help="rules JSON file; flags below override its fields")
    p.add_argument("--trim", default="", help="comma-separated columns to trim")
    p.add_argument("--required", default="", help="comma-separated required columns")
    p.add_argument("--email", default="", help="comma-separated email columns")
    p.add_argument("--dedupe-keys", default="", help="comma-separated de-dup key columns")
    p.add_argument("--keep", choices=["first", "last"], default=None)
    p.add_argument("--force", action="store_true", help="overwrite existing outputs")
    p.add_argument("--version", action="version", version=__version__)
    return p


def _cols(s: str) -> list[str]:
    return [c.strip() for c in s.split(",") if c.strip()]


def load_rules(args: argparse.Namespace) -> Rules:
    d: dict = {}
    if args.rules:
        try:
            with open(args.rules, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise RuleError(f"Cannot read rules file: {e}") from None
        if not isinstance(d, dict):
            raise RuleError("Rules file must contain a JSON object")
    for key, val in (("trim_columns", args.trim), ("required_columns", args.required),
                     ("email_columns", args.email), ("dedupe_keys", args.dedupe_keys)):
        if val:
            d[key] = _cols(val)
    if args.keep:
        d["dedupe_keep"] = args.keep
    return Rules.from_dict(d)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rules = load_rules(args)
        try:
            with open(args.input, "rb") as f:
                data = f.read()
        except OSError as e:
            raise CsvCleanError(f"Cannot read input: {e.strerror}") from None
        result = process(data, rules, args.input)
        write_outputs(result, args.out, force=args.force, input_path=args.input)
    except CsvCleanError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    c = result.summary["counts"]
    print(
        f"input={c['input_rows']} clean={c['clean_rows']} issues={c['issue_rows']} "
        f"(field_count={c['field_count_mismatch_rows']} invalid={c['invalid_rows']} "
        f"duplicate={c['duplicate_rows']}) changed_cells={c['changed_cells']} "
        f"accounting_ok={result.summary['accounting_ok']}"
    )
    print(f"outputs written to: {args.out}")
    return 0
