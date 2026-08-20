# CASCADE-1 — does forced liquidation move price, and for how long?

**Status: DRAFT, not frozen.** Awaiting Gabana. No outcome has been computed and none may be
until this is frozen and hashed.

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
observation per day. **Events escape that**: the recording already holds **48,104 liquidations
across 757 symbols in 37.3 hours** — 1,288 per hour — and the effect being tested is large by
construction, because forced flow is an actual market order.

Both escapes MEASURE-1 §8 names — **event-based and cross-sectional** — apply at once.

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

**Measured distribution, from the existing recording:**

| | |
|---|---|
| all events | 48,104 across 757 symbols, 37.3 h |
| median notional | $310 |
| p99 notional | $305,036 |
| **≥ $250k** | **559 events (15.0/hour)** |
| **≥ $1M** | **234 events (6.3/hour)** |
| sides | 25,237 SELL / 22,867 BUY |

**Cohort: events ≥ $1M notional.** Fixed here. The median event is $310 and cannot move
anything; testing it would guarantee a null and waste the sample.

## 5. Power — mandatory section, and the reason this contract is worth running

Adopted as standing practice after the power audit. **No contract is frozen without this.**

For a continuation hit rate at 80% power, α = 0.05 two-sided:

| effect to detect | independent events needed | collection time at 6.3/hour |
|---|---|---|
| 60% vs 50% | **196** | **31 hours — already have 234** |
| 55% vs 50% | 784 | ~5 days |
| 52.5% vs 50% | 3,136 | ~21 days |

**The existing recording already powers the 60% question.** Five days of collection powers 55%.

**Independence:** events span 757 symbols, so simultaneous liquidations in different symbols are
far closer to independent than repeated observations of one instrument. **This is not assumed.**
K3 requires the effective breadth of the event set to be measured and reported, by the same
participation-ratio method used on the cross-section holon, and the effective n used in every
interval is the measured one, never the raw count.

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

- **K1.** No read before **196 events at ≥$1M** with measured effective breadth ≥ 20.
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
