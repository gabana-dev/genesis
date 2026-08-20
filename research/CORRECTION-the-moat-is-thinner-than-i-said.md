# Correction: three claims I made about the data market were wrong, and the scanner is the wrong instrument

**Date:** 2026-08-20
**Supersedes parts of** [`hyperliquid-data-market-map.md`](hyperliquid-data-market-map.md),
written ninety minutes earlier.

Every correction below comes from the providers' own documentation, fetched. Two of them make
the opportunity smaller. One makes the ceiling much higher.

---

## 1. "Not one provider publishes a coverage figure" — WRONG

**0xArchive publishes data-quality metrics through its REST API**, under `/v1/data-quality/*`:

- a `gaps` field carrying `start`, `end`, `duration_minutes` for every gap
- `completeness_24h` as a 0–100 percentage, per data type
- coverage windows per symbol and per data type
- system-wide and per-exchange status

They also recommend storing quality results alongside market data "to maintain audit trails of
data reliability decisions."

**That is the completeness discipline I described as unique to Genesis, shipped as an API.** The
positioning I proposed — *"every other feed hides its gaps, ours declares them"* — is not
available. Someone is already saying it.

## 2. "Nobody has the exact forward map, and nobody has its history" — WRONG

0xArchive's projected liquidation levels are, in their words, *"computed from clearinghouse
positions and margin state and bucketed around the snapshot mark price."*

**Not estimated from open interest and assumed leverage.** They are reading account state.

| | |
|---|---|
| history retained from | **2026-07-27** |
| refresh | **~45 minutes** |
| granularity | aggregate buckets |

Three and a half weeks of head start, refreshing faster than our hourly fast scan, from a funded
team. Our archive began 2026-08-19.

## 3. "Account state cannot be backfilled by anyone, ever" — WRONG, and this is the big one

A Hyperliquid node writes **`periodic_abci_states` every 10,000 blocks** — roughly every 34
minutes at the measured 4.84 blocks/s. Those snapshots contain the onchain state including
clearinghouse data and user positions, and `hl-node --chain <chain> translate-abci-state
<snapshot> out.json` converts them to JSON.

**Anyone running a node gets every account, natively, with no polling and no rate limit.**

And **Dwellir already archives `replica_cmds` and `periodic_abci_states` back to January 2025.**
The historical account state I said could not exist is sitting in an archive that predates
Genesis by seven months.

## 4. What this does to our instrument

The two-tier scanner was built on the belief that account state is only obtainable by polling
`clearinghouseState` one wallet at a time. That belief was false.

| | our scanner | a node |
|---|---|---|
| coverage | **53.3%**, CI [40.9%, 70.8%] | **100%, by construction** |
| universe discovery | must be inferred from the trade tape | not required |
| rate limits | ~1.9 req/s, 429 after ~70 | none |
| deep scan duration | 2 h 22 m | one file read |
| wallets missed | anyone quiet during the recording window | none |

**We built a careful, rate-limit-aware, completeness-labelled instrument for a problem that a
node solves exactly.** Everything measured with it — the 5.8%, the 20.24%, tonight's 53.3%, the
whole coverage argument — was measuring the limitations of the wrong approach.

The cost is real: **16 vCPU, 128 GB RAM, 500 GB SSD, Ubuntu 24.04, ~100 GB of logs per day.**
That is a dedicated machine, not a small VPS, and it is far beyond the current server.

## 5. What actually survives

Stated narrowly, because the last version of this document was not narrow enough:

**Nobody sells per-wallet account state.** 0xArchive is explicit that its levels are *"aggregate
bucketed estimates, not an account, wallet, or position liquidation-price endpoint."* Verified
absent from Tardis, QuickNode, Dwellir, PurrData and Coinglass. The per-wallet view exists in
node state and nobody has productised it.

**Nobody publishes the derived layers.** No provider offers cluster defensibility from free
collateral, cascade depth against book liquidity, or empirical hit rates for clusters. Those are
computation, not collection.

**Everything else is a normal competitive market.** The raw material is obtainable by anyone
willing to run a node. **The moat is the work, not the access** — which is a different and much
more ordinary kind of business than the one I described.

## 6. The honest read

Ninety minutes ago I wrote that account state "can only be accumulated" and that every other
dataset "can be bought by a competitor tomorrow." Both sentences were wrong in the same
direction: they made a crowded market look empty.

**This is the third closure of mine to invert in one session**, and the second in which I claimed
uniqueness without checking whether anyone else had it. The pattern is recorded in
`feedback_dont_close_early`, and it applies to optimistic claims exactly as much as to
pessimistic ones — a moat asserted without checking is the same error as a door closed without
measuring.

## 7. Still unverified

- The **Kaggle 5-minute DEX order book** dataset — not fetched
- Whether `periodic_abci_states` includes `withdrawable` / free collateral, or only positions and
  margin. **This is the decisive question for the defensibility metric**, which is currently the
  most differentiated thing on the list
- What Dwellir charges, and whether their archived states are parsed or raw `.rmp`
- Whether 0xArchive's projected levels disclose coverage the way their orderbook metrics do
