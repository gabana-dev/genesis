---
id: F-0002
title: Order-book depth falls as price moves get larger, so a static-book cascade estimate is optimistic
status: MEASURED
observation: near-book depth falls to 0.8462 at a 5-minute horizon during the largest moves (p25 0.6573), against 1.0015 in quiet markets
sample: BTCUSDT, 1,324 days (2023-01-01 to 2026-08-19), 3,733,943 snapshots, 0 missing days; largest bucket n=313 across 160 distinct days
method: notional within +/-1% after a window divided by before, bucketed by absolute move, de-overlapped at the horizon
evidence: research/evaporation-result.md, market/evaporation_run.py, ~/genesis-evidence/bookdepth/evaporation.json
confidence: quiet-market control reads 1.000 to four decimals across 1,320 days, so the effect appears only where claimed; one venue, one asset
market_gap: no liquidation product models a non-static book
first_recorded: 2026-08-20
last_updated: 2026-08-20
supersedes: none
---

**Structure that was not expected.** Withdrawal takes minutes, not seconds: at a 1-minute horizon
the book barely flinches (0.9773), at 5 minutes it has fallen to 0.8462. So a fast cascade meets a
nearly full book and a slow grinding one does not — identical forced flow, different outcome.
Withdrawal is also concentrated near the touch: at 5 minutes the near book falls to 0.846 while
the far book holds at 0.887.

**An earlier version reported 0.726 for the largest bucket** — the most dramatic number in the
table — and it **vanished entirely** once overlapping observations were removed. 26 rows were 26
views of the same few minutes. The full history puts the real figure at 0.8462 on 313
observations across 160 distinct days.

**What it does not mean.** It does not show that market makers withdraw. Depth falling during a
move is equally consistent with quotes being consumed. Both make a cascade travel further, which
is what the model needs, but the mechanism is untested.
