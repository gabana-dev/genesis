---
id: F-0008
title: The position map is up to an hour stale relative to the order book, which manufactures phantom triggers
status: MEASURED
observation: clock gap of 3,055 s (51 min) between the latest l2Book snapshot and the latest position snapshot
sample: first end-to-end cascade run, 2026-08-20
method: compare observation timestamps of the two joined sources
evidence: market/cascade_live.py
confidence: structural, not incidental -- the fast position scan runs hourly while the book updates every 5.3 s
market_gap: no liquidation product discloses the age of the positions behind its map
first_recorded: 2026-08-20
last_updated: 2026-08-20
supersedes: none
---

Found only by running the model end-to-end. In the first run, $10.6M of positions had a
liquidation price **at or above** the current book mid -- meaning price had already passed
through them and they should have fired. They had not been re-observed.

So a naive trigger rule reads those as "about to liquidate" when they are really "the map is
old". **The number is an artifact of the join, not a forecast.**

**What this forces, and the first fix was also wrong.** Defining the trigger against the map's
spot removed the phantom triggers but folded the price DRIFT since the map was taken into the
cascade impact: a $222k trigger against $225M of bids reported a 0.252% move, which is
arithmetically impossible. All of it was the 180-point gap between a 33-minute-old map and the
current book.

The two prices have different jobs and conflating them fakes a move:

| price | job |
|---|---|
| **map spot** | decides which clusters are still AHEAD of the market |
| **book top** | where the sweep starts, and what the move is measured FROM |

With both separated the same input reports **0.0000%** -- correct, since $222k does not clear the
top bid level.

**Publish the drift.** `map_to_book_drift_pct` bounds how far the market has moved since the map
could last be trusted, and it belongs next to any forecast rather than hidden inside it.
