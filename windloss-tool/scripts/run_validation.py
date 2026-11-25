"""Reproduce the model-selection and back-test results on the supplied sample data.

Usage:  python scripts/run_validation.py [--scope before_outage|outside_outage]

Writes to results/:
  validation_results_<scope>.md         model comparison, holdout and back-test tables
  hidden_period_predictions_<scope>.csv reconstructed wind speed, power and energy for the
                                        detected outage (1-3 Sep in the sample data)
"""
import argparse
import glob
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import data_loader as dl, data_validation as dv, outage_detection as od, pipeline as pl, reporting as rp  # noqa: E402
from src.power_curve import PowerCurve  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default="before_outage", choices=["before_outage", "outside_outage"])
    ap.add_argument("--data", default=os.path.join(ROOT, "sample_data"))
    a = ap.parse_args()
    out_dir = os.path.join(ROOT, "results")
    os.makedirs(out_dir, exist_ok=True)

    files = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(a.data, "*_data.*")))]
    prep = dv.prepare(dl.load_timeseries_files(files))
    curves = dl.load_power_curves([(os.path.basename(f), f) for f in glob.glob(os.path.join(a.data, "*_power_curve.*"))])
    cfg = pl.Config(training_scope=a.scope)
    results, backtests = [], []
    L = [f"# Validation results (training scope: {a.scope})", "",
         f"Generated {pd.Timestamp.now():%Y-%m-%d %H:%M}. All numbers below are produced by this script.", ""]
    for t in sorted(curves):
        refs, _ = pl.eligible_references(prep.wide["wind_speed"].columns, t)
        s, e, _ = od.suggest_outage(prep.wide["wind_speed"][t], prep.wide["wind_speed"], refs, prep.freq)
        curve = PowerCurve.from_frame(curves[t], t)
        t0 = time.time()
        r = pl.run_target(prep, t, refs, s, e, curve, cfg)
        results.append(r)
        test = prep.wide["test_set"][t] & prep.wide["wind_speed"][t].notna()
        bt = pl.backtest(prep, t, refs, test[test].index.min(), test[test].index.max(), curve, cfg)
        backtests.append(bt)
        L += [f"## {t}  (references: {', '.join(refs)}; outage {s:%Y-%m-%d %H:%M} – {e:%Y-%m-%d %H:%M}; "
              f"{time.time() - t0:.0f}s)", "", "### Feature-group selection (Ridge, CV RMSE)", "",
              r.group_log.to_markdown(index=False, floatfmt=".4f"), "",
              "### Model comparison (rolling-origin CV, identical validation timestamps)", "",
              r.comparison.to_markdown(index=False, floatfmt=".4f"), "",
              f"Selected: **{r.selected_model}** — {r.selection_reason}", "",
              f"### Final holdout ({r.split_info['holdout']}, scored after selection)", "",
              r.holdout.to_markdown(index=False, floatfmt=".4f"), "",
              f"### Back-test on shown test period {bt.period[0]:%Y-%m-%d %H:%M} – {bt.period[1]:%Y-%m-%d %H:%M}", "",
              f"(full procedure re-run with these target values hidden; model chosen: {bt.result.selected_model}, "
              f"features: {', '.join(bt.result.groups)})", "",
              f"- Wind speed: RMSE {bt.wind['RMSE (m/s)']:.3f} m/s, MAE {bt.wind['MAE (m/s)']:.3f} m/s, "
              f"bias {bt.wind['Bias (m/s)']:+.3f} m/s, R² {bt.wind['R²']:.3f}",
              f"- Power (via power curve): RMSE {bt.power['RMSE (kW)']:.0f} kW, MAE {bt.power['MAE (kW)']:.0f} kW",
              f"- Energy: predicted {bt.energy['predicted energy (kWh)']:,.0f} kWh vs actual-wind "
              f"{bt.energy['reference energy (kWh)']:,.0f} kWh → {bt.energy['deviation (%)']:+.2f} %",
              f"- Actual energy inside empirical 80% band "
              f"({bt.result.energy_band['P10 (kWh)']:,.0f} – {bt.result.energy_band['P90 (kWh)']:,.0f}): {bt.band_hit}",
              "", f"### Hidden-outage estimate: {r.energy_kwh:,.0f} kWh "
              f"(80% band {r.energy_band['P10 (kWh)']:,.0f} – {r.energy_band['P90 (kWh)']:,.0f})", ""]
        print(t, r.selected_model, r.groups, f"BT wind RMSE {bt.wind['RMSE (m/s)']:.3f} MAE {bt.wind['MAE (m/s)']:.3f}",
              f"power RMSE {bt.power['RMSE (kW)']:.0f} MAE {bt.power['MAE (kW)']:.0f}",
              f"energy {bt.energy['deviation (%)']:+.2f}%", f"hidden {r.energy_kwh:,.0f} kWh")
    # aggregate back-test
    c = pd.concat([b.compare for b in backtests])
    c = c[c["actual_ws"].notna() & c["predicted_ws"].notna()]
    ep, ea = (c["expected_power_kw"].sum() / 6), (c["actual_power_kw"].sum() / 6)
    L += ["## All target turbines combined (back-test)", "",
          f"- Wind RMSE {np.sqrt(((c.predicted_ws - c.actual_ws) ** 2).mean()):.3f} m/s, "
          f"MAE {(c.predicted_ws - c.actual_ws).abs().mean():.3f} m/s",
          f"- Power RMSE {np.sqrt(((c.expected_power_kw - c.actual_power_kw) ** 2).mean()):.0f} kW, "
          f"MAE {(c.expected_power_kw - c.actual_power_kw).abs().mean():.0f} kW",
          f"- Summed energy deviation {100 * (ep - ea) / ea:+.2f} % ({ep - ea:+,.0f} kWh)", "",
          f"## Hidden outage, all turbines: {sum(r.energy_kwh for r in results):,.0f} kWh"]
    with open(os.path.join(out_dir, f"validation_results_{a.scope}.md"), "w") as f:
        f.write("\n".join(L))
    with open(os.path.join(out_dir, f"hidden_period_predictions_{a.scope}.csv"), "wb") as f:
        f.write(rp.predictions_csv(results))
    print("\n".join(L[-6:]))


if __name__ == "__main__":
    main()
