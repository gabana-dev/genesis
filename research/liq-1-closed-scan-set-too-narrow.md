# LIQ-1 closed: the scan set sees 5.8% of the exchange, and it was selected on the wrong thing

**Date:** 2026-08-19
**Status:** LIQ-1 CLOSED after one snapshot and zero analysis
(`sha256 f5c54584e46c4e942e288852158602a99ec9a07182566222996bb41fb29d4bb3`). Superseded by
[`../market/CONTRACT-liquidation-map-2.md`](../market/CONTRACT-liquidation-map-2.md),
`sha256 3ec70684b2aec79882191cb8393a22239a7c5c86821930c9cf60f6441639a800`, frozen with
Amendment 1 before any LIQ-2 snapshot was taken.

---

## 1. The measurement that closed it

LIQ-1's scan set was **the 200 most active wallets by appearance count** in the `hl1` trade
recording. One snapshot, then this check:

| | |
|---|---|
| exchange BTC open interest | **39,890.9 BTC — $2,580,544,188** |
| held by the scan set | **2,330.0 BTC — $150,195,992** |
| **coverage** | **5.8%** |

**The map saw one twentieth of the forced flow, and the ninety-four percent it missed is not
random.**

## 2. Why activity was the wrong selection criterion

Appearance count in a trade feed selects for **wallets that trade often**. On a perpetual
exchange those are disproportionately market makers — high turnover, tight inventory, flat or
near-flat books, and liquidation prices far from spot precisely because they do not carry
directional risk.

**The wallets whose liquidations matter are the opposite**: leveraged directional traders who
trade rarely and hold size. They appear in the tape less often per dollar of position than any
market maker.

So the selection rule was **anti-correlated with the quantity being measured.** 127 of 200
scanned wallets did hold a BTC position, which looked reassuring and was not — the positions
were there, they were simply small.

This was declared in the contract as *"a proxy for the exchange, not the exchange"* and
*"a lower bound on cluster density"*. **Declaring a limitation is not the same as it being
acceptable**, and 5.8% is not acceptable for a map whose entire purpose is completeness.

## 3. A second gap, and this one loses data permanently

`clearinghouseState` returns **`withdrawable`** — free collateral. LIQ-1 stored `accountValue`
and `crossMaintenanceMarginUsed` but **not** `withdrawable`.

That field is the direct measure of the first hard caveat: **can this trader move the
goalposts?** A wallet with substantial free collateral can top up margin and push its
liquidation price away. A wallet with `withdrawable` near zero cannot do so from inside the
account.

**`clearinghouseState` has no historical version.** Every hour collected without that field is
an hour in which the credibility of each liquidation price is permanently unrecoverable.

## 4. Why this is a closure and not an amendment

The precedent is CAP-1. That contract was frozen, found to rest on an instrument that could not
answer its question, and **closed rather than amended** — CAP-2 was declared fresh.

The same applies here, and one further reason: **expanding a scan set mid-flight breaks
comparability across snapshots.** A time series whose population changes partway through is two
series pretending to be one. Since only one snapshot exists and no analysis has been run,
restarting costs an hour.

LIQ-1's predictions are **not** scored. Its single snapshot is retained as evidence and is not
used.

## 5. What carries forward

The finding that made LIQ-1 worth declaring is untouched: **`liquidationPx` is public per
wallet, forced flow is a published obligation rather than an inference, and the liquidation
engine does not fire faster for a faster participant.** That remains the one line in this
project where the 291 ms floor is irrelevant by construction.

What changes is only the instrument — and the 5.8% figure is itself the most useful number
LIQ-1 produced, because it says exactly how wrong a naive scan set is.
