"""Streamlit UI. All processing goes through csvclean.core (same code as the CLI).

Run: streamlit run app.py
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from csvclean import __version__
from csvclean.core import CsvCleanError, Rules, process, read_table, render_outputs

SAMPLE = Path(__file__).parent / "data" / "demo_customers.csv"
PREVIEW_ROWS = 20

st.set_page_config(page_title="CSV Cleaning & Validation", page_icon="🧹", layout="wide")


def table(columns: list[str], rows: list[list[str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=columns, dtype=str)


def csv_frame(b: bytes) -> pd.DataFrame:
    rows = list(csv.reader(io.StringIO(b.decode("utf-8-sig"), newline="")))
    return table(rows[0], rows[1:])


st.title("CSV Data Cleaning & Validation Tool")
st.caption(f"v{__version__} · Personal demo · Synthetic data only · Runs locally")

# ---- 1. Input -------------------------------------------------------------
st.header("1. Upload CSV")
up = st.file_uploader("UTF-8 CSV file, first row is the header", type=["csv"])
if st.button("Use bundled synthetic sample", help="data/demo_customers.csv (seed 42)"):
    st.session_state["sample"] = True
if up is not None:
    st.session_state["sample"] = False
    data, name = up.getvalue(), up.name
elif st.session_state.get("sample"):
    data, name = SAMPLE.read_bytes(), SAMPLE.name
else:
    st.info("Upload a CSV file to begin. The original file is never modified.")
    st.stop()

digest = hashlib.sha256(data).hexdigest()
if st.session_state.get("input_sha") != digest:  # new input: drop old results
    st.session_state["input_sha"] = digest
    st.session_state.pop("result", None)

try:
    header, body = read_table(data)
except CsvCleanError as e:
    st.error(f"Cannot read this file: {e}")
    st.stop()

# ---- 2. Preview -----------------------------------------------------------
st.header("2. Preview")
bad_shape = sum(len(r) != len(header) for r in body)
c1, c2, c3 = st.columns(3)
c1.metric("Data rows", len(body))
c2.metric("Columns", len(header))
c3.metric("Rows with wrong field count", bad_shape)
st.caption(f"File: {name} · SHA-256 {digest[:12]}… · showing first {min(PREVIEW_ROWS, len(body))} rows")
preview = [(r + [""] * len(header))[: len(header)] for r in body[:PREVIEW_ROWS]]
st.dataframe(table(header, preview), width="stretch", hide_index=True)
if bad_shape:
    st.warning(f"{bad_shape} row(s) do not match the header. They will be listed as issues "
               "with their original text, not dropped.")

# ---- 3. Rules -------------------------------------------------------------
st.header("3. Rules")
r1, r2 = st.columns(2)
trim = r1.multiselect("Trim leading/trailing spaces", header, key="trim")
required = r1.multiselect("Required (empty or spaces only = missing)", header, key="required")
email = r2.multiselect("Email format check (format only, not existence)", header, key="email")
keys = r2.multiselect("Remove duplicates by", header, key="keys")
keep = r2.radio("When duplicated, keep", ["first", "last"], horizontal=True, key="keep",
                format_func=lambda k: f"{k} occurrence")
rules = Rules(trim_columns=trim, required_columns=required, email_columns=email,
              dedupe_keys=keys, dedupe_keep=keep)
st.download_button("Download rules.json", json.dumps(rules.to_dict(), indent=2) + "\n",
                   file_name="rules.json", mime="application/json")

if st.button("Run cleaning", type="primary"):
    try:
        res = process(data, rules, name)
        st.session_state["result"] = (rules.to_dict(), render_outputs(res))
    except CsvCleanError as e:
        st.session_state.pop("result", None)
        st.error(str(e))

if "result" not in st.session_state:
    st.stop()
ran_rules, files = st.session_state["result"]
if ran_rules != rules.to_dict():
    st.warning("Rules changed since the last run. Click **Run cleaning** to update the results.")

# ---- 4. Results -----------------------------------------------------------
summary = json.loads(files["summary.json"])
c = summary["counts"]
st.header("4. Results")
m = st.columns(4)
m[0].metric("Input rows", c["input_rows"])
m[1].metric("Clean rows", c["clean_rows"])
m[2].metric("Issue rows", c["issue_rows"])
m[3].metric("Cells trimmed", c["changed_cells"])
ok = "✅" if summary["accounting_ok"] else "❌"
st.markdown(
    f"{ok} **{c['input_rows']} input = {c['clean_rows']} clean + {c['issue_rows']} issues** "
    f"(field count {c['field_count_mismatch_rows']} · invalid {c['invalid_rows']} · "
    f"duplicate {c['duplicate_rows']})"
)
t_clean, t_issues, t_log, t_sum = st.tabs(
    [f"Clean data ({c['clean_rows']})", f"Issues ({c['issue_rows']})",
     f"Change log ({c['changed_cells']})", "Summary"])
with t_clean:
    st.dataframe(csv_frame(files["clean.csv"]), width="stretch", hide_index=True)
with t_issues:
    st.dataframe(csv_frame(files["issues.csv"]), width="stretch", hide_index=True)
    st.caption("Reason counts: " + ", ".join(f"{k} = {v}" for k, v in summary["reason_counts"].items()))
with t_log:
    st.dataframe(csv_frame(files["changes.csv"]), width="stretch", hide_index=True)
with t_sum:
    st.json(summary)

# ---- 5. Download ----------------------------------------------------------
st.header("5. Download")
st.caption("Files are UTF-8 (CSV with BOM for Excel). Check a download with its SHA-256 below.")
mimes = {".csv": "text/csv", ".json": "application/json"}
cols = st.columns(len(files))
for col, (fname, b) in zip(cols, files.items()):
    col.download_button(f"⬇ {fname}", b, file_name=fname, mime=mimes[Path(fname).suffix],
                        key=f"dl_{fname}")
st.dataframe(
    pd.DataFrame([{"file": f, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
                  for f, b in files.items()]),
    width="stretch", hide_index=True)
