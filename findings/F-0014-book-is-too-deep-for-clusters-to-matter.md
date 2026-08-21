---
id: F-0014
title: Both venues' ±1% BTC book holds roughly a quarter of a billion dollars, so a single sweep costs about 1 bp at retail size and a typical liquidation cluster is too small to move price
status: PRELIMINARY
observation: "standing notional within ±1% of mid is $247.6M median on Binance futures and $225.6M median on Hyperliquid — within 9% of each other. At burst level, a same-side sweep worth 0.5–1% of that book costs the taker 0.8–1.1 bps of slippage. The median published liquidation cluster is 0.44% of the Hyperliquid book; the p90 cluster is 5.1%."
sample: 221,778 aggressive bursts ≥ $50,000 over 2 Binance futures days (2025-03-10/11), joined to bookDepth ±1%; 5,112 Hyperliquid l2Book snapshots 2026-08-20/21; 433 published clusters
method: contiguous same-side aggTrades within 200 ms grouped into one burst; cost = executed VWAP against the price at which the burst began, signed against the taker; conditioned on the PREVIOUS minute's range so that volatility already in progress cannot be credited to the burst
evidence: market/impact2.py, market/impact.py, market/CONTRACT-impact.md §4 P1/P2, ~/genesis-evidence/hl2/btc-l2book.jsonl
confidence: two Binance days and 34 hours of Hyperliquid book. The order of magnitude is not in doubt; the day-to-day variation is not established, and neither is behaviour in a stressed regime, where F-0002 measured near-book depth falling to 0.657
market_gap: liquidation heatmaps publish cluster notional without ever stating it as a fraction of the book standing in front of it, which is the only form in which the number means anything
first_recorded: 2026-08-22
last_updated: 2026-08-22
supersedes: none
---

This was meant to be pre-condition P1 of IMPACT-1 — a check that minute-level aggregation had not
distorted the cost estimate. It found a distortion in the **opposite direction to the one the
contract predicted**, and the correction is larger than the experiment.

## What was measured

**Burst-level cost, median bps paid by the taker**, by the previous minute's range (the control)
and the burst's size as a fraction of the standing ±1% book:

| prior range | 0+ | 0.005+ | 0.01+ | 0.02+ |
|---|---|---|---|---|
| 5–10 bps | 0.0 (25k) | 0.8 | 1.4 | 2.3 |
| 10–20 bps | 0.0 (74k) | 1.0 | 1.6 | 2.7 |
| 20–40 bps | 0.1 (85k) | 1.1 | 1.8 | 3.0 |
| 40+ bps | 0.1 (25k) | 1.1 | 2.2 | 3.7 |

**The rows are not flat**, so the relationship IMPACT-1 set out to measure is real at burst
resolution too. But the magnitudes are an order of magnitude below the minute-level table —
0.1 to 3.7 bps against 16 to 44 — for a reason that is obvious in hindsight and was not stated in
the contract: the minute-level outcome was the whole minute's high-low excursion, which is
**everyone's** trading, while this is what **one** taker actually paid.

## The number that reframes the product

| | ±1% standing notional |
|---|---|
| Binance futures BTCUSDT | **$247.6M** median |
| Hyperliquid BTC | **$225.6M** median |

Two things follow, and they point in opposite directions.

**1. F-0006's transfer assumption looks far safer than assumed.** The two venues' BTC books are
within 9% of each other in depth. Binance-derived microstructure is not obviously the wrong
model for Hyperliquid at this asset. *This does not settle F-0006* — depth parity is not the same
as identical response under stress — but it removes the largest reason to doubt it.

**2. The retail execution-cost product is dead on BTC.** A $2.1M position is 0.9% of that book.
Closing it in one sweep costs about **1 bp — roughly $200**. Nobody subscribes to learn that.

## And it explains F-0010 rather than merely repeating it

F-0010 measured that liquidation clusters do not move price: +40.07 bps at 15 minutes, which lost
to a volatility-matched control at 44.52 bps. That was a refutation without a mechanism.

Here is the mechanism, in the same units:

| published cluster | notional | as % of HL ±1% book | implied one-sweep displacement |
|---|---|---|---|
| median | $1.0M | 0.44% | under 2 bps |
| p90 | $11.4M | 5.1% | roughly 4 bps |
| p99 | $85.8M | 38% | outside the measured range |

**A p90 cluster firing all at once accounts for about a tenth of the move F-0010 observed.** The
cluster is not the cause of the move; it is a passenger on it. Liquidation heatmaps are drawn at a
scale that invites the reader to compare clusters to each other, never to the book — and against
the book, almost all of them disappear.

## Where the value survives

Nothing here says impact modelling is worthless. It says **it is worthless where the book is
deep**, and both BTC books are deep. The measurement retains value in exactly three places, none
of which has been measured yet:

- **Thin markets** — Hyperliquid altcoins, where a $2M position is a meaningful share of the book
- **Stressed regimes** — F-0002 measured near-book depth at 0.657 in the worst quarter; the cost
  that matters is the cost when depth is gone, and every estimate above is a median across calm
- **The tail cluster** — the p99 at 38% of the book is a different object from the median at 0.44%,
  and IMPACT-1 P2 forbids quoting it because the cells backing it are empty

## The methodological note

The contract's P1 asserted that minute aggregation **understates** single-sweep cost. It
overstates it, by an order of magnitude. The assertion was written before the measurement and was
wrong, which is the correct order in which to be wrong; it is recorded in
`market/CONTRACT-impact.md` as an amendment rather than a silent edit, because the contract was
still unfrozen when the error was found.
