# Crypto Cross-Section Breadth Study

**Date:** 2026-08-13
**Status:** **CLOSED.** A factual measurement, not a direction decision.
**Classification:** environment study under
[`decisions/0003-engineering-posture-real-data.md`](decisions/0003-engineering-posture-real-data.md).
Nothing was built, traded, backtested or paper-traded. No instrument, strategy or research
direction is selected here.
**Companion studies:** [`nem-battery-environment-study.md`](nem-battery-environment-study.md),
[`kalshi-mechanical-settlement-environment-study.md`](kalshi-mechanical-settlement-environment-study.md),
[`prospective-observability-study.md`](prospective-observability-study.md).
**Ledger:** recorded as CONTEXT, not a trial. No hypothesis is tested and nothing is accepted
or rejected.

---

## 1. Why the question was asked

[`experiments/0008-measure-1-cost-of-being-right.md`](experiments/0008-measure-1-cost-of-being-right.md)
§8 established a boundary rather than a backlog:

> The daily-horizon question **cannot be settled by more BTCUSDT history.** Sixty-eight years
> of it does not exist and never will; the instrument is seven years old. This is a hard limit
> of the same kind as the ~291 ms latency floor.

and named the escape:

> Any claim about affordable horizons must come from evidence of a different kind —
> **conditional, cross-sectional or event-based**.

The cross-sectional route is the one with an arithmetic precondition, and it is cheap to check
before committing to it. Statistical power grows with `sqrt(n)`, and a cross-section multiplies
`n` by the number of instruments **only to the extent those instruments are independent**.
Grinold's fundamental law states the same thing for strategy capacity: `IR ~ IC * sqrt(BR)`,
where `BR` counts independent bets, not tickers.

Crypto is widely observed to trade as a single risk asset. If that holds here, thirty perps
might carry the statistical weight of two, and the cross-sectional escape would be far narrower
than it appears.

## 2. Method

[`../market/breadth.py`](../market/breadth.py), tested in
[`../tests/test_breadth.py`](../tests/test_breadth.py) against matrices with answers known by
construction — independence returns `k`, perfect correlation returns 1, and the hand-computed
`k=30, rho=0.7` case returns 1.41.

- **Data:** Binance USD-M perpetual futures monthly kline archives — perps, because that is the
  market the question concerns.
- **Horizon:** **4h bars.** Correlation is horizon-dependent; instruments that look distinct
  minute to minute routinely move as one over hours. 4h is where MEASURE-1 located the
  affordability floor, so measuring anywhere else would answer a different question.
- **Window:** 2025-08-01 to 2026-07-31, **2,189 aligned bars**, `n/k ≈ 66`.
- **Alignment:** timestamp intersection across all instruments. No forward-filling — an
  inserted zero return drags correlations toward zero and would flatter the very quantity being
  measured.
- **Instruments:** 33 liquid perps (34 requested; PEPEUSDT unavailable in the archive).

Two measures, reported together because the simple one flatters:

```
BR_equicorrelation = k / (1 + (k-1) * rho_bar)          assumes every pair shares one rho
N_eff              = (sum lambda_i)^2 / sum(lambda_i^2)  participation ratio, no such assumption
```

Where they disagree the participation ratio is the one to believe, and the disagreement itself
says the cross-section is not uniform.

## 3. Results

| Quantity | Value |
|---|---|
| Instruments | 33 |
| Mean pairwise correlation | **0.672** (median 0.699, range 0.310–0.865) |
| PC1 share of variance | **69.0%** |
| PC2 share of variance | 3.5% |
| Effective breadth — equicorrelation | 1.47 |
| **Effective breadth — participation ratio** | **2.08** |
| **Effective breadth, PC1 removed** | **24.06** |
| Mean residual correlation after removing PC1 | **−0.031** |

Least correlated pairs: ICP/TRX 0.310, ORDI/TRX 0.332, TON/TRX 0.342. Most correlated:
BTC/ETH 0.865, ETH/LINK 0.860. TRXUSDT is the least correlated instrument to BTCUSDT (0.408).

## 4. What this establishes

**Directionally, the cross-section is one bet.** 33 tickers carry the statistical weight of
about 2. PC1 takes 69% of all variance and PC2 takes 3.5% — one dominant factor and then
nothing. For a directional strategy `sqrt(BR) = 1.44x` against `sqrt(33) = 5.74x` if the
instruments were independent. **Breadth buys almost nothing.**

**Once the market factor is removed, the cross-section is nearly independent.** Residual
breadth 24.06, mean residual correlation −0.031, `sqrt(BR) = 4.91x` against a 5.74x ceiling.

**So the cross-sectional escape named in MEASURE-1 §8 exists, but in one shape: relative
value.** A view on *crypto* is one bet. A view on *one perp against another* is one of roughly
twenty-four.

## 5. What this does NOT establish

- **Breadth is necessary, not sufficient.** Grinold counts independent *bets*, which requires a
  signal that works on the residual. This measures the room available, not that anything
  occupies it. No signal is proposed, implied or tested here.
- **It does not reopen the daily variance-ratio question.** A cross-sectional test asks a
  different question than a single-series variance ratio. MEASURE-1 §8's boundary stands.
- **In-sample PC removal flatters.** The eigenvector is estimated on the same 2,189 bars it is
  removed from, so 24.06 is an upper bound. Random-matrix eigenvalue cleaning (Laloux &
  Bouchaud) would tighten it, and should be applied before the number is relied upon.
- **Cost scales with legs.** MEASURE-1's break-even table prices *one* position. A neutral book
  pays the round trip on every leg, and trades residual moves smaller than the market moves it
  hedges away. Cheap breadth, expensive execution.
- **Breadth and history trade off.** The instruments contributing independence — TRX, ICP,
  ORDI, TON — are the newest and least liquid. Those with long history (BTC, ETH, LTC, BCH) are
  the most correlated. Over a five-year window the surviving set is smaller *and* tighter, so
  breadth over long samples is lower than 24.06. **This measurement is a one-year window and
  should not be extrapolated backwards.**
- **One venue, one year, one asset class**, and correlations are regime-dependent — they rise
  in stress, which is when breadth is needed most.

## 6. Provenance

The question arose in conversation on 2026-08-13 while discussing MEASURE-1 §8's structural
limit. The estimate quoted before any data was fetched — "thirty perps at rho ~ 0.7 gives about
1.4 effective bets" — is the equicorrelation formula above, and the measured value of 1.47
matched it. The residual-breadth result was not anticipated.
