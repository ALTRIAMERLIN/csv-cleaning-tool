# Delivery check (v0.1, 2026-11-03)

Personal demo project. Synthetic data only. Not a client project.

## Deliverables

| Item | Where | Checked how | Status |
|---|---|---|---|
| Source code and dependencies | `src/`, `app.py`, `scripts/`, `requirements.txt`, `pyproject.toml`; video: `video/package.json`, `video/package-lock.json` | Fresh clone of `dca40f8`: install per README, 42 tests pass, `run_tests.py --check` matches, CLI output identical to the recorded downloads | ✅ |
| English README, Chinese quick start | `README.md`, `docs/QUICKSTART.zh-CN.md` | Every Python command in them was run | ✅ |
| Requirements and acceptance cases | `docs/REQUIREMENTS.md`, `docs/ACCEPTANCE.md` | 33 core cases + 6 UI cases, all pass | ✅ |
| Tests | `tests/`, saved run in `test-results/` | `42 passed`; saved results match the current sources | ✅ |
| Synthetic input and expected results | `data/demo_customers.csv` (seed 42), `data/expected/demo_expected.json` | Generator re-run gives the same files; tool output matches the expected results | ✅ |
| Actual outputs | `demo/outputs/` | Byte-identical to the core output and to a separate CLI run | ✅ |
| Raw screen recording | `demo/recording/raw_recording.mp4` | 59.53 s, 1920x1080, 30 fps, complete run, no cuts | ✅ |
| `demo_manifest.json` | `demo/demo_manifest.json` | Program commit `59d9b96` (clean tree), input hash, rules, timeline, output hashes, 6 checks all true | ✅ |
| Remotion source | `video/` | Type-checks; renders | ✅ |
| Final MP4 | `video/out/csv-cleaning-tool-demo.mp4` | ffprobe: H.264, 1920x1080, 30 fps, 1650 frames, 55.0 s, 8.0 MB, no audio | ✅ |
| Cover | `deliverables/cover.png` | 2000x1500 (4:3), real screenshot and real counts | ✅ |
| Three real screenshots | `deliverables/screenshot-1-rules.png`, `-2-results-and-issues.png`, `-3-summary-and-downloads.png` | Taken during the recorded run, cursor marker hidden, no file paths | ✅ |
| Upwork title and description | `deliverables/UPWORK.md` | Title 60 characters; description 596 characters (≤ 600) | ✅ |
| Implemented / limits / not verified | this file | — | ✅ |

## Implemented

- Trim leading and trailing whitespace in chosen columns; every changed cell is logged in
  `changes.csv`.
- Required fields: empty or whitespace-only values are missing. `N/A`, `null` and similar text
  stay as written.
- Basic email format check (format only, not whether the address exists).
- Duplicates removed by chosen key columns, keeping the first or the last occurrence; exact,
  case-sensitive match after trimming, among rows that passed the other checks.
- Rows with the wrong number of fields are reported with their original text.
- Every rejected row goes to `issues.csv` with all its reasons; no row is dropped silently.
- `summary.json` with counts, reason counts and an accounting check that re-reads the written
  `clean.csv` and `issues.csv`.
- The input file is never changed; existing outputs are not overwritten without `--force`;
  outputs are written to temporary files first.
- Same input and rules give byte-identical output files (no timestamps or paths in outputs).
- Clear errors (CLI exit code 2) for empty files, bad headers, non-UTF-8 input, CSV syntax
  errors, unknown rule columns, bad rules files and output folder problems.
- Command line and Streamlit page share one core and produce identical files.
- Streamlit page: upload, preview, rules from the real header, run, four result tabs,
  downloads with SHA-256.

## Known limitations

- UTF-8 CSV only (BOM accepted), comma separator, header on the first line. No Excel files,
  other encodings or other separators.
- An empty first line is rejected. Empty lines at the end are ignored and counted; an empty line
  between rows is reported as `field_count_mismatch`.
- The whole file is loaded into memory.
- The email check is a simple pattern; it accepts some invalid addresses and rejects some
  unusual valid ones.
- Duplicate matching is exact and case-sensitive; no fuzzy matching.
- No type conversion: dates, numbers and phone numbers are not parsed or normalized.
- `source_row`, `reasons` and `raw_record` are reserved column names.
- Output files are replaced one at a time; a rename that fails midway is reported with the
  files already replaced.
- The web page is a local, single-user app: no accounts, no saved history.

## Not verified

- Other systems and versions. Everything ran on Windows (10.0.26200) with Python 3.11.9,
  Streamlit 1.66.1, Playwright 1.64.1, Node.js 24.21.0 and Remotion 4.0.540.
- Other browsers. The browser check, the recording and the video render all used Microsoft
  Edge 156 (headless). Remotion's own downloaded headless Chrome was not tried.
- Rebuilding the video from a fresh clone (`npm ci`, then render) was not run; only the Python
  part was checked in a fresh clone.
- Opening the output CSV files in Excel.
- Speed and memory use on large files.
- How Upwork shows the cover, screenshots and video, and whether its form accepts the MP4.
  Upwork was not opened, by design.
- No hand-operated run was recorded. The page was operated by Playwright
  (`scripts/ui_check.py`, `scripts/record_demo.py`) and Streamlit AppTest.
- Code review: the Entire review agents passed the code at `be9b69d` (3 rounds, 13 findings
  fixed). Later additions (`scripts/record_demo.py`, `video/`, docs) were not reviewed by them.
- The undo-the-fix checks that showed the tests catch the reviewed bugs (8 checks) were run
  during development and are not saved as files.
