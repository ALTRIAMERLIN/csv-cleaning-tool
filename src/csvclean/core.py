"""Shared processing core. Used by both the CLI and the Streamlit UI.

Spec: docs/REQUIREMENTS.md. Implementation lands in the "core logic" stage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


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


@dataclass(frozen=True)
class Rules:
    trim_columns: list[str] = field(default_factory=list)
    required_columns: list[str] = field(default_factory=list)
    email_columns: list[str] = field(default_factory=list)
    dedupe_keys: list[str] = field(default_factory=list)
    dedupe_keep: Literal["first", "last"] = "first"


@dataclass
class Result:
    header: list[str]
    clean_rows: list[dict]
    issue_rows: list[dict]
    changes: list[dict]
    summary: dict


def process(data: bytes, rules: Rules, input_name: str) -> Result:
    """Run read -> structure check -> trim -> validate -> dedupe. Pure: no file I/O."""
    raise NotImplementedError("core logic stage")


def write_outputs(result: Result, out_dir: str, force: bool = False) -> list[str]:
    """Write clean.csv, issues.csv, changes.csv, summary.json. Returns file names."""
    raise NotImplementedError("core logic stage")
