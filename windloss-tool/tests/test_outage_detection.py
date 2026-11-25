import numpy as np
import pandas as pd

from src import outage_detection as od

F = pd.Timedelta("10min")


def _s(vals):
    return pd.Series(vals, index=pd.date_range("2026-01-01", periods=len(vals), freq=F), dtype=float)


def test_isolated_and_block_runs():
    v = [1.0] * 20
    v[2] = np.nan
    for i in range(8, 15):
        v[i] = np.nan
    runs = od.find_missing_runs(_s(v), F, block_threshold=6)
    assert runs["kind"].tolist() == ["isolated", "block"]
    assert runs.loc[1, "intervals"] == 7
    assert runs.loc[1, "duration_h"] == 7 / 6


def test_missing_at_start_and_end():
    v = [np.nan, np.nan, 1, 1, 1, np.nan]
    runs = od.find_missing_runs(_s(v), F, block_threshold=2)
    assert runs["start"].iloc[0] == _s(v).index[0]
    assert runs["end"].iloc[-1] == _s(v).index[-1]


def test_no_missing():
    assert od.find_missing_runs(_s([1, 2, 3]), F).empty


def test_suggest_prefers_block_with_reference_data():
    n = 100
    t = [1.0] * n
    for i in list(range(10, 40)) + list(range(60, 80)):
        t[i] = np.nan
    target = _s(t)
    ref = [1.0] * n
    for i in range(10, 40):
        ref[i] = np.nan  # references also down in the longer block
    wide = pd.DataFrame({"T1": target, "H1": _s(ref)})
    s, e, runs = od.suggest_outage(target, wide, ["H1"], F)
    assert s == target.index[60] and e == target.index[79]


def test_manual_adjustment_mask():
    idx = pd.date_range("2026-01-01", periods=10, freq=F)
    m = od.outage_mask(idx, idx[2], idx[4])
    assert m.sum() == 3 and m[2] and m[4] and not m[5]


def test_reference_availability():
    idx = pd.date_range("2026-01-01", periods=4, freq=F)
    w = pd.DataFrame({"H1": [1, np.nan, 1, 1], "O1": [np.nan, np.nan, 1, 1]}, index=idx)
    a = od.reference_availability(w, ["H1", "O1"], idx[0], idx[3])
    assert a.set_index("reference").loc["H1", "available %"] == 75.0
    assert a.attrs["any_reference_%"] == 75.0
