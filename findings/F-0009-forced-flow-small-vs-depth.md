---
id: F-0009
title: Visible forced flow on Hyperliquid BTC is small relative to visible book depth
status: PRELIMINARY
observation: $63.6M total forced selling in the visible map against $222.5M of bids within 2.71% of mid; a $10.6M trigger moved price 0.069%
sample: one snapshot pair, 2026-08-20, fast-tier map at 24.2% coverage
method: cascade sweep of the observed ladder against the observed book, evaporation not applied
evidence: market/cascade_live.py
confidence: ONE observation, low coverage, static book, and a 51-minute clock gap (F-0008)
market_gap: no product publishes forced flow as a ratio to available depth
first_recorded: 2026-08-20
last_updated: 2026-08-20
supersedes: none
---

If it survives better coverage, a fresh map and measured evaporation, it points at an
uncomfortable conclusion for the whole product line: **the cascades everyone draws heatmaps of
may be routinely absorbed.**

That would still be a finding worth publishing -- *"most liquidation clusters are smaller than
the book that meets them"* is contrarian and checkable -- but it is not the product anyone
imagines buying.

**Do not lean on this.** One snapshot, 24% coverage, static book, stale map. It is recorded so it
cannot later be rediscovered and presented as new.
