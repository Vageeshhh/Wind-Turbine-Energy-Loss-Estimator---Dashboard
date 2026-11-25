# Validation results (training scope: outside_outage)

Generated 2026-11-23 21:36. All numbers below are produced by this script.

## T1  (references: H1, H2, H3, H4, H5, O1, O2; outage 2026-09-01 00:00 – 2026-09-03 23:50; 49s)

### Feature-group selection (Ridge, CV RMSE)

|   step | feature groups                                  |   CV RMSE (m/s) | decision                   |
|-------:|:------------------------------------------------|----------------:|:---------------------------|
|      0 | wind_speed                                      |          1.3322 | baseline                   |
|      1 | wind_speed + smoothed                           |          1.2910 | added                      |
|      1 | wind_speed + direction                          |          1.3079 | not best this round        |
|      1 | wind_speed + temperature                        |          1.3305 | not best this round        |
|      1 | wind_speed + pressure                           |          1.3428 | not best this round        |
|      1 | wind_speed + turbulence                         |          1.3334 | not best this round        |
|      2 | wind_speed + smoothed + direction               |          1.2717 | added                      |
|      2 | wind_speed + smoothed + temperature             |          1.2939 | not best this round        |
|      2 | wind_speed + smoothed + pressure                |          1.3033 | not best this round        |
|      2 | wind_speed + smoothed + turbulence              |          1.2981 | not best this round        |
|      3 | wind_speed + smoothed + direction + temperature |          1.2816 | not best this round        |
|      3 | wind_speed + smoothed + direction + pressure    |          1.2924 | not best this round        |
|      3 | wind_speed + smoothed + direction + turbulence  |          1.2775 | rejected (gain -0.5% < 1%) |

### Model comparison (rolling-origin CV, identical validation timestamps)

| model                    |   CV RMSE (m/s) |   CV MAE (m/s) |   CV R² |   RMSE std across folds |   worst-fold RMSE |   fit+predict time (s) | complexity   | selected   | reason                                                                       |
|:-------------------------|----------------:|---------------:|--------:|------------------------:|------------------:|-----------------------:|:-------------|:-----------|:-----------------------------------------------------------------------------|
| Ridge Regression         |          1.2717 |         0.9550 |  0.5913 |                  0.0922 |            1.3838 |                 0.0663 | low          | True       | Selected: lowest CV RMSE and simplest model.                                 |
| Linear Regression        |          1.2728 |         0.9559 |  0.5904 |                  0.0913 |            1.3840 |                 0.0755 | low          | False      | Not selected: equivalent accuracy (+0.1%), but a simpler model is preferred. |
| Random Forest            |          1.3062 |         0.9774 |  0.5558 |                  0.0096 |            1.3167 |                12.4904 | high         | False      | Not selected: +2.7% higher CV RMSE than the best model.                      |
| Gradient Boosting        |          1.3557 |         1.0194 |  0.5184 |                  0.0375 |            1.3957 |                 3.8248 | high         | False      | Not selected: +6.6% higher CV RMSE than the best model.                      |
| Mean (no-skill baseline) |          2.0526 |         1.6011 | -0.0440 |                  0.2451 |            2.3114 |                 0.0424 | trivial      | False      | Sanity baseline only (not eligible).                                         |

Selected: **Ridge Regression** — Selected: lowest CV RMSE and simplest model.

### Final holdout (2026-09-17 22:50 to 2026-09-30 23:50, scored after selection)

| model             |   RMSE (m/s) |   MAE (m/s) |   Bias (m/s) |     R² |    n | selected   |
|:------------------|-------------:|------------:|-------------:|-------:|-----:|:-----------|
| Linear Regression |       1.3050 |      0.9746 |      -0.2553 | 0.7216 | 1855 | False      |
| Ridge Regression  |       1.3045 |      0.9744 |      -0.2557 | 0.7218 | 1855 | True       |
| Random Forest     |       1.2755 |      0.9491 |      -0.2425 | 0.7340 | 1855 | False      |
| Gradient Boosting |       1.2707 |      0.9369 |      -0.2196 | 0.7360 | 1855 | False      |

### Back-test on shown test period 2026-09-04 00:00 – 2026-09-09 23:50

(full procedure re-run with these target values hidden; model chosen: Ridge Regression, features: wind_speed, smoothed, direction)

- Wind speed: RMSE 1.508 m/s, MAE 1.180 m/s, bias +0.467 m/s, R² 0.652
- Power (via power curve): RMSE 928 kW, MAE 654 kW
- Energy: predicted 248,617 kWh vs actual-wind 213,160 kWh → +16.63 %
- Actual energy inside empirical 80% band (245,181 – 276,675): False

### Hidden-outage estimate: 88,091 kWh (80% band 83,560 – 110,525)

## T2  (references: H1, H2, H3, H4, H5, O1, O2; outage 2026-09-01 00:00 – 2026-09-03 23:50; 35s)

### Feature-group selection (Ridge, CV RMSE)

|   step | feature groups                      |   CV RMSE (m/s) | decision                   |
|-------:|:------------------------------------|----------------:|:---------------------------|
|      0 | wind_speed                          |          1.1885 | baseline                   |
|      1 | wind_speed + smoothed               |          1.1534 | added                      |
|      1 | wind_speed + direction              |          1.1952 | not best this round        |
|      1 | wind_speed + temperature            |          1.1966 | not best this round        |
|      1 | wind_speed + pressure               |          1.1914 | not best this round        |
|      1 | wind_speed + turbulence             |          1.1811 | not best this round        |
|      2 | wind_speed + smoothed + direction   |          1.1566 | not best this round        |
|      2 | wind_speed + smoothed + temperature |          1.1569 | not best this round        |
|      2 | wind_speed + smoothed + pressure    |          1.1666 | not best this round        |
|      2 | wind_speed + smoothed + turbulence  |          1.1442 | rejected (gain +0.8% < 1%) |

### Model comparison (rolling-origin CV, identical validation timestamps)

| model                    |   CV RMSE (m/s) |   CV MAE (m/s) |   CV R² |   RMSE std across folds |   worst-fold RMSE |   fit+predict time (s) | complexity   | selected   | reason                                                                       |
|:-------------------------|----------------:|---------------:|--------:|------------------------:|------------------:|-----------------------:|:-------------|:-----------|:-----------------------------------------------------------------------------|
| Ridge Regression         |          1.1534 |         0.8704 |  0.6809 |                  0.0615 |            1.2015 |                 0.0426 | low          | True       | Selected: lowest CV RMSE and simplest model.                                 |
| Linear Regression        |          1.1544 |         0.8711 |  0.6802 |                  0.0622 |            1.2035 |                 0.0477 | low          | False      | Not selected: equivalent accuracy (+0.1%), but a simpler model is preferred. |
| Random Forest            |          1.1933 |         0.8981 |  0.6629 |                  0.0468 |            1.2551 |                 8.6866 | high         | False      | Not selected: +3.5% higher CV RMSE than the best model.                      |
| Gradient Boosting        |          1.2431 |         0.9369 |  0.6336 |                  0.0375 |            1.2861 |                 3.1080 | high         | False      | Not selected: +7.8% higher CV RMSE than the best model.                      |
| Mean (no-skill baseline) |          2.1814 |         1.7378 | -0.0731 |                  0.2764 |            2.6203 |                 0.0271 | trivial      | False      | Sanity baseline only (not eligible).                                         |

Selected: **Ridge Regression** — Selected: lowest CV RMSE and simplest model.

### Final holdout (2026-09-18 00:00 to 2026-09-30 23:50, scored after selection)

| model             |   RMSE (m/s) |   MAE (m/s) |   Bias (m/s) |     R² |    n | selected   |
|:------------------|-------------:|------------:|-------------:|-------:|-----:|:-----------|
| Linear Regression |       1.0421 |      0.8187 |      -0.0553 | 0.8248 | 1862 | False      |
| Ridge Regression  |       1.0419 |      0.8185 |      -0.0554 | 0.8248 | 1862 | True       |
| Random Forest     |       1.0721 |      0.8456 |      -0.1164 | 0.8146 | 1862 | False      |
| Gradient Boosting |       1.1007 |      0.8628 |      -0.1416 | 0.8045 | 1862 | False      |

### Back-test on shown test period 2026-09-04 00:00 – 2026-09-09 23:50

(full procedure re-run with these target values hidden; model chosen: Ridge Regression, features: wind_speed, smoothed)

- Wind speed: RMSE 1.165 m/s, MAE 0.870 m/s, bias +0.005 m/s, R² 0.813
- Power (via power curve): RMSE 744 kW, MAE 498 kW
- Energy: predicted 310,908 kWh vs actual-wind 312,231 kWh → -0.42 %
- Actual energy inside empirical 80% band (298,425 – 329,326): True

### Hidden-outage estimate: 120,961 kWh (80% band 115,186 – 138,742)

## T3  (references: H1, H2, H3, H4, H5, O1, O2; outage 2026-09-01 00:00 – 2026-09-03 23:50; 35s)

### Feature-group selection (Ridge, CV RMSE)

|   step | feature groups                      |   CV RMSE (m/s) | decision                   |
|-------:|:------------------------------------|----------------:|:---------------------------|
|      0 | wind_speed                          |          1.1606 | baseline                   |
|      1 | wind_speed + smoothed               |          1.1164 | added                      |
|      1 | wind_speed + direction              |          1.1675 | not best this round        |
|      1 | wind_speed + temperature            |          1.1620 | not best this round        |
|      1 | wind_speed + pressure               |          1.1623 | not best this round        |
|      1 | wind_speed + turbulence             |          1.1575 | not best this round        |
|      2 | wind_speed + smoothed + direction   |          1.1248 | not best this round        |
|      2 | wind_speed + smoothed + temperature |          1.1183 | not best this round        |
|      2 | wind_speed + smoothed + pressure    |          1.1201 | not best this round        |
|      2 | wind_speed + smoothed + turbulence  |          1.1169 | rejected (gain -0.0% < 1%) |

### Model comparison (rolling-origin CV, identical validation timestamps)

| model                    |   CV RMSE (m/s) |   CV MAE (m/s) |   CV R² |   RMSE std across folds |   worst-fold RMSE |   fit+predict time (s) | complexity   | selected   | reason                                                                       |
|:-------------------------|----------------:|---------------:|--------:|------------------------:|------------------:|-----------------------:|:-------------|:-----------|:-----------------------------------------------------------------------------|
| Ridge Regression         |          1.1164 |         0.8386 |  0.6432 |                  0.0269 |            1.1538 |                 0.0408 | low          | True       | Selected: lowest CV RMSE and simplest model.                                 |
| Linear Regression        |          1.1174 |         0.8393 |  0.6425 |                  0.0272 |            1.1544 |                 0.0454 | low          | False      | Not selected: equivalent accuracy (+0.1%), but a simpler model is preferred. |
| Random Forest            |          1.1794 |         0.8807 |  0.6008 |                  0.0438 |            1.2313 |                 8.6842 | high         | False      | Not selected: +5.6% higher CV RMSE than the best model.                      |
| Gradient Boosting        |          1.2189 |         0.9128 |  0.5696 |                  0.0599 |            1.2999 |                 3.0392 | high         | False      | Not selected: +9.2% higher CV RMSE than the best model.                      |
| Mean (no-skill baseline) |          1.9984 |         1.5746 | -0.0931 |                  0.2869 |            2.4587 |                 0.0285 | trivial      | False      | Sanity baseline only (not eligible).                                         |

Selected: **Ridge Regression** — Selected: lowest CV RMSE and simplest model.

### Final holdout (2026-09-17 21:40 to 2026-09-30 23:50, scored after selection)

| model             |   RMSE (m/s) |   MAE (m/s) |   Bias (m/s) |     R² |    n | selected   |
|:------------------|-------------:|------------:|-------------:|-------:|-----:|:-----------|
| Linear Regression |       1.0999 |      0.8783 |       0.0179 | 0.7775 | 1862 | False      |
| Ridge Regression  |       1.0998 |      0.8782 |       0.0175 | 0.7775 | 1862 | True       |
| Random Forest     |       1.1616 |      0.9188 |      -0.1015 | 0.7518 | 1862 | False      |
| Gradient Boosting |       1.1962 |      0.9449 |      -0.1215 | 0.7368 | 1862 | False      |

### Back-test on shown test period 2026-09-04 00:00 – 2026-09-09 23:50

(full procedure re-run with these target values hidden; model chosen: Ridge Regression, features: wind_speed, smoothed)

- Wind speed: RMSE 1.272 m/s, MAE 0.971 m/s, bias -0.059 m/s, R² 0.740
- Power (via power curve): RMSE 828 kW, MAE 585 kW
- Energy: predicted 263,520 kWh vs actual-wind 271,666 kWh → -3.00 %
- Actual energy inside empirical 80% band (251,471 – 281,787): True

### Hidden-outage estimate: 95,517 kWh (80% band 88,539 – 111,212)

## All target turbines combined (back-test)

- Wind RMSE 1.323 m/s, MAE 1.007 m/s
- Power RMSE 837 kW, MAE 579 kW
- Summed energy deviation +3.26 % (+25,988 kWh)

## Hidden outage, all turbines: 304,569 kWh