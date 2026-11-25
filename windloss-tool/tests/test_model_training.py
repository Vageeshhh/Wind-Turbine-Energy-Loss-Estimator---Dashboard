import numpy as np
import pandas as pd
import pytest

from src import data_validation as dv
from src import feature_engineering as fe
from src import model_training as mt
from tests.conftest import make_long


def _setup(n_days=10):
    prep = dv.prepare(make_long(n_days=n_days))
    y = prep.wide["wind_speed"]["T1"]
    pool = y.notna().to_numpy()
    fs = fe.build_features(prep.wide, ["H1", "O1"], ["wind_speed", "smoothed"], prep.freq, pool)
    return prep, y, pool, fs


def test_chronological_folds_no_overlap_and_embargo():
    prep, y, pool, fs = _setup()
    sp = mt.chronological_split(y.index, pool)
    for tr, va in sp.cv_folds:
        assert y.index[tr].max() < y.index[va].min() - mt.EMBARGO + pd.Timedelta("1min")
    if len(sp.holdout):
        last_val = max(va.max() for _, va in sp.cv_folds)
        assert sp.holdout.min() > last_val


def test_identical_validation_timestamps_across_models():
    prep, y, pool, fs = _setup()
    sp = mt.chronological_split(y.index, pool)
    a = mt.cross_validate("Ridge Regression", fs.X, y, sp)
    b = mt.cross_validate("Gradient Boosting", fs.X, y, sp)
    assert np.array_equal(a.oof_pos, b.oof_pos)


def test_reproducible_with_seed():
    prep, y, pool, fs = _setup()
    sp = mt.chronological_split(y.index, pool)
    a = mt.cross_validate("Random Forest", fs.X, y, sp, seed=1)
    b = mt.cross_validate("Random Forest", fs.X, y, sp, seed=1)
    assert np.allclose(a.oof_pred, b.oof_pred)


def test_no_preprocessing_leakage():
    """Imputer statistics come from training rows only."""
    prep, y, pool, fs = _setup()
    X = fs.X.copy()
    X.iloc[-50:, 0] = 1e6           # extreme values only in 'future' rows
    tr = np.arange(0, len(X) - 100)
    m = mt.make_model("Ridge Regression").fit(X.to_numpy()[tr], y.to_numpy()[tr])
    imp = m.named_steps["impute"].statistics_[0]
    assert imp < 100


def test_missing_features_handled():
    prep, y, pool, fs = _setup()
    X = fs.X.copy()
    X.iloc[::7, 1] = np.nan
    sp = mt.chronological_split(y.index, pool)
    r = mt.cross_validate("Linear Regression", X, y, sp)
    assert np.isfinite(r.oof_pred).all()


def test_insufficient_data_raises():
    idx = pd.date_range("2026-01-01", periods=100, freq="10min")
    with pytest.raises(mt.InsufficientDataError):
        mt.chronological_split(idx, np.ones(100, bool))


def test_selection_prefers_ridge_on_linear_problem():
    prep, y, pool, fs = _setup()
    sp = mt.chronological_split(y.index, pool)
    table, chosen, reason, _ = mt.compare_models(fs.X, y, sp)
    assert chosen in ("Ridge Regression", "Linear Regression")
    assert table["selected"].sum() == 1
    base = table.set_index("model").loc["Mean (no-skill baseline)", "CV RMSE (m/s)"]
    assert table.set_index("model").loc[chosen, "CV RMSE (m/s)"] < base


def test_feature_selection_log():
    prep, y, pool, _ = _setup()
    fs = fe.build_features(prep.wide, ["H1", "O1"], fe.ALL_GROUPS, prep.freq, pool)
    sp = mt.chronological_split(y.index, pool)
    groups, log = mt.select_feature_groups(fs.X, fs.descriptions, y, sp)
    assert groups[0] == "wind_speed" and len(log) >= 2
