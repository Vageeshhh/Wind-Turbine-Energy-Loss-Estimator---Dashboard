# Outage Energy-Loss Estimator – User Guide

## What the tool does

The tool tells you how much energy (kWh) a wind turbine would have produced during a period when its data was missing, for example during a communication outage. You need this number for an insurance claim, a lost-revenue report or an internal incident review.

When a turbine goes offline, its own wind measurements are missing too. The tool fills that gap in three steps:

1. **Learn.** It studies the past weeks, when both the affected turbine and turbines in *other* wind parks were measuring, and learns how their winds relate.
2. **Reconstruct.** It applies that relationship to the reference turbines' wind during the outage to estimate the missing wind speeds.
3. **Convert.** It turns each estimated wind speed into power with the turbine's power curve and adds everything up to kWh.

You don't need to know statistics or programming. The tool picks the method, checks its own accuracy and explains every choice in plain words.

**Who it is for:** asset managers, operations engineers, claims handlers and anyone who has to put a number on lost production.

## Quick start: your first result in about 3 minutes

Start the app (double-click `start_windows.bat` or `start_mac.command`). It opens in your browser at http://localhost:8501. Then:

1. In the left sidebar, keep **Demo data (hackathon sample)** selected.
2. Open tab **② Outage** and click **✅ Confirm outage and run analysis**. Wait about a minute; a progress bar shows each turbine.
3. Open tab **④ Wind & energy**. The large number at the top left is the **estimated energy-yield loss**.
4. Optional: open tab **⑤ Validation** and click **▶ Run back-test** to see how accurate the method is.
5. Open tab **⑥ Report & export** to download the results, the report and a ready-made insurance e-mail.

The tabs are numbered in the order you use them. You can always go back, change something and run the analysis again.

## The sidebar: choosing your data

The sidebar on the left is where your data comes in. Everything else happens in the tabs.

| Setting | What it means | What to choose |
| --- | --- | --- |
| **Data source** | Demo data uses the hackathon files built into the tool. Upload lets you use your own files. | Demo to try it out; Upload for a real case |
| **Wind data** (upload only) | Time series of every turbine: target turbines *and* reference turbines. CSV or Excel. | All `…_data` files, e.g. T1–T3, H1–H5, O1–O2 |
| **Power curve(s)** (upload only) | Wind speed vs. power for each affected turbine. | One file per target turbine, e.g. `T1_power_curve` |
| **Power-curve unit** | Unit of the power column in your curve files. | kW (default). Pick MW or W if your file uses those |
| **Treat sensor-fault zero records as missing** | Rows where wind speed, direction *and* temperature are all exactly 0 are a sensor fault, not calm wind. | Leave ticked |

## Tab ① Data: check what was loaded and pick the turbines

This tab confirms the tool read your files correctly and lets you say which turbine is affected.

**At the top** four boxes summarise the data: number of turbines and wind parks, the period covered, the time step (normally 10 min) and which power curves were found.

**Choose the turbines:**

- **Target turbine(s)** – the affected turbines whose wind speeds are missing. Turbines with a power curve are pre-selected. You can select several; each is calculated separately and then added up.
- **Reference turbines** – turbines in *other* wind parks whose data is used to fill the gap. The tool only offers turbines from a different park, read from the first letters of the name (T1 is park T, H3 is park H). By default all eligible ones are selected, which is the recommended setting.
- **Let the tool pick the best subset of references automatically** – optional. The tool adds references one by one while they make the prediction more accurate.

**Check the data:**

- **Dataset summary** – one row per turbine: share of missing wind data, average wind speed, and which extra measurements exist. "constant (not measured)" means a placeholder value, which the tool never uses.
- **Column mapping** (fold-out) – which column of your file was recognised as timestamp, wind speed and so on. Only open it if your own files have unusual column names; fields marked * are required.
- **Data-quality actions** (fold-out) – everything the tool corrected, e.g. inserted missing timestamps or sensor-fault rows set to missing.
- **Power curves as interpreted** (fold-out) – a chart of each curve, so you can check the shape and unit.

Red messages here tell you exactly what is missing, for example a target turbine without a power curve.

## Tab ② Outage: confirm the period and run the analysis

The tool finds the outage for you. Your job is to check it and press the run button.

**Detected outage.** A green message shows the longest stretch of missing target data during which the reference turbines still had data, e.g. *Tue 01 Sep 2026 00:00 → Thu 03 Sep 2026 23:50 (432 intervals)*.

**Adjust it if needed.** Change the start/end date and time if you know the real outage times, for example from an alarm log. The end time is the *last* missing 10-minute interval.

**Minimum length of a missing block.** Gaps shorter than this (default 6 intervals = 1 hour) count as random missing values, not as an outage.

**Timeline chart.**

- Top: one row per turbine with a tick wherever wind data exists. A gap in a row = missing data.
- Bottom: the measured wind speed of the target turbine(s).
- The shaded band is the outage you selected.

**Two tables underneath.**

- *Reference data during the selected outage*: how much of the outage each reference turbine covers. Aim for close to 100%.
- *Missing-data runs*: every longer gap found in the target turbine.

**Advanced analysis settings** (fold-out, optional – the defaults are recommended):

| Setting | Default | When to change it |
| --- | --- | --- |
| Training data | Only data before the outage | Choose "all data outside the outage" when data after the outage exists and you want to use it too |
| Input features | Automatic | "Choose manually" only if you want to force e.g. wind direction in |
| Candidate models | All four | Remove Random Forest and Gradient Boosting for a faster run |
| Tolerance for equivalent accuracy | 2% | Rarely; a higher value favours simpler models more strongly |
| Wind above the end of the power curve | Hold last power value | "Assume shutdown" for a more conservative estimate in storms |

**Run it.** Click **✅ Confirm outage and run analysis**. It takes about 20 seconds per turbine with all four models. When you see *Analysis complete*, go to tabs ③ and ④.

A missing measurement does not prove the turbine stopped. The estimate assumes the turbine would have run normally during the selected period.

## Tab ③ Model: how the wind was predicted, and how well

This tab explains the method in plain words. Use it when someone asks "how did you get this number, and can I trust it?". Pick a turbine with the buttons at the top.

**Four headline boxes:**

- **Selected model** – the method chosen, usually *Ridge Regression*: a weighted sum of the reference turbines' wind speeds.
- **CV RMSE** – the typical error of one predicted 10-minute wind speed, measured on past data the model had not seen (about 1.2–1.3 m/s on the demo data).
- **CV MAE** – the average size of the error, in m/s.
- **Skill vs. no-skill** – how much better the model is than simply guessing the average wind (about 35–40% better on the demo data).

Below the boxes, **What it does**, **Why it was chosen** and **Inputs used** say the same in one sentence each.

**Model comparison table.** Four methods are tested on exactly the same past periods, plus a no-skill baseline. The selected row is bold, and the *reason* column explains each decision. The rule: if a complex method is not clearly better (more than 2%), the simpler one wins.

**How the inputs were chosen.** The tool starts with the reference wind speeds and tries adding smoothed wind, wind direction, temperature, pressure and turbulence one group at a time. A group is kept only if it improves accuracy by at least 1%.

**Validation design.** Shows which past days were used for training and testing. The model is always tested on days *after* the ones it learned from, like a real outage.

**Charts:**

- *Predicted vs. measured* – dots close to the dotted diagonal = good predictions.
- *Error distribution* – most errors should sit close to 0.
- *Error by measured wind speed* – shows whether the model is weaker at low or high wind.

**Fold-outs:** *Model weights* (how much each input counts), *Feature definitions* and *Limitations*.

## Tab ④ Wind & energy: the result

This is the tab with the answer: how much energy was lost.

**Four headline boxes:**

- **Estimated energy-yield loss** – the total for all selected turbines, in MWh and kWh. This is the number for your claim.
- **Indicative range** – a realistic low and high value, based on how large the model's errors were in the past.
- **Outage duration** – hours analysed, with start and end.
- **Equivalent full-load** – the loss as a share of what the turbines could produce running at full power the whole time. A quick sanity check: low wind gives a low percentage.

**Totals table.** One row per turbine plus a TOTAL row: energy, low/high range (P10/P90), average predicted wind speed, and how many 10-minute intervals were reconstructed (ideally all of them).

**Wind speed chart.** Pick a turbine; the slider sets how many days around the outage are shown.

- Blue: wind measured at the turbine before and after the outage.
- Orange: wind reconstructed by the tool during the outage.
- Light orange band: the likely range around the reconstruction.
- Green: average wind measured at the reference turbines.

If the orange line joins the blue line smoothly at both ends, the reconstruction is plausible.

**Power curve chart.** The grey line is the power curve. Each orange dot is one reconstructed 10-minute interval, showing where on the curve the turbine would have run.

**Expected power during the outage.** Power over time in kW, as it would have been fed in.

**Lost energy over time.** Bars per day or per hour (switch with *Resolution*), stacked by turbine, and a line showing the cumulative loss. Useful to show *when* most energy was lost.

**10-minute results.** The full table of reconstructed values with a download button. The *flags* column marks intervals that need attention, e.g. where reference data had to be gap-filled.

**How the energy is calculated, and assumptions** (fold-out) – the formula and the assumptions to quote in a claim.

## Tab ⑤ Validation: prove the method works

The real outage has no measurements to compare against. So this tab runs a **back-test**: it hides a period where the true wind *is* known, lets the tool predict it with exactly the same procedure, and compares.

**How to use it:**

1. Check the period. By default it is the data's marked test period (4–9 Sep in the demo data). Otherwise it is the 3 days just before the outage. Any period with real measurements works.
2. Click **▶ Run back-test** (about 20 seconds per turbine).

**What you get:**

- **Five headline boxes** for all turbines together: wind RMSE and MAE (m/s), power RMSE and MAE (kW), and the summed energy deviation (%).
- **A table per turbine** with the same numbers, plus whether the true energy fell inside the predicted range.
- **A wind chart**: blue = what was really measured (hidden from the tool), orange = what the tool predicted, light band = predicted range. The caption says what share of real values fell inside the band (about 80% is the aim).
- **Three small charts**: predicted vs. true power, error by wind-speed range, and energy predicted vs. energy from the real wind.

**How to read the numbers (demo data, 4–9 Sep):**

| Measure | Result | Plain meaning |
| --- | --- | --- |
| Wind RMSE | 1.34 m/s | Typical miss for a single 10-minute value |
| Wind MAE | 1.01 m/s | Average miss for a single 10-minute value |
| Power RMSE / MAE | 849 / 583 kW | Same, after converting to power |
| Summed energy deviation | +2.9% | Over the whole period the total energy was 2.9% too high |

Single 10-minute values can be off by more than 1 m/s, but the errors largely cancel out over days. The energy total, which is what matters for a claim, is much more accurate than any single value.

Power is compared through the power curve, because the data contains no measured electrical output.

## Tab ⑥ Report & export: take the results with you

Everything you need to document or submit the result.

**Downloads:**

| Button | File | Use it for |
| --- | --- | --- |
| Predictions, power & energy (CSV) | `outage_predictions.csv` | The 10-minute data behind the number; opens in Excel |
| Model comparison & validation metrics (CSV) | `model_metrics.csv` | Accuracy evidence for auditors or judges |
| Engineering report (Markdown) | `engineering_report.md` | A complete written summary: outage, method, result, uncertainty, assumptions |

Run the back-test in tab ⑤ first if you want its results included in the report and the metrics file. **Preview engineering report** shows the report right in the app.

**Insurance notification e-mail:**

1. Fill in the wind farm name, the recipient's salutation and your name or company.
2. The subject and body are written automatically: outage period, turbines, estimated loss, range and a short method description.
3. Edit the body freely in the text box.
4. Click **✉ Open in my e-mail program** to open a new draft in your mail app, or **⬇ Download e-mail text** to save it.

Nothing is sent automatically. Attach the report and the predictions CSV before you send it.

## Use cases: step-by-step recipes

### 1. File an insurance claim for a communication outage

1. Sidebar: **Upload my files**. Add the time series of the affected park and at least one neighbouring park, plus the affected turbines' power curves.
2. Tab ①: check that the affected turbines are selected as targets and the neighbouring park as references.
3. Tab ②: compare the detected outage with your alarm log and correct the start/end. Click **Run analysis**.
4. Tab ⑤: run the back-test on a few normal days to show the method's accuracy.
5. Tab ⑥: fill in the e-mail fields, open the e-mail, and attach the engineering report and predictions CSV.

### 2. Estimate lost production for a single turbine

In tab ①, select only that turbine as target and run as usual. The result in tab ④ is for that turbine alone.

### 3. Check a number someone else calculated

Run the same outage period, then compare their figure with the **Estimated energy-yield loss** and the **Indicative range** in tab ④. A figure far outside the range deserves a closer look.

### 4. Decide which neighbouring park to rely on

Run the analysis once with all references, then again with **Let the tool pick the best subset of references automatically** ticked. Tab ③ shows which references were chosen and how much each improved accuracy.

### 5. Test the tool before trusting it (hackathon or audit)

Use **Demo data**, run tab ②, then run the back-test in tab ⑤. Download the metrics CSV from tab ⑥ as evidence.

### 6. Explore "what if" questions

In tab ② under *Advanced analysis settings* you can, for example:

- use data from after the outage as well (often available for claims filed later),
- force wind direction or temperature in as inputs,
- treat wind above the curve's end as shutdown for a conservative estimate.

Run again and compare the totals in tab ④.

## Preparing your own files

The tool accepts CSV (comma, semicolon or tab separated) and Excel files.

**Wind data – one file per turbine, or one combined file.**

| Column | Required? | Example |
| --- | --- | --- |
| timestamp | Yes | `2026-09-01 10:20` or `01.09.2026 10:20` |
| wind_speed (m/s) | Yes | `6.42` |
| turbine_name | Only in a combined file | `T1` |
| wind_direction (°), ambient_temperature (°C), air_pressure (hPa), wind_speed_stddev (m/s), test_set | Optional | – |

- If there is no turbine column, the name comes from the file name: `H3_data.csv` becomes turbine H3.
- Name turbines as **park letters + number** (T1, H3, WF12). The tool then knows which park each belongs to and only offers other parks as references.
- Leave missing values empty. Never write 0 for a missing value.
- Include at least a few weeks of history before the outage. More history usually means better results; the minimum is one day.

**Power curves – one file per affected turbine.**

| Column | Example |
| --- | --- |
| wind_speed (m/s) | `0.5, 1.0, 1.5 … 26` |
| power | `0 … 4500` |

Name the file after the turbine (e.g. `T1_power_curve.csv`) or include a turbine_name column. Set the matching unit (kW, MW or W) in the sidebar.

Column names don't have to match exactly; common variants like *Wind Speed [m/s]* or *Time* are recognised. If one isn't, open **Column mapping** in tab ① and choose it by hand.

## Glossary

| Term | Meaning |
| --- | --- |
| Target turbine | The affected turbine whose data is missing |
| Reference turbine | A turbine in another wind park whose wind data fills the gap |
| Outage | The period whose wind speeds are reconstructed |
| Power curve | The manufacturer's table of power output per wind speed |
| RMSE | Typical prediction error; large misses count extra |
| MAE | Average size of the prediction error |
| Bias | Average over- (+) or under- (−) prediction |
| R² | Share of the wind's ups and downs the model explains (1 = perfect) |
| P10 / P90, 80% band | Likely low and high values: in about 8 of 10 cases the truth lies between them |
| Back-test | Hiding known data and predicting it, to measure accuracy honestly |
| Ridge Regression | A weighted sum of the reference winds, kept stable when references move together |
| Cross-validation (CV) | Testing on several past periods the model did not learn from |

## FAQ and troubleshooting

**The run button is greyed out.** A target has no power curve, no reference is selected, or the outage end is before the start. Tab ① shows a red message saying which.

**"Only N usable training intervals".** There is too little history before the outage. Upload a longer period, or under *Advanced analysis settings* choose "All measured data outside the outage".

**The yellow box says results belong to the previous run.** You changed a setting after running. Press **Confirm outage and run analysis** again.

**Some intervals are "unpredictable".** No reference turbine had data at those times. They are flagged and excluded from the total; choose additional references if possible.

**Why is the loss so low?** The wind was probably light. Check the *Equivalent full-load* box and the wind chart in tab ④.

**Does a missing measurement mean the turbine stopped?** Not necessarily. The tool estimates what the turbine *would have* produced running normally. Whether it actually stopped must come from operational records.

**How accurate is it?** On the demo data, the total energy over six test days was within about 3% for all turbines together. For individual turbines it ranged from −5% to +18%. Always run the back-test on your own data.

**Is my data sent anywhere?** No. The tool runs entirely on your computer; an internet connection is only needed once for installation.
