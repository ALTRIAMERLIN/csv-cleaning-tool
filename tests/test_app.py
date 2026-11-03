"""Headless UI tests with Streamlit AppTest. The UI must show the same numbers as the core."""
from __future__ import annotations

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
EXP = json.loads((ROOT / "data" / "expected" / "demo_expected.json").read_text(encoding="utf-8"))
RULES = json.loads((ROOT / "data" / "demo_rules.json").read_text(encoding="utf-8"))


def start() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
    at.run()
    return at


def test_ui_waits_for_input():
    at = start()
    assert not at.exception
    assert any("Upload a CSV" in i.value for i in at.info)


def test_ui_full_flow_matches_expected():
    at = start()
    at.button[0].click().run()  # bundled synthetic sample
    assert not at.exception
    assert at.metric[0].value == str(EXP["counts"]["input_rows"])
    at.multiselect(key="trim").set_value(RULES["trim_columns"])
    at.multiselect(key="required").set_value(RULES["required_columns"])
    at.multiselect(key="email").set_value(RULES["email_columns"])
    at.multiselect(key="keys").set_value(RULES["dedupe_keys"])
    at.run()
    run_btn = next(b for b in at.button if b.label == "Run cleaning")
    run_btn.click().run()
    assert not at.exception
    shown = {m.label: m.value for m in at.metric}
    c = EXP["counts"]
    assert shown["Input rows"] == str(c["input_rows"])
    assert shown["Clean rows"] == str(c["clean_rows"])
    assert shown["Issue rows"] == str(c["issue_rows"])
    assert shown["Cells trimmed"] == str(c["changed_cells"])
    assert any(cap.value.startswith("✅ Output check") for cap in at.caption)
    assert len(at.tabs) == 4


def test_ui_rules_change_warns():
    at = start()
    at.button[0].click().run()
    at.multiselect(key="keys").set_value(["email"]).run()
    next(b for b in at.button if b.label == "Run cleaning").click().run()
    at.radio(key="keep").set_value("last").run()
    assert any("Rules changed" in w.value for w in at.warning)


def test_ui_failed_check_says_failed(monkeypatch):
    from csvclean import core

    monkeypatch.setattr(core, "check_accounting", lambda files, counts: False)
    at = start()
    at.button[0].click().run()
    next(b for b in at.button if b.label == "Run cleaning").click().run()
    assert not at.exception
    assert any(e.value.startswith("Output check failed") for e in at.error)
    assert not any("passed" in cap.value for cap in at.caption)
