# Wind-turbine outage energy-loss estimator

When a wind farm loses communication, its turbines' wind measurements are missing.
This local web app reconstructs the missing wind speeds from turbines in **other** wind parks, converts them to
expected power with each turbine's power curve, and estimates the lost energy (kWh) — with honest validation,
uncertainty bands, an engineering report and an insurance e-mail.

## Quick start

```bash
cd windloss-tool
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py                                     # opens http://localhost:8501
```

In the sidebar choose **Demo data** (the hackathon files) or upload your own CSVs, then follow the tabs
① Data → ② Outage (press *Confirm outage and run analysis*, ~20 s per turbine) → ③ Model → ④ Wind & energy →
⑤ Validation (*Run back-test*) → ⑥ Report & export. No internet connection is needed.

```bash
python -m pytest -q                                      # 56 tests incl. headless GUI click-throughs (~2 min)
python scripts/run_validation.py                         # reproduces results/validation_results_before_outage.md
```

## Method in one paragraph

For each target turbine, a **Ridge regression** (a weighted sum of reference measurements with a penalty against
extreme weights) predicts its 10-minute wind speed from the reference turbines' wind speed in the same interval plus
the references' wind speed averaged over centred 30/60/120-minute windows. Averaging matters because parks are
kilometres apart: individual gusts do not coincide, and weather reaches each park minutes apart. The model is
fitted on periods where target and references were both measured, then applied to the outage. Expected power =
linear interpolation of the power curve; energy = Σ power × 10/60 h.

The model and the inputs are **not hard-coded**: for every turbine and every run the tool tests

* feature groups by greedy forward selection (reference wind speed → + smoothed wind, direction (sin/cos),
  temperature, time-varying pressure, wind std-dev), keeping a group only if it lowers cross-validated RMSE ≥ 1 %;
* four models — Linear, Ridge, Random Forest, Histogram Gradient Boosting — plus a no-skill mean baseline, on
  identical validation timestamps;
* and selects with an explicit rule: models within 2 % of the best CV RMSE are "equally accurate" and the simplest
  wins; a tree model must beat Ridge by > 2 % **and** in most folds.

### Validation design

Training pool = intervals with measured target wind, outside the outage, and (default) **before** it.
It is split in time: 4 rolling-origin folds (train on the past, validate on the next block, 6-hour embargo against
autocorrelation leakage) for all choices, then a final holdout block (latest 15 %) scored once after selection.
Imputation/scaling are fitted inside the pipeline on training rows only. The **back-test** (tab ⑤) hides a period
with known truth, re-runs the entire procedure including model selection, and scores wind, power and energy.

## Results on the hackathon data (produced by the code, `results/`)

Selected in every case: **Ridge Regression** with *reference wind speed + smoothed reference wind speed*.
Direction, temperature, pressure and std-dev each improved CV RMSE by < 1 % and were rejected. Random Forest and
Gradient Boosting were 3–9 % worse in cross-validation.

Back-test on the shown test period 4–9 Sep (864 intervals per turbine; trained only on data before 4 Sep, test
values hidden; power via power curve):

| Turbine | Wind RMSE | Wind MAE | Power RMSE | Power MAE | Summed energy deviation |
|---|---|---|---|---|---|
| T1 | 1.52 m/s | 1.18 m/s | 941 kW | 653 kW | +18.0 % |
| T2 | 1.18 m/s | 0.88 m/s | 754 kW | 504 kW | −0.8 % |
| T3 | 1.29 m/s | 0.98 m/s | 843 kW | 593 kW | −4.7 % |
| **All** | **1.34 m/s** | **1.01 m/s** | **849 kW** | **583 kW** | **+2.9 %** |

Estimated energy-yield loss for the hidden outage 1 Sep 00:00 – 3 Sep 23:50: **T1 99.8 MWh, T2 121.1 MWh,
T3 95.5 MWh, total 316.5 MWh** (`results/hidden_period_predictions_before_outage.csv`).

Sensitivity checks run during development (numbers in `results/`):
* Training on all data outside the outage (before and after) gives a back-test of 1.32 / 1.01 m/s and
  +3.3 % energy — practically the same — but moves T1's hidden-outage estimate to 88.1 MWh (total 304.6 MWh).
  The T1 relationship is the least stable of the three.
* Automatic reference selection lowers CV error slightly but was marginally worse on the back-test
  (e.g. T2 1.20 vs 1.18 m/s), so all eligible references remain the default; auto-selection is an option.
* Longer smoothing windows (up to 6 h) did not improve CV RMSE.

## Data handling (see `sample_data/README.md` for the inspection report)

NaN is always missing, never zero. Rows absent from a file are inserted as missing. Duplicate timestamps keep the
first record. Off-grid timestamps are dropped and reported. Sensor-fault records (speed, direction and temperature
all exactly 0) are treated as missing. Constant "pressure" (O park) and absent std-dev are detected and never used.
Missing reference inputs: gaps ≤ 30 min are interpolated, longer ones filled from the other references (scaled by the
long-run ratio), and intervals with no reference at all are flagged *unpredictable* — never filled with zero.
Every action is listed in the app and in the report.

## Outputs

* `outage_predictions.csv` — timestamp, turbine, reconstructed wind speed, 80 % band, expected power, interval
  energy, data-quality and power-curve flags.
* `model_metrics.csv` — CV comparison, holdout and back-test metrics.
* `engineering_report.md` — outage, method, model choice and reasons, energy, uncertainty, assumptions.
* Insurance e-mail (editable, opens in your mail program; nothing is sent automatically).

## Project structure

```
app.py                      Streamlit GUI only (calls src/)
.streamlit/config.toml      light, minimal theme
docs/USER_GUIDE.md          user guide shown inside the app
src/data_loader.py          CSV/Excel reading, column mapping, power-curve loading
src/data_validation.py      quality rules, regular grid, summary
src/outage_detection.py     missing runs, outage suggestion, reference availability
src/feature_engineering.py  reference features + missing-reference strategy
src/model_training.py       models, chronological split, feature & model selection rule
src/model_evaluation.py     RMSE/MAE/R²/bias, error by speed bin, energy deviation
src/prediction.py           reconstruction + flags
src/power_curve.py          validation, interpolation, out-of-range policy
src/energy_calculation.py   kW → kWh, durations, daily/hourly totals
src/uncertainty.py          empirical bands, block-bootstrap energy range
src/reporting.py            CSVs, report, insurance e-mail
src/pipeline.py             orchestration: run_target(), backtest()
scripts/run_validation.py   reproduces results/
tests/                      56 pytest tests (synthetic fixtures for unit tests, real data end-to-end + GUI)
```

## Assumptions and limitations

* The energy is a **counterfactual estimate**: the turbine is assumed available and operating on its supplied power
  curve (no curtailment, icing, grid limits, wakes or air-density correction). Missing data alone does not prove the
  turbine stopped.
* Power accuracy is evaluated through the power curve; measured electrical output is not in the data.
* Power-curve unit is not stated in the files; max 4500 is interpreted as kW (selectable in the app).
* Cross-park correlation is moderate (r ≈ 0.7–0.8), so 10-minute errors of ~1.2–1.5 m/s remain; regression
  smooths peaks and lulls.
* The empirical 80 % band replays real historical error sequences (1-day blocks). It captured the actual energy
  for T2 and T3 in the back-test but **not for T1**, whose week-long bias (+0.5 m/s) exceeded anything in its
  training errors: the band understates regime-level uncertainty and is not a guaranteed confidence interval.
* Centred smoothing uses reference data shortly after each timestamp — valid after the fact, not for real-time use.

## Possible improvements

Direction-sector-specific relationships (classic MCP by sector), longer multi-season histories, an
air-density-corrected power curve where pressure is measured, and wider bands that include week-to-week bias.
