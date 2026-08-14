# Volatility scaling, and the decay of minute-scale structure

**Date:** 2026-08-14
**Status:** exploration — **descriptive measurement, not a trial.** No hypothesis is tested,
nothing is accepted or rejected, no strategy is proposed. Recorded as CONTEXT in the ledger.
**Data:** BTCUSDT 1m spot, 2019-01-01 → 2026-07-31, 3,983,271 bars, 23 contiguous segments
(22 halts). Already cached; no new download.
**Method:** returns computed **inside contiguous segments only**, so no return spans a halt.

---

## 1. The question

MEASURE-1 §3(G) plotted a realized-volatility signature. This turns the plot into a number.

For a random walk, variance grows linearly with time, so the standard deviation of returns
scales as `sd ~ dt^H` with **H = 0.5**. H below 0.5 means variance grows more slowly than
linearly — mean reversion. H above 0.5 means momentum.

It is the same quantity the variance ratio measures (`VR(q) = q^(2H-1)`), read as a scaling
exponent rather than a test statistic.

## 2. Pooled result — and why the pooled result misleads

A single log-log fit across all seven horizons gives **H = 0.4864, R² = 0.99996**. That looks
like a beautifully clean power law, and it is wrong to stop there: the implied VR at one day
would be 0.820, while MEASURE-1 *measured* 0.977. A single exponent cannot fit both.

The local exponent between adjacent horizons shows why:

| span | H_local | ± | implied VR over the span |
|---|---|---|---|
| 1m → 5m | 0.4993 | 0.0005 | 0.998 |
| 5m → 15m | **0.4770** | 0.0014 | 0.951 |
| 15m → 1h | **0.4740** | 0.0022 | 0.931 |
| 1h → 4h | 0.4887 | 0.0044 | 0.969 |
| 4h → 1d | 0.4954 | 0.0081 | 0.984 |
| 1d → 3d | 0.4821 | 0.0249 | 0.961 |

**The mean reversion occupies a band, roughly 5 minutes to 1 hour, with a boundary at each
end.** MEASURE-1 established the upper edge. The lower edge is new here: below 5 minutes the
series is a random walk to four decimal places, 0.4993 ± 0.0005.

Above 4h the standard errors grow and nothing is distinguishable from 0.5 — the same blindness
MEASURE-1 §8 documented, arrived at by a different route.

## 3. The finding that matters — it is decaying

Per-year local exponents, same method:

| year | 1m → 5m | 15m → 1h | 4h → 1d |
|---|---|---|---|
| 2019 | 0.4975 ± 0.0015 | 0.4826 ± 0.0061 | 0.5130 ± 0.0226 |
| 2020 | 0.4842 ± 0.0015 | **0.4624** ± 0.0061 | 0.5504 ± 0.0227 |
| 2021 | 0.5060 ± 0.0015 | **0.4490** ± 0.0061 | 0.4473 ± 0.0226 |
| 2022 | 0.5043 ± 0.0015 | 0.4971 ± 0.0061 | 0.5267 ± 0.0223 |
| 2023 | **0.5179** ± 0.0015 | 0.4877 ± 0.0061 | 0.5154 ± 0.0224 |
| 2024 | 0.4933 ± 0.0015 | 0.4946 ± 0.0061 | 0.5075 ± 0.0223 |
| 2025 | 0.5026 ± 0.0015 | 0.4971 ± 0.0061 | 0.4680 ± 0.0223 |
| 2026 | 0.4943 ± 0.0019 | 0.4746 ± 0.0080 | 0.5481 ± 0.0293 |

**Two things the pooled numbers hid.**

**(a) The 15m→1h reversion is concentrated in 2020–2021.** At 6.2 and 8.4 standard errors below
0.5 it was unmistakable then. In 2022, 2024 and 2025 it sits within one standard error of a
random walk. The pooled 0.4740 is largely those two early years.

MEASURE-1 reported the direction as consistent across 8 of 8 years, which remains true — every
year is below 0.5. **The direction persisted; the magnitude collapsed.**

**(b) The 1m→5m band flips sign between years.** 2020 is 10.5 se *below* 0.5; 2023 is 12 se
*above* it — momentum. The pooled 0.4993 ± 0.0005 is not a clean random walk but the average
of opposing years cancelling out. A pooled estimate over a non-stationary series can be
precise and uninformative at the same time.

## 4. What this does and does not establish

**Establishes:** the scaling exponent has structure in scale (a reversion band at 5m–1h) and
structure in time (the band's depth has decayed since 2021). Both are measured, well-powered
at 1m–1h, and computed without ever aggregating across a halt.

**Does not establish:**

- **Nothing at 4h and beyond.** Standard errors at 4h→1d are ±0.008 pooled and ±0.022 per
  year, so nothing there is distinguishable from 0.5. Same wall as MEASURE-1 §8: absence of
  evidence.
- **No cause.** The decay is consistent with a market becoming more competed, and consistent
  with several other things. Nothing here identifies which.
- **Nothing tradable.** Even at its 2021 strongest, `H = 0.449` at 15m→1h implies VR 0.931 over
  that span — MEASURE-1 already established that structure of this size at that horizon does
  not survive costs. This measures the shape of an effect that was never affordable.
- **Linear only.** Like the variance ratio, this sees linear dependence. Non-linear or
  conditional structure is untested.

## 5. Why it is worth recording anyway

An effect that halves in strength over five years is a different object from a stable one. Any
future work at minute scale would be building on something the data says is going away, and the
per-year table is the cheapest possible warning of that.

It also sharpens the open anomaly. MEASURE-1 recorded minute-scale reversion that was *not*
bid-ask bounce and left it unexplained. The shape here — random walk below 5m, reversion from
5m to 1h, efficiency above — is the signature a transient-impact model predicts: impact decays
over some timescale, and reversion appears at that scale. That is a **candidate reading, not a
finding**; testing it needs a separate pre-registered study and order-flow data this recording
does not contain.

## 6. Reproduction

`market/data.py` (cached), `research/explorations/` — the computation is thirty lines: load,
`contiguous_segments`, `aggregate` at each horizon, `std` of log returns, and the local exponent
`H = log(sd2/sd1) / log(k2/k1)` with `se = sqrt(1/2n1 + 1/2n2) / log(k2/k1)`.
