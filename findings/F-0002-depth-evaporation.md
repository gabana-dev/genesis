---
id: F-0002
title: Order-book depth falls as price moves get larger, so a static-book cascade estimate is optimistic
status: PRELIMINARY
observation: depth after / depth before = 0.894 during moves of 0.475-1.271%, against 1.00 in quiet markets
sample: BTCUSDT, 30 days of Binance bookDepth, 6,478 non-overlapping observations, largest bucket n=58 across 14 distinct days
method: notional within +/-1% after a window divided by before, bucketed by absolute move, de-overlapped at the horizon
evidence: research/... (full-history run in progress), market/evaporation.py
confidence: 30 days only; the full 1,324-day run is running and will decide whether the extreme buckets survive
market_gap: no liquidation product models a non-static book
first_recorded: 2026-08-20
last_updated: 2026-08-20
supersedes: none
---

**Why PRELIMINARY and not MEASURED.** An earlier version of this table showed 0.726 for the
largest moves — the most dramatic number in it — and that bucket **vanished entirely** once
overlapping observations were removed. 26 rows were 26 views of the same few minutes.

**What it does not mean.** It does not show that market makers withdraw. Depth falling during a
move is equally consistent with quotes being consumed. Both make a cascade travel further, which
is what the model needs, but the mechanism is untested.
