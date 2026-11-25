import io

import numpy as np
import pandas as pd
import pytest

from src import data_loader as dl
from src import data_validation as dv


def _csv(df):
    b = io.BytesIO(df.to_csv(index=False).encode())
    return b


def test_separate_csv_files_use_filename_for_turbine():
    df = pd.DataFrame({"Time": ["2026-01-01 00:00", "2026-01-01 00:10"], "Wind Speed [m/s]": [5.0, 6.0]})
    data = dl.load_timeseries_files([("H7_data.csv", _csv(df)), ("T2_data.csv", _csv(df))])
    assert sorted(data["turbine"].unique()) == ["H7", "T2"]
    assert data["wind_speed"].tolist() == [5.0, 6.0, 5.0, 6.0]


def test_combined_csv_with_turbine_column():
    df = pd.DataFrame({"timestamp": ["2026-01-01 00:00"] * 2, "turbine_name": ["T1", "H1"], "wind_speed": [4, 5]})
    data = dl.load_timeseries_files([("combined.csv", _csv(df))])
    assert set(data["turbine"]) == {"T1", "H1"}


def test_semicolon_csv_and_dayfirst_timestamps():
    raw = "timestamp;wind_speed\n13.09.2026 10:00;5,0\n13.09.2026 10:10;6\n"
    t = dl.read_table(io.BytesIO(raw.encode()), "x.csv")
    ts, bad = dl.parse_timestamps(t["timestamp"])
    assert bad == 0 and ts.iloc[0] == pd.Timestamp("2026-09-13 10:00")


def test_missing_required_column_raises_actionable_error():
    df = pd.DataFrame({"timestamp": ["2026-01-01 00:00"], "foo": [1]})
    with pytest.raises(dl.DataLoadError, match="wind_speed"):
        dl.load_timeseries_files([("T1.csv", _csv(df))])


def test_invalid_timestamps_are_reported_and_dropped():
    df = pd.DataFrame({"timestamp": ["2026-01-01 00:00", "not a date", "2026-01-01 00:20"], "wind_speed": [1, 2, 3]})
    log = dl.LoadLog()
    data = dl.load_timeseries_files([("T1.csv", _csv(df))], log=log)
    assert len(data) == 2
    assert any("could not be parsed" in m for _, m in log.messages)


def test_all_invalid_timestamps_raise():
    df = pd.DataFrame({"timestamp": ["x", "y"], "wind_speed": [1, 2]})
    with pytest.raises(dl.DataLoadError):
        dl.load_timeseries_files([("T1.csv", _csv(df))])


def test_ambiguous_columns_not_silently_mapped():
    mapping, amb = dl.suggest_mapping(["time", "ts", "wind_speed"])
    assert "timestamp" not in mapping and "timestamp" in amb


def test_park_identifier():
    assert dl.park_of("T1") == "T" and dl.park_of("WF12") == "WF" and dl.park_of("turbine") is None


def test_duplicates_kept_first_and_logged(synth_long):
    d = pd.concat([synth_long, synth_long.iloc[[0]].assign(wind_speed=99.0)], ignore_index=True)
    prep = dv.prepare(d)
    assert prep.wide["wind_speed"]["H1"].iloc[0] != 99.0
    assert (prep.log.to_frame()["check"] == "duplicate timestamps").any()


def test_nan_is_missing_not_zero_and_absent_rows_inserted(synth_long):
    d = synth_long.copy()
    d.loc[(d.turbine == "T1") & (d.index % 50 == 0), "wind_speed"] = np.nan
    d = d.drop(index=d[(d.turbine == "H1")].index[10:20])
    prep = dv.prepare(d)
    assert prep.wide["wind_speed"]["H1"].iloc[10:20].isna().all()
    assert (prep.wide["wind_speed"]["T1"] == 0).sum() == 0


def test_irregular_off_grid_timestamps_dropped(synth_long):
    d = synth_long.copy()
    extra = d.iloc[[5]].copy()
    extra["timestamp"] = extra["timestamp"] + pd.Timedelta(minutes=3)
    prep = dv.prepare(pd.concat([d, extra], ignore_index=True))
    assert prep.freq == pd.Timedelta("10min")
    assert (prep.log.to_frame()["check"].str.contains("off-grid")).any()


def test_sensor_fault_zero_records(synth_long):
    d = synth_long.copy()
    i = d[d.turbine == "T1"].index[3]
    d.loc[i, ["wind_speed", "wind_direction", "ambient_temperature"]] = 0.0
    prep = dv.prepare(d)
    assert np.isnan(prep.wide["wind_speed"]["T1"].iloc[3])
    prep2 = dv.prepare(d, zero_fault_rule=False)
    assert prep2.wide["wind_speed"]["T1"].iloc[3] == 0.0


def test_constant_pressure_detected():
    s = pd.Series([990.27] * 100)
    assert dv.variable_availability(s) == "constant (not measured)"
    assert dv.variable_availability(pd.Series([np.nan] * 100)) == "unavailable"


def test_power_curve_loading_units():
    df = pd.DataFrame({"wind_speed": [3, 4], "power": [0.0, 0.1]})
    c = dl.load_power_curves([("T9_power_curve.csv", _csv(df))], unit="MW")
    assert c["T9"]["power_kw"].tolist() == [0.0, 100.0]
