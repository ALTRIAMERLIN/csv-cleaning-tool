# CSV Data Cleaning & Validation Tool

**Personal demo project. All data is synthetic. Not a client project.**

中文启动说明: [docs/QUICKSTART.zh-CN.md](docs/QUICKSTART.zh-CN.md)

A small Python tool that cleans and validates one CSV file. It trims stray spaces, checks
required fields and basic email format, and removes duplicate rows by the columns you choose.
Rows it does not keep go to an issues file with the reason, so no row is dropped silently.
The command line and the Streamlit web page call the same processing code
(`src/csvclean/core.py`) and write identical files.

## What it does

- **Trim** leading and trailing whitespace in the columns you pick. Every changed cell is logged.
- **Required fields.** A value counts as missing only when it is empty or only whitespace.
  Text such as `N/A`, `null` or `-` is kept as written.
- **Email format check.** A basic format check only; it does not test whether an address exists.
- **Remove duplicates** by one or more key columns, keeping the first or the last occurrence.
  Keys are compared exactly (case-sensitive) after trimming. Only rows that passed the other
  checks take part.
- **Broken rows** with the wrong number of fields are reported with their original text.
- **Every row is accounted for.** Each input row ends up in exactly one of `clean.csv` or
  `issues.csv`.
- **The input is never changed**, and earlier outputs are not overwritten unless you pass
  `--force`.
- **Repeatable.** The same input and rules give byte-identical output files.
- **No guessing.** Dates, phone numbers and all other values stay exactly as typed.

## Output files

| File | Content |
|---|---|
| `clean.csv` | Rows that passed every rule. The first column, `source_row`, is the row's position in the input (1 = first data row). |
| `issues.csv` | All other rows: `source_row`, `reasons`, the original columns, and `raw_record` (the original text of rows with the wrong field count). |
| `changes.csv` | One line per trimmed cell: `source_row`, `column`, `action`, `old_value`, `new_value`. |
| `summary.json` | Tool version, input file name, size and SHA-256, the rules, all counts, reason counts and `accounting_ok`. No timestamps or absolute paths. |

Reasons: `field_count_mismatch`, `missing_required:<column>`, `invalid_email:<column>` and
`duplicate_of:<source_row of the kept row>`. A row can have several reasons and is still
counted once.

The counts always satisfy:

```
input_rows = clean_rows + issue_rows
issue_rows = field_count_mismatch_rows + invalid_rows + duplicate_rows
```

`accounting_ok` is not copied from the counters: the tool reads the written `clean.csv` and
`issues.csv` back and checks that every row number appears exactly once.

CSV files are written as UTF-8 with a byte-order mark (which Excel uses to detect UTF-8) and
`\n` line endings.

## Install

Python 3.10 or newer (tested with 3.11.9).

```bash
git clone https://github.com/ALTRIAMERLIN/csv-cleaning-tool.git
cd csv-cleaning-tool
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -e .
```

On Windows you can also skip activation and call `.venv\Scripts\python` directly.

The processing core needs only the Python standard library. `requirements.txt` adds
Streamlit (web page), pytest (tests) and Playwright (browser check).

## Command line

```bash
python -m csvclean data/demo_customers.csv --out out/demo --rules data/demo_rules.json
```

Output of this command on the bundled demo file:

```
input=191 clean=165 issues=26 (field_count=2 invalid=16 duplicate=8) changed_cells=25 accounting_ok=True
outputs written to: out/demo
```

The same rules as flags (flags override fields from `--rules`):

```bash
python -m csvclean data/demo_customers.csv --out out/flags --trim name,email,city --required customer_id,name,email --email email --dedupe-keys email --keep first
```

A rules file is a JSON object; every field is optional:

```json
{
  "trim_columns": ["name", "email", "city"],
  "required_columns": ["customer_id", "name", "email"],
  "email_columns": ["email"],
  "dedupe_keys": ["email"],
  "dedupe_keep": "first"
}
```

| Exit code | Meaning |
|---|---|
| `0` | Success |
| `2` | Input, rule or output problem: a one-line `error:` message on stderr, no traceback |
| `1` | Unexpected error |

Run `python -m csvclean --help` for all options.

## Web page

Run from the project folder, so that `.streamlit/config.toml` applies:

```bash
streamlit run app.py
```

Then open http://127.0.0.1:8501. The config binds the server to `127.0.0.1` and turns off
Streamlit's usage statistics.

1. **Upload CSV**, or click **Use bundled synthetic sample**.
2. **Preview**: row and column counts, rows with the wrong field count, the first 20 rows.
3. **Rules**: choose the columns for each rule from the file's real header, then click
   **Run cleaning**.
4. **Results**: counts, the accounting line, an output check, and tabs for the clean data,
   issues, change log and summary.
5. **Download** the four files. The page lists each file's size and SHA-256, so a download
   can be checked.

## Tests and checks

```bash
python -m pytest                                      # all automated tests
python scripts/run_tests.py                           # run tests, save results to test-results/
python scripts/run_tests.py --check                   # do the saved results match the current sources?
python scripts/ui_check.py out/ui_check --start-app   # real browser run (needs Microsoft Edge)
```

`ui_check.py` starts the app on a free local port, uploads the demo file in Edge, sets the
demo rules, runs, downloads the four files, and compares each download byte for byte with the
core output.

## Demo recording

`python scripts/record_demo.py` records one complete run of the real local page in Microsoft
Edge, driven by Playwright at 1920x1080: upload → preview → rules → run → clean data, issues,
change log and summary → download. Every frame the browser paints is captured and encoded at
its real timing. Afterwards the script compares the downloaded files with the core output and
with a separate command-line run.

The recorded run is in `demo/`:

| Path | Content |
|---|---|
| `demo/recording/raw_recording.mp4` | The complete recording (59.5 s), no cuts and no speed changes |
| `demo/screens/` | Six screenshots taken during the run |
| `demo/outputs/` | The four downloaded files |
| `demo/demo_manifest.json` | Program version and git commit, input hash, rules, timeline, output hashes, counts and checks |

A small cursor marker is injected into the page so viewers can see where the script points
and clicks. Nothing else on the page is changed.

## Demo video

`video/out/csv-cleaning-tool-demo.mp4`: 55 s, 1920x1080, 30 fps, H.264, no audio, English
captions. It is made with [Remotion](https://www.remotion.dev/) from the recording above.

- The clips come from `demo/recording/raw_recording.mp4` and all play at normal speed. Only
  the waiting time between steps is cut. `video/src/Demo.tsx` lists each clip's start second
  in the raw recording.
- Every number and example row comes from `video/src/demo-data.json`, which
  `video/scripts/make_data.py` builds from `demo/demo_manifest.json`, the downloaded files in
  `demo/outputs/`, the input CSV and `test-results/run_info.json`.
- The opening comparison shows six real rows from the input file and where this run put them.
  The verification card near the end shows the real checks from the manifest.
- There are no customers, reviews, time savings, accuracy or speed figures.

Rebuild the video (Node.js 18 or newer):

```bash
cd video
npm ci
python scripts/make_data.py
npx remotion render src/index.ts CsvCleanDemo out/csv-cleaning-tool-demo.mp4 --codec h264 --crf 18
```

On first render Remotion downloads its own headless Chrome. This video was rendered with the
installed Microsoft Edge instead, by adding
`--browser-executable="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --chrome-mode=chrome-for-testing`.
Remotion is free for individuals and small companies; see its
[license](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md).

## Documentation

- Spec: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)
- Acceptance cases and their status: [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)
- Latest saved test run: [test-results/run_info.json](test-results/run_info.json)

## Synthetic demo data

`data/demo_customers.csv` has 191 rows made by `scripts/generate_data.py` with a fixed seed
(42). Names come from short fixed lists. Every well-formed email address uses the reserved
`example.com`, `example.org` or `example.net` domains; the deliberately malformed ones are
fragments such as `user@` or `user@example`. The generator adds stray spaces, missing values,
malformed emails, duplicates (some identical only after trimming), one near-duplicate that
differs only in letter case (kept, because matching is exact), rows with the wrong field
count, Chinese text, quotes and commas inside values, a line break inside a value and mixed
date formats.

The expected results come from the generator's own plan, not from running the tool. They are
stored in `data/expected/demo_expected.json`:

| | Rows |
|---|---|
| Input | 191 |
| Clean | 165 |
| Issues | 26 |
| – wrong field count | 2 |
| – missing value or invalid email | 16 |
| – duplicate | 8 |
| Trimmed cells | 25 |

`python scripts/generate_data.py` rewrites these files with the same content.

## Project layout

```
app.py                     Streamlit page; calls csvclean.core only
src/csvclean/core.py       processing core (standard library only)
src/csvclean/cli.py        command line
tests/                     pytest tests (core, CLI and Streamlit AppTest)
scripts/generate_data.py   synthetic data and expected results
scripts/run_tests.py       runs the tests, saves results without local paths
scripts/ui_check.py        real-browser check in Microsoft Edge
scripts/record_demo.py     records the demo run and writes demo/demo_manifest.json
data/                      demo input, demo rules, expected results
demo/                      the recorded run: video, screenshots, downloads, manifest
video/                     Remotion source and the final demo video (video/out/)
docs/                      requirements, acceptance cases, Chinese quick start
test-results/              latest saved test run
```

## Known limitations

- Input must be a UTF-8 CSV (a BOM is fine) with commas as separators and the header on the
  first line. Other encodings are rejected with a clear message. No Excel files, no other
  separators.
- An empty first line is rejected. Empty lines at the end of the file are ignored and counted
  in `summary.json`; an empty line between rows is reported as `field_count_mismatch`.
- The whole file is loaded into memory.
- The email check is a simple pattern, `^[^@\s]+@[^@\s]+\.[^@\s]+$`: one `@`, no spaces and a
  dot after the `@`. It accepts some invalid addresses and rejects some unusual valid ones.
- Duplicates must match exactly: `A@x.com` and `a@x.com` are different. There is no fuzzy
  matching.
- Trimming removes only leading and trailing whitespace; spaces inside a value stay.
- No type conversion: dates, numbers and phone numbers are not parsed or normalized.
- `source_row`, `reasons` and `raw_record` are reserved column names.
- The four output files are replaced one at a time. If a rename fails midway, the error names
  the files already replaced.
- The web page is a local, single-user app with no accounts and no saved history.

## Not verified

- Tested only on Windows (10.0.26200) with Python 3.11.9, Streamlit 1.66.1 and Playwright
  1.64.1. macOS, Linux and other Python versions were not tested.
- The browser check ran only in Microsoft Edge 156 (headless). Other browsers were not tested.
- Opening the output files in Excel was not checked.
- Speed and memory use on large files were not measured.
