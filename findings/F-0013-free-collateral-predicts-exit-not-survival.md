---
id: F-0013
title: Wallets holding free collateral leave the market more often than trapped ones, so disappearance cannot be read as liquidation
status: PRELIMINARY
observation: "across 4 deep-to-deep transitions, of wallets within 5% of liquidation: 62.7% of those WITH free collateral were absent at the next scan, against 45.1% of those with none. The sign is opposite to the hypothesis that free collateral aids survival."
sample: 2,302 wallet-transitions within 5% (3,331 within 10%) across 5 deep scans of the frozen 5,395-wallet universe, Hyperliquid BTC, 2026-08-19 to 2026-08-21
method: track each wallet's BTC position between consecutive DEEP scans only; classify as absent, survived-improved or survived-worsened; split by whether withdrawable was above zero
evidence: product/calibration.py, ~/genesis-evidence/liqmap/snapshots-liq2.jsonl
confidence: only 4 transitions, 12.9h apart, so wallets are counted repeatedly and these are not independent observations. One venue, one asset, 54 hours. The direction is clear; the magnitude is not established.
market_gap: no provider publishes wallet-level survival at all, because none archives per-wallet account state over time
first_recorded: 2026-08-21
last_updated: 2026-08-21
supersedes: none
---

The proposed product was a base rate: *"wallets in your situation escaped 3 times in 10."* It
required that wallets which survive be distinguishable from wallets which do not.

They are not, and the reason is more interesting than the failure.

## What was measured

| within 5% of liquidation | n | absent at next scan | improved | cut size |
|---|---|---|---|---|
| **free collateral > 0** | 1,109 | **62.7%** | 63.8% | 39.4% |
| **free collateral = 0** | 1,193 | **45.1%** | 70.8% | 37.1% |

**Wallets with the means to defend themselves disappear more often than wallets without.**

## Why, and why it kills the base rate

**"Absent" conflates two opposite events.** A wallet holding free collateral can close its
position and walk away. A wallet at zero free collateral is *stuck* — it cannot exit without
realising the loss, and it cannot move its liquidation price either.

So the most likely reading is that free collateral predicts **voluntary exit**, not survival, and
that trapped wallets persist in the data precisely because they are trapped.

Our archive cannot separate the two. A wallet is recorded only while it holds a BTC position, so
a wallet that closed out and a wallet that was liquidated both vanish identically. **No amount of
further collection fixes this**, because the distinguishing event is not in the data we collect.

## What it does not mean

It does not mean free collateral is useless — F-0001 stands, and the venue's own figure is still
the only correct way to compute it. It means **presence in a later scan is the wrong outcome
variable**, and any product built on it would have been measuring exits and calling them escapes.

## The remedy, and it is specific

Liquidation *events* are published, and 0xArchive's free tier carries them alongside trades,
funding and open interest. Joining their events to our states labels each disappearance as
liquidation or exit, and the base rate becomes answerable.

That join is the next thing to try. Until it exists, the escape-rate product is not merely
unproven — it is unmeasurable.

## The methodological warning

The same analysis run on the **fast** tier gives 13.3% absent instead of 49.1%, because a wallet
leaving the top-300 by notional looks identical to a wallet leaving the market. Had this been run
on the hourly data — the obvious thing to do, since there is six times more of it — it would have
produced a confident number that was almost entirely scan-set churn. F-0011 again, in a new place.
