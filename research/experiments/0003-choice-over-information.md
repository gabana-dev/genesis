# 0003 — Choice over information (Laboratory 3)

**Date:** 2026-08-07
**Status:** done — but the environment did not discriminate the hypotheses (see Validation)

Genesis's first introduction of **choice**: the agent selects which channel to observe.
Code: [`../../src/laboratory3.py`](../../src/laboratory3.py) (self-contained), check:
[`../../tests/test_laboratory3.py`](../../tests/test_laboratory3.py).

## Contract (pre-registered)

**Hypothesis:** observation selection can be expressed using only belief-state + Update +
reads, or agency exposes a new operation.
**Interpretations (binding):** I1 pure-read suffices · I2 simulation (reapplied Update on
imagined observations) necessary · I3 neither — candidate third primitive.
**Environment:** 2 static bits; channel A observes b1, channel B observes b1⊕b2, equal
noise 0.20; budget N; guess the joint.
**Agents:** passive (random) · pure_read (rank by target marginal entropy — a pure read) ·
simulation (rank by expected posterior entropy — reapplied Update). Identical otherwise.
**Controls:** same prior, models, Update, budget, hidden-state distribution; compute
reported separately; full accuracy-vs-budget curve (no single threshold).

## Validation (run first, per the design-review requirement)

Across **20,000 non-tie belief states**, the pure-read ranking disagreed with the
info-gain (optimal) ranking **0 times**. The environment is **non-discriminating**: it
cannot exhibit I2 or I3.

**Why, analytically:** for a one-step, single-function, equal-noise channel, expected
information gain `I(state; obs)` reduces to `H_b(n + p(1−2n)) − H_b(n)`, a strictly
monotone function of the target's marginal `p = P(target=1)`. Same noise on both channels
⇒ ranking by info-gain ≡ ranking by target marginal entropy ≡ a pure read. The XOR
entanglement does not change this, because each channel still observes a *single* function.

## Result (empirical — what the experiment demonstrates)

```
budget |  passive | pure_read | simulation | sim imagined-Updates/step
     2 |    0.514 |     0.630 |      0.630 | 4.0
     4 |    0.648 |     0.713 |      0.714 | 4.0
     6 |    0.729 |     0.796 |      0.796 | 4.0
     8 |    0.797 |     0.873 |      0.875 | 4.0
    10 |    0.844 |     0.916 |      0.917 | 4.0
```

`pure_read` and `simulation` are functionally identical (differences ≤0.002, at the
Monte-Carlo / floating-point floor — consistent with the 0/20,000 validation). Both beat
`passive`. Simulation spent 4 imagined-Updates per step for no accuracy gain.

## Interpretation (architectural — kept separate from the empirical result)

- At the compositional level this is **I1**: observation selection *is* expressible as a
  read of the belief-state, and it improves accuracy over passive.
- **But the validation voids the I1/I2/I3 discrimination.** The environment could not have
  shown I2 or I3, so this is *not* evidence for the two-primitive architecture surviving
  agency. It is only evidence that, *where selection reduces to a read*, the read composes.
- Belief-necessity remains **Working**. No canon claim is authorized or made.

## What it does NOT establish

- Nothing about whether agency *ever* requires simulation or a new primitive.
- Nothing to promote to canon.
- Nothing about consequential (world-changing) action, dynamic state, or external reward.

## The finding worth keeping (postmortem headline)

The one-step boundary — required to keep the experiment isolated — is *also* what makes I2/I3
unreachable: one-step expected value over single-function channels is always a closed-form
read, so reapplied-Update-as-simulation is never *necessary*, only one way to compute it.
The architectural question "does choice/agency require new machinery" can only be posed
where expected value is **not** a closed-form read: multi-step selection, channels whose
informativeness depends on the joint belief non-marginally (e.g. state-dependent noise), or
intractable beliefs. The lab thus **bounds where the question lives** — a clean design
failure that is more informative than a rigged confirmation would have been.
