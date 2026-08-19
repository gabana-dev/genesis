# Adverse selection decays: it is a short-horizon cost, not a permanent one

**Date:** 2026-08-19
**Data:** the EXEC-1 / q3 recording, SHA-256 `740fc04d4cf40d81…`, 7 days, 60,480 declared orders
at the 291 ms arm. Simulated in 5,627 s.
**Report:** [`../market/evidence/as-horizon.json`](../market/evidence/as-horizon.json)
**Classification: measurement. The declared EXEC-1 grid, reported at additional horizons.**

---

## 1. The measurement

Median markout on filled passive orders, certain pool:

| horizon | adverse selection | n |
|---|---|---|
| 60 s | 1.1871 bps | 39,473 |
| 5 min | 1.1722 | 39,473 |
| 1 hour | 1.1637 | 39,473 |
| **6 hours** | **0.4041** | 39,029 |
| **24 hours** | **0.1301** | 34,274 |

**Flat through an hour, then it collapses.** At 24 hours adverse selection is **11% of its
60-second value**.

## 2. I predicted the opposite, and said so in advance

Before running this I wrote:

> *"Saturated at 1.19 bps means it's still 1.19 bps at one day... My honest expectation: this
> comes back around 1 bps and closes BTC directional trading at retail scale."*

That reasoning was wrong. EXEC-1's X1 finding — adverse selection *"grows with horizon and
stabilises past 60 s"* — was correct **within the horizons it measured**, and I extrapolated a
plateau observed over 60 s → 300 s across a 288× extension. The plateau does not hold. It is a
local flat spot on a curve that turns over somewhere between one and six hours.

**The measured value is roughly 9× smaller than my prediction.**

## 3. Why this is economically sensible in hindsight

Adverse selection is the cost of being handed liquidity at a moment chosen by someone better
informed. That informational advantage is **short-lived**: the price moves against the passive
fill immediately, and then ordinary volatility swamps it and much of the move reverts.

At 60 seconds, 1.19 bps is enormous — the median absolute move over that window is a fraction
of a basis point. At 24 hours, the same 1.19 bps of initial pickoff sits inside a **142 bps**
median move, and what survives is 0.13.

This is consistent with Genesis's own tick-scale finding, and with the general result that
informed order flow has a short half-life. **It was available to reason about and I reasoned
about it badly.**

## 4. What it does to the decision

Round-trip adverse selection at 1 day = 2 × 0.1301 = **0.2601 bps**.

| venue | total cost | bar | measured 0.5242 |
|---|---|---|---|
| Binance USD-M VIP 0 | 4.259 bps | 0.5299 | **fails** |
| **Hyperliquid T0 base** | **3.105 bps** | **0.5218** | **clears** |
| Hyperliquid T0 Bronze | 2.805 bps | 0.5197 | clears |

**ECON-1's K4 does not fire.** The contract is not void and the forward test proceeds.

### 4.1 The caveat that matters most

**That "clears" column uses the accuracy bar — the metric ECON-1 was written to replace.**

`p* = 0.5 + c/(2φm)` uses the *median* move against a *mean*-driven payoff, which is the
methodological defect ECON-1 §1 documents. So this table says the signal clears **the old,
defective bar** at Hyperliquid. It does not say the strategy makes money.

That question is what ECON-1 measures, forward, from 2026-08-20, against buy-and-hold and a
sign-permutation null. Nothing here shortcuts it.

### 4.2 Three further limits

**Sample composition shifts with horizon.** n falls from 39,473 to 34,274 at 24 hours, because
fills in the recording's final day have no 24-hour future. The 24-hour figure is measured on 87%
of the fills, systematically the earlier ones. Not a large distortion; not nothing.

**Median, not mean.** Markout distributions are fat-tailed and P&L is driven by the mean. The
mean markout at 24 hours is not reported by `summarise` at this call and is not claimed.

**One week, one regime.** August 2026 only.

## 5. What this changes

For the first time in this project a measurement came back **favourable**.

Three directions were closed on evidence — market making, carry, unconditional direction. This
one does not close. It says: at a venue costing 3 bps rather than 4, with adverse selection
measured rather than assumed, the signal Genesis found is **not obviously dead**.

That is a much weaker claim than "we have a strategy", and the distance between those two
statements is exactly what ECON-1 exists to measure over the next several months.

**The honest summary:** every previous estimate in this project has been wrong in the direction
that made things look worse, and this one was wrong in the direction that made things look
worse too. The correction is the same either way — **measure the term instead of extrapolating
it.**
