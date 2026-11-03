"""Command-line entry. Thin wrapper over csvclean.core."""
from __future__ import annotations

import argparse
import sys

from csvclean import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="csvclean", description="Clean and validate a CSV file.")
    p.add_argument("input")
    p.add_argument("--out", required=True)
    p.add_argument("--rules")
    p.add_argument("--trim", default="")
    p.add_argument("--required", default="")
    p.add_argument("--email", default="")
    p.add_argument("--dedupe-keys", default="")
    p.add_argument("--keep", choices=["first", "last"], default="first")
    p.add_argument("--force", action="store_true")
    p.add_argument("--version", action="version", version=__version__)
    return p


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    print("not implemented yet (core logic stage)", file=sys.stderr)
    return 1
