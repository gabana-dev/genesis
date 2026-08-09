# 0006 — RDB-1: does the imported machinery survive real, untuned data? (Real-Data Bridge)

**Date:** 2026-08-08 (baselines, rolling arm) / 2026-08-09 (expanding arm, paired analysis)
**Classification: IMPORT + BUILD — engineering validation. Not research. No novelty claimed.**
Contract: [`../../rdb/README.md`](../../rdb/README.md). Code: [`../../rdb/`](../../rdb/).
Check: [`../../tests/test_rdb_series.py`](../../tests/test_rdb_series.py).
Analysis: [`../../rdb/report.py`](../../rdb/report.py).

The first Genesis milestone whose environment was **not authored by Genesis**. Follows the
closure of the toy-milestone sequence at M2
([`0005`](0005-sparse-observation-decision-relevance.md)) and the draft decision
[`../decisions/0002-close-the-genesis-research-program.md`](../decisions/0002-close-the-genesis-research-program.md).

---

## 1. The question

> Does the imported state-estimation and adaptation machinery survive contact with a real,
> untuned sequential dataset, under an evaluation protocol that transfers directly to market
> data?

A negative answer was pre-committed as a valid outcome, not to be rescued.

Nothing here tests a Genesis idea. Every modelling component is established science
(Kalman 1960; Harvey 1989; Durbin & Koopman 2012), and **no Genesis code was reused** — the
`src/` implementations are discrete-state and 1-bit, and nothing transfers. What transfers is
the experimental discipline.

## 2. Protocol (frozen in the contract before the runs)

| | |
|---|---|
| Data | AEMO NEM public price & demand, region NSW1. *Source: AEMO.* |
| Target | `TOTALDEMAND`, 30-minute canonical series |
| Series | 140,256 observations, 2015-01-01 00:30 → 2023-01-01 00:00 |
| Horizon | 48 steps (24 hours) |
| Origins | 729, daily, 2021-01-01 → 2022-12-30 |
| Baselines | seasonal-naive (the serious one), persistence, calendar OLS |
| Model | one `statsmodels` `UnobservedComponents` spec: local level + trigonometric seasonals (period 48, 6 harmonics; period 336, 3 harmonics) |
| Refit | monthly parameter re-estimation, capped at 104 weeks; recursive filtering between refits |
| **Adaptation test** | **expanding window vs rolling 26 weeks — the training slice is the only difference** |
| Metrics | MAE, RMSE, skill vs seasonal-naive, 50/80/95% coverage, CRPS |
| Holdout | 2023-01 → 2026-06 — not downloaded, not readable, lock enforced in code |

Two data facts were established from the raw files rather than assumed: the native resolution
changes at the 5-minute settlement go-live (2021-10, inside the development period, aggregated
6:1 thereafter), and NEM market time does not observe DST. Timestamps are interval-**ending**;
treating them as interval-starting would leak 30 minutes of future into every forecast.

## 3. Provenance of the analysis — what was fixed when

Recorded so the inference cannot be read as tighter than it is:

- **Fixed before any run:** the contract in §2 — target, horizon, origins, specification, refit
  schedule, baselines, metrics, the two arms, and the holdout lock.
- **Added after the rolling arm, before the expanding arm:** the `expanding_only` /
  `rolling_only` entry points and `load_saved()` in `run.py`. Convenience only; no contract
  constant was touched, and the expanding arm ran the specification exactly as frozen.
- **Added after seeing the expanding point estimates:** the moving-block bootstrap in
  `report.py`. This is a **post-hoc choice of interval**, adopted because daily origins share
  weather and regime and the iid interval therefore understates spread. It is the conservative
  direction — it widened every interval by roughly 60% — and it did not change any verdict.
  Both intervals are reported side by side rather than the favourable one alone.

## 4. Execution

Baselines and the rolling arm ran 2026-08-08; the expanding arm ran 2026-08-09 (24 monthly
refits, 127.3 minutes wall). Both arms cover all 729 origins with no failures.

---

# RESULTS

## A. Headline (729 origins)

| arm | MAE | RMSE | skill vs SN | cov50 | cov80 | cov95 | CRPS |
|---|---|---|---|---|---|---|---|
| persistence | 437.07 | 544.24 | +0.201 | — | — | — | — |
| seasonal-naive | 547.04 | 676.30 | 0.000 | — | — | — | — |
| calendar OLS | 828.49 | 940.62 | −0.514 | — | — | — | — |
| state-space, **expanding** | 522.69 | 637.51 | +0.045 | 0.578 | 0.812 | 0.923 | 386.53 |
| state-space, **rolling** | **421.11** | **528.83** | **+0.230** | 0.590 | 0.813 | 0.919 | **316.05** |

## B. PRIMARY — the adaptation test

Paired per-origin difference, expanding minus rolling. Positive favours rolling. The
block-bootstrap interval (14-day moving blocks) is the interval of record.

| metric | mean diff | boot 95% | iid 95% | rolling wins |
|---|---|---|---|---|
| MAE | **+101.59** | [+65.20, +141.72] | [+81.87, +121.31] | 57.5% |
| RMSE | +108.67 | [+69.19, +152.15] | [+86.82, +130.53] | 57.8% |
| CRPS | +70.48 | [+45.26, +98.61] | [+56.62, +84.35] | 61.2% |

**Adaptation matters, and the effect is large.** All three intervals exclude zero under the
conservative interval. Discarding history is worth ~24% of MAE.

Note the shape: rolling wins 57.5% of origins but by an average of 101 MAE. The advantage is
not uniform — it is concentrated in the origins where expanding fails badly.

## C. Each arm against the trivial baselines

Negative favours the state-space arm.

| comparison | mean diff | boot 95% | verdict |
|---|---|---|---|
| rolling vs seasonal-naive | −125.94 | [−179.41, −75.80] | **beats it** |
| rolling vs persistence | −15.96 | [−49.32, +19.51] | **indistinguishable** |
| expanding vs seasonal-naive | −24.35 | [−72.10, +20.15] | **indistinguishable** |
| expanding vs persistence | +85.63 | [+39.30, +134.60] | **worse than it** |

Stated plainly: **the imported machinery, in its best configuration, is not reliably better
than "yesterday at this clock time."** It clearly beats last week's profile. It does not
clearly beat yesterday. In its worse configuration it fails to beat last week's profile at all,
and is beaten by yesterday.

## D. Stability — the gap is not an artifact of one period

Mean expanding-minus-rolling MAE:

| by year | | by season | |
|---|---|---|---|
| 2021 | +83.98 | autumn | +37.99 |
| 2022 | +119.25 | winter | +66.86 |
| | | spring | +102.69 |
| | | **summer** | **+201.55** |

The sign never reverses in any year or season. The gap is largest in summer — the
operationally hard season — and grew year on year.

Per-arm MAE: expanding 563.2 (2021) → 482.0 (2022); rolling 479.3 → 362.8. Summer: expanding
660.3, rolling 458.8.

## E. Slice and specification are separable

The training slice moved accuracy by ~24% and moved calibration essentially not at all:

| | cov50 | cov80 | cov95 |
|---|---|---|---|
| nominal | 0.50 | 0.80 | 0.95 |
| expanding | 0.578 | 0.812 | 0.923 |
| rolling | 0.590 | 0.813 | 0.919 |

**The slice governs accuracy; the specification governs calibration.** Both arms share one
miscalibration signature: intervals too *wide* in the middle (0.58–0.59 against 0.50 nominal)
and too *narrow* in the tails (0.92 against 0.95). That is the standard fat-tail signature of a
Gaussian predictive distribution — observed here on a smooth, doubly-seasonal, well-behaved
demand series.

---

## Verdict

**The machinery survives contact with real, untuned data — conditionally.**

1. **The pipeline is sound.** Ingestion, snapshotting, resolution-transition handling,
   interval-ending validation, rolling-origin evaluation, calibration and CRPS all ran over
   eight years of real data across a mid-period resolution change, with the holdout unreachable.
   This is the durable artifact.
2. **The adaptation test returns a clear positive for the rolling window** — large, stable
   across years and seasons, and robust to the conservative interval.
3. **The model's advantage over trivial baselines is not established.** Rolling versus
   persistence straddles zero. A 105k-observation Kalman filter performs like a one-line
   benchmark unless the slice is right, and even then it only ties the better of the two
   trivial baselines.
4. **Adaptation is what makes the imported machinery worth anything on this series.** That is
   the result, and it is a result about the training regime, not about the model.

No novelty is claimed. Everything above is established method applied to public data.

## What limitation this exposes

Stated as observation, not as a plan. The next step is chosen by the researcher from the
evidence, not from a sequence fixed in advance.

- **The target is too easy to discriminate the machinery.** Demand is smooth and doubly
  seasonal; persistence is already near the achievable frontier at a 24-hour horizon, which is
  why a correctly-configured state-space model cannot separate from it. The evaluation is a
  fair *validation* of the machinery and a weak *test* of it.
- **Miscalibration is present on the easy case**, and it is a property of the specification,
  which no choice of training slice repairs.
- **Nothing consumes the forecast.** There is no cost, no decision, and no consequence attached
  to being wrong — the exact condition [`0005`](0005-sparse-observation-decision-relevance.md)
  §E identified as making usefulness undemonstrable. RDB-1 measures forecast quality, not
  decision quality.
- **The holdout remains unopened**, so nothing here is an out-of-sample claim. All of it is
  development-period evidence.

## Source

Contract and licence: [`../../rdb/README.md`](../../rdb/README.md). Preceding closure:
[`../decisions/0002-close-the-genesis-research-program.md`](../decisions/0002-close-the-genesis-research-program.md).
Preceding result on costless environments:
[`0005`](0005-sparse-observation-decision-relevance.md) §E. Environment distinction:
[`../journal/2026-08-09-real-data-is-not-a-simulator.md`](../journal/2026-08-09-real-data-is-not-a-simulator.md).
Prior-art classification: [`../prior-art-and-opportunity-map.md`](../prior-art-and-opportunity-map.md).
