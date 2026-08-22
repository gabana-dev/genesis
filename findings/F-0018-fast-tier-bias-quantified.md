---
id: F-0018
title: The hourly scan reproduces coverage and forced notional to within a point, but sees only 28% of positions near liquidation where the full scan sees 47%
status: PRELIMINARY
observation: "across 7 deep scans paired with the fast scan nearest in time, coverage agrees to within 1.6 points (36.8% vs 36.2% on the closest pair) and forced sell-side notional within ±12%; but median distance to liquidation is 11.6% in the deep tier against 26.5% in the fast tier, and the share of positions sitting within 10% of liquidation is 47.4% deep against 27.8% fast"
sample: 7 deep/fast snapshot pairs within one hour of each other, 10,585 deep positions and 1,896 fast positions, Hyperliquid BTC, 2026-08-19 to 2026-08-22
method: pair each deep snapshot with the fast snapshot closest in time; compare the published aggregates directly, and compare the full distance-to-liquidation distribution of the positions each tier actually holds
evidence: ~/genesis-evidence/liqmap/snapshots-liq2.jsonl, research/QUEUE.md Q7
confidence: three days, one venue, one asset, 7 pairs. The direction is unambiguous and consistent across every pair; the exact ratio is not established. The earliest pair sat at 20% coverage while the archive was still filling and its forced-notional gap (71.3M vs 33.6M) is far larger than any later pair's
market_gap: no provider states which of its published figures survive its own sampling and which do not
first_recorded: 2026-08-22
last_updated: 2026-08-22
supersedes: none
---

F-0011 established that the fast tier — the 300 largest positions, scanned hourly — sits further
from liquidation than the full universe, and the site has carried that warning as words ever
since. Q7 asked how much it actually matters. The answer separates our published numbers into two
groups, which is more useful than a single verdict.

## What survives the sampling

| paired, deep vs fast | deep | fast |
|---|---|---|
| coverage (closest pair) | 36.8% | 36.2% |
| forced sell-side notional | $21.7M | $19.3M |

**Coverage and notional are safe.** Both are notional-weighted, and the notional lives in a
handful of very large accounts (F-0017: ten wallets hold 57% of an unbiased sample) which *both*
tiers see. Scanning 5,395 wallets instead of 300 adds 1,000 more positions and almost no dollars.

So the coverage figure on the map is not distorted by which tier produced it. That is worth
knowing precisely because it was not obvious.

## What does not survive

| distance to liquidation | deep | fast |
|---|---|---|
| p10 | 1.2% | 3.2% |
| p25 | 3.2% | 9.0% |
| **median** | **11.6%** | **26.5%** |
| p75 | 43.3% | 80.3% |
| p90 | 130.9% | 571.7% |
| **within 10% of liquidation** | **47.4%** | **27.8%** |

**The hourly map sees a market where 28% of positions are near liquidation. The full scan sees
47%.** Every quantity counted in *positions* rather than dollars inherits that, and the gap widens
at every percentile.

The mechanism is not mysterious and it is the same one as F-0017: the largest positions are the
best capitalised, so ranking by notional selects for distance from liquidation. The fast tier is
not a random sample of the market — it is a sample of the market's biggest accounts, and being big
is correlated with being safe.

## What this changes

Nothing about coverage, and nothing about the forced-exposure totals. It changes the caveat, which
until now said *"these sit further from liquidation than the full universe"* without saying how
much further. **28% against 47%** is a measurement; the sentence it replaces was a hedge.

It also sets a rule going forward: any figure this project publishes as a **count of positions**
or a **share of positions** must state its tier, and must not be compared across tiers. Dollar
figures may be.

## What it does not establish

Whether the deep tier is itself representative. It is the frozen 5,395-wallet universe, which
F-0017 showed is selected for trading activity and is not a uniform draw of the market either. The
deep tier is *less* biased than the fast tier on this axis. It is not unbiased. WIDE-1 exists to
find out how much of a difference that second layer of selection makes, and it needs months.
