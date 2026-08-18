# CAP-1 — how much size does the execution saving survive?

**Status: FROZEN 2026-08-18, before any capacity result has been computed.** No measurement,
grid, threshold, prediction or kill condition below may be changed after this point. If a
defect is found in the contract it is reported and recorded, not silently repaired.

**Classification: BUILD + IMPORT. No novelty claimed.** Instrument:
[`fills.py`](fills.py), already built and tested; this contract supplies orders to it and
adds no new simulation machinery.

---

## 1. Why the question changed shape

T1.2 was written as *"does the edge scale?"*, meaning market-making capacity.
[`../research/cost-model-and-the-two-questions.md`](../research/cost-model-and-the-two-questions.md)
closed that: passive quoting on BTCUSDT loses 5.19 bps per round trip against a spread of
0.00154 bps, and a 0% maker fee does not rescue it.

What survives is the **execution saving** — 1.81 bps per side by posting rather than crossing.
That saving is only useful to a directional strategy, and a directional strategy has a size.
So the live capacity question is:

> **CAP-1: at what order size does the 1.81 bps execution saving stop being worth having?**

This is not a rewrite of a frozen contract. EXEC-1 remains exactly as it was. CAP-1 is a new
declaration, with its own family, because it asks a question EXEC-1's grid could not answer.

## 2. Why EXEC-1 cannot answer it

EXEC-1's grid fixed size at **$10,000 notional** — a single value, by design (§4 of
[`CONTRACT-execution.md`](CONTRACT-execution.md)). One size measures no slope. The recording
itself is unaffected: it carries full depth, so the same book can be re-simulated at other
sizes without new data.

**The recording is reused; the result is new.** That is legitimate precisely because this
contract is frozen before the re-simulation runs.

---

## 3. Data

The **q3 / EXEC-1 recording**, SHA-256
`740fc04d4cf40d81ab60090d3717266c1bc7d6f2e81d8e7880e34193e8381d63`, 3.4 GB, 580,658 events,
integrity verified, analysis window 2026-08-10T13:58:23.770905Z → 2026-08-17T13:58:23.770905Z.

**Not q5.** q5 is recording until 25 August and is spoken for by COND-1. Using it here would
put two frozen contracts on one unseen dataset, and the second would be reading a set the
first had already looked at.

---

## 4. The grid — fixed in advance

Identical to EXEC-1's in every respect **except size**, so the size slope is the only thing
that varies and any difference is attributable.

| | |
|---|---|
| Offsets from touch | 0, 1, 5 ticks (as EXEC-1) |
| Sides | buy, sell |
| Latency arm | **291 ms only** — the measured floor, as EXEC-1's primary |
| TTL | 60,000 ms (as EXEC-1) |
| **Size, notional USD** | **$1,000 · $10,000 · $100,000 · $1,000,000** |
| Decision times | the same ~10,080 as EXEC-1 |

$10,000 is retained deliberately as an **anchor**: it must reproduce EXEC-1's published
figures. If it does not, the re-simulation is wrong and no other cell may be read.

**Family CAP-1 = 4 sizes × 3 offsets = 12 declared trials.** Fixed by this grid, unable to
grow. Benjamini–Hochberg at q = 0.05, reported alongside Bonferroni α = 0.05/12 = 0.004167.

**Primary endpoint:** net execution saving per side in bps — `maker_advantage − adverse
selection` at 60 s, certain-fill pool — as a function of size. Reach rate and fill rate are
reported per cell as secondary, and may not replace the primary.

---

## 5. Predictions, recorded before the data

- **C1.** The saving is monotonically non-increasing in size. Larger orders rest longer, and
  resting longer is what adverse selection charges for.
- **C2.** At $1,000,000 the net saving is **negative** — the order is large relative to
  displayed depth and the fills that do occur are the adversely selected ones.
- **C3.** The $10,000 cell reproduces EXEC-1's 1.81 bps at 60 s to within 0.05 bps.
- **C4.** Reach rate **falls** with size, because a larger order needs more of the queue ahead
  of it to clear.
- **C5.** The ambiguity bracket (optimistic minus certain) **widens** with size. Bigger orders
  depend more on queue position, which the depth-only recording cannot resolve.

## 6. Kill conditions, declared before the data

- **K1.** If C3 fails — the anchor cell does not reproduce EXEC-1 — **the whole run is void**
  and reported as a defect in the re-simulation. No other cell may be interpreted.
- **K2.** Fewer than 200 certain fills in a cell reports **insufficient data** and is excluded
  from correction, with the exclusion recorded. Cells are not merged to reach the threshold.
- **K3.** If no cell shows a size effect surviving BH, CAP-1 reports **no measurable capacity
  constraint in this range**, which is a finding and not a licence to extend the range. A
  wider grid requires a new declaration.
- **K4.** $1,000,000 exceeds the median displayed depth at the touch for much of the
  recording. Where a cell's order exceeds available depth it is reported as **partially
  fillable**, and its markout is computed on the filled portion only. This limit is declared
  here rather than discovered later.

---

## 7. Known limitations, stated before results

**The depth-only recording cannot resolve queue position**, so every fill is a
CERTAIN/OPTIMISTIC/PESSIMISTIC bracket. Size makes this worse, not better — which is why C5
predicts the bracket widens. The result is a bracket at every size, never a point.

**Market impact is not modelled.** A resting order that is filled does not move the book in
this simulation, and at $1,000,000 that is optimistic. CAP-1 therefore reports an **upper
bound** on the saving at large size. The true figure is lower by an amount this recording
cannot measure.

**One instrument, one week, one regime.** No claim is made about other symbols or other
periods.

---

## 8. Out of scope

No strategy, no signal, no sizing recommendation, no P&L. CAP-1 measures how a cost behaves as
size grows. Choosing a size is T3.1's problem and requires a strategy that does not yet exist.
