---
id: F-0001
title: Free collateral cannot be derived from position and margin data; naive arithmetic misclassifies one wallet in five
status: MEASURED
observation: withdrawable == accountValue - totalMarginUsed for 19% of wallets; 20% misclassified as able to defend
sample: 74 Hyperliquid wallets holding open BTC positions, queried live 2026-08-20
method: compare venue-reported `withdrawable` against marginSummary arithmetic on the same response
evidence: research/withdrawable-is-not-derivable.md
confidence: single venue, single moment, wallets already known to hold positions; would be strengthened by repetition across days and by a second venue
market_gap: no provider checked (HyperTracker, Coinglass, 0xArchive, Tardis, QuickNode, Dwellir, PurrData) exposes this field
first_recorded: 2026-08-20
last_updated: 2026-08-20
supersedes: none
---

The venue applies constraints beyond position margin — plausibly margin reserved against open
orders, isolated allocation, or restrictions on unrealised PnL. Whatever the cause, the number is
computed by the exchange and is not a function of the fields a reconstruction would have.

**What it does not mean.** It does not establish that defensibility predicts anything. It
establishes only that the input cannot be obtained any other way.

**What would refute it.** Finding a formula over publicly available fields that reproduces
`withdrawable` to within a tolerance across a larger sample.
