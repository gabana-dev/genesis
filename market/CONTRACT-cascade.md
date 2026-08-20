# CASCADE-1 — does forced liquidation move price, and for how long?

**Status: FROZEN 2026-08-20, before any outcome was computed.** Declared by Gabana. No cohort
threshold, horizon, benchmark, prediction or kill condition below may be changed after this
point. If a defect is found it is reported and recorded, not silently repaired.

**Classification: MEASUREMENT + IMPORT.** Liquidation-driven price impact is studied in the
literature and sold commercially as heatmaps. No novelty is claimed for the idea. What is
different is stated in §2 and it is narrow.

---

## 1. Why this contract exists

Every liquidation-map product on the market — Coinglass, HyperPerps, 0xArchive, HyperTracker —
shows **where** forced liquidations sit. **Not one publishes whether reaching a cluster does
anything.** Coinglass's own documentation calls it a probability map and attaches no probability.

The commercial question behind the whole data line is therefore unanswered by anyone:
**is forced flow economically consequential, or is it a picture people like looking at?**

## 2. What is different here, stated narrowly

**Not the data.** Binance's `!forceOrder@arr` is public and free.

**The design.** Liquidations are *events*, not calendar time. The power audit
([`../research/POWER-AUDIT-the-daily-lane-is-unpowerable.md`](../research/POWER-AUDIT-the-daily-lane-is-unpowerable.md))
established that daily-horizon questions need decades because one instrument yields one
observation per day. **Events escape that**, though by less than the raw counts suggest. The recording holds 48,104
liquidations across 757 symbols in 37.3 hours, but §5 shows that at any notional large enough to
matter these collapse to a few hundred *episodes* across a few dozen symbols. The escape is real
and it is roughly **an order of magnitude, not three** — days instead of decades, not minutes.

What genuinely helps is the second half: **the effect is large by construction**, because forced
flow is an actual market order rather than a statistical whisper, and required observations fall
as the square of effect size.

## 3. The question

> **After a large forced liquidation, does price continue in the direction the forced flow
> pushed it, over the following seconds to minutes, by more than the cost of acting?**

A forced SELL is a market sell; if it moves price down and price keeps falling, that is
continuation. If price reverts, the liquidation was absorbed and the map is decoration.

## 4. Data

**Source:** the `q5` recording, `~/genesis-evidence/q5/btcusdt-q5.jsonl`, `forceOrder` channel —
Binance USD-M market-wide, hash-chained, with completeness labels.

**Prices:** Binance 1-minute klines per affected symbol, free from `data.binance.vision` and the
public API. Fetched per symbol; no vendor, no cost.

**Event definition:** one `forceOrder` order with venue time `T`, symbol, side, average price and
quantity. **Notional = quantity × price.**

**Measured distribution, from the existing recording** (events, before episode collapse — see §5):

| | |
|---|---|
| all events | 48,104 across 757 symbols, 37.3 h |
| median notional | $310 |
| p99 notional | $305,036 |
| **≥ $250k** | **559 events (15.0/hour)** |
| **≥ $1M** | **234 events (6.3/hour)** |
| sides | 25,237 SELL / 22,867 BUY |

**Cohort: three declared notional strata**, because §5 shows the trade-off between effect size
and observation count is the whole design, not a detail to tune later.

## 5. Power — mandatory, and it corrected this contract before it was frozen

Adopted as standing practice after the power audit. **No contract freezes without this.**

**The first draft of this section was wrong in exactly the way the audit warned about.** It
claimed 234 independent events at ≥$1M across 757 symbols. Both numbers were inflated:

- **90% of large events fall within 60 s of another** — they are cascade *episodes*, not
  independent draws
- at ≥$1M the events sit in **12 symbols**, not 757. The breadth is at the small end, where the
  notional is $310 and nothing can move

Collapsing to episodes (same symbol, same side, ≥60 s apart) gives the honest picture:

| stratum | events | symbols | **episodes** | smallest detectable hit rate |
|---|---|---|---|---|
| ≥ $1M | 234 | 12 | **80** | **0.657** |
| **≥ $250k** | 559 | 27 | **170** | **0.607** |
| ≥ $50k | 1,554 | 75 | **570** | **0.559** |

**Primary stratum: ≥ $250k.** The other two are declared secondaries, family-corrected across
three, and they are what makes C3 testable rather than a fishing grid.

**Time to better power:** episodes accrue at ~4.6/hour at ≥$250k. q5 runs to roughly 24 August
on current disk, which would take the primary stratum to about **500 episodes, detecting 0.563**.

**Independence is measured, never assumed.** K3 requires effective breadth by the
participation-ratio method used on the cross-section holon, and the measured value is the
effective n in every interval.

## 6. Endpoint and benchmarks

**Primary: mean net return in the forced direction over the horizon, in bps, after costs** — not
hit rate. GEN-1 established that a bar near 0.50 is clearable by accident.

**Horizons: 1, 5 and 15 minutes.** Three declared, family-corrected, non-substitutable.

**Benchmarks, per the hierarchy in
[`../research/next-phase-review-2026-08-19.md`](../research/next-phase-review-2026-08-19.md) §8:**

- **Tier 0 — luck.** Sign permutation, 10,000 draws, must exceed the p95.
- **Tier 1 — cost.** Must survive the full cost stack at the traded venue.
- **Tier 2 — matched control.** **Random timestamps in the same symbol within the same hour**,
  matched on realised volatility. This is the load-bearing benchmark: liquidations happen when
  markets are already moving, so an unmatched comparison measures volatility clustering and
  calls it causation.
- **Tier 3 — competent incumbent.** A same-size *ordinary* aggressive trade in the same symbol
  and hour. If forced flow is no different from any large market order, there is nothing specific
  about liquidation here and the map adds nothing over trade size.

**A result must clear all four.**

## 7. Predictions

- **C1.** Continuation is positive at 1 minute and decays by 15 minutes.
- **C2.** Tier 3 **fails** — forced flow behaves like any large aggressive order of the same size.
  *This is my expectation, and it is the prediction that matters commercially:* if true, the
  liquidation map adds nothing that trade size does not already say.
- **C3.** Effect scales with notional relative to the symbol's typical volume.
- **C4.** Effect is larger in thin symbols than in BTCUSDT.
- **C5.** Net of costs, the 1-minute effect is **not** capturable at a 291 ms latency floor.

## 8. Kill conditions

- **K1.** No read before **170 episodes in the primary ≥$250k stratum**, episodes defined as
  same symbol, same side, separated by ≥60 s. **Events are not observations.**
- **K2.** If Tier 2 fails — no better than volatility-matched random times — the map is reported
  as **describing volatility, not causing it**, and the line closes.
- **K3.** Effective breadth is measured, not assumed, and used as the effective n everywhere.
- **K4.** If Tier 3 fails, the finding is reported as **"large trades move price"**, which is
  established and not ours, and no liquidation-specific claim is made.
- **K5.** Any change to cohort threshold, horizons, or benchmarks voids the run.
- **K6.** Completeness labels are restated on every figure; intervals the recorder marked
  incomplete are excluded and the exclusion is counted.

## 9. What this cannot establish

One venue. Thirty-seven hours at declaration. Says nothing about Hyperliquid, whose liquidation
mechanics and HLP backstop differ. Says nothing about whether a *cluster* is reached — only what
happens once one fires.

## 10. Why it is worth running even though C2 predicts failure

**It is the only cheap decisive test of the commercial question**, it uses data already recorded
at zero marginal cost, and it is the first question in this project with enough independent
observations to be answerable in days rather than decades.

If C2 holds, the entire liquidation-data line closes on evidence and months are saved. If C2
fails, we have a measured, publishable finding that no vendor selling these maps has produced.
