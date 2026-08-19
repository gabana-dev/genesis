# CAP-2 — how does fill quality degrade with size?

**Status: FROZEN 2026-08-19, before the size-aware instrument has been pointed at any real
recording.** No grid value, endpoint, prediction or kill condition below may be changed after
this point. If a defect is found it is reported and recorded, not silently repaired.

**Classification: MEASUREMENT, descriptive. No hypothesis is tested and no profitability claim
is made.** See §6, which is the reason this contract can reuse data that other contracts have
already read.

**Instrument:** [`sized_fills.py`](sized_fills.py), built 2026-08-19, 10 checks against
hand-computed answers. **`fills.py` is not modified** — EXEC-1 and BAV-1 were validated against
it.

---

## 1. Why CAP-1 could not answer this, and what changed

CAP-1 was frozen at `a239531e…` and then found unrunnable: `size_usd` appeared in one operative
line of `fills.py` and never entered queue position, the fill condition, or partial fills. A
**1,000× size range produced identical reach (0.8833) and identical fill counts (159)**. Run to
completion it would have returned twelve identical numbers and a clean kill-condition pass,
readable as *"no capacity constraint detected"*.

`sized_fills.py` supplies the missing term: a full fill requires
`consumed >= queue_ahead + our_size`, and between the two thresholds the order fills partially.

**CAP-1 is not amended or revived.** It is closed as blocked, and its record stands. CAP-2 is a
new declaration, and it deliberately reuses **CAP-1's grid unchanged** so the two are directly
comparable and the earlier work is not wasted.

## 2. The question

> **CAP-2 asks one descriptive question: as order size grows, what happens to the fraction of
> requested size that fills, and to the uncertainty in that fraction?**

It does **not** ask whether any strategy is profitable at any size, does not estimate a capacity
limit for a strategy, and produces no P&L.

**Why this question and not "what is our capacity".** Genesis has no strategy with a declared
size. ECON-1 and NET-1 assume maker fills at an unstated size, which is a gap in both — and the
gap cannot be closed by asserting a number. It is closed by measuring how fill quality behaves
across sizes and letting a future contract choose.

## 3. Data

The **q3 / EXEC-1 recording**, SHA-256
`740fc04d4cf40d81ab60090d3717266c1bc7d6f2e81d8e7880e34193e8381d63`, 3.4 GB, 580,658 events,
integrity verified, window `2026-08-10T13:58:23.770905Z → 2026-08-17T13:58:23.770905Z`.

**q3 has been read before** — by EXEC-1 for markout and reach, and by the adverse-selection
horizon study. This is a third reading. §6 states why that is acceptable here and exactly when
it would stop being so.

**Not q5.** q5 is spoken for by COND-1, which is frozen and unrun. Two frozen contracts on one
unseen dataset means whichever runs second is read by an analyst who has seen the data.

**Venue transferability, declared.** q3 is Binance. The strategy that would eventually care
about capacity is priced at Hyperliquid, whose depth feed is throttled to 0.2 updates/second
(`l2Book`) and whose fast feed (`bbo`, 5.55/s) carries **no depth at all**. **Capacity is
therefore not measurable on Hyperliquid with what Genesis can currently observe**, and nothing
here may be presented as a Hyperliquid capacity figure.

## 4. The grid — CAP-1's, unchanged

| | |
|---|---|
| Offsets from touch | 0, 1, 5 ticks |
| Sides | buy, sell |
| Latency arm | 291 ms, the measured floor |
| TTL | **300,000 ms** — EXEC-1's actual value |
| **Size, notional USD** | **$1,000 · $10,000 · $100,000 · $1,000,000** |
| Decision times | the ~10,080 of EXEC-1 |

**On the TTL.** CAP-1's grid table said *"60,000 ms (as EXEC-1)"*, which was self-contradictory
— EXEC-1's TTL is 300,000 ms. That was recorded as defect D-C1
([`../research/cap-1-contract-defect.md`](../research/cap-1-contract-defect.md)). CAP-2 states
the correct value outright rather than inheriting the contradiction.

**12 cells** = 4 sizes × 3 offsets, both sides pooled at each offset. Fixed by this table.

## 5. Endpoints

All fill quantities are in **base units**, never order counts. With partial fills an order is no
longer a yes/no, and an order-count rate scores a 1% fill and a 100% fill identically.

**Primary, per cell:**
- `fill_rate_upper_bound` — optimistic filled size ÷ requested size
- `fill_rate_lower_bound` — pessimistic filled size ÷ requested size
- `median_ambiguity_fraction` — the width of the bracket, as a fraction of requested size

**Secondary, non-substitutable:** median depth ratio (order size ÷ displayed depth at the
posted price), the size classification (`small` / `material` / `dominant`), and the count of
partial fills.

**No p-values, no correction, no benchmark.** §6.

## 6. Why a descriptive contract may reuse data, and when it stops being allowed

Every other contract in this project guards against the forking path: a hypothesis chosen after
seeing the data, or a threshold moved to fit a result. **CAP-2 tests no hypothesis.** It reports
how a measured quantity behaves across a declared grid. There is no null to reject, so there is
nothing to reject falsely.

That is why reading q3 a third time is acceptable here, and it is the **only** reason.

> **The moment any CAP-2 output is used to support a profitability claim — a capacity limit for
> a strategy, a size at which an edge survives, a justification for trading larger — it
> inherits the full reuse problem and must be re-established on data that contract has not
> seen.** Stated here so it cannot be forgotten by whoever reaches for these numbers.

## 7. Predictions, recorded before the data

- **G1.** `fill_rate_upper_bound` falls monotonically with size across all four sizes.
- **G2.** At \$1,000 the upper bound is within 5 points of EXEC-1's published fill rate
  (65.27%), because a \$1,000 order is small relative to the queue and should behave much as
  the size-blind model assumed.
- **G3.** At \$1,000,000 the upper bound is **below 20%**.
- **G4.** Absolute ambiguity **rises** with size while `median_ambiguity_fraction` **falls** —
  a larger order has more units in doubt but a smaller share of its total could have filled at
  all. Both directions are stated because "the bracket widens" is ambiguous without them, and
  CAP-1's C5 said only the first.
- **G5.** At \$1,000,000 the median depth ratio exceeds 1.0 and the size classifies as
  `dominant` in the majority of cells — meaning the order is larger than everything resting in
  front of it, and §8's ceiling binds hardest exactly there.

## 8. Known limitations, stated before results

**Market impact is not modelled.** A resting order that fills does not move the book in this
instrument. **Every figure CAP-2 produces is a CEILING, and the overshoot grows with size.** At
\$1,000,000 against BTCUSDT's displayed depth the true fill quality is worse than reported by an
amount this recording cannot measure.

**The depth-only recording cannot resolve queue position**, which is why every result is a
bracket rather than a point. Size makes this worse, not better — that is G4.

**One instrument, one week, one venue, one regime.** August 2026, BTCUSDT, Binance.

**Fills remain hypothetical.** Genesis has no order in the book.

## 9. Kill conditions

- **K1.** Fewer than 200 orders resolving in a cell reports **insufficient data**, recorded as
  such and not merged with a neighbour.
- **K2.** If the \$10,000 cell does not reproduce EXEC-1's reach rate within 5 points, the
  re-simulation is reported as **defective** and no other cell is interpreted. This is CAP-1's
  anchor condition, carried forward — it is the only check that the new instrument agrees with
  the old one where they should agree.
- **K3.** If `fill_rate_upper_bound` is identical across all four sizes to within 0.001, the
  instrument is reported as **still size-blind** and the run is void. This is the exact failure
  that blocked CAP-1, and it is checked rather than assumed fixed.
- **K4.** Where an order's size exceeds displayed depth at its price, the cell is reported as
  `dominant` and its figures carry §8's ceiling warning on every line.

## 10. Out of scope

No strategy, no sizing recommendation, no capacity limit, no P&L, no live order. CAP-2 measures
how a cost behaves as size grows. Choosing a size requires a strategy that does not yet exist.
