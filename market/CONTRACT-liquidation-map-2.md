# LIQ-2 — the forced-flow map, with a scan set selected on the right thing

**Status: FROZEN 2026-08-19, before any LIQ-2 snapshot has been taken.** No scan rule, bucket,
horizon, threshold, prediction or kill condition below may be changed after this point.

**Classification: MEASUREMENT, descriptive primary. IMPORT for the secondary.** Supersedes
[`CONTRACT-liquidation-map.md`](CONTRACT-liquidation-map.md), closed at 5.8% coverage — see
[`../research/liq-1-closed-scan-set-too-narrow.md`](../research/liq-1-closed-scan-set-too-narrow.md).

> ## AMENDMENT 1 — 2026-08-19, before any LIQ-2 snapshot has been taken
>
> **Two factual errors in §2.2, found while implementing it. Both are corrected here rather than
> in code, and both enlarge the scan set.**
>
> **The population was misnamed.** §2.2 said the deep scan covers "every wallet in the harvest
> set (2,701 at declaration)". The harvest set is the wrong object and the number was wrong
> twice over: `hl_harvest` completed **200 wallets**, which is LIQ-1's failure exactly. The
> population is instead **every distinct wallet appearing in the `hl1` trade recording — 5,395**,
> measured at declaration. Harvesting fills for a wallet is expensive; reading its
> `clearinghouseState` is one request, so there is no reason to inherit the harvester's limit.
>
> **The deep scan is slower than stated.** §2.2 said ~70 minutes. At the measured rate — LIQ-1's
> 200-wallet scan took 317 s, so **1.585 s/wallet** — 5,395 wallets take roughly **2 hours 22
> minutes**. The 6-hour cadence is unchanged and still fits with margin; only the claim about
> duration was wrong.
>
> **The universe is frozen at first deep scan and never regrown.** The recording keeps
> accumulating wallets. A population that grew with it would make coverage incomparable across
> snapshots — the denominator would stay the exchange while the numerator quietly widened, and a
> rising coverage figure would mean nothing.

---

## 1. What LIQ-1 got wrong, and it is the whole reason for this contract

LIQ-1 scanned **the 200 most active wallets**. Measured against the exchange:

| | |
|---|---|
| exchange BTC open interest | $2,580,544,188 |
| held by the scan set | $150,195,992 |
| **coverage** | **5.8%** |

Appearance count selects for **wallets that trade often** — market makers, with flat books and
distant liquidation prices. The wallets whose liquidations matter trade *rarely* and hold size.
**The selection rule was anti-correlated with the quantity being measured.**

LIQ-2 selects on **position notional**, which is the thing that determines forced-flow
magnitude. That is not selection on the outcome: it is selection on the input.

## 2. The two hard caveats, and what is actually done about each

### 2.1 Traders move the goalposts

A trader approaching liquidation can deposit margin and push the price away. **The map is a
moving snapshot, not a calendar.**

**What LIQ-1 did:** measured the instability (L5) and killed the contract if it exceeded 50%
(K3). That is detection, not handling.

**What LIQ-2 adds:** `withdrawable` is collected on every position. It is the direct measure of
capacity to move the goalpost — a wallet with free collateral can top up; one with
`withdrawable` near zero cannot, from inside the account.

The map is therefore reported **twice**: raw, and **credibility-weighted**, where a position's
forced notional is discounted by that wallet's ability to escape:

```
credible_notional = forced_notional × 1 / (1 + withdrawable / maintenance_margin)
```

A wallet with no free collateral counts at full weight. One with ten times its maintenance
requirement sitting idle counts at roughly a tenth. **The raw map is the primary and the
weighted map is reported alongside it** — the weighting is a declared hypothesis about
behaviour, not a measurement, and it does not get to quietly become the headline.

**`clearinghouseState` has no history.** A field not collected now is unrecoverable, which is
why this is a new contract rather than a later refinement.

### 2.2 The speed limit

The info endpoint is a **token bucket**: roughly 1.9 requests/second briefly, then HTTP 429
after ~70 cumulative requests regardless of spacing. Measured, not assumed. A 200-wallet scan
took **317 seconds**; a full 2,700-wallet scan would take roughly **70 minutes**.

**LIQ-2 scans in two tiers**, which is the intelligent-filtering answer:

- **DEEP scan, every 6 hours:** every wallet in the harvest set (2,701 at declaration). Its only
  job is to re-rank by position notional. ~70 minutes, four times a day.
- **FAST scan, hourly:** the **top 300 by position notional** from the most recent deep scan.
  ~8 minutes.

**The ranking rule is mechanical and admits no discretion:** top 300 by `|szi| × liquidationPx`
at the last deep scan. It is re-derived every 6 hours by that rule alone, never by judgement,
and the rule itself is fixed here.

**Why re-ranking is legitimate here and drift was not in LIQ-1.** The objection to a moving scan
set is selection on the *outcome*. Position notional is not an outcome — it is the input that
determines how much forced flow a wallet contributes. A set that failed to track it would
measure the wrong wallets, which is exactly what LIQ-1 did.

## 3. Coverage is a reported number, not an assumption

**Every snapshot reports measured coverage**: scanned position notional divided by exchange BTC
open interest, from `metaAndAssetCtxs`. LIQ-1's failure was invisible until this was computed,
and it is now a first-class output rather than a check somebody might run.

**K2 requires coverage above 25%** on the deep scan. Below that the map is reported
**unevaluable** — a map of a twentieth of the exchange is not a map.

## 4. The map

Unchanged from LIQ-1 §4, and restated so this contract stands alone. Per snapshot, per wallet
with an open BTC position: `liquidationPx`, `szi`, `accountValue`,
`crossMaintenanceMarginUsed`, **`withdrawable`**, leverage, entry.

**A short liquidates by BUYING, a long by SELLING.** Aggregated into **0.5% buckets** out to
**±10%** of spot.

## 5. Endpoints

**PRIMARY — descriptive.** The map: total forced notional within ±10% raw and
credibility-weighted, distance to the nearest bucket above **$1M**, distribution across
buckets, and **measured coverage**.

**SECONDARY — one directional test.** Normalised imbalance within ±5% against the forward
**1-hour** return.

**Family LIQ-2 = 1 declared trial.** One imbalance definition, one horizon, one test. Bucket
width, range, imbalance window, dense threshold and the weighting formula are all fixed here.

## 6. Predictions

- **M1.** Deep-scan coverage exceeds 25% — the harvest set holds a materially larger share than
  LIQ-1's activity-selected 200. *If this fails, K2 fires and the approach needs a different
  wallet source entirely.*
- **M2.** The map is sell-heavy most of the time: forced sell below spot exceeds forced buy
  above, because retail is structurally long. *LIQ-1's single snapshot showed −0.280, which is
  one observation and not evidence.*
- **M3.** Cluster density is concentrated: the largest single 0.5% bucket holds more than 25% of
  forced notional on its side.
- **M4.** The credibility-weighted map is **materially smaller** than the raw map — more than
  40% smaller within ±5% — because most wallets carry free collateral and can escape.
- **M5. The secondary test is NOT significant.** The map is public and commercially productised;
  any first-order effect should already be priced. *This remains my expectation.*
- **M6.** More than 20% of liquidation prices move between consecutive hourly fast scans, and
  the movers are disproportionately wallets with high `withdrawable` — the goalpost caveat is
  real and predictable from the collateral buffer.

## 7. Kill conditions

- **K1.** No secondary read before **270 hourly observations spanning at least 30 distinct
  days.** Both, because 270 overlapping hours inside 11 days is 11 independent observations.
- **K2.** Deep-scan coverage below **25%**: the map is **unevaluable** and the secondary is not
  computed.
- **K3.** If more than **50%** of liquidation prices move between consecutive fast scans, the map
  is reported **too unstable to act on** and the secondary is not computed.
- **K4.** A significant secondary may **not** be called tradeable without a separate cost
  analysis at the 1-hour horizon. MEASURE-1 put that break-even at **66.9%** under the old cost
  stack, so a statistically significant effect there is very likely uneconomic.
- **K5.** Measured coverage is restated on every reported figure.
- **K6.** Any change to the scan rule, buckets, weighting formula or horizon voids the run.

## 8. Known limitations

**The harvest set is not the exchange.** Wallets come from Genesis's own recording, so wallets
that never traded during it are invisible however large their positions. Coverage measures how
much this costs and K2 makes it binding.

**The weighting formula is a hypothesis.** It encodes a belief that escape capacity scales with
free collateral relative to maintenance margin. It is reported alongside the raw map and never
instead of it.

**Cross-margin complicates attribution.** A wallet's BTC liquidation price depends on its whole
cross-margined book, so a position in another asset can move the BTC number without any BTC
activity. This is visible in the data and not modelled.

**One asset, one venue.**

## 9. Out of scope

No strategy, no sizing, no live order, no cascade trading, no agent.
