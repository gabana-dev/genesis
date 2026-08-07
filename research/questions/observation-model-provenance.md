# Where does the observation model come from?

**Status:** open
**Weight:** high — it sits directly on the belief-necessity result and the next laboratory likely depends on it.

Surfaced by Laboratory 1 ([`../experiments/0001-belief-vs-memoryless.md`](../experiments/0001-belief-vs-memoryless.md)).

## Why it matters

Update's earned signature is `(state, input) → state`. But performing a Bayesian Update on a
belief-state *requires* the likelihood `P(observation | hidden cause)` — the observation
model — which is neither the state nor the input. In Laboratory 1 it was handed to the agent
from outside (as `noise`). The canon does not say where it comes from. A system that must be
*given* its observation model is not yet adaptive about the thing that matters most: how its
observations relate to reality.

## What we know so far

- It cannot be part of Update's signature without changing that signature (earned, tested).
- It is plausibly itself the state of a *second* Update loop — the system learning its own
  observation model from experience — which would make it belief-about-the-sensor, recursively.
- This connects to the belief-necessity result: if the observation model must be learned, the
  agent is estimating not just the hidden state but the hidden *coupling* between world and
  observation.

## What would move it

The next laboratory, in which the observation model is *not* given but must be estimated from
data alongside the hidden state — and a test of whether an agent that learns its own
observation model still beats one handed a wrong fixed model.
