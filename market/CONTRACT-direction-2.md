# DIR-2 — does direction become predictable in identified states?

**Status: FROZEN 2026-08-19, before any predictive figure has been computed.** No gate,
feature, horizon, model class, threshold, prediction or kill condition below may be changed
after this point. If a defect is found it is reported and recorded, not silently repaired.

**Classification: IMPORT + BUILD. No novelty claimed.**

---

## 1. What DIR-1 did not test

[`../research/dir-1-result.md`](../research/dir-1-result.md) closed unconditional directional
prediction: twelve cells, none clearing its bar, best at 0.5111 against 0.5281.

**DIR-1 predicted at every decision point — always in, 5,940 predictions per cell.** That
demands the market be predictable *all the time*. A strategy that acts only in identified
states is a structurally different hypothesis and DIR-1 says nothing about it.

> **DIR-2 asks: conditional on an observable state of flow or positioning, does direction
> become predictable at 1 or 3 days?**

**The bar does not move.** 52.8% at 1 day, 51.5% at 3 days (φ = 0.5), imported from MEASURE-1
and unchanged. Trading less often does not lower a per-trade break-even — the cost per round
trip is identical. This sentence exists so nobody quietly relaxes the threshold on the grounds
of selectivity.

## 2. The information is new; that is the point

DIR-1's features were five price-derived quantities plus funding. Funding was its only
non-price feature and it scored 0.5032. DIR-2 introduces a class Genesis has never tested:
**who is positioned how, and which side is aggressing.**

## 3. Data

`~/genesis-evidence/metrics/` — Binance's published USD-M futures metrics for BTCUSDT,
**2,177 daily files, 2020-09-01 → 2026-08-17**, at 5-minute resolution. Consolidated to
`metrics-consolidated.npy`, 701,594 rows × 7 columns, SHA-256
`30b98a961a461adc9478cd62b7ee75ba60e8d9ee69c3592fe75d9d281af06db0`.

Joined to the price series and forward labels from DIR-1, on the same 8-hourly decision grid.

### 3.1 Coverage, audited before this contract was written

| field | coverage | note |
|---|---|---|
| `sum_open_interest` | 100.0% | |
| `sum_open_interest_value` | 100.0% | |
| `sum_taker_long_short_vol_ratio` | 94.7% | **2022 only 65.0%** |
| `count_long_short_ratio` | 99.2% | |
| `count_toptrader_long_short_ratio` | 86.9% | |
| `sum_toptrader_long_short_ratio` | 86.9% | |

Median row spacing 300 s; 300 gaps longer than that; largest gap 10.5 h.

**The 2022 hole is declared as a limitation, not worked around.** 2022 is the bear market in
this sample, and the taker ratio — the single most important field here — is missing for 35% of
it. Any result is therefore weighted toward bull and chop regimes. Missing values are **dropped
and counted, never interpolated.**

### 3.2 What this data is not

`sum_taker_long_short_vol_ratio` is a **5-minute ratio of taker buy to taker sell volume.** It
is **not VPIN**, which is a volume-bucketed probability of informed trading, and no result may
describe it as VPIN or as "order flow toxicity". It is order-flow *imbalance*, which is a
weaker and different quantity.

The `toptrader` fields use **Binance's own undisclosed classification** of which accounts are
"top". Genesis cannot audit that definition, cannot verify it is stable over six years, and
does not know if it changed. Results resting on those two fields carry that caveat explicitly.

## 4. The gates — the conditioning states, fixed in advance

Each gate is computed from a trailing 30-day window ending at the decision timestamp. A
decision point passes a gate or it does not; **no gate is tuned, and no gate threshold may be
moved.** All use |z| > 2.0, chosen once, before any result, and applied uniformly.

| | Gate | State it identifies |
|---|---|---|
| **G1** | \|z(taker ratio)\| > 2 | aggressive flow is one-sided to an unusual degree |
| **G2** | z(24h change in open interest) > 2 | leverage is being added rapidly |
| **G3** | \|z(top-trader long/short, size-weighted)\| > 2 | large accounts are unusually positioned |
| **G4** | \|z(all-account long/short)\| > 2 | the crowd is unusually positioned |
| **G5** | **no gate** | the unconditional control, on the new features |

G5 is not filler. **Without it, a positive gated result cannot be attributed to the gate rather
than to the new features**, and that distinction is the entire question.

## 5. Features

The same feature vector in every cell, so the gate is the only thing that varies:

`z(taker ratio)`, `z(open interest)`, `z(24h ΔOI)`, `z(top-trader L/S)`, `z(all-account L/S)`

All standardised on a trailing 30-day window ending at the decision timestamp — never
full-sample, which is the silent leak DIR-1's harness checks were built to exclude.

**Family DIR-2 = 5 gates × 2 horizons = 10 declared trials.** Fixed by this table, unable to
grow.

## 6. Method

Identical to DIR-1 except for the gate, and deliberately so — the two results must be
comparable.

- **Model: OLS on the forward return, prediction is the sign of the fit.** Linear only, for the
  reason DIR-1 gave: Pindza (2026) measured −10.94% out-of-sample R² from LightGBM against
  +1.23% from linear OLS. A non-linear model requires a separate declaration and may only be
  declared after a linear one clears the bar.
- **Purged walk-forward**, train 730 days, test 90 days, roll 90 days, embargo one full horizon
  in both directions.
- **The gate is applied to the test set only.** Training uses all points. Gating the training
  set as well would shrink it below usefulness and would change what is being tested — the
  question is whether the *state* selects predictable moments, not whether a model fitted only
  on rare states generalises.
- **Reported:** pooled out-of-sample accuracy, moving-block bootstrap 95% interval, and
  per-window accuracy as a series.

### 6.1 K3 is corrected here

DIR-1's K3 compared the best cell against the **mean** of the best-of-N distribution under zero
skill. Beating a mean is a coin flip, so it rejected only half of pure noise — recorded as
defect D-D1 in [`../research/dir-1-result.md`](../research/dir-1-result.md) §4.

**DIR-2 compares against the 95th percentile of the null maximum.** A best cell not exceeding
the p95 of best-of-10 coin flips at its own sample size is reported as **noise**.

## 7. Predictions, recorded before the data

- **E1.** G5 (unconditional, new features) fails to clear 52.8% at 1 day, reproducing DIR-1's
  finding with a different feature class.
- **E2.** At least one gate has materially higher accuracy than G5 at the same horizon. If no
  gate beats the control, conditioning adds nothing and the whole idea is wrong.
- **E3.** G1 (flow extreme) is the best gate, because aggressive one-sided flow is the only
  gate describing what is *happening* rather than what is *held*.
- **E4.** Gated cells have far fewer predictions and correspondingly wider intervals; at least
  one gate at 3 days fails K1 for insufficient predictions.
- **E5.** The sign of the G4 (crowd positioning) coefficient is **contrarian** — an unusually
  long crowd precedes negative returns.
- **E6.** No cell clears its bar with a 95% interval excluding it.

**I expect E6 to hold and DIR-2 to return negative.** Written down so a null is a scored
prediction rather than a disappointment. E2 and E3 are where I would be most interested to be
wrong.

## 8. Kill conditions

- **K1.** Fewer than 200 out-of-sample predictions in a cell reports **insufficient data**, is
  excluded from correction, and the exclusion is recorded. Gates are not widened to reach it.
- **K2.** If no cell exceeds its bar, **DIR-2 reports conditional directional prediction on
  flow and positioning as CLOSED.** It does not license new gates, new thresholds, new
  features, another model class or another symbol. Each needs a new declaration.
- **K3.** A best cell not exceeding the **p95** of the zero-skill best-of-10 at its own sample
  size is reported as **noise**, whatever its p-value. See §6.1.
- **K4.** If per-window accuracy standard deviation exceeds the cell's distance from 0.50, that
  cell may **not** be reported as tradeable, whatever its pooled accuracy. This fired in all
  twelve DIR-1 cells and is carried forward unchanged.
- **K5.** Any feature found to use information unavailable at its decision timestamp voids the
  entire run. Leakage is not repaired in place.
- **K6.** If a gate's passing points are concentrated such that more than 60% fall in a single
  calendar year, that cell is reported as **regime-bound** and not as a general finding.

## 9. Out of scope

No sizing, no leverage, no P&L, no live order, no agent, no non-linear model. DIR-2 answers
whether a linear function of five positioning and flow quantities, evaluated only in declared
states, beats a measured threshold out of sample.
