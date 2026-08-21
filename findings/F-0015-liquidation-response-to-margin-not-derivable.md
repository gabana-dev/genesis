---
id: F-0015
title: How a liquidation price responds to added margin cannot be derived from Hyperliquid's published state, so the "add $500 and your liquidation moves to X" feature cannot be built from arithmetic
status: PRELIMINARY
observation: "the documented formula reproduces the venue's own liquidationPx to within 10 bps for only 56.4% of cross positions (median error 4.79 bps, n=1,019); inverting it position-by-position within a single account recovers margin_available values that disagree by 3.49% at the median and 73.7% at p90, so only 28.2% of accounts are internally consistent within 1%"
sample: 90 Hyperliquid accounts fetched live 2026-08-22 (1,474 positions, 1,019 cross); 39 accounts holding 2+ cross positions; 1,923 wallet-transitions across 6 deep scans
method: "liq_px = entry - side*margin_available/|szi|/(1 - l*side) with l = 1/(2*maxLeverage), margin_available = crossMarginSummary.accountValue - crossMaintenanceMarginUsed; then the same formula inverted per position and compared within each account; then the implied derivative compared against observed liquidationPx movement in wallets whose position size was unchanged"
evidence: market/liqcalc.py, ~/genesis-evidence/liqmap/snapshots-liq2.jsonl
confidence: one venue, one afternoon, 90 accounts. The three checks disagree with the formula in three different ways, which is stronger than any one of them; but the third conflates unrealised PnL with deposited collateral and cannot yet isolate a real deposit
market_gap: no provider offers a margin-response figure at all, and this measurement suggests why -- the obvious arithmetic is wrong in a way that only shows up in the tail
first_recorded: 2026-08-22
last_updated: 2026-08-22
supersedes: none
---

Two independent product reviews converged on the same feature as the one worth building:

> *"Add $500 and your liquidation price moves from $72,840 to $72,310."*

It is the right instinct. It is decision support rather than a forecast, the exchange does not
offer it, and no competitor does either. `product/IA.md` made it build-order item 1 — **gated on
reproducing the venue's own `liquidationPx` first, exactly as F-0001 gated free collateral.**

**The gate caught it.** Three checks, each failing differently.

## 1. The formula does not reproduce the venue

Hyperliquid documents `liq_px = entry − side · margin_available / |szi| / (1 − l·side)`.

| `l` | median &#124;error&#124; | within 10 bps |
|---|---|---|
| **1/(2 · maxLeverage)** | **4.79 bps** | **56.4%** |
| 1/80 fixed | 838 bps | 3.3% |
| 0 | 953 bps | 0.6% |

The first row identifies the right constant — the error collapses by two orders of magnitude — and
is still wrong for **43.6% of positions**. A median of 4.79 bps is $3.75 on BTC and looks
shippable. That is the F-0001 shape exactly: right on average, badly wrong in a tail, and the tail
is where somebody gets told $500 saves them.

## 2. It is not internally consistent

A stronger test needs no faith in `accountValue` at all. Every cross position in one account
shares one `margin_available`, so inverting the formula per position must recover the same number.

| worst within-account disagreement | |
|---|---|
| median | **3.49%** |
| p90 | 73.7% |
| p95 | 138.7% |
| accounts consistent within 1% | **28.2%** |

They do not agree. **The published form is not the computation the venue performs**, or not all of
it.

## 3. The observed response is not the predicted one

Across 1,923 transitions where a wallet's position size was **unchanged** and its account value
moved, the ratio of observed liquidation-price shift to predicted shift has median **0.000**, and
only **2.8%** land within 10% of the prediction.

**This third check is the weakest of the three and must not be read as more than it is.** Account
value moves mostly with unrealised PnL, which is not the same event as depositing collateral. What
it establishes is only that account value moving does not move the liquidation price the way the
formula says it should — which is consistent with checks 1 and 2 and does not on its own settle
what a real deposit does.

## What this does not mean

It does not mean the feature is impossible. It means **it cannot be computed**, and must instead
be **measured** — the same move that turned free collateral from a guess into F-0001.

The instrument is specific: `userNonFundingLedgerUpdates` publishes actual deposits and transfers.
Joining a real deposit to the wallet's `liquidationPx` before and after it gives the venue's true
margin response as an observation rather than a derivation.

**That join requires exactly the thing this project has and its competitors do not — per-wallet
account state recorded over time.** The one product feature both reviews wanted turns out to need
the one dataset nobody else collects. It is not buildable today because the archive is three days
old and deposits are rare; it becomes buildable as the archive thickens.

## The rule this reinforces

Derived arithmetic about someone's money does not ship until it has been checked against the
venue's own figure. F-0001 established the rule after naive free collateral misclassified one
wallet in five. This is the second time the gate has fired, and the second time the obvious
formula looked good enough to ship.
