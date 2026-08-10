# EXEC-1 — what execution actually costs

**Status: FROZEN 2026-08-10, before the data exists.** No measurement, grid, threshold,
prediction or kill condition below may be changed after this point. If a defect is found in
the contract it is reported and recorded, not silently repaired.

**Classification: BUILD + IMPORT — markout and queue accounting are standard practice. No
novelty claimed.** Instrument: [`fills.py`](fills.py), built and tested before this contract
was written, 12 checks against synthetic books with hand-computed answers.

This is **Q3** of [`CONTRACT-measurement.md`](CONTRACT-measurement.md) §1:

> Can Genesis actually capture structure through realistic execution?

No strategy code, no signal, no optimisation, no position sizing, no P&L, no conditional
hypothesis search. Every order evaluated here is placed on a fixed grid specified below.

---

## 1. Why this is frozen before the data lands

A one-hour calibration pass on 2026-08-10 returned **~32% of the maker advantage lost** to
adverse selection. That number is already known to the analyst, which is exactly the condition
under which a contract is worth writing: at 30% the result would read as confirmation, and at
80% the temptation would be to find a reason the sample was unrepresentative. The predictions
in §5 are recorded now so neither move is available later.

The calibration figures are **superseded, not evidence.** One hour, one instrument,
unconditional orders.

## 2. The questions

| | |
|---|---|
| **E1** | What fraction of hypothetical resting orders is reached, and does it fill? |
| **E2** | How much adverse selection follows a fill, at 1 s, 10 s, 60 s and 300 s? |
| **E3** | **What portion of the 3 bps per-side maker advantage survives adverse selection?** |
| **E4** | How do E1–E3 change with distance from the touch? |
| **E5** | How do E1–E3 change with latency, from the 291 ms floor to the p95? |

E3 is the deliverable. It decides whether the maker column of the MEASURE-1 break-even table
is real or decorative.

## 3. Data

`~/genesis-evidence/q3/btcusdt-q3.jsonl` — BTCUSDT depth, recording started 2026-08-10 16:58
UTC, 7 days, hash-chained. Genesis's own observation, integrity-verified before use.

**The recording carries no trade stream.** Every fill is therefore reported as CERTAIN,
OPTIMISTIC or PESSIMISTIC, and the width of that bracket is a first-class reported number.
Calibration found the width to be **0.0 at the touch**; §5 predicts it rises away from the
touch, and that prediction is testable here.

Intervals the recorder labels incomplete are excluded. That label was validated by BAV-1
(p = 0.0165), so using it is a measured property rather than an assumption.

## 4. The grid — fixed in advance, and the reason

| Parameter | Values |
|---|---|
| Side | buy, sell |
| Offset from touch | **0, 1, 5 ticks** ($0.01 tick) |
| Size | $10,000 notional |
| Decision times | every **60 s** across the whole recording |
| Time to live | **300 s** |
| Latency arms | **291 ms** (measured floor) and **650 ms** (measured p95) |
| Markout horizons | 1 s, 10 s, 60 s, 300 s |
| Book sampling | **500 ms** |

Six cells per decision time, two latency arms, ~10,000 decision times.

**Nothing in this grid may be adjusted after seeing a result.** It is a grid rather than a
choice precisely so that no price, time or size is ever selected — a selected order is a
strategy, and this is not one.

Single size by design: MEASURE-1 measured impact as indistinguishable from zero to $100k, so
size is not the interesting axis. Distance from the touch is.

**Declared limitations of the grid**, before results: book sampling at 500 ms means the 1 s
markout is resolved to ±500 ms; fills are resolved to 500 ms; and orders are placed
unconditionally, so this measures the adverse selection facing an *uninformed* maker. A maker
acting on a signal faces a different, unmeasured number.

## 5. Pre-registered predictions

Recorded before the data exists. Each carries a falsification criterion.

| # | Prediction | Falsified if |
|---|---|---|
| X1 | Adverse selection **grows** with markout horizon and stabilises past 60 s | 300 s markout is materially smaller in magnitude than 60 s |
| X2 | **20–50%** of the maker advantage lost at the 60 s horizon, at the touch, 291 ms | outside that band |
| X3 | Fill ambiguity stays ~0 at the touch and **rises** away from it | ambiguity width at 5 ticks is not greater than at the touch |
| X4 | Reach rate falls sharply with distance: >60% at the touch, <20% at 5 ticks | either bound violated |
| X5 | Adverse selection per fill is **worse in low-volume hours** (03:00–06:00 UTC) than in the US session | equal or better in quiet hours |
| X6 | Doubling latency (291 → 650 ms) **worsens** adverse selection measurably | no measurable difference |
| X7 | Adverse selection is **worse further from the touch** per fill — those fills are more informed | equal or better at 5 ticks |

**X5 is the one I am least confident of, which is why it is here.** The intuition cuts both
ways: quiet hours have less informed flow but also thinner books.

## 6. Kill condition

> **If more than 100% of the maker advantage is lost to adverse selection at the touch at the
> 60 s horizon — that is, resting is worse than crossing after costs — then the maker column of
> the MEASURE-1 break-even table is withdrawn**, and every affordability conclusion is
> recomputed at taker fees only.

Consequences if triggered, stated now: 1d futures **taker** at φ=0.5 is 57.0% and still clears
the 60% bar, so this would not close the market direction. It would remove 4h from the
reachable region and make the daily horizon the floor.

**Passing licenses nothing.** A surviving maker advantage says execution is affordable; it says
nothing about whether there is anything worth executing.

## 7. Trial accounting

Every test declared in the ledger **before** it runs, family
`EXEC-1/<question>`, per [`ledger.py`](ledger.py). The grid is fixed, so the family size is
known in advance and cannot grow to accommodate a search.

Descriptive measurements — reach rates, markout distributions, ambiguity widths — are recorded
as CONTEXT, not trials. Comparisons that could change a decision (X5, X6, X7 and the E3
threshold) are trials and are counted.

## 8. What this cannot establish

- **Nothing about whether an edge exists.** Execution being affordable is necessary, never
  sufficient.
- **Nothing about an informed maker.** The grid is unconditional by construction. A signal-
  driven maker faces different adverse selection, and measuring that needs a signal, which is
  out of scope here and at Phase 5.
- **Nothing about queue position under real competition.** Genesis's hypothetical order does
  not exist in the book, so it never displaces anyone or changes what others do.
- **One symbol, one venue, seven days, one geography.** BTCUSDT is the deepest crypto market
  in existence; every liquidity conclusion is a best case.
- **Fees are a snapshot** taken 2026-08-10 and are not guaranteed to be the tier available.

## 9. Analysis order

Raw outcomes before interpretation, E1 → E5, with the fill bracket reported alongside every
fill-dependent number. Interpretation is a separate section, as in MEASURE-1 §7.

Results are reported **by day as well as pooled**. Seven days is short, and a figure that is
unstable across days is not a figure.
