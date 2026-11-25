# Sample data (BayWa r.e. hackathon)

Files copied unchanged from the challenge package. The app's **Demo data** option loads them.

| File | Content |
|---|---|
| `T1_data.xlsx` … `T3_data.xlsx` | Target park T. Wind speed NaN for 1 Sep 00:00 – 3 Sep 23:50 (hidden test = the outage). |
| `H1_data.xlsx` … `H5_data.xlsx` | Reference park H (all variables measured). |
| `O1_data.xlsx`, `O2_data.xlsx` | Reference park O: 0.1 m/s resolution, **constant** air pressure (990.27, not measured), no wind std-dev. |
| `T1_power_curve.xlsx` … | 0.5–26 m/s, max 4500 (interpreted as kW), derated above 20 m/s. Identical for T1–T3. |

## Findings from inspection

- Columns: `turbine_name, timestamp, wind_speed, wind_direction, ambient_temperature, air_pressure, wind_speed_stddev, test_set`.
- 12,960 rows per file, 10-minute grid, 1 Jul – 30 Sep 2026. **3–4 Aug is absent from every file** (288 rows); the app re-inserts these as missing.
- No duplicate timestamps; all files chronologically ordered.
- `test_set = True` for 1–9 Sep (1,296 rows): 1–3 Sep hidden (NaN in T1–T3), 4–9 Sep observed ("shown test").
- Random isolated NaNs in all files (≈100–130 per turbine).
- Communication gaps: H1 13 Jul 23:40 – 15 Jul 01:50 (two blocks, 156 intervals), T1 7 Aug 15:50–20:40 (30 intervals).
- **Sensor-fault records** in T1 (3), T2 (2), T3 (4): wind speed, direction, temperature and std-dev all exactly 0. Treated as missing.
- Cross-park correlation of 10-min wind speed: 0.67–0.80 (T vs H/O); within-park 0.82–0.97.

## Uploading your own data

CSV (comma, semicolon or tab separated) or Excel. One file per turbine (turbine id taken from a column or the file
name, e.g. `H3_data.csv`) or one combined file with a turbine column. Required: timestamp + wind speed. Turbine names
like `T1`, `WF12` let the app enforce the "reference from another park" rule automatically; otherwise you confirm it.
Power curves: one file per target with wind speed and power columns (unit selectable: kW, MW, W).
