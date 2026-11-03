# Acceptance Cases (v0.1)

Each case maps to at least one automated test in `tests/`. Status is filled from real `pytest` runs only.

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

UI acceptance (manual, recorded): upload → preview → rules → run → view tabs → download →
downloaded files match CLI outputs by SHA-256. Status: not run.
