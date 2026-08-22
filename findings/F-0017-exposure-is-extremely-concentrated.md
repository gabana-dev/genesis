---
id: F-0017
title: In a uniform random sample of Hyperliquid BTC traders, ten wallets hold 57% of the leveraged exposure and the median position is $1,308
status: PRELIMINARY
observation: "of 8,000 wallets drawn uniformly at random from 51,765 discovered, 2,249 held a BTC position totalling $222.9M. The top 1 wallet holds 14.0%, the top 10 hold 56.6%, the top 100 hold 87.6%. Median position $1,308 against a mean of $99,108 — a mean 76 times the median"
sample: WIDE-1 first scan, 8,000 wallets, Hyperliquid BTC, 2026-08-22
method: uniform random sample without replacement, seed 20260822 recorded before drawing, from every distinct wallet seen in the BTC trade recording; positions read from the venue's own clearinghouse state
evidence: market/wide.py, ~/genesis-evidence/liqmap/snapshots-wide.jsonl
confidence: one scan. Concentration through time is the question worth asking and this is a single point on it. The draw is uniform over wallets that TRADED BTC during the recording window, which is not the same as uniform over all Hyperliquid accounts
market_gap: every provider reports aggregate open interest. None reports how few accounts it belongs to, because none holds an unbiased per-wallet sample
first_recorded: 2026-08-22
last_updated: 2026-08-22
supersedes: none
---

The published map is built on a universe of 5,395 wallets frozen on 2026-08-19. Those wallets
entered it by appearing in a trade recording, which orders wallets by how often they trade — so
the universe is **selected for activity**, and every per-wallet statistic taken from it inherits
that selection. WIDE-1 was built to have one population that is not.

The first scan of it says two things, and the second is the interesting one.

## What an unbiased sample of this market looks like

| | uniform sample (WIDE-1) | activity-selected (LIQ-2) |
|---|---|---|
| wallets scanned | 8,000 | 5,395 |
| holding a BTC position | 2,249 | 1,312 |
| total notional | $222.9M | $607.6M |
| **median position** | **$1,308** | $1,630 |
| mean position | $99,108 | $463,109 |
| top 1 wallet | 14.0% | 15.9% |
| **top 10 wallets** | **56.6%** | 64.9% |
| top 100 wallets | 87.6% | 96.4% |

**A mean 76 times the median.** The typical leveraged BTC trader on this venue is carrying about
thirteen hundred dollars of exposure, and ten accounts carry more than half of everything.

## The methodological half, which is F-0011 again

The uniform sample scanned **48% more wallets** and saw **10.5%** of open interest, against the
selected universe's **36.8%**. That is not a worse scan. It is the same fact from the other side:
the exposure lives in a handful of accounts, and a random draw mostly misses them.

**Both figures are correct and they answer different questions.** Coverage as published — scanned
notional over exchange open interest — is a statement about *notional* and stays valid however the
wallets were chosen. But any statement about *wallets* — what share can defend themselves, how
they behave, how they fail — inherits the selection, and until now every such statement this
project has made came from the activity-selected universe.

That is the third time selection has bitten: F-0011 on the fast tier, F-0013 on disappearance, and
now the deep universe itself.

## Why this one might matter where the others did not

F-0016 searched nine public market-state variables over six years and found nothing beyond the
trailing tape, and noted that all nine were public. **Concentration is not public.** No provider
publishes it, because computing it needs an unbiased per-wallet sample and none of them holds one.

It also has the property every dead hypothesis lacked: **it varies by construction.** Whether it
varies with anything is unknown and is Q2 in `research/QUEUE.md`. One scan cannot answer it. The
recorder now runs every six hours, which is the only way to find out.

**Nothing here is a claim about price.** It is a description of who holds the leverage.
