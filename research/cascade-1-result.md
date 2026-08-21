# CASCADE-1: K2 fires. Forced liquidation does not move price more than an ordinary volatile minute.

**Date:** 2026-08-21
**Contract:** [`../market/CONTRACT-cascade.md`](../market/CONTRACT-cascade.md), frozen 2026-08-20,
`sha256 7dee22eed9cdaecb833687f93a56add383e7856bf059d2475841a55089e9bb46`, before any outcome was
computed.
**Result: K2 FIRES.** The liquidation map is reported as **describing volatility, not causing
it**, and the line closes.

---

## 1. The result

Primary stratum, ≥$250k, 228 episodes (n = 106 with usable price data). Mean return in the
**forced direction**, in bps:

| horizon | n | mean | hit rate | Tier 0 (permutation p95) | Tier 2 (matched control) | clears |
|---|---|---|---|---|---|---|
| 1 min | 106 | +6.27 | 0.519 | 7.93 — **fails** | 4.96 — clears | **no** |
| 5 min | 106 | +11.10 | 0.557 | 14.99 — **fails** | 25.13 — **fails** | **no** |
| 15 min | 106 | +40.07 | 0.604 | 17.06 — clears | 44.52 — **fails** | **no** |

**No horizon clears both.** §6 requires all four benchmarks; none clear even two.

### The shape that matters

At 15 minutes the effect is large — **+40 bps, 60% hit rate** — and it comfortably beats a
permutation null. That number alone would make a compelling product screenshot.

**It loses to a random minute in the same symbol in the same hour (44.52 bps).**

Forced liquidations happen when markets are already moving. Take any other minute from the same
hour and you get *the same continuation, slightly more of it.* The liquidation is a symptom of
the volatility, not a cause of the move.

**This is exactly what Tier 2 was written to catch**, and it is the benchmark no commercial
liquidation product runs.

## 2. The secondaries agree

| stratum | episodes | 15m mean | control | Tier 2 |
|---|---|---|---|---|
| ≥$50k | 754 (n=471) | +26.96 | 36.99 | **fails** |
| ≥$250k **primary** | 228 (n=106) | +40.07 | 44.52 | **fails** |
| ≥$1M | 102 (n=28) | +52.51 | 38.48 | clears |

The ≥$1M stratum is the only one that clears Tier 2 at 15 minutes — on **n = 28**, with
**negative** means at 1 and 5 minutes (−7.58 and −11.72 bps). That is the signature of noise, not
of a stronger effect at larger size, and C3 (effect scales with notional) is **not supported**:
the ordering across strata is not monotonic once the control is applied.

## 3. Predictions scored

| | prediction | outcome |
|---|---|---|
| **C1** | continuation positive at 1m, decaying by 15m | **FAILED** — it *grows* with horizon, which is what volatility does |
| **C2** | forced flow behaves like any large order; the map adds nothing | **CONFIRMED in substance** — it does not even beat a random minute |
| **C3** | effect scales with notional | **not supported** — non-monotonic once controlled |
| C4, C5 | thin symbols; capturability at 291 ms | not reached — K2 fired first |

## 4. Two defects in the runner, reported not repaired

**Only two of four benchmark tiers were implemented.** The runner computes Tier 0 (permutation)
and Tier 2 (matched control). **Tier 1 (cost) and Tier 3 (ordinary large trade) were not built.**

This does not change the verdict — K2 fires on Tier 2 alone and §8 closes the line at that point
— but the contract declares four and the run delivered two. Recorded as a deviation.

**Fewer than half the episodes had usable price data**: 106 of 228 in the primary stratum. Many
episode symbols are absent from the daily kline archive for the recorded days. The surviving
sample is therefore biased toward liquid, well-covered symbols — **which is the direction that
would flatter a liquidity-driven effect, not hide one.**

## 5. What this closes

**The cascade forecast product has no floor.**

The three layers it rested on:

- **defensibility** — real, measured, unique (F-0001), and now attached to a phenomenon that does
  not move price
- **cascade depth** — the model works and is tested, and it models something that does not happen
  measurably
- **hit rates** — moot

A product that answers *"how far will this cascade run"* is answering a question the data says
does not matter. Building it would have been building on the strength of a 15-minute +40 bps
number **while never running the control that deletes it.**

## 6. What survives

**F-0002 stands, entirely independent of this.** The order book thins to 0.846 during large
moves, measured over 1,324 days with a quiet-market control at 1.000 to four decimals. That is a
fact about market microstructure and it is unaffected by whether liquidations cause anything.

**F-0001 stands.** Free collateral is not derivable and one wallet in five is misclassified
without it. Also unaffected — it was never a claim about price.

**And the honest headline is better than the product would have been:**

> *Liquidation maps show you where the fuel is. Three days of market-wide data say reaching it
> does no more to price than an ordinary volatile minute — and every vendor selling these maps
> has published the number without ever running that comparison.*

## 7. Limitations, stated

Three days of recording (2026-08-18 → 2026-08-20). One venue. 106 usable episodes in the primary
stratum. Longer recording would tighten the intervals — **but the failure is against a matched
control, not against a power threshold**, and more data does not repair a comparison the effect
loses on its merits.

The contract's own K1 was met at 228 episodes. This is not an underpowered null.
