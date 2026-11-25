import numpy as np
import pandas as pd
import pytest

from src.power_curve import PowerCurve, PowerCurveError


def test_values_at_supplied_points(curve_df):
    c = PowerCurve.from_frame(curve_df)
    p, f = c.power(curve_df["wind_speed"].to_numpy())
    assert np.allclose(p, curve_df["power_kw"])


def test_linear_interpolation(curve_df):
    c = PowerCurve.from_frame(curve_df)
    p, _ = c.power([7.0, 3.5])
    assert p[0] == pytest.approx(100 + (2000 - 100) * 0.5)
    assert p[1] == pytest.approx(50)


def test_out_of_range_flagged(curve_df):
    c = PowerCurve.from_frame(curve_df)
    p, f = c.power([30.0, -1.0, np.nan])
    assert f[0] == "above curve range" and p[0] == 3000
    assert f[1] == "" and p[1] == 0            # lowest point is 0 kW -> idle, no flag
    assert f[2] == "no wind speed" and np.isnan(p[2])
    p0, _ = c.power([30.0], above_policy="zero")
    assert p0[0] == 0


def test_unsorted_sorted_and_noted(curve_df):
    c = PowerCurve.from_frame(curve_df.iloc[::-1])
    assert np.all(np.diff(c.wind_speed) > 0) and c.notes


def test_invalid_curves():
    with pytest.raises(PowerCurveError):
        PowerCurve.from_frame(pd.DataFrame({"wind_speed": [1, 2], "power_kw": [0, -5]}))
    with pytest.raises(PowerCurveError):
        PowerCurve.from_frame(pd.DataFrame({"wind_speed": [1, 1], "power_kw": [0, 5]}))
    with pytest.raises(PowerCurveError):
        PowerCurve.from_frame(pd.DataFrame({"wind_speed": [1], "power_kw": [0]}))


def test_derived_values(curve_df):
    c = PowerCurve.from_frame(curve_df)
    assert c.rated_kw == 3000 and c.cut_in == 4


def test_real_curve_file():
    import os
    from src.data_loader import load_power_curves
    from tests.conftest import SAMPLE
    f = os.path.join(SAMPLE, "T1_power_curve.xlsx")
    if not os.path.exists(f):
        pytest.skip("sample data not present")
    c = PowerCurve.from_frame(load_power_curves([("T1_power_curve.xlsx", f)])["T1"], "T1")
    assert c.rated_kw == 4500 and c.power([11.5])[0][0] == 4500
