"""Headless GUI tests: run app.py with the demo data and press the buttons."""
import os

import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import ROOT, SAMPLE

HAS_SAMPLE = os.path.exists(os.path.join(SAMPLE, "T1_data.xlsx"))


@pytest.mark.skipif(not HAS_SAMPLE, reason="sample data missing")
def test_gui_full_workflow():
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=900)
    at.run()
    assert not at.exception
    # limit to Ridge + Linear for speed
    ms = [m for m in at.multiselect if m.label == "Candidate models"][0]
    ms.set_value(["Linear Regression", "Ridge Regression"]).run()
    run = [b for b in at.button if "run analysis" in b.label][0]
    run.click().run()
    assert not at.exception, at.exception
    assert any("Analysis complete" in s.value for s in at.success)
    bt = [b for b in at.button if "Run back-test" in b.label][0]
    bt.click().run()
    assert not at.exception, at.exception
    labels = " ".join(m.value for m in at.markdown)
    assert "Estimated energy-yield loss" in labels and "Summed energy deviation" in labels
    # progress stepper reflects the completed steps
    assert "stp done" in labels


def test_user_guide_integrated():
    from src import user_guide as ug
    secs = ug.sections()
    for p in ["Tab ①", "Tab ②", "Tab ③", "Tab ④", "Tab ⑤", "Tab ⑥", "The sidebar", "Quick start"]:
        assert ug.section(p), p
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=120)
    at.run()
    assert not at.exception
    labels = [e.label for e in at.expander]
    assert labels.count("How to use this tab") == 6
    assert any("Glossary" in str(m.value) for m in at.markdown)
    jump = [s for s in at.selectbox if s.label == "Jump to section"][0]
    jump.set_value(list(secs)[0]).run()
    assert not at.exception


def test_landing_page_without_files():
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=120)
    at.run()
    src = [r for r in at.radio if r.label == "Data source"][0]
    src.set_value(src.options[1]).run()
    assert not at.exception
    assert any("Step 1" in str(m.value) for m in at.markdown)
