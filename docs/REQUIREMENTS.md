# CSV Data Cleaning & Validation Tool — Requirements (v0.1)

Personal portfolio demo. Synthetic data only. Not a client project.

## 1. Scope

In scope (v0.1):
- Input: one CSV file, UTF-8 (a UTF-8 BOM is accepted), comma delimiter, first row is the header.
- One shared processing core (`csvclean.core`), used by both the CLI (`csvclean.cli`) and the Streamlit UI (`app.py`).
- Rules: trim, required fields, basic email format, de-duplication by key columns.
- Outputs: clean data, issue records, change log, summary JSON.

Out of scope (v0.1): Excel/JSON input, other encodings or delimiters, accounts, payment,
multi-tenant, databases, online AI calls, type conversion, date/phone normalization,
guessing missing values.

## 2. Data model

- Every cell is read and written as a **string**. No type inference (dates, numbers, phones stay as typed).
- Each data row gets `source_row` = its 1-based position among data rows (header excluded).
- A value is **missing** only when it is empty or whitespace-only. Text such as `N/A`, `null`, `-` is
  NOT treated as missing (no guessing). This is documented to the user.

## 3. Rules (one `Rules` object, also saved as JSON)

| Field | Type | Meaning |
|---|---|---|
| `trim_columns` | list[str] | Remove leading/trailing whitespace (Python `str.strip()`) in these columns. |
| `required_columns` | list[str] | Value must not be missing. |
| `email_columns` | list[str] | Non-missing values must pass the basic email format check. |
| `dedupe_keys` | list[str] | Rows with identical values in all these columns are duplicates. Empty list = no de-dup. |
| `dedupe_keep` | `"first"` \| `"last"` | Which duplicate is kept, by `source_row` order. Default `"first"`. |

Rule validation (before any processing): every column named in a rule must exist in the header.
Otherwise the run fails with a clear error listing the missing columns, and **no output files are written**.

## 4. Processing order (fixed)

1. **Read.** Reject: 0-byte or whitespace-only file (`EmptyFileError`); blank/duplicate
   header names, or the reserved names `source_row`, `reasons`, `raw_record` (`HeaderError`);
   undecodable UTF-8 (`EncodingError`).
2. **Structure check.** A row whose field count differs from the header (including a blank line
   in the middle of the file) goes to issues with reason `field_count_mismatch` and skips all
   further steps. Its original fields are kept, re-joined as CSV text, in `raw_record`.
3. **Trim.** Apply to `trim_columns`. Each actual change is written to the change log.
4. **Validate.** For each remaining row, collect ALL reasons:
   - `missing_required:<column>`
   - `invalid_email:<column>`
   Reason order: all `missing_required` (header column order), then all `invalid_email`
   (header column order). A missing value is not also format-checked.
   Rows with ≥1 reason go to issues. A row is never dropped silently.
5. **De-duplicate** among rows that passed validation only. Key comparison is exact, case-sensitive,
   on the trimmed values. Removed rows go to issues with reason `duplicate_of:<kept source_row>`.
6. **Write outputs.**

Basic email check (format only, never claims the address exists):
`^[^@\s]+@[^@\s]+\.[^@\s]+$` — exactly one `@`, no whitespace, a dot in the domain part, no empty parts.

## 5. Accounting (must always hold)

```
input_rows = clean_rows + issue_rows
issue_rows = field_count_mismatch_rows + invalid_rows + duplicate_rows
```

Each input `source_row` appears exactly once: either in `clean.csv` or in `issues.csv`.
A row with several reasons counts once in `issue_rows`; reason counts are reported separately
(`reason_counts`), so their sum may exceed `invalid_rows`.

## 6. Outputs (written into an output folder)

| File | Content |
|---|---|
| `clean.csv` | `source_row`, then the header columns with values after trim, rows in `source_row` order. |
| `issues.csv` | `source_row`, `reasons` (`;`-joined, fixed order), the header columns (post-trim values; empty for field-count rows), `raw_record` (original fields for field-count rows, else empty). |
| `changes.csv` | `source_row`, `column`, `action` (`trim`), `old_value`, `new_value`. |
| `summary.json` | Tool version, input file name + SHA-256 + size, columns, rules, counts, reason counts (`duplicate` groups all `duplicate_of:N`), `accounting_ok`, output file names. |

- CSV outputs use UTF-8 with BOM (`utf-8-sig`) so Excel shows Chinese correctly; `\n` line endings.
- `summary.json` contains no timestamp and no absolute paths, so the same input + rules gives
  byte-identical outputs.
- The input file is never modified. The tool refuses to write if the output folder is the input
  file's own path, and refuses to overwrite existing outputs unless `--force` is given.

## 7. Interfaces

CLI:
```
python -m csvclean INPUT.csv --out OUTDIR [--rules rules.json] [--trim a,b] [--required a,b]
       [--email col] [--dedupe-keys a,b] [--keep first|last] [--force]
```
Exit codes: `0` success, `2` input/rule/output error (message on stderr), `1` unexpected error.
`render_outputs()` returns the exact output bytes; the CLI writes them and the UI offers them
as downloads, so both produce identical files.

Streamlit UI: upload → preview (first rows + column list + row count) → choose rules from the
real header → Run → tabs for Clean / Issues / Change log / Summary → download each output file.
Every button and panel shows real results from the core; no placeholder widgets.

## 8. Demo & delivery (later stages)

- Synthetic data generated with a fixed seed (`scripts/generate_data.py`, seed 42); expected
  counts recorded in `data/expected/`.
- Real screen recording of the local Streamlit page; `demo_manifest.json` records data, version,
  output files and counts from the real run.
- Remotion video: 1920x1080, 30 fps, MP4 < 100 MB, ~55 s, English captions, no invented metrics.
