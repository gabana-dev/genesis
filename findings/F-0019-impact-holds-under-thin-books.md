---
id: F-0019
title: Holding trade size against the standing book fixed, a book thinner than three-quarters of its own daily normal costs about 20% more — so the ratio absorbs most but not all of the stress regime
status: PRELIMINARY
observation: "across 985,950 aggressive bursts, median cost at a burst/depth ratio of 0.01-0.02 is 1.88 bps when the book is below 0.75x its day's median, against 1.62, 1.54 and 1.62 bps in the three deeper regimes. The pattern repeats at every ratio band: 0.98 vs 0.80-0.83 at 0.005+, 3.24 vs 2.58-2.74 at 0.02+. Only the thinnest band separates; the other three are indistinguishable"
sample: 985,950 same-side aggressive bursts of $50,000 or more, 22 days sampled every 60 days across Binance futures BTCUSDT from 2023-01-01 to 2026-06-14, joined to bookDepth within ±1%
method: contiguous same-side aggTrades within 200 ms grouped into one burst; cost is executed VWAP against the price at which the burst began, signed against the taker; depth regime is the standing ±1% notional divided by the same day's median, so the split is "thin for this market" rather than "thin for 2023"
evidence: market/impact2.py run_stress, market/CONTRACT-impact.md K4, research/QUEUE.md Q6
confidence: the daily-median regime is not the same stress F-0002 measured, which was depth AFTER a large move relative to before — a sharper and rarer condition this test does not isolate. Bursts within a day are not independent. The high-ratio cells above 0.05 remain empty, so nothing is established about large trades
market_gap: every execution model assumes a static book; none states whether its own estimate survives the regime where it would be used
first_recorded: 2026-08-22
last_updated: 2026-08-22
supersedes: none
---

`market/CONTRACT-impact.md` lists five kill conditions. **K4** is the one that would have mattered
most:

> *the relationship reverses or vanishes in the stressed-depth regime — i.e. it holds only when it
> is useless*

This is the first kill condition this project has tested and not fired.

## The measurement

Cost paid in bps, by how thin the book is against its own daily normal, and by trade size against
that book. **If the ratio were sufficient, the rows would be flat.**

| book vs day median | 0+ | 0.005+ | 0.01+ | 0.02+ |
|---|---|---|---|---|
| **< 0.75×** | 0.10 | **0.98** | **1.88** | **3.24** |
| 0.75–0.9× | 0.02 | 0.82 | 1.62 | 2.68 |
| 0.9–1.1× | 0.00 | 0.80 | 1.54 | 2.74 |
| > 1.1× | 0.01 | 0.83 | 1.62 | 2.58 |

They are nearly flat, and the exception is consistent.

**The ratio does almost all the work.** Moving across a row multiplies the cost three- to
fourfold. Moving down a column changes it by a fifth at most. One number — size against the book
standing in front of you — carries the relationship.

**But the thinnest regime is genuinely more expensive**, by roughly **20%**, at every ratio band
tested, in the same direction each time. The three deeper regimes are indistinguishable from each
other, so this is not a gradient: it is a threshold that only bites once the book has lost a
quarter of its usual depth.

## What it means for the model

The book does not merely shrink under stress — its shape changes slightly too, and a cost estimate
calibrated on ordinary conditions **understates by about a fifth exactly when someone would want
it**. That is a small correction, and it is the kind that only exists because it was looked for.

It is also the second time F-0002's finding has been confirmed from a different direction: depth
withdrawal during large moves is real, and here it shows up as a residual the size-ratio cannot
absorb.

## What this does not establish

**This is not the stress F-0002 measured.** That was depth *after* a large move divided by depth
*before* it, falling to 0.657 in the worst quarter — a sharper and much rarer condition. "Below
0.75× the day's median" includes quiet overnight thinness, which is not the same event. The real
stress premium may be larger than 20% and this design cannot see it.

**And the tail is still empty.** Every cell above a ratio of 0.05 has too few observations to
report, which is `CONTRACT-impact.md` P2 unresolved. Nothing here says anything about a trade
large enough to matter to a large account.
