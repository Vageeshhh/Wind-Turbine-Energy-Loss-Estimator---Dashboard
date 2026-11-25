import glob
import os

import numpy as np
import pandas as pd
import pytest

from src import data_loader as dl
from src import data_validation as dv
from src import outage_detection as od
from src import pipeline as pl
from src import reporting as rp
from src.power_curve import PowerCurve
from tests.conftest import SAMPLE, make_long


def test_synthetic_end_to_end(curve_df):
    d = make_long(n_days=10)
    m = (d.turbine == "T1") & (d.timestamp >= "2026-01-08") & (d.timestamp < "2026-01-09")
    truth = d.loc[m, "wind_speed"].to_numpy()
    d.loc[m, "wind_speed"] = np.nan
    prep = dv.prepare(d)
    refs, enforced = pl.eligible_references(prep.wide["wind_speed"].columns, "T1")
    assert enforced and set(refs) == {"H1", "O1"}
    s, e, _ = od.suggest_outage(prep.wide["wind_speed"]["T1"], prep.wide["wind_speed"], refs, prep.freq)
    assert s == pd.Timestamp("2026-01-08") and e == pd.Timestamp("2026-01-08 23:50")
    cfg = pl.Config(models=["Linear Regression", "Ridge Regression"], n_boot=50)
    r = pl.run_target(prep, "T1", refs, s, e, PowerCurve.from_frame(curve_df), cfg)
    assert len(r.outage_table) == 144
    assert (r.outage_table["source"] == "reconstructed").all()
    # outside the outage, observations are preserved
    obs = r.series[r.series["source"] == "observed"]
    assert np.allclose(obs["ws_final"], obs["observed_ws"])
    rmse = np.sqrt(np.mean((r.outage_table["predicted_ws"].to_numpy() - truth) ** 2))
    assert rmse < 0.8
    assert r.energy_kwh == pytest.approx(np.nansum(r.outage_table["expected_power_kw"]) / 6)
    assert r.energy_band["P10 (kWh)"] <= r.energy_band["P90 (kWh)"]
    # exports
    assert b"reconstructed_wind_speed_m_s" in rp.predictions_csv([r])
    assert "Estimated energy-yield loss" in rp.engineering_report([r])
    subj, body = rp.insurance_email([r], "Test park")
    assert "kWh" in body and "Test park" in subj


def test_hidden_values_never_used(curve_df):
    """Changing the hidden target values must not change predictions."""
    d = make_long(n_days=10)
    m = (d.turbine == "T1") & (d.timestamp >= "2026-01-08") & (d.timestamp < "2026-01-09")
    cfg = pl.Config(models=["Ridge Regression"], feature_groups=["wind_speed"], n_boot=20)
    out = []
    for val in (0.0, 30.0):
        dd = d.copy()
        dd.loc[m, "wind_speed"] = val
        prep = dv.prepare(dd)
        bt = pl.backtest(prep, "T1", ["H1", "O1"], "2026-01-08", "2026-01-08 23:50",
                         PowerCurve.from_frame(curve_df), cfg)
        out.append(bt.compare["predicted_ws"].to_numpy())
    assert np.allclose(out[0], out[1])


def test_unpredictable_rows_flagged(curve_df):
    d = make_long(n_days=10)
    m = (d.timestamp >= "2026-01-08") & (d.timestamp < "2026-01-08 02:00")
    d.loc[m & (d.turbine == "T1"), "wind_speed"] = np.nan
    d.loc[m & d.turbine.isin(["H1", "O1"]), "wind_speed"] = np.nan
    prep = dv.prepare(d)
    cfg = pl.Config(models=["Ridge Regression"], n_boot=20)
    r = pl.run_target(prep, "T1", ["H1", "O1"], "2026-01-08", "2026-01-08 01:50", PowerCurve.from_frame(curve_df), cfg)
    assert (r.outage_table["source"] == "unpredictable").all()
    assert r.outage_table["predicted_ws"].isna().all()   # never silently zero
    assert r.energy_band["intervals reconstructed"] == 0


@pytest.mark.skipif(not os.path.exists(os.path.join(SAMPLE, "T1_data.xlsx")), reason="sample data missing")
def test_real_sample_data_workflow():
    files = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(SAMPLE, "*_data.xlsx")))]
    prep = dv.prepare(dl.load_timeseries_files(files))
    curves = dl.load_power_curves([(os.path.basename(f), f) for f in glob.glob(os.path.join(SAMPLE, "*_power_curve.xlsx"))])
    refs, enforced = pl.eligible_references(prep.wide["wind_speed"].columns, "T2")
    assert enforced and all(not r.startswith("T") for r in refs)
    s, e, _ = od.suggest_outage(prep.wide["wind_speed"]["T2"], prep.wide["wind_speed"], refs, prep.freq)
    assert s == pd.Timestamp("2026-09-01 00:00") and e == pd.Timestamp("2026-09-03 23:50")
    cfg = pl.Config(models=["Linear Regression", "Ridge Regression"], n_boot=50)
    r = pl.run_target(prep, "T2", refs, s, e, PowerCurve.from_frame(curves["T2"], "T2"), cfg)
    assert len(r.outage_table) == 432 and r.outage_table["predicted_ws"].notna().all()
    assert 0 < r.energy_kwh < 4500 * 72
    # training must not touch the outage or anything after it
    assert pd.Timestamp(r.split_info["training period"].split(" to ")[1]) < s
    assert b"T2" in rp.metrics_csv([r])
