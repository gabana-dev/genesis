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

**What this forces.** Any published cascade figure must carry the age of the position map, and a
trigger rule must be defined against the map's own spot rather than the current book mid.
Reconciling the two is a design decision, not a detail.
