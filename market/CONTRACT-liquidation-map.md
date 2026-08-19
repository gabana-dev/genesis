# LIQ-1 — the forced-flow map: who must trade, and at what price

**Status: FROZEN 2026-08-19, before any snapshot has been taken.** No scan set, bucket, horizon,
threshold, prediction or kill condition below may be changed after this point. If a defect is
found it is reported and recorded, not silently repaired.

**Classification: MEASUREMENT, descriptive primary. IMPORT for the secondary.** Liquidation
heatmaps are a commercial product. No novelty is claimed for the idea; §2 states precisely what
is different here and it is narrower than it sounds.

---

## 1. What this is

Hyperliquid's `clearinghouseState` endpoint is **public, per wallet, and live**. Verified
2026-08-19 on wallets taken from Genesis's own recording:

```
0x6e8bc7cd09   short 9.18 BTC @ 64,405   16x cross
               liquidationPx 68,142      accountValue $41,469
```

That wallet is a **forced buyer at 68,142**, against a spot near 64,300, and the fact is on the
public record before anything happens.

> **LIQ-1 asks: aggregated across wallets, does the map of who must trade and at what price tell
> us anything about how price behaves?**

**This is not a prediction of information. It is a reading of obligation.** The liquidation
engine fires when price touches a level. It does not fire faster for a faster participant, which
is why this is the one line in the project where Genesis's 291 ms floor is irrelevant by
construction.

## 2. What is genuinely different, stated narrowly

**Liquidation heatmaps are sold commercially** — Coinglass, Hyperdash and others. Anyone can
look, and this is not an unexploited idea.

The difference is one thing only: **those products ESTIMATE clusters from aggregate open
interest and assumed leverage. LIQ-1 computes them EXACTLY, per wallet, from the venue's own
`liquidationPx`.**

Whether exact beats estimated by enough to matter is unknown, and is not assumed anywhere in
this contract. If the answer is no, that is a finding.

## 3. Data — and why there is no snooping risk

`clearinghouseState` is a **snapshot**. There is no historical version and it **cannot be
backfilled**. Every observation LIQ-1 uses will be collected after this contract was frozen.

That is unusually clean: no survivorship, no data reuse, no forking path, because the data does
not exist yet.

**Scan set:** the **200 most active wallets** in the `hl1` recording, by appearance count.
Fixed at first scan and **never re-selected** — re-ranking mid-experiment would let the scan set
drift toward whatever is currently interesting.

**Cadence: hourly.** A 200-wallet scan takes roughly ten minutes at the measured token-bucket
rate, so hourly is achievable and 24 observations a day is what makes a read possible this month
rather than next quarter.

**Declared limitation of the scan set.** 200 wallets is a proxy for the exchange, not the
exchange. Forced flow from unscanned wallets is invisible, and the map is therefore a **lower
bound on cluster density everywhere.** Whether the 200 most active wallets carry most of the
forced flow is not established and is not assumed.

## 4. The map

At each hourly snapshot, for every scanned wallet with an open BTC position:

- `liquidationPx`, `szi` (signed size), `accountValue`, `crossMaintenanceMarginUsed`
- **forced direction**: a short liquidates by BUYING, a long by SELLING
- **forced notional** = `|szi| × liquidationPx`

Aggregated into **0.5% price buckets** from spot, out to **±10%**:

```
forced_buy(b)   = sum of forced notional from shorts with liquidationPx in bucket b above spot
forced_sell(b)  = sum of forced notional from longs  with liquidationPx in bucket b below spot
```

## 5. Endpoints

**PRIMARY — descriptive.** The map itself, reported per snapshot: total forced notional within
±10%, distance to the nearest bucket exceeding **$1M** of forced flow on each side, and the
distribution across buckets.

**No hypothesis is tested by the primary.** It answers "what does this look like", which nothing
in Genesis has ever measured.

**SECONDARY — one directional test, and only one.** The normalised imbalance

```
imb(t) = (forced_buy within 5% − forced_sell within 5%) / (forced_buy + forced_sell)
```

against the **forward 1-hour return**. One horizon, chosen because liquidation cascades resolve
in minutes to hours and a 1-day horizon would average the phenomenon away.

**Family LIQ-1 = 1 declared trial.** One imbalance definition, one horizon, one test. The
grid cannot grow: bucket width, the ±10% range, the 5% imbalance window and the $1M threshold
are all fixed here.

**Reported with it:** a moving-block bootstrap 95% interval, block = 24, and the count of
independent days.

## 6. Predictions

- **L1.** The map is **asymmetric most of the time** — forced-sell notional below spot exceeds
  forced-buy above, because retail is structurally long and long liquidations dominate.
- **L2.** Cluster density is **highly concentrated**: the largest single 0.5% bucket holds more
  than 25% of forced notional on its side. Liquidation prices cluster because leverage settings
  cluster at round multiples.
- **L3. The secondary test is NOT significant.** The map is public and commercially productised,
  so any first-order effect should already be priced. *This is my expectation.*
- **L4.** Forced notional within ±10% is **small relative to daily volume** — under 5% of it — so
  even a full cascade is a modest fraction of a day's flow. If this holds, the phenomenon is
  real and economically minor.
- **L5.** `liquidationPx` moves materially between snapshots for more than 20% of wallets, as
  traders add or remove margin. **The map is a snapshot, not a schedule**, and L5 measures how
  much of a schedule it is at all.

## 7. Kill conditions

- **K1.** No secondary read before **270 hourly observations spanning at least 30 distinct
  days.** Both conditions, because 270 overlapping hours inside 11 days is 11 independent
  observations and the interval would be a fiction.
- **K2.** If fewer than 50 scanned wallets hold an open BTC position at a typical snapshot, the
  map is **unevaluable** and reported as such — a scan set that is mostly flat measures nothing.
- **K3.** If L5 shows more than 50% of liquidation prices moving between consecutive hourly
  snapshots, LIQ-1 reports the map as **too unstable to act on**, and the secondary is not
  computed. A schedule that rewrites itself hourly is not a schedule.
- **K4.** If the secondary is significant, it may **not** be reported as tradeable without a
  separate cost analysis at the 1-hour horizon. MEASURE-1 put the 1-hour break-even at **66.9%**
  under the old cost stack; a significant statistical effect there is very likely uneconomic and
  must be priced before it is called an edge.
- **K5.** The §3 scan-set limitation is restated on every reported figure. The map is a lower
  bound on cluster density.

## 8. Why this is worth running even though L3 predicts failure

Three reasons, all independent of the secondary test.

**It is the missing ground truth for COND-1's conditioner C.** That conditioner infers
liquidation cascades from trade-stream signatures because Binance samples its liquidation feed.
Here the positions are visible beforehand.

**It is a cost-conditioning variable.** Quoting into a dense cluster is a different proposition
from quoting into an empty book, and Genesis has never been able to tell the difference.

**It measures something nobody in this project has looked at.** Every prior contract asked
whether the market could be predicted. This asks what the market is *obliged* to do, which is a
question with an answer that does not depend on anyone being clever.

## 9. Out of scope

No strategy, no sizing, no live order, no cascade trading, no agent. LIQ-1 builds a map and runs
one test against it.
