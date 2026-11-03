# Acceptance Cases (v0.1)

Each case maps to at least one automated test in `tests/`. Status is filled from real `pytest` runs only.

Statuses below come from the run saved in `test-results/` (`run_info.json` records the date,
versions and a SHA-256 digest of the tested sources: files git tracks or would track under
`app.py`, `pyproject.toml`, `requirements.txt`, `src`, `tests`, `scripts`, `data`; ignored build
files such as `*.egg-info` are excluded). After any code change, re-run
`python scripts/run_tests.py`; `python scripts/run_tests.py --check` reports whether the saved
results still match the current sources.

| ID | Case | Input | Rules | Expected result | Test | Status |
|---|---|---|---|---|---|---|
| AC-01 | Normal input | 3 valid rows, distinct emails | required=[email], email=[email], dedupe=[email] | clean=3, issues=0, changes=0; accounting holds | `test_normal_input` | pass (pytest, 2026-11-03) |
| AC-02 | Empty file (0 bytes) | `""` | any | `EmptyFileError`; CLI exit 2; no output files | `test_empty_file` | pass (pytest, 2026-11-03) |
| AC-03 | Whitespace-only file | `"  \n\n"` | any | `EmptyFileError` | `test_whitespace_only_file` | pass (pytest, 2026-11-03) |
| AC-04 | Header only | `id,name,email\n` | required=[email] | success; all counts 0; 4 output files written | `test_header_only` | pass (pytest, 2026-11-03) |
| AC-05 | Rule names missing column | header lacks `phone` | required=[phone] | `RuleError` naming `phone`; no output files | `test_missing_column_in_rules` | pass (pytest, 2026-11-03) |
| AC-06 | Duplicate header names | `id,id,email` | any | `HeaderError` | `test_duplicate_header` | pass (pytest, 2026-11-03) |
| AC-07 | Duplicates, keep first | rows 1,3 share email | dedupe=[email], keep=first | row 1 clean; row 3 issue `duplicate_of:1` | `test_dedupe_keep_first` | pass (pytest, 2026-11-03) |
| AC-08 | Duplicates, keep last | rows 1,3 share email | dedupe=[email], keep=last | row 3 clean; row 1 issue `duplicate_of:3` | `test_dedupe_keep_last` | pass (pytest, 2026-11-03) |
| AC-09 | Duplicate only after trim | `" a@x.com"` vs `"a@x.com"` | trim=[email], dedupe=[email] | treated as duplicates; trim logged | `test_dedupe_after_trim` | pass (pytest, 2026-11-03) |
| AC-10 | Case differs | `A@x.com` vs `a@x.com` | dedupe=[email] | NOT duplicates (exact match, documented) | `test_dedupe_case_sensitive` | pass (pytest, 2026-11-03) |
| AC-11 | Chinese & special chars | `张三`, `O'Brien, "Jr."`, emoji, embedded newline in quoted cell | trim=[name] | values preserved byte-for-byte except trimmed spaces; output readable as UTF-8 | `test_unicode_and_special_chars` | pass (pytest, 2026-11-03) |
| AC-12 | UTF-8 BOM input | BOM + header | any | first header name has no BOM | `test_bom_input` | pass (pytest, 2026-11-03) |
| AC-13 | Non-UTF-8 input | GBK bytes | any | `EncodingError`, clear message | `test_non_utf8` | pass (pytest, 2026-11-03) |
| AC-14 | Missing required value | email `""` and `"   "` | required=[email] | issues with `missing_required:email`; `N/A` NOT missing | `test_missing_required` | pass (pytest, 2026-11-03) |
| AC-15 | Invalid email | `a@`, `@x.com`, `a b@x.com`, `a@@x.com`, `a@x` | email=[email] | each in issues with `invalid_email:email` | `test_invalid_email` | pass (pytest, 2026-11-03) |
| AC-16 | Valid email shapes | `a.b+c@sub.x.co` | email=[email] | clean | `test_valid_email` | pass (pytest, 2026-11-03) |
| AC-17 | Optional empty email | email empty, not required | email=[email] | clean (format check skips missing) | `test_optional_empty_email` | pass (pytest, 2026-11-03) |
| AC-18 | Multiple reasons | missing name + bad email | required=[name], email=[email] | one issue row, both reasons, `;`-joined, counted once | `test_multiple_reasons` | pass (pytest, 2026-11-03) |
| AC-19 | Invalid row not used for dedupe | row 1 invalid, row 2 same key valid | dedupe=[email] | row 2 clean, row 1 issue (not duplicate) | `test_invalid_rows_excluded_from_dedupe` | pass (pytest, 2026-11-03) |
| AC-20 | Field count mismatch | row with extra/missing fields | any | issue `field_count_mismatch`; raw text kept | `test_field_count_mismatch` | pass (pytest, 2026-11-03) |
| AC-21 | No guessing | dates `03/04/2025`, phone `0123`, `N/A` | none | values unchanged in clean.csv | `test_no_inference` | pass (pytest, 2026-11-03) |
| AC-22 | Accounting | synthetic seed-42 file | demo rules | `input = clean + issues`; every source_row exactly once; counts equal `data/expected` | `test_synthetic_matches_expected` | pass (pytest, 2026-11-03) |
| AC-23 | Determinism | same input + rules, run twice | demo rules | all 4 output files byte-identical | `test_repeat_run_identical` | pass (pytest, 2026-11-03) |
| AC-24 | Input preserved | any | any | input SHA-256 unchanged after run | `test_input_not_modified` | pass (pytest, 2026-11-03) |
| AC-25 | No overwrite | output files exist | no `--force` | refuse, exit 2; with `--force` succeeds | `test_cli_no_overwrite` | pass (pytest, 2026-11-03) |
| AC-26 | CLI = core | same file via CLI and core API | demo rules | identical outputs | `test_cli_matches_core` | pass (pytest, 2026-11-03) |
| AC-27 | Summary has no paths/time | any | any | `summary.json` has file name only, no timestamp | `test_summary_no_paths` | pass (pytest, 2026-11-03) |
| AC-28 | Empty lines at end of file | `id,email\n1,a@x.com\n\n\n`; header + `\r\n` | required=[email] | not counted as rows; `trailing_blank_lines_ignored` = 2 / 1; header-only case still all zeros; an empty line *between* rows is still `field_count_mismatch` | `test_trailing_blank_lines` | pass (pytest, 2026-11-03) |
| AC-29 | Empty first line | `\nid,email\n1,a@x.com\n` | any | `HeaderError` (first line must be the header) | `test_leading_blank_line` | pass (pytest, 2026-11-03) |
| AC-30 | CSV syntax error in a data row | field over the csv size limit on line 3 | any | `ParseError` naming line 3, not `HeaderError`; CLI exit 2 | `test_parse_error_is_not_header_error` | pass (pytest, 2026-11-03) |
| AC-31 | Output path problems | `--out` is an existing file; 3rd file write fails | demo rules | exit 2, `error:` message, no traceback; the file is untouched; no output or temp files left | `test_cli_out_is_a_file`, `test_failed_write_leaves_nothing` | pass (pytest, 2026-11-03) |
| AC-32 | Bad rules file | GBK-encoded JSON; invalid JSON | — | `RuleError`, exit 2, no outputs | `test_cli_bad_rules_file` | pass (pytest, 2026-11-03) |
| AC-33 | Accounting check can fail | rendered `clean.csv` missing a row; `issues.csv` with a doubled row; non-numeric `source_row` | demo rules | `check_accounting` is `false` for each; `true` for the real output | `test_accounting_check_detects_tampering` | pass (pytest, 2026-11-03) |
| AC-34 | Rename fails midway | 2nd rename raises `OSError` | demo rules | `OutputError` that names the file already replaced (`clean.csv`); no temp files left | `test_failed_rename_is_reported` | pass (pytest, 2026-11-03) |

## UI acceptance

| ID | Case | How | Status |
|---|---|---|---|
| UI-01 | Page loads, asks for input | `tests/test_app.py::test_ui_waits_for_input` (Streamlit AppTest) | pass (pytest, 2026-11-03) |
| UI-02 | Sample → demo rules → run shows expected counts and the ✅ output check | `tests/test_app.py::test_ui_full_flow_matches_expected` | pass (pytest, 2026-11-03) |
| UI-03 | Changing rules after a run shows a "Rules changed" warning | `tests/test_app.py::test_ui_rules_change_warns` | pass (pytest, 2026-11-03) |
| UI-05 | A failed output check reads as a failure (no "passed" wording) | `tests/test_app.py::test_ui_failed_check_says_failed` (check forced to fail) | pass (pytest, 2026-11-03) |
| UI-06 | Recorded demo run: upload → preview → rules → run → all four tabs → download four files; downloads identical to the core output and to a separate CLI run; counts and reason counts equal `data/expected` | `python scripts/record_demo.py` → `checks` in `demo/demo_manifest.json` | pass (2026-11-03: all 6 checks true, 59.5 s recording) |
| UI-04 | Real browser (Edge): upload file → preview → set rules → run → Issues tab → download 4 files; each download is byte-identical to the core output | `python scripts/ui_check.py OUT --start-app` | pass (2026-11-03, re-run after review fixes: 4/4 MATCH, counts 191 = 165 + 26) |

UI-04 is not part of `pytest`. With `--start-app` the script starts the app on a free
127.0.0.1 port and stops it afterwards; without it, the app must already run at
127.0.0.1:8501. Re-run before recording.
