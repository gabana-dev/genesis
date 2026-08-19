# DIR-2 result: the information is real, and it is smaller than the costs

**Date:** 2026-08-19
**Contract:** [`../market/CONTRACT-direction-2.md`](../market/CONTRACT-direction-2.md), frozen
at `df746b42458e5fdd…` before any figure was computed.
**Report:** [`../market/evidence/dir2-report.json`](../market/evidence/dir2-report.json)
**Instrument:** [`../market/dir2.py`](../market/dir2.py), 6 harness checks on top of DIR-1's 7.

---

## 1. The result

| cell | gate pass | n | accuracy | bar | 95% CI | window SD |
|---|---|---|---|---|---|---|
| **G3 top-trader extreme \| 1d** | 7.2% | 560 | **0.5464** | 0.5281 | [0.4964, 0.5946] | 0.185 |
| **G5 no gate \| 1d** | 100% | 4,880 | **0.5242** | 0.5281 | **[0.5063, 0.5404]** | 0.069 |
| G3 top-trader extreme \| 3d | 7.2% | 560 | 0.5214 | 0.5151 | [0.4554, 0.5732] | 0.132 |
| G5 no gate \| 3d | 100% | 4,880 | 0.5131 | 0.5151 | [0.4871, 0.5394] | 0.067 |
| G1 flow extreme \| 1d | 3.2% | 216 | 0.5000 | 0.5281 | [0.4306, 0.5602] | 0.162 |
| G4 crowd extreme \| 1d | 6.2% | 425 | 0.4894 | 0.5281 | [0.4329, 0.5412] | 0.173 |
| G2 leverage build \| 1d, 3d | 2.1% | 121 | — | — | **excluded, K1** | — |

Two cells exceed their bar on the point estimate. **Both are rejected**, by K3 and by K4, and
neither has an interval excluding anything. **DIR-2 returns negative.**

## 2. The finding that is not a null

**G5 — unconditional, on positioning and flow features — scores 0.5242 at 1 day with a 95%
interval of [0.5063, 0.5404]. That interval excludes 0.50.**

There is a **statistically detectable directional signal** in open interest, taker imbalance
and long/short positioning at a one-day horizon, over 4,880 out-of-sample predictions across 20
purged walk-forward windows. It is real.

**It is also not enough.** The bar is 0.5281 and it scores 0.5242. It misses by **0.4
percentage points** — small enough to be maddening, large enough that no amount of care closes
it.

For contrast, DIR-1's best price-derived cell was 0.5111 with an interval spanning 0.50.
**Positioning data beats price data by 1.3 percentage points and still cannot pay a 4 bps round
trip.**

This independently reproduces Pindza (2026), from different data and a different method:
*"microstructure signals carry genuine but weak information content ... not exploitable at
standard retail fee levels."* Genesis has now arrived at that sentence twice, by two routes.

## 3. Last night's defect prevented tonight's false positive

This is the most important thing in this document.

**G3 (top-trader positioning extreme) scored 0.5464 at 1 day against a 0.5281 bar.** On the
point estimate it clears by 1.8 percentage points. It is the only cell in either directional
experiment that has ever looked like an edge.

DIR-1's K3 tested a best cell against the **mean** of the best-of-N distribution under zero
skill. That was recorded as defect **D-D1** last night: beating a mean is a coin flip, so the
test rejected only half of pure noise. DIR-2 replaced it with the **95th percentile**.

The null for this grid, best-of-8 at n=492:

| | value | G3 verdict |
|---|---|---|
| mean of null maximum | 0.5321 | **PASSES** — the old, defective test |
| **p95 of null maximum** | **0.5569** | **FAILS** — the corrected test |

**Under the rule as originally written, G3 would have been reported as a finding.** Under the
corrected rule it is inside the null distribution and is reported as noise.

A defect found by running one contract stopped a false positive in the next contract, one day
later. That is the entire argument for pre-registration, and it happened to be worth exactly
one spurious trading strategy.

**K4 rejects G3 independently:** its per-window accuracy standard deviation is **0.185** against
an edge over a coin flip of **0.046**. The regime-to-regime variation is four times the effect.
And its 95% interval, [0.4964, 0.5946], contains 0.50.

Three independent reasons, any one of which is sufficient.

## 4. Predictions, scored

- **E1 — CONFIRMED.** G5 fails to clear 52.8% at 1 day. By 0.4 points.
- **E2 — CONFIRMED.** G3 beats the control by 2.2 points (0.5464 vs 0.5242). Conditioning does
  something. It is simply not enough to survive the null.
- **E3 — WRONG.** I predicted G1 (aggressive flow) would be the best gate, because it describes
  what is *happening* rather than what is *held*. G1 was the **worst** at exactly 0.5000, and
  the winner was **G3, top-trader positioning** — a *held* quantity. I had the mechanism
  backwards.
- **E4 — CONFIRMED.** G2 (leverage build) fails K1 at both horizons, 121 predictions against a
  200 threshold.
- **E5 — CONFIRMED.** The crowd-positioning coefficient is **−2.49 × 10⁻³**, negative and the
  largest magnitude of the five. An unusually long crowd precedes negative returns. **The one
  mechanism I predicted correctly is the contrarian one** — and it still does not clear the bar.
- **E6 — CONFIRMED.** No cell clears its bar with an interval excluding it.

Four of six confirmed. The one I got most wrong (E3) is the one that produced the tempting cell.

## 5. Defects, recorded

**D-D2 — divide-by-zero in the open-interest change.** Six of 8,307 decision points carry a
reported open interest of exactly zero, producing `inf` in the 24-hour log change and a runtime
warning. The affected values are non-finite and are therefore excluded by the existing
`isfinite` filter, so **no result is contaminated** — 1,840 of 8,307 `doi` values are non-finite
in total, the great majority being the pre-2020-09 period where metrics do not exist.

It is recorded rather than silenced because a zero open interest on BTCUSDT perpetual is not a
real market state; it is a venue reporting artefact, and a future contract using this field
should exclude it explicitly rather than rely on a downstream filter catching it.

## 6. Where this leaves Genesis

| direction | verdict |
|---|---|
| Market making | **closed** — spread 0.00154 bps against 5.19 bps of cost |
| Carry | **positive, uneconomic** — ≈2.6–4.3% on capital against a 4–5% risk-free rate |
| Direction, unconditional, price features | **closed** — 0.5111 against 0.5281 |
| Direction, conditional, flow and positioning | **closed** — best cell inside the null |

**Four pre-registered experiments, four answers, no strategy.**

And one genuinely positive finding underneath them: **the market is not efficient at a one-day
horizon.** Positioning data carries a real, statistically detectable directional signal —
[0.5063, 0.5404], excluding a coin flip. Genesis measured it.

It is worth about 2.4 percentage points of accuracy over chance, and it costs 4 bps per round
trip to act on, and **those two numbers do not meet.** Not by a lot. By 0.4 points.

### What remains untested

- **VPIN proper**, volume-bucketed, from tick data. The taker ratio used here is a 5-minute
  volume ratio and is a weaker instrument. Kitvanitphasu et al. (2026) find VPIN predicts price
  *jumps*; whether it predicts *sign* is unestablished.
- **Non-linear models**, still locked: §3 of both directional contracts permits them only after
  a linear model clears a bar. None has.
- **A lower fee tier.** The bar is a function of cost. At futures VIP 9 the round trip falls
  from 4 bps to 1.7 bps and the 1-day bar falls from 52.8% to roughly 51.2% — which **G5's
  0.5242 would clear.** That is not a result and must not be reported as one: it requires a fee
  tier Genesis does not hold, and it is exactly the kind of retrospective threshold move the
  contracts forbid. **It is recorded as the single most valuable open question**, and it needs
  its own declaration.
