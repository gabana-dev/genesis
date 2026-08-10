# 0008 — MEASURE-1: the cost of being right

**Date:** 2026-08-10
**Status:** done
**Classification: IMPORT — every method established and cited. No novelty claimed.**
Contract: [`../../market/CONTRACT-measurement.md`](../../market/CONTRACT-measurement.md),
frozen before any code, `sha256 f74e8cf28f48fdd636b8ed0189a3522bdad136c8283fe222ef6a7c0e46b395d2`.
Code: [`../../market/`](../../market/). Checks: [`../../tests/test_market.py`](../../tests/test_market.py) (16).

Phase 2 of the market direction: measure the environment, do not trade it. No strategy code,
no optimisation, no backtest, no orders, no paper trading.

Raw outputs are reported first, in contract order, Q1 before Q2. Interpretation is §7 and is
kept separate on purpose.

---

## 1. Data, and what verification found

BTCUSDT, Binance public monthly kline archives, 2019-01-01 → 2026-07-31.
**3,983,271 one-minute bars.** Zero duplicate timestamps. Order-book measurements come from
Genesis's own BAV-1 run-3 recording (3 hours, hash-chain verified).

The contract required verifying kline timestamp semantics against the raw bytes rather than
assuming them. That requirement found three properties of the source, each of which had
already produced a wrong answer:

| Finding | Evidence |
|---|---|
| **Halt-truncated bars** | 2019-06-07 21:13 spans 13,524 ms, zero volume, zero trades, then 61 bars missing. **22 halts, 4,089 missing bars, 0.10% of the series.** |
| **`close_time` is unreliable** | 2021-12-24 04:59 spans 54,362 ms with 1,124 trades and *no* following gap. The field is simply wrong there. |
| **Silent unit change** | Binance switched the archives from millisecond to **microsecond** timestamps during 2025. Concatenating both unconverted places every 2025+ bar ~50,000 years in the future. |

A fourth test was **tried and discarded as invalid**: `open[i] == close[i-1]` fails for 51.8%
of adjacent bars, because the first trade of a minute is not generally at the last trade price
of the previous minute. Ordinary microstructure, not misalignment.

Interval-**opening** semantics are confirmed by boundary alignment. Halts are never aggregated
across; aggregation runs inside contiguous segments only, at a measured cost of 11 of 2,766
daily blocks (0.4%). Gaps are reported, never interpolated.

## 2. A — return magnitude

Median absolute log return, with moving-block bootstrap 95% intervals.

| Horizon | n | median | 95% CI | q25 | q75 |
|---|---|---|---|---|---|
| 1m | 3,983,248 | **0.0316%** | [0.0314, 0.0319] | 0.0124% | 0.0661% |
| 5m | 796,629 | 0.0729% | [0.0720, 0.0737] | 0.0313% | 0.1462% |
| 15m | 265,523 | 0.1251% | [0.1230, 0.1271] | 0.0561% | 0.2471% |
| 1h | 66,357 | **0.2371%** | [0.2309, 0.2426] | 0.1036% | 0.4821% |
| 4h | 16,565 | 0.4624% | [0.4433, 0.4822] | 0.1931% | 0.9981% |
| 1d | 2,733 | **1.4247%** | [1.3318, 1.5507] | 0.5769% | 2.8180% |
| 3d | 889 | 2.6427% | [2.3342, 2.8773] | 1.2468% | 5.2588% |

## 3. Q1 — is there measurable directional structure?

### F — variance ratio (Lo & MacKinlay 1988), heteroskedasticity-robust z2

| Base | q | Horizon | VR | z2 | p | Rejects random walk |
|---|---|---|---|---|---|---|
| 1m | 5 | 5m | 0.9809 | −2.24 | 0.025 | **yes** |
| 1m | 15 | 15m | 0.9357 | −4.42 | 9.8e−06 | **yes** |
| 1m | 60 | 60m | 0.8933 | −4.44 | 9.1e−06 | **yes** |
| 1h | 4 | 4h | 0.9628 | −1.69 | 0.091 | no |
| 1h | 24 | 1d | 0.9767 | −0.44 | 0.66 | no |
| 1h | 72 | 3d | 0.9487 | −0.64 | 0.52 | no |

Every VR is below 1 — the mean-reverting direction. Rejection is confined to minute-scale
aggregation and disappears from 4 hours upward.

### F by calendar year

Sliced by calendar year first, then segmented within the year.

| Year | 1m base, q=60 | | | 1h base, q=24 | | |
|---|---|---|---|---|---|---|
| | VR | z2 | p | VR | z2 | p |
| 2019 | 0.9339 | −1.62 | 0.10 | 1.0251 | 0.24 | 0.81 |
| 2020 | 0.8315 | −1.68 | 0.092 | 0.9606 | −0.17 | 0.86 |
| 2021 | 0.8468 | −3.74 | **0.00019** | 0.9499 | −0.56 | 0.58 |
| 2022 | 0.9513 | −1.60 | 0.11 | 0.9984 | −0.02 | 0.99 |
| 2023 | 0.9559 | −1.05 | 0.29 | 1.0874 | 1.03 | 0.30 |
| 2024 | 0.9328 | −2.16 | **0.031** | 0.9487 | −0.62 | 0.54 |
| 2025 | 0.9392 | −1.71 | 0.087 | 0.9173 | −0.95 | 0.34 |
| 2026 | 0.9269 | −2.27 | **0.023** | 0.9582 | −0.38 | 0.71 |

At minute scale, VR < 1 in **8 of 8 years**, individually significant in 3. At daily scale VR
straddles 1 and never rejects.

### G — realized-volatility signature plot

| Sampling | 1m | 2m | 5m | 10m | 15m | 30m | 60m | 120m |
|---|---|---|---|---|---|---|---|---|
| Daily RV | 3.445% | 3.469% | 3.441% | 3.392% | 3.355% | 3.340% | 3.237% | 3.212% |

**Essentially flat.** Total variation from 1m to 120m is 7%, with no inflation blow-up at fine
sampling.

### H — Roll (1984) effective spread

| | Value |
|---|---|
| Pooled 1-minute lag-1 autocorrelation | **+0.00442** |
| Roll spread, longest segment | 0.00998% (cov = −11.4) |
| Directly measured spread (§4) | **0.000015%** |
| Per year | 2019 −0.0089 · 2020 −0.0022 · **2021 +0.0106 (cov > 0, model does not apply)** · 2023 −0.0026 |

The Roll estimate is **~665× the directly measured spread**, and the pooled lag-1
autocorrelation is positive.

## 4. Q2 — does structure survive realistic costs?

### C, D — spread and impact, from Genesis's own recordings

2,042 book samples, 1 Hz, restricted to intervals the recorder labels complete.

| | Value |
|---|---|
| Spread, median | **$0.01 — one tick — 0.000015% of mid** |
| Recorded bid-side depth, median | $33.8M |
| Round-trip spread+impact, $1k | 0.00002% |
| Round-trip spread+impact, $10k | **0.00002%** |
| Round-trip spread+impact, $50k | 0.00002% |
| Round-trip spread+impact, $100k | 0.00008% |
| Round-trip spread+impact, $500k | 0.01205% |

Depth was never exhausted at any size tested. **E** (square-root impact law) is not reported:
impact is indistinguishable from zero up to $100k, so there is no curve to fit. Reported as
not-estimable rather than fitted to noise.

### B — break-even hit rate, `p* = 1/2 + c/(2·φ·m)`

`c` = fees + 0.00002% measured spread/impact at $10k. **n/a means p\* > 1: even perfect
prediction loses money.**

| Horizon | move | spot taker 0.20% |||fut taker 0.10% ||| fut maker 0.04%\* |||
|---|---|---|---|---|---|---|---|---|---|---|
| | | φ=1 | φ=.5 | φ=.25 | φ=1 | φ=.5 | φ=.25 | φ=1 | φ=.5 | φ=.25 |
| 1m | 0.032% | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 5m | 0.073% | n/a | n/a | n/a | n/a | n/a | n/a | 77.4% | n/a | n/a |
| 15m | 0.125% | n/a | n/a | n/a | 90.0% | n/a | n/a | 66.0% | 82.0% | n/a |
| 1h | 0.237% | 92.2% | n/a | n/a | 71.1% | 92.2% | n/a | 58.4% | 66.9% | 83.8% |
| 4h | 0.462% | 71.6% | 93.3% | n/a | 60.8% | 71.6% | 93.3% | 54.3% | **58.7%** | 67.3% |
| 1d | 1.425% | 57.0% | 64.0% | 78.1% | 53.5% | **57.0%** | 64.0% | 51.4% | **52.8%** | 55.6% |
| 3d | 2.643% | 53.8% | 57.6% | 65.1% | 51.9% | **53.8%** | 57.6% | 50.8% | **51.5%** | 53.0% |

\* The maker column is an **upper bound on maker attractiveness**. Adverse selection is a Q3
term and is not included anywhere in this table.

### I, J — liquidity and seasonality

Activity concentrates on the US session: 13:00–16:00 UTC carries median |1h return| of
0.27–0.33% on $69–89M median hourly volume, against 0.19–0.20% on $38–44M at 03:00–06:00 UTC.
Amihud illiquidity is ~15% higher in the quiet hours. Weekdays run 0.25–0.27%; Sunday 0.16%
and Monday 0.19% are the quiet days.

## 5. Pre-registered predictions — scored

| # | Prediction | Outcome |
|---|---|---|
| P1 | median \|1d\| in 1.2–2.0% | **confirmed** — 1.425% |
| P2 | median \|1h\| in 0.25–0.45% | **falsified** — 0.237%, just below the band |
| P3 | median \|1m\| in 0.03–0.08% | **confirmed** — 0.0316% |
| P4 | p\* at 1h spot taker φ=1 > 70% | **confirmed** — 92.2% |
| P5 | p\* at 1d futures maker φ=0.5 in 52–58% | **confirmed** — 52.8% |
| P6 | VR ≈ 1 at every horizon ≥ 1h | **falsified at 1h** (VR 0.893, p 9e−06); **holds at 4h, 1d, 3d** |
| P7 | 1m autocorrelation negative, fully explained by Roll | **falsified** — pooled autocorrelation is **positive** (+0.0044), and Roll returns 665× the measured spread |
| P8 | noise dominates below ~1–5 minutes | **falsified** — the signature plot is flat to 1 minute |
| P9 | spread ≈ 1 tick, negligible beside fees | **confirmed** as 1 tick; the "~0.001%" figure was wrong by 65× (actual 0.000015%) |
| P10 | slippage at $10k < 0.01% | **confirmed** — 0.00002% |
| P11 | **cost, not depth, binds** | **confirmed** — fees are 500–2,000× spread+impact at our size |
| P12 | reachable region is 1-day-plus, as a maker | **partly falsified** — 4h clears as a maker (58.7%), and 1d clears as a **taker** (57.0%). Maker is not required at 1d, and the region extends below a day. |

Five confirmed, five falsified, one partly, one confirmed with a wrong magnitude.

## 6. The kill condition

> No horizon at any fee tier yielding `p* ≤ 60%` at φ = 0.5 closes the directional line.

**Not triggered.** Four cells clear it: 4h futures maker (58.7%), 1d futures maker (52.8%),
1d futures taker (57.0%), 3d at every tier except spot taker.

Per the contract, **passing licenses nothing beyond continuing to Q3.**

## 7. Interpretation — kept separate, as §8 requires

**The two answers do not overlap, and that is the finding.**

Q1 locates linear structure at **minute scale**, rejecting the random walk at 5m, 15m and 60m,
directionally consistent across 8 of 8 years. Q2 locates affordability at **4 hours and
longer**. Between them lies a gap: *where structure is detectable we cannot afford to act on
it, and where we can afford to act there is no detectable linear structure.*

At 1h with the best available fee tier and half capture, the bar is 66.9%. The measured
structure at that scale is a variance ratio of 0.893 — real, but nowhere near enough to
deliver two-thirds accuracy.

**What P7's falsification means, stated carefully.** The minute-scale mean reversion is *not*
bid-ask bounce. Lag-1 autocorrelation is positive; the true spread is one tick; and Roll's
estimator returns a spread 665× too large, which means it is being fed something its model
does not describe. Genesis pre-registered the bounce explanation and the data refused it.
**This is not a discovery.** It is an unexplained residual, at a horizon we have just measured
to be unaffordable, and it survives none of Q2 or Q3. Recorded as an open question, claimed as
nothing.

**What this does not establish.** The variance ratio tests **linear** structure only —
non-linear or conditional structure is untested and this says nothing about it. One symbol, on
the deepest crypto market in existence, from one location. All Q3 terms — fills at ~291 ms
latency, adverse selection, the maker's curse — remain entirely unmeasured, and the maker
column is an upper bound precisely because of that.

**And the 4h+ null is far weaker than §3 makes it look. See §8, which corrects it.**

## 8. Power analysis — a correction to §7, run 2026-08-10

§7 above reported that structure and affordability do not overlap. The second half of that
claim was not supported by the evidence, and this section corrects it.

Minimum detectable effect at 80% power, two-sided 5%: `|VR − 1| ≥ 2.80 × se`.

| Horizon | n | VR | 95% CI | se | Detectable only if | Verdict |
|---|---|---|---|---|---|---|
| 5m | 3,983,248 | 0.9809 | [0.9642, 0.9976] | 0.0085 | ≤ 0.976 or ≥ 1.024 | rejected, but **underpowered for an effect this small** — marginal |
| 15m | 3,983,248 | 0.9357 | [0.9072, 0.9642] | 0.0145 | ≤ 0.959 or ≥ 1.041 | **well-powered rejection** |
| 60m | 3,983,248 | 0.8933 | [0.8462, 0.9404] | 0.0240 | ≤ 0.933 or ≥ 1.067 | **well-powered rejection** |
| 4h | 66,357 | 0.9628 | [0.9196, 1.0059] | 0.0220 | ≤ 0.938 or ≥ 1.062 | **blind** |
| 1d | 66,357 | 0.9767 | [0.8721, 1.0813] | 0.0534 | ≤ 0.851 or ≥ 1.150 | **blind** |
| 3d | 66,357 | 0.9487 | [0.7916, 1.1059] | 0.0802 | ≤ 0.775 or ≥ 1.225 | **blind** |

At 4h and beyond the observed VR sits inside the zone the study could never have resolved.
**The failure to reject at those horizons is absence of evidence, not evidence of absence.**
At daily scale the smallest effect detectable is VR ≤ 0.851 — a *larger* mean reversion than
the strongest thing found anywhere in this study (0.893 at 60m). The null is close to
uninformative.

### The structural limit

How much history would settle it?

| Horizon | Have | For 80% power against true VR = 0.95 | against VR = 0.90 |
|---|---|---|---|
| 4h | 7.6 y | **12 years** | 3 years |
| 1d | 7.6 y | **68 years** | 17 years |
| 3d | 7.6 y | **153 years** | 38 years |

**The daily-horizon question cannot be settled by more BTCUSDT history.** Sixty-eight years of
it does not exist and never will; the instrument is seven years old. This is a hard limit of
the same kind as the ~291 ms latency floor — not a gap to be closed by working harder, but a
boundary on what this route can ever resolve.

### The corrected finding

> **Established:** linear mean-reverting structure at 15m–60m, well-powered, directionally
> consistent across 8 of 8 years.
> **Established:** affordability begins at 4h.
> **NOT established, and not establishable by this method:** whether structure exists at 4h and
> beyond. The variance ratio is the wrong instrument at that horizon — it lacks the resolution
> and cannot be given it.

The overlap question is therefore **open**, not closed. Any claim about affordable horizons
must come from evidence of a different kind — conditional, cross-sectional or event-based — or
be accepted as unfalsifiable by this route. Recorded as a measured constraint on method, not as
a result about markets.

**What it changes.** The reachable region is **4 hours and longer**, and the fee tier moves the
bar more than a horizon step does: at 1d, moving from spot taker to futures maker cuts the
required hit rate from 64.0% to 52.8%. Execution is not a detail. It is the larger lever, which
is why the fill/execution simulator — the largest unbuilt component — is the thing that decides
whether any of this is real.


## 9. Multiple-comparison correction — a second tightening, 2026-08-10

The trial ledger ([`../../market/ledger.py`](../../market/ledger.py)) was built before any
hypothesis search began and seeded with the trials this experiment had already run. Counting
them honestly corrects §3 further.

**Family: pooled variance ratio, 6 tests.** Bonferroni α = 0.0083.

| Horizon | p | Survives correction |
|---|---|---|
| 15m | 9.8e−06 | **yes** |
| 60m | 9.1e−06 | **yes** |
| 5m | 0.0252 | **no** |
| 4h, 1d, 3d | 0.09–0.66 | no |

**Family: per-year variance ratio, 16 tests.** Bonferroni α = 0.0031.

Only **2021** (p = 0.00019) survives. The 2024 (p = 0.031) and 2026 (p = 0.023) rejections do
not. Benjamini-Hochberg agrees with Bonferroni in both families.

**The corrected §3 claim.** Structure at 15m and 60m survives both the power analysis and the
multiple-comparison correction, in two families, independently. Everything else weakens:

- The 5m rejection fails on **both** grounds — underpowered for an effect that size, and it
  does not survive six trials. It should not be cited.
- "Individually significant in 3 of 8 years" becomes **1 of 8 after correction**.
- The **8-of-8 sign consistency stands**, because it is a sign test rather than a threshold
  on any single p-value, and it was not selected after the fact.

Total trials on the ledger for this experiment: **23**, all pre-registered, none outstanding,
chain verified.

**What this demonstrates about the instrument, not the market.** Two mechanisms — power and
multiple comparisons — were applied after the headline was written, and both moved it in the
same direction: *less* was established than first reported. Neither was available at the time
the original claim was made, which is the argument for having them in place before the next
question rather than after it.
