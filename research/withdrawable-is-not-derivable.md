# `withdrawable` is not derivable from position and margin data — measured

**Date:** 2026-08-20
**Sample:** 74 wallets holding BTC positions, drawn from the most recent deep scan, queried live.

**Result: the venue's free-collateral figure matches naive margin arithmetic 19% of the time.**
Anyone computing it from `accountValue − totalMarginUsed` misclassifies **20% of wallets** as
able to defend their liquidation price when the venue says they cannot.

---

## 1. The measurement

| | |
|---|---|
| wallets sampled | 74 |
| `withdrawable == accountValue − totalMarginUsed` | **14 (19%)** |
| naive arithmetic says wallet has free collateral | 71 (96%) |
| **venue says wallet has free collateral** | **56 (76%)** |
| **naive wrongly says "has free collateral"** | **15 (20%)** |
| median overstatement, where it overstates | **$4,906** |
| largest single overstatement | **$3,601,390** |
| aggregate free collateral | naive $63.1M vs venue $50.6M — **1.2× overstated** |

The mismatch is one-directional. `withdrawable` is systematically **lower** than the margin
arithmetic implies, and frequently **exactly zero** for wallets the naive calculation says hold
tens or hundreds of thousands in free collateral.

The venue is applying constraints beyond position margin — plausibly margin reserved against
open orders, isolated-margin allocation, or restrictions on unrealised PnL. Whatever the cause,
**the number is computed by the exchange and is not a function of the fields a reconstruction
would have.**

## 2. Why this matters to the product question

The defensibility metric — *can this liquidation cluster actually defend itself?* — is the most
differentiated thing on our list. Nothing on the market publishes it.

This measurement establishes that it **cannot be reconstructed**. Order flow gives positions.
Node state gives positions and margin. Neither gives `withdrawable`, unless the node's state
snapshot happens to carry that exact field.

So the earlier finding — **48% of wallets with open positions hold zero free collateral and
cannot push their liquidation price away** — is not something a competitor derives from data they
already have. Naive arithmetic on the same wallets would report **96% have room to defend**. That
is not a small discrepancy; it inverts the conclusion.

## 3. What it rescues, and what it does not

**Rescues:** reading `clearinghouseState` directly captures a venue-computed value that
reconstruction from order flow or margin data does not reproduce. The polling approach is not
strictly dominated by a node after all — it depends entirely on §4.

**Does not rescue:** coverage. A node still sees 100% of accounts against our measured 53.3%, and
the correction in
[`CORRECTION-the-moat-is-thinner-than-i-said.md`](CORRECTION-the-moat-is-thinner-than-i-said.md)
stands in every other respect.

## 4. The one question this now turns on

**Does `periodic_abci_states` carry `withdrawable`, or only positions and margin?**

- If it **does**: a node gives 100% coverage *and* the defensibility field, and polling is
  obsolete for every purpose.
- If it **does not**: polling `clearinghouseState` is the only route to a field that 20% of the
  time contradicts what every other method would conclude — and that is a genuine, narrow,
  defensible edge.

This is the highest-value unresolved question in the whole data line, and it cannot be settled
from documentation. It requires running a node and reading a snapshot.

## 5. Method note

Sampled from wallets already known to hold positions, so it does not describe the exchange
population — it describes wallets with open BTC exposure, which is the population the metric is
about. Comparison is against `marginSummary.accountValue` and `marginSummary.totalMarginUsed`
from the same response, so there is no timing mismatch between the two sides.
