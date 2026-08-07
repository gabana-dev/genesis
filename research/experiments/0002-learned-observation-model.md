# 0002 — Learned observation model (variation of Laboratory 1)

**Date:** 2026-08-07
**Status:** done

Genesis Laboratory 2. Two purposes at once (production + governance):

- **Production:** attack [`../questions/observation-model-provenance.md`](../questions/observation-model-provenance.md)
  — the one piece of reality-generated architecture Lab 1 exposed. Is the observation model
  itself the state of a *second* Update loop?
- **Governance:** serve as the **variation test** for belief-necessity. Lab 1 handed the
  agent its model; Lab 2 makes it learn one. Same invariant (belief-state), different
  representation. If the invariant survives, belief-necessity has earned *stability*, not
  just one successful implementation.

Code: [`../../src/laboratory2.py`](../../src/laboratory2.py), `agents.py`
(`LearningBeliefAgent`), `environment.py` (`reveal()`). Check:
[`../../tests/test_laboratory2.py`](../../tests/test_laboratory2.py). Standard library only.

## Hypotheses (stated before running)

1. The observation model is learnable as the state of a second Update loop — the learned
   noise estimate converges to the true noise.
2. Belief-necessity survives the variation — a belief agent with a *learned* model still
   beats memoryless and approaches a belief agent given the true model.

## Setup

Same environment as Lab 1 (`noise = 0.30`, `horizon = 12`), but the true hidden state is
revealed after each episode. `LearningBeliefAgent` runs two nested Update loops: within an
episode it Updates a belief over the hidden bit using its *current* noise estimate; across
episodes it Updates a tally of faithful vs corrupted observations (Laplace pseudocounts,
starting at an uninformative 0.5), whose ratio is the noise estimate. 8000 episodes, seed 7.

## Result

```
memoryless accuracy           : 0.698
belief, GIVEN model           : 0.927
belief, LEARNED model (early) : 0.926   (first 2000 episodes)
belief, LEARNED model (late)  : 0.925   (last 2000 episodes)
learned noise estimate        : 0.299   (true 0.30)
```

Both hypotheses held. The model converged to the truth (0.299 vs 0.30) — **the observation
model is the state of a second Update loop.** Belief-necessity survived the variation:
learned-model belief (0.925) is statistically indistinguishable from given-model belief
(0.927) and far above memoryless (0.698).

## What it changes

- **The "fourth thing" from the Lab 1 postmortem dissolves back into Update.** The
  observation model has no special status — it is Update applied to the sensor rather than
  the world. `observation-model-provenance` is answered for this case: the model is learned
  by a nested Update loop. (The question stays open for the harder unsupervised case where
  the true state is never revealed.)
- **Belief-necessity now has variation evidence.** The same invariant survived a genuinely
  different representation. This is what the Canon bar
  ([`../../canon/architecture.md`](../../canon/architecture.md) — "stability under
  variation") requires beyond a single implementation. One variation done (representation);
  environment variation not yet tested.
- **Measurement lesson (postmortem):** the learned-model agent reaches full accuracy within
  ~10 episodes (each episode supplies 12 labelled sensor samples), so the learning transient
  is invisible at 2000-episode granularity — the "early" window already reads 0.926. Seeing
  the curve would require per-episode logging over the first ~20 episodes. Noted, not fixed.

No hypothesis was falsified. The variation strengthened belief-necessity and dissolved the
observation-model puzzle into the already-earned Update primitive — a compression, not a new
concept.
