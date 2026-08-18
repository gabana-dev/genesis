# CAP-1 is not executable: the fill simulator is size-blind

**Date:** 2026-08-18
**Status: CAP-1 BLOCKED. No result computed, and none may be quoted.**
**Classification: engineering finding about an instrument, not a market finding.**

CAP-1 ([`../market/CONTRACT-capacity.md`](../market/CONTRACT-capacity.md), frozen at
`a239531e…`) asks at what order size the 1.81 bps execution saving stops being worth having.
`fills.py` cannot answer it. The question is not hard here — it is **unposed**, because the
instrument has no size dimension.

## The finding

`size_usd` appears in exactly one operative line of `fills.py`:

```python
o.fill_size_usd = o.size_usd        # line 202
```

It is a label copied onto the result. It does not enter:

- **queue position** — `queue_ahead` is the *full displayed size* at the level on arrival
  (line 138), independent of how large our own order is;
- **the fill condition** — an order fills when `consumed >= queue_ahead` (line 168). **Our own
  size never has to be consumed.** A \$1,000,000 order fills at the same instant as a \$1,000
  one;
- **partial fills** — `fill_size_usd` is always the full requested size. There is no path in
  which an order fills partially against insufficient depth.

The CERTAIN outcome is *"price traded through our level"*, which is a statement about the book
moving and is size-independent by definition.

## The evidence, from the smoke run

Thirty minutes of the q3 recording, all four declared sizes, one pass:

| size | reach rate | certain fills |
|---|---|---|
| \$1,000 | 0.8833 | 159 |
| \$10,000 | 0.8833 | 159 |
| \$100,000 | 0.8833 | 159 |
| \$1,000,000 | 0.8833 | 159 |

**A thousand-fold range in size, identical to the last order.** This is not a weak size effect.
It is the absence of a size dimension.

## Why this matters more than a blocked task

Had CAP-1 been run to completion on the full seven days, it would have returned **twelve
identical numbers** and a clean K1 pass. Read without opening `fills.py`, that output says:

> *"The execution saving is flat in size from \$1,000 to \$1,000,000 — no capacity constraint
> detected."*

That reading is available, superficially reasonable, and **entirely an artefact of the
simulator**. K3 was written to catch a null result and would have fired approvingly. The
contract's kill conditions guard against the market being uninformative; none of them guards
against the instrument being uninformative.

The smoke run cost 170 seconds. The full run would have cost roughly sixteen hours and
produced a confident false negative.

## What EXEC-1's grid actually tells us in hindsight

CONTRACT-execution.md fixed size at \$10,000 — a single value. That now reads less like a
scoping decision and more like the only choice available: **\$10,000 was not one size among
many, it was the only thing the simulator could represent.** The single-size grid and the
size-blind simulator are the same fact seen from two directions.

## What would be required

CAP-1 needs a fill model in which size is physical:

1. **Queue including our own size.** A full fill requires `consumed >= queue_ahead + our_size`,
   not `>= queue_ahead`. Today the second condition stands in for the first.
2. **Partial fills.** When consumption stops between the two thresholds, the order is partly
   filled and the markout applies to the filled portion only. K4 of CAP-1 already anticipates
   this and calls it "partially fillable" — the contract asked for behaviour the code does not
   have.
3. **Depth-relative sizing.** \$1,000,000 must be priced against *observed* displayed depth at
   the time, not assumed to be absorbable.
4. **A stated position on market impact.** A resting fill that does not move the book is
   optimistic at large size, and CAP-1 §7 already declares its result an upper bound for this
   reason.

That is **new simulation machinery**, which CAP-1 §title explicitly excludes: *"this contract
supplies orders to it and adds no new simulation machinery."* Building it inside CAP-1 would
break the contract's own scope.

**So CAP-1 is blocked, not amended, not quietly rescoped.** A size-aware fill model requires
its own declaration, its own validation against synthetic books with hand-computed answers, and
a fresh capacity contract written against it.

## What is preserved

[`../market/cap1.py`](../market/cap1.py) is kept as written. It implements the declared grid
faithfully and is correct in everything except the assumption that its instrument can
distinguish the cells. When a size-aware simulator exists, the grid is ready.

D-C1, the TTL transcription defect recorded in
[`cap-1-contract-defect.md`](cap-1-contract-defect.md), stands and is unaffected. It was found
first and remains a separate defect in the same contract.

## Two defects in one contract, and what that says

CONTRACT-capacity.md was frozen with a parameter that contradicted its own governing sentence,
and asked for a measurement its named instrument could not make. Both were found by attempting
to run it rather than by re-reading it, and the second only by looking at the output of a
thirty-minute smoke test with an eye on whether the numbers were *too* clean.

**Freezing a contract does not make it correct. It makes it auditable.** These are the audit.
