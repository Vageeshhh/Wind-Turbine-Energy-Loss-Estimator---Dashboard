# Validation results (training scope: before_outage)

Generated 2026-11-23 21:34. All numbers below are produced by this script.

## T1  (references: H1, H2, H3, H4, H5, O1, O2; outage 2026-09-01 00:00 – 2026-09-03 23:50; 53s)

### Feature-group selection (Ridge, CV RMSE)

|   step | feature groups                      |   CV RMSE (m/s) | decision                   |
|-------:|:------------------------------------|----------------:|:---------------------------|
|      0 | wind_speed                          |          1.3043 | baseline                   |
|      1 | wind_speed + smoothed               |          1.2676 | added                      |
|      1 | wind_speed + direction              |          1.3315 | not best this round        |
|      1 | wind_speed + temperature            |          1.3059 | not best this round        |
|      1 | wind_speed + pressure               |          1.3023 | not best this round        |
|      1 | wind_speed + turbulence             |          1.3114 | not best this round        |
|      2 | wind_speed + smoothed + direction   |          1.2907 | not best this round        |
|      2 | wind_speed + smoothed + temperature |          1.2666 | rejected (gain +0.1% < 1%) |
|      2 | wind_speed + smoothed + pressure    |          1.2678 | not best this round        |
|      2 | wind_speed + smoothed + turbulence  |          1.2711 | not best this round        |

### Model comparison (rolling-origin CV, identical validation timestamps)

| model                    |   CV RMSE (m/s) |   CV MAE (m/s) |   CV R² |   RMSE std across folds |   worst-fold RMSE |   fit+predict time (s) | complexity   | selected   | reason                                                                       |
|:-------------------------|----------------:|---------------:|--------:|------------------------:|------------------:|-----------------------:|:-------------|:-----------|:-----------------------------------------------------------------------------|
| Ridge Regression         |          1.2676 |         0.9369 |  0.5354 |                  0.1335 |            1.4805 |                 0.0341 | low          | True       | Selected: lowest CV RMSE and simplest model.                                 |
| Linear Regression        |          1.2682 |         0.9379 |  0.5349 |                  0.1334 |            1.4805 |                 0.0388 | low          | False      | Not selected: equivalent accuracy (+0.0%), but a simpler model is preferred. |
| Random Forest            |          1.3432 |         0.9899 |  0.4768 |                  0.1413 |            1.5486 |                 8.4481 | high         | False      | Not selected: +6.0% higher CV RMSE than the best model.                      |
| Gradient Boosting        |          1.3780 |         1.0289 |  0.4496 |                  0.1353 |            1.5735 |                 9.9208 | high         | False      | Not selected: +8.7% higher CV RMSE than the best model.                      |
| Mean (no-skill baseline) |          1.9149 |         1.4870 | -0.0591 |                  0.0753 |            2.0248 |                 0.0246 | trivial      | False      | Sanity baseline only (not eligible).                                         |

Selected: **Ridge Regression** — Selected: lowest CV RMSE and simplest model.

### Final holdout (2026-08-23 01:00 to 2026-08-31 23:50, scored after selection)

| model             |   RMSE (m/s) |   MAE (m/s) |   Bias (m/s) |     R² |    n | selected   |
|:------------------|-------------:|------------:|-------------:|-------:|-----:|:-----------|
| Linear Regression |       1.5308 |      1.1763 |      -0.3471 | 0.4813 | 1277 | False      |
| Ridge Regression  |       1.5307 |      1.1763 |      -0.3469 | 0.4814 | 1277 | True       |
| Random Forest     |       1.5136 |      1.1782 |      -0.2620 | 0.4929 | 1277 | False      |
| Gradient Boosting |       1.5496 |      1.1906 |      -0.2110 | 0.4685 | 1277 | False      |

### Back-test on shown test period 2026-09-04 00:00 – 2026-09-09 23:50

(full procedure re-run with these target values hidden; model chosen: Ridge Regression, features: wind_speed, smoothed)

- Wind speed: RMSE 1.518 m/s, MAE 1.177 m/s, bias +0.497 m/s, R² 0.648
- Power (via power curve): RMSE 941 kW, MAE 653 kW
- Energy: predicted 251,514 kWh vs actual-wind 213,160 kWh → +17.99 %
- Actual energy inside empirical 80% band (244,988 – 275,975): False

### Hidden-outage estimate: 99,827 kWh (80% band 95,666 – 119,446)

## T2  (references: H1, H2, H3, H4, H5, O1, O2; outage 2026-09-01 00:00 – 2026-09-03 23:50; 58s)

### Feature-group selection (Ridge, CV RMSE)

|   step | feature groups                      |   CV RMSE (m/s) | decision                   |
|-------:|:------------------------------------|----------------:|:---------------------------|
|      0 | wind_speed                          |          1.2385 | baseline                   |
|      1 | wind_speed + smoothed               |          1.2124 | added                      |
|      1 | wind_speed + direction              |          1.2706 | not best this round        |
|      1 | wind_speed + temperature            |          1.2538 | not best this round        |
|      1 | wind_speed + pressure               |          1.2575 | not best this round        |
|      1 | wind_speed + turbulence             |          1.2342 | not best this round        |
|      2 | wind_speed + smoothed + direction   |          1.2255 | not best this round        |
|      2 | wind_speed + smoothed + temperature |          1.2272 | not best this round        |
|      2 | wind_speed + smoothed + pressure    |          1.2270 | not best this round        |
|      2 | wind_speed + smoothed + turbulence  |          1.2036 | rejected (gain +0.7% < 1%) |

### Model comparison (rolling-origin CV, identical validation timestamps)

| model                    |   CV RMSE (m/s) |   CV MAE (m/s) |   CV R² |   RMSE std across folds |   worst-fold RMSE |   fit+predict time (s) | complexity   | selected   | reason                                                                       |
|:-------------------------|----------------:|---------------:|--------:|------------------------:|------------------:|-----------------------:|:-------------|:-----------|:-----------------------------------------------------------------------------|
| Ridge Regression         |          1.2124 |         0.8865 |  0.6122 |                  0.1315 |            1.3953 |                 0.0315 | low          | True       | Selected: lowest CV RMSE and simplest model.                                 |
| Linear Regression        |          1.2132 |         0.8871 |  0.6118 |                  0.1317 |            1.3954 |                 0.0345 | low          | False      | Not selected: equivalent accuracy (+0.1%), but a simpler model is preferred. |
| Random Forest            |          1.2453 |         0.9040 |  0.5909 |                  0.1482 |            1.4624 |                 8.4315 | high         | False      | Not selected: +2.7% higher CV RMSE than the best model.                      |
| Gradient Boosting        |          1.2824 |         0.9438 |  0.5663 |                  0.1477 |            1.4825 |                10.1661 | high         | False      | Not selected: +5.8% higher CV RMSE than the best model.                      |
| Mean (no-skill baseline) |          2.0710 |         1.6582 | -0.1406 |                  0.1526 |            2.3156 |                 0.0198 | trivial      | False      | Sanity baseline only (not eligible).                                         |

Selected: **Ridge Regression** — Selected: lowest CV RMSE and simplest model.

### Final holdout (2026-08-23 00:10 to 2026-08-31 23:50, scored after selection)

| model             |   RMSE (m/s) |   MAE (m/s) |   Bias (m/s) |     R² |    n | selected   |
|:------------------|-------------:|------------:|-------------:|-------:|-----:|:-----------|
| Linear Regression |       1.2098 |      0.9498 |       0.0823 | 0.6273 | 1282 | False      |
| Ridge Regression  |       1.2098 |      0.9497 |       0.0822 | 0.6273 | 1282 | True       |
| Random Forest     |       1.3579 |      1.0425 |       0.0125 | 0.5305 | 1282 | False      |
| Gradient Boosting |       1.4045 |      1.0742 |       0.0047 | 0.4976 | 1282 | False      |

### Back-test on shown test period 2026-09-04 00:00 – 2026-09-09 23:50

(full procedure re-run with these target values hidden; model chosen: Ridge Regression, features: wind_speed, smoothed)

- Wind speed: RMSE 1.178 m/s, MAE 0.880 m/s, bias -0.014 m/s, R² 0.809
- Power (via power curve): RMSE 754 kW, MAE 504 kW
- Energy: predicted 309,790 kWh vs actual-wind 312,231 kWh → -0.78 %
- Actual energy inside empirical 80% band (297,058 – 329,255): True

### Hidden-outage estimate: 121,149 kWh (80% band 113,348 – 136,788)

## T3  (references: H1, H2, H3, H4, H5, O1, O2; outage 2026-09-01 00:00 – 2026-09-03 23:50; 28s)

### Feature-group selection (Ridge, CV RMSE)

|   step | feature groups                      |   CV RMSE (m/s) | decision                   |
|-------:|:------------------------------------|----------------:|:---------------------------|
|      0 | wind_speed                          |          1.1752 | baseline                   |
|      1 | wind_speed + smoothed               |          1.1534 | added                      |
|      1 | wind_speed + direction              |          1.2250 | not best this round        |
|      1 | wind_speed + temperature            |          1.1787 | not best this round        |
|      1 | wind_speed + pressure               |          1.1872 | not best this round        |
|      1 | wind_speed + turbulence             |          1.1763 | not best this round        |
|      2 | wind_speed + smoothed + direction   |          1.1828 | not best this round        |
|      2 | wind_speed + smoothed + temperature |          1.1577 | not best this round        |
|      2 | wind_speed + smoothed + pressure    |          1.1609 | not best this round        |
|      2 | wind_speed + smoothed + turbulence  |          1.1555 | rejected (gain -0.2% < 1%) |

### Model comparison (rolling-origin CV, identical validation timestamps)

| model                    |   CV RMSE (m/s) |   CV MAE (m/s) |   CV R² |   RMSE std across folds |   worst-fold RMSE |   fit+predict time (s) | complexity   | selected   | reason                                                                       |
|:-------------------------|----------------:|---------------:|--------:|------------------------:|------------------:|-----------------------:|:-------------|:-----------|:-----------------------------------------------------------------------------|
| Ridge Regression         |          1.1534 |         0.8351 |  0.5603 |                  0.1584 |            1.3993 |                 0.0328 | low          | True       | Selected: lowest CV RMSE and simplest model.                                 |
| Linear Regression        |          1.1541 |         0.8359 |  0.5598 |                  0.1589 |            1.4001 |                 0.0352 | low          | False      | Not selected: equivalent accuracy (+0.1%), but a simpler model is preferred. |
| Random Forest            |          1.1902 |         0.8582 |  0.5312 |                  0.1594 |            1.4066 |                 7.7820 | high         | False      | Not selected: +3.2% higher CV RMSE than the best model.                      |
| Gradient Boosting        |          1.2283 |         0.8962 |  0.5004 |                  0.1581 |            1.4404 |                 2.9154 | high         | False      | Not selected: +6.5% higher CV RMSE than the best model.                      |
| Mean (no-skill baseline) |          1.8423 |         1.4526 | -0.1378 |                  0.1654 |            2.0777 |                 0.0207 | trivial      | False      | Sanity baseline only (not eligible).                                         |

Selected: **Ridge Regression** — Selected: lowest CV RMSE and simplest model.

### Final holdout (2026-08-22 23:30 to 2026-08-31 23:50, scored after selection)

| model             |   RMSE (m/s) |   MAE (m/s) |   Bias (m/s) |     R² |    n | selected   |
|:------------------|-------------:|------------:|-------------:|-------:|-----:|:-----------|
| Linear Regression |       1.1958 |      0.9373 |      -0.0425 | 0.5968 | 1285 | False      |
| Ridge Regression  |       1.1959 |      0.9376 |      -0.0430 | 0.5967 | 1285 | True       |
| Random Forest     |       1.2312 |      0.9544 |      -0.0303 | 0.5725 | 1285 | False      |
| Gradient Boosting |       1.2783 |      0.9738 |      -0.0425 | 0.5392 | 1285 | False      |

### Back-test on shown test period 2026-09-04 00:00 – 2026-09-09 23:50

(full procedure re-run with these target values hidden; model chosen: Ridge Regression, features: wind_speed, smoothed)

- Wind speed: RMSE 1.290 m/s, MAE 0.984 m/s, bias -0.104 m/s, R² 0.732
- Power (via power curve): RMSE 843 kW, MAE 593 kW
- Energy: predicted 258,900 kWh vs actual-wind 271,666 kWh → -4.70 %
- Actual energy inside empirical 80% band (245,473 – 279,753): True

### Hidden-outage estimate: 95,549 kWh (80% band 87,734 – 111,168)

## All target turbines combined (back-test)

- Wind RMSE 1.336 m/s, MAE 1.013 m/s
- Power RMSE 849 kW, MAE 583 kW
- Summed energy deviation +2.90 % (+23,148 kWh)

## Hidden outage, all turbines: 316,525 kWh