# The Hyperliquid data market: what exists, and the one gap nobody fills

**Date:** 2026-08-20
**Method:** every claim below was fetched from the provider's own docs, not inferred from a
landing page or a search snippet. Where a provider does not disclose something, it is marked
**not disclosed** rather than assumed absent.

---

## 1. The field, verified

| provider | what they sell | account-level data? | history from |
|---|---|---|---|
| **Tardis** | trades, `l2Book` 20 levels ~5.4 s, `fastBook` 5 levels ~500 ms (since 2026-06-17), `bbo` (since 2025-06-26), funding + OI | **no** | **2024-10-29** |
| **QuickNode** | trades, orders, **L4 book**, book diffs, **TWAP**, **TP/SL updates**, blocks, mempool, gossip | **no** | not disclosed |
| **0xArchive** | trades (2023-04-19), **L4 book with wallet identity** (2026-03-10), order lifecycle, candles, liquidation **events**, L2 books (2023-04-15), funding + OI (2023-05-20) | **no** | **2023-04** |
| **PurrData** | liquidation **events**, $50–300/mo | no | not disclosed |
| **Coinglass** | 150+ endpoints, **estimated** heatmaps from OI + assumed leverage, $35–879/mo | no — estimates | — |
| **HyperPerps** | **exact** forward liquidation map, free, cross-margin excluded by design | live only, **no history** | none |
| **HRC** | institutional research reports, free by email | n/a | — |

**Two of these are richer than anything Genesis records.** 0xArchive's L4 book carries *order-level
identity with wallets* from 2026-03-10. QuickNode streams the mempool and TP/SL updates. On market
microstructure we are behind, and there is no point competing there.

## 2. The gap

**Not one provider sells account state.** No positions, no exact liquidation prices, no margin, no
account value, no free collateral.

Everyone covers what the market *did*. Nobody covers what the participants *hold*.

## 3. Why the gap persists — and it is structural, not an oversight

Every vendor above is built on **stream capture**: connect a WebSocket, write what arrives.
That architecture is why they all have books and trades from 2023–2024 and why their coverage
is deep and cheap.

`clearinghouseState` breaks that model in three ways:

1. **It is a poll, not a stream.** One REST request per wallet. There is no subscription and no
   bulk endpoint, so it cannot be captured by connecting to anything.
2. **It requires a wallet universe you must discover yourself** — from the trade tape, over time.
   The universe is the hard part, and it is the part we got wrong twice before measuring it
   properly at 31,349 wallets.
3. **It has no history and cannot be backfilled by anyone, ever.** A vendor deciding tomorrow to
   add it starts at zero, exactly like us.

That third point is the whole opportunity. **Every other dataset on that table can be bought by a
competitor at any time. This one can only be accumulated.**

## 4. What account state makes possible that order flow cannot

Order flow tells you who traded. Account state tells you who is **exposed**, which is a different
question and is the one that matters for risk:

- **Exact forward liquidation map**, per wallet, from the venue's own engine — not Coinglass's
  leverage assumption, and unlike HyperPerps it need not exclude cross-margin
- **Defensibility**: 48% of wallets with open positions hold **zero** free collateral and cannot
  push their liquidation price away. Nobody computes this. It is the difference between a cluster
  that is real and one that evaporates
- **Cascade depth**: forced size at a level, met with book depth, gives where a cascade stops.
  Requires positions *and* book — the book half is free from the venue's own WebSocket
- **Position deltas**: "this wallet went from flat to 40× long in an hour" is visible directly,
  rather than inferred from fills
- **Exchange risk**: HLP takes the other side of liquidations. Aggregate account state is the
  input to modelling that exposure, and nobody publishes it

## 5. Free inputs, verified

Every input is free. The cost is compute, storage and uptime, not data:

| | |
|---|---|
| Hyperliquid `info` API (`clearinghouseState`, trades, meta) | free, rate-limited (~1.9 req/s, 429 after ~70) |
| Hyperliquid L1 explorer (`rpc.hyperliquid.xyz/explorer`) | free |
| Hyperliquid WebSocket (book, trades) | free |
| `data.binance.vision` archives | free |
| 0xArchive | "start free" |
| HyperPerps map | free, public |

## 6. Coverage, measured

**53.3%** of exchange BTC open interest, 95% CI **[40.9%, 70.8%]**, on a 31,349-wallet universe —
and still rising, because the universe is activity-derived and the recording keeps discovering
wallets. See [`coverage-measured-53-percent.md`](coverage-measured-53-percent.md).

## 7. The positioning nobody occupies

Reading all seven providers' documentation, **not one publishes a coverage or completeness
figure.** Tardis names its infrastructure location and points at a status dashboard. QuickNode
warns only that volume varies. The rest say nothing.

They all present a complete-looking picture and let the buyer discover the holes.

**Genesis's completeness machinery is the only thing here that is genuinely unusual**, and it
happens to be the thing a quantitative researcher most needs, because a backtest run on silently
holed data produces confident nonsense.

## 8. What remains unverified

Recorded so it is not quietly assumed later:

- **Dwellir** and the **Kaggle 5-minute DEX order book** set — not yet fetched
- Whether **0xArchive's L4 wallet identity** already permits reconstructing positions from order
  flow. **This is the single most dangerous open question**: if positions can be derived from
  their L4 feed, the gap in §2 is much smaller than it looks
- Whether anyone archives account state privately without selling it
- Whether Hyperliquid will publish account-state history itself
- Whether researchers pay a premium for disclosed coverage, or merely say they value it
