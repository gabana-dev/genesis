---
id: F-0011
title: The hourly map systematically under-represents the positions closest to liquidation
status: PRELIMINARY
observation: "deep scan (5,395 wallets): median distance to liquidation 15.5%, 42.8% of positions within 10%. Fast scan (top 300 by notional) at the same period: median 31.6%, 23.0% within 10%."
sample: one deep snapshot of 1,327 BTC positions against three fast snapshots of 267-270, 2026-08-21
method: distance to liquidation as |liquidationPx - spot| / spot, per position, compared across scan tiers
evidence: market/liqmap.py (tier definitions), ~/genesis-evidence/liqmap/snapshots-liq2.jsonl
confidence: one deep snapshot against three fast ones, same day, single venue, single asset. Needs several deep/fast pairs across different market conditions before it is more than PRELIMINARY.
market_gap: no liquidation product we surveyed states which population its map is drawn from, let alone how that population biases the result
first_recorded: 2026-08-21
last_updated: 2026-08-21
supersedes: none
---

The LIQ-2 fast tier is the **top 300 wallets by position notional**, re-ranked by each deep scan.
That rule was chosen because position notional is what determines forced flow, and it is the
right rule for measuring *size*.

It appears to be the wrong rule for measuring *proximity*. The largest positions sit further from
their liquidation price than smaller ones — plausibly because size and caution correlate, and
because a wallet large enough to rank in the top 300 has usually not levered itself to the edge.
The consequence is that the map we publish every hour is drawn from the population **least likely
to be near liquidation**, and the six-hourly deep scan sees nearly twice the share of close
positions.

## What it means

The hourly figures are not wrong, but they answer a narrower question than they appear to: *among
the 300 largest positions*, this much forced selling sits nearby. That is not the same as *among
all observable positions*.

It may also bear on the near-constant `cannot_defend_pct` recorded the same day — 71% of clusters
at exactly 100%. If the hourly population is large, distant positions, the clusters built from it
may be dominated by a handful of wallets, and a bucket containing one fully-committed wallet is
100% by construction. That is a hypothesis, not a result.

## What it does not mean

It does not mean the fast tier should be abandoned. A 5,395-wallet scan takes about 2h22m; an
hourly cadence is only possible on a subset, and `clearinghouseState` has no history, so an
uncollected hour is lost permanently. The trade is real.

It also does not mean the deep scan is unbiased. Its universe is every wallet appearing in the
`hl1` trade recording, frozen at first scan — a population selected by having traded BTC during
one recording window, which is its own bias and is documented in the LIQ-2 contract.

## What would refute it

Several deep/fast pairs across different volatility regimes showing no consistent gap in median
distance or in the share within 10%. A single pair on a single day is a coincidence until it
repeats.

## Why it was nearly missed

It surfaced while checking something else entirely — whether ETH's near-empty map was a universe
problem or a market fact. The ETH and SOL numbers come from the fast tier, so the same bias
applies to them, and the conclusion "ETH traders simply sit further from liquidation" was about to
be drawn from the population least able to support it. The first multi-asset **deep** scan will
settle that, and it is already scheduled.
