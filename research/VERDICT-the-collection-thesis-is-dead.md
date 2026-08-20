# Verdict: the collection thesis is dead. HyperTracker already sells it, with 16 months of history.

**Date:** 2026-08-20
**Supersedes** the core claim of
[`hyperliquid-data-market-map.md`](hyperliquid-data-market-map.md) and its correction. This is
the fourth inversion in one session and the one that closes the line.

---

## 1. The finding

I claimed no provider sells per-wallet account state. **HyperTracker sells exactly that**, from
its own endpoint documentation:

```
id, address, coin, side, dex, size, value, entryPrice, unrealizedPnl, funding,
liquidationPrice, liquidationProgress, crossLeverage, isolatedLeverage, openTime,
profile_totalEquity, profile_perpEquity, profile_countOpenPositions, profile_pnl,
profile_balance, ...
```

| | HyperTracker | Genesis |
|---|---|---|
| coverage | **complete market-wide**, "tens of thousands of positions" | **53.3%**, CI [40.9%, 70.8%] |
| snapshot frequency | **every 15–20 min** | hourly / 6-hourly |
| history from | **2025-04-04** (16 months) | 2026-08-19 (1 day) |
| liquidation price | yes, and *evolving* since 2025-09-02 | yes |
| API | REST, WebSocket, webhooks | none |
| pricing | $179 / $399 / $799 / $1,999 per month | — |

**They are ahead on every axis that matters, by sixteen months.** Entering here means competing
late, with half the coverage, at a slower refresh, against a product that already has paying
customers and an SLA.

## 2. What survives — and it is one field

Their field list does **not** include margin used, and does **not** include
**`withdrawable` / free collateral.**

That is the one thing measured yesterday in
[`withdrawable-is-not-derivable.md`](withdrawable-is-not-derivable.md):

- `withdrawable` matches naive margin arithmetic **19% of the time**
- naive says **96%** of wallets can defend their liquidation price; the venue says **76%**
- **20% of wallets are misclassified**, median overstatement $4,906, maximum $3.6M

So a defensibility metric built on HyperTracker's fields would be wrong for a fifth of wallets,
in the direction of overstating how easily clusters evaporate.

**One field is not a business.** It is, however, the input to something nobody publishes.

## 3. The reframe this forces, and it is cheaper than what we were building

We were building a **collector**. The collector is now redundant — outgunned on coverage,
frequency and history by a product costing $179/month.

What is *not* redundant is the **computation**. Nothing on the market publishes:

- **cluster defensibility** — needs `withdrawable`, which nobody sells
- **cascade depth** — forced size met with book liquidity, giving where a cascade stops
- **empirical hit rates** — how often clusters at a given size and distance are actually reached

And the key operational insight: **`withdrawable` is only needed for wallets near liquidation.**
Not 32,000 wallets — the few hundred whose liquidation price sits within a few percent of spot.
That is **minutes of polling, not a 2h22m deep scan.**

So the shape changes completely:

| | old plan | reframe |
|---|---|---|
| position data | collect it ourselves, 53% coverage | **buy it**, complete, $179/mo |
| free collateral | full scan, hours | **targeted poll of at-risk wallets**, minutes |
| the product | a data feed | **an analytics layer on commodity data** |
| infrastructure | node or scanner, 100 GB/day | a small VPS |
| time to parity | 16 months of collection | **none** |

That inverts the economics. We stop paying to catch up on history we can simply buy, and spend
the effort on the layer nobody occupies.

## 4. What is still unproven, and it is the whole thing

**Nobody has shown that anyone wants the derived layers.** Everything above establishes that they
are *unoccupied*, which is not the same as *valuable*. An empty shelf can mean nobody stocked it
or nobody buys from it.

The cheap decisive test is unchanged and is now cheaper still, because it needs no collection
infrastructure at all: **snapshot clusters, join to forward price, publish the hit rate.** If
clusters at a given size and distance are reached at a rate meaningfully different from chance,
that is a finding nobody has published and the seed of the analytics product. If they are not,
the entire liquidation line closes on evidence rather than on opinion.

## 5. The record

Four claims of mine inverted in one session, in both directions:

| claim | reality |
|---|---|
| universe exhausted at 20.24% coverage | 53.3% on a proper universe |
| Coinglass is free | $35–879/mo |
| nobody publishes coverage metrics | 0xArchive ships them via API |
| nobody sells per-wallet account state | HyperTracker, 16 months, complete coverage |

**Two were too pessimistic and two were too optimistic**, which is the useful pattern: the error
is not bias in a direction, it is asserting without fetching. Recorded in
`feedback_dont_close_early`, and this document is the fourth application of it.

The collection thesis is closed. The computation thesis is open, untested, and an order of
magnitude cheaper to test.
