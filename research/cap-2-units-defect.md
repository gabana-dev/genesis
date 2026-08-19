# D-CAP2-1 — a units error that passed both kill conditions

**Date:** 2026-08-19
**Status:** found, fixed, run discarded and repeated.
**Classification: defect record.**

---

## What happened

CAP-2's first full pass over q3 completed in 239 seconds, resolved all 241,920 orders, and
**passed both of its kill conditions.** It produced this:

| size | fill rate (upper bound) |
|---|---|
| \$1,000 | 0.83981364322**07295** |
| \$10,000 | 0.83981364322**90504** |
| \$100,000 | 0.8397095785573713 |
| \$1,000,000 | 0.8347930247821519 |

A 1,000× range in order size moved the fill rate by **half a percentage point**, and the first
two cells agreed to the **twelfth decimal place**.

## The cause

`book.size_at()` returns **notional in quote currency** — it computes `q * p` internally. The
runner converted the grid's notional into **base units** at post time (`size_usd / price`) and
compared that against the book's notional.

**Every order was therefore about 64,000× too small. A \$1,000,000 order was simulated as
\$15.60.**

At that scale no order is ever large relative to the queue, so every order fills as soon as the
queue ahead of it clears — which is precisely the size-blind behaviour CAP-2 exists to escape.
The median depth ratio at \$1,000,000 came out as **6.69 × 10⁻⁵**, meaning the order looked like
0.0067% of displayed depth. MEASURE-1 measured median displayed depth at \$33.8M, so the true
figure is nearer 3%. That number was on the screen and I did not check it against the one
already in the repository.

## Why the kill conditions did not catch it

**K2 (the anchor) passed, correctly.** It compares reach rate against EXEC-1's 0.6529 and
observed 0.65286. Reach does not depend on order size — it asks whether the market came to the
price — so the anchor was never going to detect this. It did its job: it confirmed the
re-simulation agrees with EXEC-1 where the two should agree.

**K3 passed, and should not have.** It voids the run if fill rate is identical across sizes to
within 0.001. The observed spread was **0.005** — five times the threshold — so it reported
`instrument_still_size_blind: false`.

That spread was floating-point and rounding noise from orders that were all effectively
identical. K3 cleared a bad run by a factor of five.

> **K3 tests whether the INSTRUMENT is size-blind. It cannot test whether the CALLER handed it
> the wrong units.** The instrument was fine — `sized_fills.py` is unit-agnostic by design, and
> that design is exactly what let the error through silently.

## What would have happened

The run would have been written up as: *"fill rate is 84% at \$1,000 and 83% at \$1,000,000 —
no meaningful capacity constraint in this range."*

That is a confident, plausible, entirely wrong answer to the question ECON-1 and NET-1 both
depend on, and it would have supported sizing decisions up to a million dollars on evidence
gathered at sixteen.

It is the same failure as CAP-1's, arriving by a different route — and CAP-1's kill condition,
written specifically to prevent a repeat, did not stop it.

## The fix

Size stays in notional throughout. `o.size = o.size_usd`, no conversion.

A regression check is added to `tests/test_sized_fills.py` asserting that a \$1M order against a
\$10M level is 0.1 of it — and asserting that the defective form gives 1.6 × 10⁻⁶ and classifies
as `small`, so the signature is recognisable if it recurs.

## What this says about the kill conditions

K3 was written to catch a repeat of CAP-1 and caught nothing, because it guards the instrument
while the defect was in the caller. A kill condition that only checks downstream of the error
is not a kill condition for that error.

**The check that would have caught it in one line was already available:** MEASURE-1's median
displayed depth of \$33.8M. A \$1M order is ~3% of that. Any depth ratio near 10⁻⁵ is off by
four orders of magnitude, and the repository already held the number to compare against.

The lesson is not "add more kill conditions". It is that **a computed quantity with a known
scale should be checked against that scale**, and this project has the scales written down.
