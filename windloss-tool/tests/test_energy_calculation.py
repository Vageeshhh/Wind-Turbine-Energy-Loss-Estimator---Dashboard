import numpy as np
import pandas as pd
import pytest

from src import energy_calculation as ec
from src.model_evaluation import energy_deviation


def test_kw_to_kwh_10min():
    h = ec.interval_hours(pd.Timedelta("10min"))
    assert h == pytest.approx(1 / 6)
    e = ec.interval_energy_kwh([600, 1200], h)
    assert np.allclose(e, [100, 200])


def test_one_hour_constant_power():
    h = ec.interval_hours(pd.Timedelta("10min"))
    assert ec.interval_energy_kwh(np.full(6, 4500.0), h).sum() == pytest.approx(4500)


def test_irregular_timestamps_flagged():
    ts = pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:10", "2026-01-01 00:13", "2026-01-01 00:40"])
    hours, ok = ec.durations_from_timestamps(ts, pd.Timedelta("10min"))
    assert ok.tolist() == [True, False, False, False]
    assert np.isnan(hours[2]) and hours[0] == pytest.approx(1 / 6)
    # a pure gap (00:10 -> 00:40) is fine: it is just missing intervals
    ts2 = pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:10", "2026-01-01 00:40"])
    _, ok2 = ec.durations_from_timestamps(ts2, pd.Timedelta("10min"))
    assert ok2.all()


def test_zero_reference_energy():
    d = energy_deviation(10.0, 0.0)
    assert np.isnan(d["deviation (%)"]) and d["difference (kWh)"] == 10.0 and d["note"]


def test_energy_deviation_percent():
    assert energy_deviation(110, 100)["deviation (%)"] == pytest.approx(10)


def test_aggregation_multiple_turbines():
    t = ec.totals({"T1": 100.0, "T2": 50.5})
    assert t.iloc[-1]["energy (kWh)"] == pytest.approx(150.5)


def test_daily_summary():
    ts = pd.date_range("2026-01-01 23:00", periods=12, freq="10min")
    s = ec.summarize_energy(ts, np.ones(12), "D")
    assert s["energy (kWh)"].tolist() == [6.0, 6.0]


def test_nan_power_contributes_nothing():
    e = ec.interval_energy_kwh([np.nan, 600.0], 1 / 6)
    assert np.nansum(e) == pytest.approx(100)
