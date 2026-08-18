# holons/ — the decision layer

**Classification: IMPORT + BUILD — engineering. Not research. No novelty claimed.**
Permitted by [DR0003](../research/decisions/0003-engineering-posture-real-data.md); the
classification is stated here before anything is built on top, per
[`../canon/operations.md`](../canon/operations.md) §1.

Nothing here has been used to declare a trial. Nothing here trades.

---

## What this is

A layer of small, specialised components — **holons** — each of which measures one thing, knows
how badly it does it, and may decline to answer. Above them sits an **integrator** whose job is
not to average their opinions but to find out whether those opinions are actually independent.

## Why "holon" and not "agent"

A holon is a whole at its own level and a part at the level above. Both halves are enforced
here, because the word is otherwise decoration:

**Downward — it is a whole.** It owns its state, its own tests, and its own estimate of its own
error. Critically, **it may return `None` — no opinion.** A component that must always emit a
number is a subroutine wearing a costume, and a holon that cannot say *"this month is a random
walk, I have nothing"* will invent structure to fill the silence.

**Upward — it is a part.** It emits one common currency, a `Claim`, never a raw signal and
never an instruction. The layer above cannot weigh "buy" against "0.7".

## The one problem this layer exists to solve

MEASURE-1's cross-section work found that **33 liquid crypto perps carry roughly two
independent bets.** Thirty instruments, two opinions. Holding all of them is one position with
extra fees.

**Six holons are the same trap one level up.** They all consume the same substrate, so they will
correlate. Averaging them, or combining them by inverse variance, silently claims an
independence they do not have — the combined error bar comes out too tight, position sizing
reads that as confidence, and the system stakes real money on six copies of one opinion.

So the integrator measures effective breadth **over the holons' own claim history**, using the
same machinery [`../market/breadth.py`](../market/breadth.py) uses on instruments, and combines
by GLS given the answer rather than assuming independence.

**This was not hypothetical.** Pointed at two real volatility holons on 2,476 aligned decision
times, it measured ρ = 0.969, effective breadth **1.03**, and refused to combine them — because
combining them scored *worse out of sample* than the better one alone. The first version had no
refusal gate and produced exactly that failure.

## Contents

| | |
|---|---|
| [`holon.py`](holon.py) | the `Claim` contract and the `Holon` base. `Basis` marks whether a claim rests on a completed measurement, a fitted model, or nothing yet. |
| [`integrate.py`](integrate.py) | the integrator. Four refusal paths: insufficient history, collinear holons, effective breadth below 1.35, non-positive-definite covariance. |
| [`volatility.py`](volatility.py) | the first real holon — Corsi HAR-RV, walk-forward, with self-measured uncertainty. |

Tests: [`../tests/test_holons.py`](../tests/test_holons.py) (14),
[`../tests/test_holon_volatility.py`](../tests/test_holon_volatility.py) (9).

Each test constructs the failure it guards against rather than asserting that a healthy case
looks healthy — a suite that only checked the healthy case would pass with every detector
removed.

## Two fields that make a Claim different from a number

**`completeness`** carries the L0 invariant upward. BAV-1 established that the recorder's
completeness label *predicts* agreement with an independent channel (p = 0.0165), so a claim
resting on an unvouched record is a different kind of object from one that does not. It is
refused at the integrator rather than quietly discounted.

**`basis`** stops an untested component being treated as a measured one because both arrive as
floats. `UNTESTED` claims are logged and scored but carry **zero weight** — the burn-in an
unvalidated holon serves before it can move anything.

## What this layer may not do

- **It may not declare a trial.** Predictive work requires a named consumer under
  [DR0006](../research/decisions/0006-no-prediction-without-a-consumer.md), and that is a
  contract decision, not a code decision.
- **It may not size a position on assumed independence.** Measured breadth or refusal.
- **It may not treat an LLM as a signal.** *"LLM enters at Phase 5 … never the signal"* —
  [`../canon/roadmap.md`](../canon/roadmap.md).

## Where the edge is expected to live, and where it is not

The measurements say direction is not linearly predictable at affordable horizons (OOS
R² = −0.0037 next-day) while volatility is (R² 0.26–0.39 per year, never zero in eight years),
and that resting orders earn 1.83 bps of maker advantage that survives adverse selection.

So this layer is built on the expectation that **the edge is in execution and sizing, not in
prediction** — and it is built to make that expectation falsifiable rather than assumed.
