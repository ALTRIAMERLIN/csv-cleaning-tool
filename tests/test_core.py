"""Acceptance tests. IDs refer to docs/ACCEPTANCE.md."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from csvclean.cli import main as cli_main
from csvclean.core import (
    EmptyFileError, EncodingError, HeaderError, OutputError, RuleError, Rules,
    process, render_outputs, write_outputs,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO_CSV = ROOT / "data" / "demo_customers.csv"
DEMO_RULES = ROOT / "data" / "demo_rules.json"
DEMO_EXPECTED = ROOT / "data" / "expected" / "demo_expected.json"
EMAIL_RULES = Rules(required_columns=["email"], email_columns=["email"], dedupe_keys=["email"])


def run(text: str, rules: Rules = Rules(), name: str = "t.csv"):
    return process(text.encode("utf-8"), rules, name)


def reasons(result) -> dict[int, str]:
    return {r["source_row"]: r["reasons"] for r in result.issue_rows}


def read_csv(b: bytes) -> list[dict]:
    assert b.startswith(b"\xef\xbb\xbf")
    return list(csv.DictReader(io.StringIO(b.decode("utf-8-sig"), newline="")))


def assert_accounting(result):
    s = result.summary
    c = s["counts"]
    rows = sorted([r["source_row"] for r in result.clean_rows]
                  + [r["source_row"] for r in result.issue_rows])
    assert rows == list(range(1, c["input_rows"] + 1))
    assert c["input_rows"] == c["clean_rows"] + c["issue_rows"]
    assert c["issue_rows"] == (c["field_count_mismatch_rows"] + c["invalid_rows"]
                               + c["duplicate_rows"])
    assert s["accounting_ok"] is True


# AC-01
def test_normal_input():
    r = run("id,name,email\n1,Ann,a@x.com\n2,Bo,b@x.com\n3,Cy,c@x.com\n", EMAIL_RULES)
    c = r.summary["counts"]
    assert (c["clean_rows"], c["issue_rows"], c["changed_cells"]) == (3, 0, 0)
    assert [row["name"] for row in r.clean_rows] == ["Ann", "Bo", "Cy"]
    assert_accounting(r)


# AC-02
def test_empty_file(tmp_path):
    with pytest.raises(EmptyFileError):
        process(b"", Rules(), "e.csv")
    src = tmp_path / "e.csv"
    src.write_bytes(b"")
    out = tmp_path / "out"
    assert cli_main([str(src), "--out", str(out)]) == 2
    assert not out.exists()


# AC-03
def test_whitespace_only_file():
    with pytest.raises(EmptyFileError):
        process(b"  \n\n", Rules(), "w.csv")
    with pytest.raises(EmptyFileError):
        process(b"\xef\xbb\xbf\n", Rules(), "w.csv")


# AC-04
def test_header_only(tmp_path):
    r = run("id,name,email\n", Rules(required_columns=["email"]))
    assert all(v == 0 for v in r.summary["counts"].values())
    assert_accounting(r)
    files = write_outputs(r, str(tmp_path / "o"))
    assert sorted(files) == sorted(p.name for p in (tmp_path / "o").iterdir())
    assert len(files) == 4


# AC-05
def test_missing_column_in_rules(tmp_path):
    with pytest.raises(RuleError, match="phone"):
        run("id,email\n1,a@x.com\n", Rules(required_columns=["phone"]))
    src = tmp_path / "in.csv"
    src.write_text("id,email\n1,a@x.com\n", encoding="utf-8")
    out = tmp_path / "out"
    assert cli_main([str(src), "--out", str(out), "--required", "phone"]) == 2
    assert not out.exists()


# AC-06
def test_duplicate_header():
    with pytest.raises(HeaderError, match="id"):
        run("id,id,email\n1,2,a@x.com\n")
    with pytest.raises(HeaderError):
        run("id,,email\n1,2,a@x.com\n")
    with pytest.raises(HeaderError, match="reserved|Reserved"):
        run("source_row,email\n1,a@x.com\n")


DUP = "id,email\n1,a@x.com\n2,b@x.com\n3,a@x.com\n"


# AC-07
def test_dedupe_keep_first():
    r = run(DUP, Rules(dedupe_keys=["email"], dedupe_keep="first"))
    assert [row["id"] for row in r.clean_rows] == ["1", "2"]
    assert reasons(r) == {3: "duplicate_of:1"}
    assert_accounting(r)


# AC-08
def test_dedupe_keep_last():
    r = run(DUP, Rules(dedupe_keys=["email"], dedupe_keep="last"))
    assert [row["id"] for row in r.clean_rows] == ["2", "3"]
    assert reasons(r) == {1: "duplicate_of:3"}
    assert_accounting(r)


# AC-09
def test_dedupe_after_trim():
    r = run("id,email\n1, a@x.com\n2,a@x.com\n",
            Rules(trim_columns=["email"], dedupe_keys=["email"]))
    assert reasons(r) == {2: "duplicate_of:1"}
    assert r.changes == [{"source_row": 1, "column": "email", "action": "trim",
                          "old_value": " a@x.com", "new_value": "a@x.com"}]


# AC-10
def test_dedupe_case_sensitive():
    r = run("id,email\n1,A@x.com\n2,a@x.com\n", Rules(dedupe_keys=["email"]))
    assert r.summary["counts"]["duplicate_rows"] == 0
    assert len(r.clean_rows) == 2


# AC-11
def test_unicode_and_special_chars():
    text = ('id,name,notes\n'
            '1,  张三  ,"O\'Brien, ""Jr."""\n'
            '2,Zoë 😀,"line1\nline2"\n')
    r = run(text, Rules(trim_columns=["name"]))
    assert [row["name"] for row in r.clean_rows] == ["张三", "Zoë 😀"]
    assert r.clean_rows[0]["notes"] == 'O\'Brien, "Jr."'
    assert r.clean_rows[1]["notes"] == "line1\nline2"
    back = read_csv(render_outputs(r)["clean.csv"])
    assert back[0]["name"] == "张三" and back[1]["notes"] == "line1\nline2"
    summary = json.loads(render_outputs(r)["summary.json"].decode("utf-8"))
    assert summary["counts"]["changed_cells"] == 1


# AC-12
def test_bom_input():
    r = process("\ufeffid,email\n1,a@x.com\n".encode("utf-8"), Rules(), "b.csv")
    assert r.header == ["id", "email"]


# AC-13
def test_non_utf8():
    with pytest.raises(EncodingError, match="UTF-8"):
        process("id,name\n1,张三\n".encode("gbk"), Rules(), "g.csv")


# AC-14
def test_missing_required():
    r = run("id,email\n1,\n2,   \n3,N/A\n", Rules(required_columns=["email"]))
    assert reasons(r) == {1: "missing_required:email", 2: "missing_required:email"}
    assert [row["email"] for row in r.clean_rows] == ["N/A"]


BAD = ["a@", "@x.com", "a b@x.com", "a@@x.com", "a@x", "ax.com"]


# AC-15
def test_invalid_email():
    text = "id,email\n" + "".join(f"{i},{e}\n" for i, e in enumerate(BAD, 1))
    r = run(text, Rules(email_columns=["email"]))
    assert reasons(r) == {i: "invalid_email:email" for i in range(1, len(BAD) + 1)}
    assert r.clean_rows == []


# AC-16
def test_valid_email():
    r = run("id,email\n1,a.b+c@sub.x.co\n2,x_y-1@ex-ample.org\n", Rules(email_columns=["email"]))
    assert len(r.clean_rows) == 2


# AC-17
def test_optional_empty_email():
    r = run("id,email\n1,\n", Rules(email_columns=["email"]))
    assert len(r.clean_rows) == 1


# AC-18
def test_multiple_reasons():
    r = run("id,name,email\n1,,bad@\n",
            Rules(required_columns=["name"], email_columns=["email"]))
    assert reasons(r) == {1: "missing_required:name;invalid_email:email"}
    c = r.summary["counts"]
    assert (c["issue_rows"], c["invalid_rows"]) == (1, 1)
    assert r.summary["reason_counts"] == {"invalid_email:email": 1, "missing_required:name": 1}


# AC-19
def test_invalid_rows_excluded_from_dedupe():
    r = run("id,name,email\n1,,a@x.com\n2,Bo,a@x.com\n",
            Rules(required_columns=["name"], dedupe_keys=["email"]))
    assert reasons(r) == {1: "missing_required:name"}
    assert [row["id"] for row in r.clean_rows] == ["2"]


# AC-20
def test_field_count_mismatch():
    r = run("id,name,email\n1,Ann,a@x.com,EXTRA\n2,Bo\n3,Cy,c@x.com\n",
            Rules(trim_columns=["name"]))
    assert reasons(r) == {1: "field_count_mismatch", 2: "field_count_mismatch"}
    raw = {row["source_row"]: row["raw_record"] for row in r.issue_rows}
    assert raw == {1: "1,Ann,a@x.com,EXTRA", 2: "2,Bo"}
    assert r.summary["counts"]["field_count_mismatch_rows"] == 2
    assert_accounting(r)


# AC-21
def test_no_inference():
    text = "id,date,phone,note\n1,03/04/2025,0123,N/A\n2,20250304,+1 555 0100,null\n"
    r = run(text, Rules(trim_columns=["date", "phone", "note"]))
    assert [(x["date"], x["phone"], x["note"]) for x in r.clean_rows] == [
        ("03/04/2025", "0123", "N/A"), ("20250304", "+1 555 0100", "null")]
    assert r.changes == []


def demo_rules() -> Rules:
    return Rules.from_dict(json.loads(DEMO_RULES.read_text(encoding="utf-8")))


# AC-22
def test_synthetic_matches_expected():
    exp = json.loads(DEMO_EXPECTED.read_text(encoding="utf-8"))
    r = process(DEMO_CSV.read_bytes(), demo_rules(), "demo_customers.csv")
    assert r.summary["counts"] == exp["counts"]
    assert r.summary["reason_counts"] == exp["reason_counts"]
    assert {str(k): v for k, v in reasons(r).items()} == exp["issues"]
    assert_accounting(r)


# AC-23
def test_repeat_run_identical(tmp_path):
    data, rules = DEMO_CSV.read_bytes(), demo_rules()
    write_outputs(process(data, rules, "demo_customers.csv"), str(tmp_path / "a"))
    write_outputs(process(data, rules, "demo_customers.csv"), str(tmp_path / "b"))
    for name in ("clean.csv", "issues.csv", "changes.csv", "summary.json"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()


# AC-24
def test_input_not_modified(tmp_path):
    src = tmp_path / "in.csv"
    src.write_bytes(DEMO_CSV.read_bytes())
    before = hashlib.sha256(src.read_bytes()).hexdigest()
    assert cli_main([str(src), "--out", str(tmp_path / "o"), "--rules", str(DEMO_RULES)]) == 0
    assert hashlib.sha256(src.read_bytes()).hexdigest() == before
    with pytest.raises(OutputError):  # input named like an output, inside the out dir
        clash = tmp_path / "clash"
        clash.mkdir()
        (clash / "clean.csv").write_bytes(b"id\n1\n")
        r = process(b"id\n1\n", Rules(), "clean.csv")
        write_outputs(r, str(clash), force=True, input_path=str(clash / "clean.csv"))
    assert (clash / "clean.csv").read_bytes() == b"id\n1\n"


# AC-25
def test_cli_no_overwrite(tmp_path):
    out = tmp_path / "o"
    args = [str(DEMO_CSV), "--out", str(out), "--rules", str(DEMO_RULES)]
    assert cli_main(args) == 0
    first = (out / "summary.json").read_bytes()
    assert cli_main(args) == 2
    assert cli_main(args + ["--force"]) == 0
    assert (out / "summary.json").read_bytes() == first


# AC-26
def test_cli_matches_core(tmp_path):
    out = tmp_path / "o"
    assert cli_main([str(DEMO_CSV), "--out", str(out), "--rules", str(DEMO_RULES)]) == 0
    expected = render_outputs(process(DEMO_CSV.read_bytes(), demo_rules(), str(DEMO_CSV)))
    for name, b in expected.items():
        assert (out / name).read_bytes() == b


# AC-27
def test_summary_no_paths(tmp_path):
    r = process(b"id\n1\n", Rules(), str(tmp_path / "sub" / "my.csv"))
    s = render_outputs(r)["summary.json"].decode("utf-8")
    assert json.loads(s)["input_file"] == "my.csv"
    assert str(tmp_path) not in s and "Users" not in s
    assert not any(k in json.loads(s) for k in ("timestamp", "generated_at", "time"))


def test_rules_from_dict_rejects_unknown():
    with pytest.raises(RuleError):
        Rules.from_dict({"trim": ["a"]})
    with pytest.raises(RuleError):
        run("id\n1\n", Rules(dedupe_keep="middle"))
