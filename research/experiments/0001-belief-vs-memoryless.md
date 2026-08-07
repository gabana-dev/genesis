# 0001 — Belief-state vs memoryless under partial observability

**Date:** 2026-08-07
**Status:** done

Genesis Laboratory 1. The first contact between the theory and reality. Its purpose is not
performance and not novelty (the claim is known POMDP theory) — it is **architectural
validation**: can Reception, Update, and a belief-state be implemented cleanly and directly
from the canon, and does the implementation behave as the theory predicts?

Code: [`../../src/`](../../src/) (`environment.py`, `genesis.py`, `agents.py`,
`laboratory.py`), check in [`../../tests/test_laboratory.py`](../../tests/test_laboratory.py).
Descends from [`../../canon/architecture.md`](../../canon/architecture.md) Part B. Standard
library only.

## Hypothesis

Stated before running (from
[`../journal/2026-08-07-belief-derived-by-necessity.md`](../journal/2026-08-07-belief-derived-by-necessity.md)):
under partial observability, an agent that maintains a belief-state via Update outperforms a
memoryless agent that acts on the latest observation alone.

## Setup

Environment: a hidden bit, fixed per episode, never directly revealed; each timestep yields
the bit corrupted with probability `noise = 0.30`; reward +1 for a correct final guess.
`horizon = 12` observations per episode, 5000 episodes, seed 7. Memoryless agent guesses its
last observation; belief agent maintains a posterior over the hidden bit via Bayesian Update
and guesses its MAP.

## Result

```
memoryless accuracy : 0.699   (per-observation ceiling ~ 0.70)
belief accuracy     : 0.929
belief advantage    : +0.230
```

The memoryless agent is pinned to the per-observation accuracy `1 - noise`, exactly as
theory predicts — it cannot integrate. The belief agent clears it by +0.23. The prediction
held against real randomness. **The primitives implemented cleanly from the canon: concepts
became software.** That threshold is crossed.

## What it changes

The performance result was expected. The **valuable** output is the ambiguity that writing
the code exposed — three places where the canon was not precise enough to implement without
adding an unstated assumption. Each becomes a research question, per the standing loop
(implementation exposes ambiguity → ambiguity generates research):

1. **The observation model has no home in Update's signature.** Update is `(state, input) →
   state`, but Bayesian Update *requires* the likelihood `P(observation | hidden)`, which is
   neither state nor input. The belief agent had to be handed `noise` from outside. The canon
   does not say where an observation model comes from; in a real system it would itself have
   to be learned. → [`../questions/observation-model-provenance.md`](../questions/observation-model-provenance.md)

2. **Reception is nearly contentless in code** (`receive(x) = x`). The primitives entry
   established Reception and Update as co-equal, dissociable primitives — yet in
   implementation Reception carries no computation, only marks the intake boundary. Is
   Reception a computational *operation*, or a boundary/interface condition that makes Update
   meaningful? The code makes the question sharp.
   → [`../questions/reception-operation-or-boundary.md`](../questions/reception-operation-or-boundary.md)

3. **Action-selection is underspecified.** The necessity derivation says action is "a read of
   state," but not *which* read. The lab chose MAP; sampling or a threshold would be equally
   compatible with the canon and would matter in a real decision problem. Minor, noted, not
   yet its own question.

No canon claim was falsified. The build validated the architecture and produced three
precise gaps that pure contemplation had not surfaced — which is the research↔engineering
loop working as intended.
