import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
SAMPLE = os.path.join(ROOT, "sample_data")


def make_long(n_days=8, freq="10min", seed=0, start="2026-01-01"):
    """Synthetic data: target T1 = 1.1 x mean(H1, O1) + noise. For software tests only."""
    rng = np.random.default_rng(seed)
    ts = pd.date_range(start, periods=int(pd.Timedelta(days=n_days) / pd.Timedelta(freq)), freq=freq)
    base = 7 + 3 * np.sin(np.arange(len(ts)) / 50) + rng.normal(0, 0.3, len(ts)).cumsum() * 0.02
    base = np.clip(base, 0.5, None)
    frames = []
    for name, scale in [("H1", 1.0), ("O1", 0.9), ("T1", 1.1)]:
        ws = np.clip(base * scale + rng.normal(0, 0.3, len(ts)), 0, None)
        frames.append(pd.DataFrame({
            "timestamp": ts, "turbine": name, "wind_speed": ws,
            "wind_direction": (200 + rng.normal(0, 20, len(ts))) % 360,
            "ambient_temperature": 15 + rng.normal(0, 1, len(ts)),
            "air_pressure": 1000 + rng.normal(0, 1, len(ts)),
            "wind_speed_stddev": np.abs(rng.normal(1, 0.2, len(ts))),
            "test_set": False}))
    return pd.concat(frames, ignore_index=True)


@pytest.fixture
def synth_long():
    return make_long()


@pytest.fixture
def curve_df():
    return pd.DataFrame({"wind_speed": [0, 3, 4, 10, 12, 25], "power_kw": [0, 0, 100, 2000, 3000, 3000]})
