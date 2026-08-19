# GEN-1 — does the DIR-2 specification generalise, or was it fitted to Bitcoin?

**Status: FROZEN 2026-08-19, before any non-BTC metrics file has been read.** No feature,
model, horizon, threshold, prediction or kill condition below may be changed after this point.
If a defect is found it is reported and recorded, not silently repaired.

**Classification: BUILD. No novelty claimed.**

---

## 1. Why this exists, and why it is first

Every contract Genesis has frozen is BTCUSDT. MEASURE-1 chose that instrument for data quality
and **eleven contracts inherited the choice without one of them examining it.**

Measured 2026-08-19, 1,000 daily bars per symbol, identical cost stack, netted execution:

| symbol | median 1d move | break-even | distance above a coin flip |
|---|---|---|---|
| **BTCUSDT** | 122.8 bps | 0.5028 | **0.283 pp** |
| BNBUSDT | 137.9 | 0.5025 | 0.252 pp |
| XRPUSDT | 167.6 | 0.5021 | 0.208 pp |
| ETHUSDT | 174.3 | 0.5020 | 0.200 pp |
| DOGEUSDT | 240.3 | 0.5014 | 0.145 pp |
| **SOLUSDT** | 243.5 | 0.5014 | **0.143 pp** |

**The bar on SOL is half BTC's.** Cost is fixed per trade; the prize scales with the move.
Genesis optimised for the cleanest data and thereby selected the hardest instrument available.

> **GEN-1 asks one question: run unchanged on five assets it has never seen, does the DIR-2
> specification behave as it did on BTC?**

## 2. What this is and is not

**It is not ECON-1.** ECON-1 asks whether the signal makes money **forward on BTC** and reads in
November. GEN-1 asks whether the **method** holds across instruments, and reads today. Neither
substitutes for the other and no result here may be reported as ECON-1's.

**Its value is asymmetric, and that is the point.** If the specification fails on all five,
BTC's forward result is very likely noise and ECON-1's November read is close to decided in
advance. If it holds on three or more, that is stronger evidence than a single asset can ever
produce, because five assets cannot be overfitted by one grid frozen before any of them was
touched.

**Prior art cuts against it.** Pindza (2026) found **no cross-asset transfer** in crypto
microstructure models, and Genesis's own cross-section holon measured effective breadth 1.03
across 25 instruments. GEN-1 is therefore expected to fail, and is run because a declared
expectation is not a measurement.

## 3. Data

Binance published USD-M futures metrics for **ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT** —
availability verified 2026-08-19, all returning HTTP 206 for 2026-08-15 — from 2020-08 to
2026-08-17. Same fields, same 5-minute resolution, same source as the BTC archive DIR-2 used.

Prices from 8-hourly USD-M klines per symbol.

**None of these files had been read when this contract was frozen.** The download was started
in parallel with writing it and no file was opened.

## 4. The specification — frozen, and identical to DIR-2

Nothing is refitted, retuned or reselected per asset. Changing anything voids the run (K5).

- **Features:** `taker_z, oi_z, doi_z, toptrader_z, crowd_z` — trailing 30-day z-scores.
- **Model:** OLS on the forward return; the prediction is the sign of the fit. Linear only, for
  DIR-2's reason: Pindza measured −10.94% out-of-sample R² from LightGBM against +1.23% linear.
- **Protocol:** purged walk-forward, train 730 days, test 90, roll 90, embargo one full horizon
  in both directions.
- **Horizons:** 1 day primary, 3 days secondary and non-substitutable.

**Family GEN-1 = 5 assets × 2 horizons = 10 declared trials.** Fixed by this section.
Benjamini–Hochberg at q = 0.05 with Bonferroni α = 0.05/10 = 0.005 reported alongside.

## 5. Endpoints

**Primary, per asset:** directional accuracy on pooled out-of-sample predictions, with a
moving-block bootstrap 95% interval, against **that asset's own break-even bar** computed from
its own measured median move and the shared cost stack. The bar differs per asset and is
computed from §1's method, not copied from BTC.

**Reported with every cell, non-substitutable:** net exposure (long fraction), per-window
accuracy as a series, and the number of out-of-sample predictions.

**Corrected headline.** Because the natural reading is "the best asset", the **expected best of
10 under zero skill** is computed at the median sample size and the observed best compared
against its **95th percentile** — the corrected form of DIR-1's defective K3.

## 6. Predictions

- **H1.** No asset clears its own bar with an interval excluding it. *(I expect this to hold.)*
- **H2.** Accuracy is positively correlated across assets — if BTC's features carry information
  they carry it everywhere, weakly. A near-zero cross-asset correlation would mean BTC's 0.5242
  was instrument-specific and therefore probably fitted.
- **H3.** Net exposure exceeds 0.60 long on every asset, as it did on BTC (0.7098), because the
  features are positioning measures on assets that all rose over the sample.
- **H4.** SOL and DOGE come closest to their bars, not because the signal is better there but
  because their bars are lowest.
- **H5.** At least one asset shows accuracy **below 0.50** out of sample. Five assets and a weak
  signal should produce one that points the wrong way, and if none does I would suspect the
  harness before celebrating.

## 7. Kill conditions

- **K1.** Fewer than 500 out-of-sample predictions for an asset: reported **insufficient**,
  excluded from correction, not merged.
- **K2.** If no asset clears its bar, **GEN-1 reports the specification as not generalising.**
  That is a result. It does not license refitting per asset, adding features, or extending the
  asset list — each needs a new declaration.
- **K3.** A best asset not exceeding the **p95** of the zero-skill best-of-10 is reported as
  **noise**, whatever its p-value.
- **K4.** Per-asset accuracy standard deviation across windows exceeding that asset's distance
  from 0.50 means the cell may **not** be called tradeable, whatever the pooled figure. This
  fired in every DIR-1 and DIR-2 cell and is carried forward unchanged.
- **K5.** Any per-asset change to features, model, windows or horizons voids the run.

## 8. Known limitations

**Metrics coverage varies by asset and is not yet known**, because no file had been read when
this was frozen. Whatever it turns out to be is reported per asset, and any asset with coverage
below 50% over its walk-forward window is reported as degraded.

**Shared cost stack.** The same fee and adverse-selection figures are applied to all five. Both
were measured on BTC. Alt-coin spreads are wider (which helps a passive taker of liquidity) and
their adverse selection is unmeasured. **The per-asset bars in §1 are therefore approximate**,
and an asset that clears its bar narrowly has not clearly cleared anything.

**Five assets, one venue, one model form.** No claim beyond them.

## 9. Out of scope

No sizing, no P&L, no live order, no per-asset tuning, no strategy. GEN-1 asks whether a frozen
specification survives contact with instruments it was not built on.
