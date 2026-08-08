# 2026-08-08 — The first closed loop: the filter worked, the belief didn't earn its keep

> Milestone 1 of the system-construction phase. Built under an amended contract from the
> researcher: integration validity is the *primary* criterion, behavioral advantage over the
> memoryless baseline is *secondary and not load-bearing*, and the two are never collapsed
> into one metric. Experiment record:
> [`../experiments/0004-minimal-closed-loop.md`](../experiments/0004-minimal-closed-loop.md).
> Code: `src/closed_loop.py`. Check: `tests/test_closed_loop.py`.

## What was new here

Laboratories 1–3 all had the same shape: the world moved, Genesis watched, Genesis believed.
The agent's own actions never touched the hidden state it was tracking. Milestone 1 closes
that:

```
hidden state → observation → Update → belief → decision → action
  → Predict(action) → new hidden state → new observation → ...
```

The load-bearing addition is the **action-conditioned Predict step** — the belief has to
absorb the agent's own move before the next observation arrives, or it drifts behind a world
the agent is itself displacing. That is the capability the earlier labs did not contain, and
it is an import (Thrun–Burgard–Fox 2005; Åström 1965), not a discovery.

The environment was kept deliberately boring on instruction: 1-D corridor of 7 cells, fixed
target, ±1 moves, known models, no learning, no planning. It is dull on purpose. The point
was never to be impressive.

## The result split cleanly in two, which is why the amendment mattered

**A. Integration validity — passed.** Against an Update-only ablation (belief updated on
observations, but never told what the agent did), the full filter holds far more posterior on
the true cell at every noise level: 0.775 vs 0.548, 0.457 vs 0.292, 0.286 vs 0.189. MAP error
correspondingly lower. Across 3000 episodes the belief never detaches from the world. The
loop runs.

**B. Behavioral utility — did not materialize.** The memoryless agent, acting on the raw
current observation with no memory at all, matches the belief agent (2.56 vs 2.48 steps; 4.12
vs 3.95) — and at noise 0.7 it is *better*: 0.992 reached vs 0.974, 6.53 steps vs 7.03.

Had the original single criterion stood — "the belief agent reaches the target in reliably
fewer steps" — this milestone would have been recorded as a failure, and the genuinely
validated thing (the filter) would have been buried underneath a task result that was never
really about the filter. The amendment was correct, and this is the entry that proves it.

## Why the belief bought nothing

Because the task doesn't require knowing. An informative observation arrives *every single
step*, the corridor is short, and a wrong move costs one step and self-corrects on the next.
A fresh reading is a good-enough decision input; integrating history improves the *estimate*
without improving the *choice*.

The high-noise inversion is the sharper lesson. Integration is smoothing, and smoothing lags.
When observations are noisy but constant, reacting to the freshest one can beat reasoning
from an accumulated posterior — the belief agent is more *right on average* and slightly
slower *to move*. Better epistemics, marginally worse behavior. That is not a bug in the
filter; it is a fact about when belief pays.

Stated plainly: **belief helped Genesis know, not act — because acting here didn't require
knowing.**

## What the limitation actually points at

Belief becomes behaviorally load-bearing exactly when a single current observation is
*insufficient* to decide. The cheapest way to create that condition is not a harder
environment, a cleverer policy, or a bigger state space. It is to **take the observations
away some of the time.**

With sparse/intermittent observations the agent must act during gaps, deciding from the
*predicted* belief rather than a fresh reading — and then Predict is carrying behavior, not
just estimation. Prior-art class: filtering and control under intermittent observations
(POMDP with null observations, open-loop prediction between measurements). **Import.** Not
research. That is the Milestone 2 candidate, and it comes from the observed limitation rather
than from any pre-planned ladder — which was the whole methodological point of this phase.

## What did not happen here

No canon change. No novelty claim. Nothing was invented: this is established machinery
assembled into an operating agent, which is exactly what the milestone was supposed to be.
The honest one-line summary is that Genesis now has a working closed agent loop, and has
learned — cheaply, on a boring corridor — that having a belief and needing one are different
things.
