import numpy as np
import pandas as pd

from src import data_validation as dv
from src import feature_engineering as fe


def test_baseline_and_groups(synth_long):
    prep = dv.prepare(synth_long)
    mask = np.ones(len(prep.wide["wind_speed"]), bool)
    fs = fe.build_features(prep.wide, ["H1", "O1"], fe.ALL_GROUPS, prep.freq, mask)
    groups = set(fs.descriptions["group"])
    assert {"wind_speed", "smoothed", "direction", "temperature", "pressure", "turbulence"} <= groups
    assert "H1_dir_sin" in fs.X and "T1_ws" not in fs.X  # target never a feature
    assert not any("test" in c for c in fs.X.columns)


def test_direction_encoding_continuous_at_north(synth_long):
    d = synth_long.copy()
    d.loc[d.turbine == "H1", "wind_direction"] = [359.9, 0.1] * (int((d.turbine == "H1").sum()) // 2)
    prep = dv.prepare(d)
    fs = fe.build_features(prep.wide, ["H1"], ["wind_speed", "direction"], prep.freq,
                           np.ones(len(prep.wide["wind_speed"]), bool))
    assert np.allclose(fs.X["H1_dir_cos"].iloc[:2], 1, atol=1e-4)


def test_constant_pressure_excluded():
    from tests.conftest import make_long
    d = make_long()
    d.loc[d.turbine == "O1", "air_pressure"] = 990.27
    d.loc[d.turbine == "O1", "wind_speed_stddev"] = np.nan
    prep = dv.prepare(d)
    av = fe.available_groups(prep.wide, ["H1", "O1"])
    assert av["pressure"] == ["H1"] and av["turbulence"] == ["H1"]


def test_missing_reference_filled_not_discarded(synth_long):
    d = synth_long.copy()
    h = d[d.turbine == "H1"].index
    d.loc[h[100], "wind_speed"] = np.nan          # short gap -> interpolated
    d.loc[h[200:230], "wind_speed"] = np.nan      # long gap  -> cross-filled from O1
    prep = dv.prepare(d)
    mask = np.ones(len(prep.wide["wind_speed"]), bool)
    fs = fe.build_features(prep.wide, ["H1", "O1"], ["wind_speed"], prep.freq, mask)
    assert fs.ref_fill.flags["H1"].iloc[100] == "interpolated"
    assert (fs.ref_fill.flags["H1"].iloc[200:230] == "cross-filled").all()
    assert fs.X["H1_ws"].notna().all() and fs.predictable.all()


def test_no_reference_at_all_unpredictable(synth_long):
    d = synth_long.copy()
    for t in ["H1", "O1"]:
        idx = d[d.turbine == t].index[300:340]
        d.loc[idx, "wind_speed"] = np.nan
    prep = dv.prepare(d)
    fs = fe.build_features(prep.wide, ["H1", "O1"], ["wind_speed"], prep.freq,
                           np.ones(len(prep.wide["wind_speed"]), bool))
    assert not fs.predictable[310]


def test_smoothing_window_odd():
    assert fe._window(60, pd.Timedelta("10min")) == 7
    assert fe._window(30, pd.Timedelta("10min")) == 3
