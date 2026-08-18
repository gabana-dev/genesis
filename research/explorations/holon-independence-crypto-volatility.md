# Two volatility holons, disjoint data, and still one opinion

**Date:** 2026-08-18
**Status:** exploration — **descriptive measurement, not a trial.** No hypothesis is tested and
nothing is accepted or rejected. Recorded as CONTEXT under the ledger's own definition.
**Classification: IMPORT + BUILD — engineering. No novelty claimed.**
Code: [`../../holons/`](../../holons/) · Checks:
[`../../tests/test_holon_cross_section.py`](../../tests/test_holon_cross_section.py) (10).

---

## 1. The question

The [`holons/`](../../holons/) layer rests on one claim: that an integrator which *measures*
whether its components are independent is worth more than one which assumes it. That claim was
supported only by a rigged case — two holons built from the same data, which measured ρ = 0.969
and were correctly refused.

A fair test needs two holons predicting the **same quantity** from **disjoint information**:

| holon | information |
|---|---|
| `volatility.py` | BTC's own realized volatility history, from 1-minute bars |
| `cross_section.py` | the daily realized volatility of **25 other perps**, from 4h bars — **BTC excluded** |

Identical target (BTC's next-day log realized volatility), identical model form (Corsi's HAR
shape), disjoint inputs. Holding the functional form fixed means any measured independence
comes from the data rather than from one holon having a richer model.

## 2. Data

25 Binance USD-M perpetuals, 2021-01-01 → 2026-07-31, **2,038 aligned days**, zero symbols
dropped. Target built from 3.9M BTCUSDT 1-minute bars. Days where fewer than 5 instruments
reported are dropped rather than averaged over the survivors; days missing more than a third of
their 4h bars are dropped rather than scaled up.

Walk-forward throughout, 1,766 out-of-sample predictions per holon, never refitting on the
future.

## 3. Result

| | OOS R² |
|---|---|
| own history | **+0.4426** |
| cross-section (no BTC data at all) | **+0.3052** |
| correlation between their predictions | **+0.7750** |
| **effective breadth** | **1.253** of a possible 2 |
| integrator verdict | **REFUSED** — below the 1.35 gate |

**Two things are true at once.** The rest of the market predicts BTC's volatility at R² = 0.31
having never seen a single BTC observation — that is real information, and more than nothing.
And it is **77.5% the same information** as BTC's own history.

## 4. What the refusal cost

The gate is a chosen number, so the refusal was measured rather than assumed:

| blend | OOS R² |
|---|---|
| 100% own | +0.4426 |
| 80% own / 20% cross | +0.4496 |
| **best possible blend (82% own)** | **+0.4497** |

**Maximum gain from combining: +0.0071 R².** And that is at the *in-sample optimal* weight —
an upper bound, achievable only in hindsight. A walk-forward weighting would capture less.

So the gate refused something worth at most 1.6% relative improvement, priced at a weight that
could not have been known in advance. **At this instance it is well calibrated.**

> One instance is not a calibration. The gate was set at 1.35 before this measurement and has
> **not** been changed after seeing it — moving a threshold to admit a result you have already
> seen is how thresholds stop meaning anything (`canon/operations.md` §2). This is recorded as
> evidence about the gate, not as a reason to move it.

## 5. What this says about the architecture

**Holons drawn from correlated markets will tend to collapse into one opinion.** Different
*instruments* is not the same as different *information*. Twenty-five instruments and 4h bars
bought 0.25 of a second opinion.

This is consistent with what the cross-section already said: PC1 takes 69% of variance and 33
perps carry ~2 independent bets. **The same common factor that makes crypto one directional bet
makes crypto volatility one volatility bet.**

The design consequence, for anything built on this layer: independence has to come from
genuinely different *kinds* of information — order flow, funding, execution state, external
events — not from more instruments. Adding a third and fourth price-series holon should be
expected to buy very little, and now there is a number attached to that expectation.

## 6. What this does not establish

- **One asset class, one target, one model form.** Whether holons over *different* quantities
  behave the same way is untested.
- **Nothing about tradeability.** No cost, no decision, no position. Under
  [DR0006](../decisions/0006-no-prediction-without-a-consumer.md) neither holon may be declared
  as a predictive trial without a named consumer, and neither has one.
- **The 4h/1m asymmetry is a confound.** Some of the 22.5% independence may be estimator
  coarseness rather than genuine cross-sectional information. Separating those was not
  attempted.
- **In-sample optimal weights are an upper bound**, used here only to bound what the refusal
  cost.
