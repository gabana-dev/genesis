# CARRY-1 — does perpetual funding survive retail costs?

**Status: FROZEN 2026-08-18, before any carry figure has been computed.** No measurement,
grid, threshold, prediction or kill condition below may be changed after this point. If a
defect is found in the contract it is reported and recorded, not silently repaired — and the
two defects found in CONTRACT-capacity.md the same day are the reason that sentence is meant
literally.

**Classification: IMPORT. No novelty is claimed, and none is available.** Cash-and-carry basis
arbitrage is among the most documented trades in crypto. See §3.

---

## 1. The question

Genesis has no directional signal and, per
[`../research/cost-model-and-the-two-questions.md`](../research/cost-model-and-the-two-questions.md),
no market-making business. MEASURE-1's break-even table puts the reachable region at **1 day
and longer**, requiring a **52.8% hit rate** at daily horizon (futures maker, φ = 0.5).

Carry sidesteps that bar entirely, because there is no hit rate. A hedged carry position does
not predict direction — it collects a cash flow that the venue **publishes in advance**.

> **CARRY-1 asks one question: over what holding periods, if any, does accumulated perpetual
> funding exceed the full round-trip cost of establishing and unwinding a delta-hedged
> spot–perp position at Genesis's actual fee tier?**

It does **not** ask whether the trade is a good idea, does not size it, does not select entry
times by anything except the declared thresholds, and produces no strategy.

## 2. Why this and not a directional signal

Both were considered. A directional experiment at daily horizon is the other candidate and is
not abandoned. Carry goes first because:

1. **The payoff is published, not predicted.** Funding rates are announced ahead of the
   settlement they apply to. The uncertainty is in *costs and basis*, both of which Genesis has
   now measured, rather than in a forecast it has never attempted.
2. **The instrument already exists.** q5 is recording spot and perp on one clock — built for
   COND-1, and exactly what a basis strategy needs.
3. **It is falsifiable in one number.** Either accumulated funding clears the round trip or it
   does not.

## 3. Prior art, and what is actually being asked

The trade is famous. Cash-and-carry between spot and perpetual futures is executed at scale by
every crypto desk, and the published literature — including Pindza & Bambe Moutsinga (2026),
*J. Finance and Data Science* **12**, 100197, which reports annualised funding impact above
10% in stressed periods — treats its existence as given.

**So the question is not "does funding carry exist".** It does. The question is:

> **Does it survive RETAIL fee tiers, on the spot leg in particular?**

Published treatments overwhelmingly assume institutional costs. The spot leg at VIP 0 costs
**10 bps per side** — five times the futures maker fee — and is paid twice. That is the term
that decides this, and it is the term most sources omit.

---

## 4. Data

**Primary: public Binance history**, not q5.

- **Funding rates:** `/fapi/v1/fundingRate`, BTCUSDT, from contract inception to 2026-08-18.
  Approximately 7,600 eight-hourly settlements.
- **Prices:** 8-hourly spot and perp klines over the same window, for basis and for mark-to-
  market at entry and exit.

**Why not q5.** COND-1 is frozen against q5 and has not yet been run. Putting a second frozen
contract on the same unseen dataset means whichever runs second is read by an analyst who has
already seen the data. Using public history keeps the two independent, and gives roughly
**7,600 settlements against q5's 21** — the statistical power is not close.

**Secondary, and clearly labelled as such:** q5 is used *after* COND-1 completes for one
execution-feasibility check (§7.3). It contributes no primary result.

---

## 5. The position, defined precisely

**Positive funding (longs pay shorts) — the accessible case.**
Short the perp, buy the equivalent notional of spot. Delta is hedged; funding is received.

**Negative funding (shorts pay longs) — declared INACCESSIBLE.**
The mirror requires *shorting spot*, which needs a borrow Genesis does not have and whose cost
is not observable in this data. Negative-funding periods are **reported for completeness and
excluded from every primary result.** Treating them as tradeable would assume a facility that
does not exist — the same class of error as assuming a fill.

**P&L per completed round trip**, as a fraction of notional:

```
pnl = accumulated_funding
      + (basis_exit − basis_entry)        [signed for a short-perp/long-spot position]
      − 2 × spot_fee                       [enter and exit the spot leg]
      − 2 × perp_fee                       [enter and exit the perp leg]
```

**Four legs, not two.** Every published back-of-envelope that shows carry clearing easily has
counted two. At VIP 0 the fee term alone is `2×10 + 2×2 = 24 bps`.

Basis is `(perp_mid − spot_mid) / spot_mid`, sampled at the funding timestamp nearest entry and
exit. It is a **risk, not a bonus**: the position is hedged against price, not against the two
legs diverging.

---

## 6. The grid — fixed in advance

| Parameter | Declared values | |
|---|---|---|
| Holding period | 1 day, 3 days, 7 days, 14 days | 4 |
| Entry threshold on funding rate | ≥ 0 (any positive), ≥ 0.5 bp, ≥ 1 bp, ≥ 2 bp per interval | ×4 |
| | **declared trials** | **16** |

Entry is **unconditional** within a cell: every settlement meeting the threshold opens a
position, held for exactly the declared period, exited at the next settlement boundary. No
timing, no selection, no overlap-avoidance — overlapping positions are permitted and the
dependence they create is handled in §7.2, not by discarding data.

**Fee tier is a reported sensitivity, not a search dimension.** Every cell is reported at
**`futures_vip0` + `spot_vip0` (primary)** and at **`futures_vip9` + `spot_vip0`**. Both are
reported for every cell; neither is selected after the fact. Family size stays 16.

**Correction:** Benjamini–Hochberg at q = 0.05 across all 16, reported alongside Bonferroni
α = 0.05/16 = 0.003125.

---

## 7. Method

### 7.1 Primary endpoint
**Median net P&L per completed round trip, in bps**, per cell, at the primary fee tier.
Secondary and non-substitutable: fraction of round trips profitable, mean, and worst.

### 7.2 Intervals
Overlapping holding periods make round trips dependent. Confidence intervals come from a
**moving-block bootstrap** (`stats.block_bootstrap_ci`), block length ≥ the holding period in
settlements, so the dependence is carried into the resample rather than assumed away. An IID
interval here would be too narrow and would make a noisy number look settled — the failure
EXEC-1 already documented.

### 7.3 Execution feasibility, secondary
After COND-1 completes, q5 is used once to check whether the basis observed in 8-hourly klines
is attainable in a live book: for a sample of settlement timestamps, compare the kline-derived
basis against the basis in the recorded spot and perp books at that instant. **If they differ
materially, every primary result is an upper bound**, and is reported as one.

---

## 8. Predictions, recorded before the data

- **Y1.** At the primary tier, the 1-day cell is **negative** in every threshold bucket — three
  funding intervals cannot cover 24 bps of fees.
- **Y2.** The median net P&L is **monotonically increasing** in holding period, because fees
  are paid once per round trip while funding accrues per interval.
- **Y3.** At the primary tier, the 14-day cells at thresholds ≥ 1 bp have a **positive** median
  net P&L. Stated because the arithmetic demands it and pretending otherwise would be
  dishonest: 14 days is 42 settlements, and 42 bps of funding at 1 bp per interval clears 24 bps
  of fees. If the trade fails, it fails for a reason other than fees, and Y6 names the
  candidate.
- **Y6.** The **spread** of net P&L is dominated by basis movement, not by funding. Specifically,
  the interquartile range of `(basis_exit − basis_entry)` at the 14-day holding period exceeds
  the median accumulated funding at that period. If this holds, carry at long holding periods
  is a **basis bet wearing a carry costume**, and its median being positive is not sufficient
  to trade it.
- **Y4.** At `futures_vip9`, results improve but the ordering is unchanged, because the spot leg
  is unchanged and the spot leg is what binds.
- **Y5.** The highest threshold (≥ 2 bp) has the best median and the **fewest** round trips,
  and at least one of its cells fails K2 for insufficient observations.

## 9. Kill conditions, declared before the data

- **K1.** Fewer than **100 completed round trips** in a cell reports **insufficient data**,
  is excluded from correction, and the exclusion is recorded. Cells are not merged.
- **K2.** If **no** cell has a median net P&L above zero surviving BH at the primary tier,
  **CARRY-1 reports retail carry as CLOSED.** That is a result. It does not license extending
  the grid, adding thresholds, or moving to another symbol; each needs a new declaration.
- **K6.** If Y6 holds — basis variability exceeds accumulated funding — then **no positive
  median may be reported as a carry result**, whatever BH says. A position whose outcome is
  determined by basis movement is a directional bet on the basis, and this contract does not
  test one. It would be reported as *"funding is not the operative term"* and referred to a
  new declaration.
- **K3.** If a cell is positive **only** at `futures_vip9`, the finding is reported as
  *"requires a fee tier Genesis does not hold"* and is **not** counted as a positive result.
- **K4.** If the §7.3 execution check shows kline basis and book basis differ by more than the
  median net P&L of any positive cell, that cell is **withdrawn** — its edge is inside its own
  measurement error.
- **K5.** If funding history contains gaps or contract-specification changes (leverage tiers,
  funding-interval changes, the 2022 cap revisions), affected periods are **reported and
  excluded**, not interpolated.

## 10. Known limitations, stated before results

**Borrow is not modelled**, which is why negative funding is excluded rather than inverted.

**Liquidation risk is not modelled.** A delta-hedged position still carries margin risk on the
perp leg if the two legs are held at different venues or with insufficient collateral. CARRY-1
prices cash flows, not margin calls.

**8-hourly resolution.** Entry and exit are at settlement boundaries, so intra-interval basis
movement is invisible. §7.3 bounds the error this introduces; it does not remove it.

**One symbol, one venue.** BTCUSDT on Binance. No claim about other pairs or exchanges.

**Funding is not constant across history.** Binance has changed funding caps and intervals.
K5 governs.

## 11. Out of scope

No sizing, no leverage, no position management, no live order, no agent. CARRY-1 answers
whether a published cash flow clears a measured cost. If it does, choosing whether and how much
to trade it is T3.1's problem and requires machinery that does not yet exist.
