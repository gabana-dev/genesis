# 0004 — Minimal closed agent loop (Milestone 1)

**Date:** 2026-08-08
**Status:** done — integration validated; behavioral advantage did NOT materialize (reported honestly)

The first milestone of the system-construction phase. **Integration, not discovery.** The
first CLOSED loop Genesis has built: belief → action → changed world → new evidence →
updated belief. Code: [`../../src/closed_loop.py`](../../src/closed_loop.py); check:
[`../../tests/test_closed_loop.py`](../../tests/test_closed_loop.py). Governed by
[`../system-roadmap.md`](../system-roadmap.md). Interpretation:
[`../journal/2026-08-08-first-closed-loop-belief-without-behavior.md`](../journal/2026-08-08-first-closed-loop-belief-without-behavior.md).

## Contract (pre-registered, per the approved amendment)

- **A. Integration validity (primary):** the action-conditioned Predict step incorporates the
  agent's action so belief stays aligned with a state the agent is moving. Made observable by
  an Update-only ablation (no Predict), which should lose alignment.
- **B. Behavioral utility (secondary, reported not load-bearing):** acting from belief vs a
  memoryless agent on the raw observation.
- Belief quality recorded separately from task performance.
- **Import:** action-conditioned recursive Bayes filter (Thrun–Burgard–Fox 2005; Åström 1965).
  **Policy:** trivial certainty-equivalent greedy toward a fixed target.
- Environment: 1-D corridor, K=7, target=3, deterministic ±1 moves, noisy position
  observation, max 30 steps. Deliberately boring.

## Results (3000 episodes, seed 7)

```
noise | A. INTEGRATION (belief quality)              | B. BEHAVIOR (task)
      | full: true-post / MAP-err | no_predict       | full reached/steps | memoryless
0.2   | 0.775 / 0.269             | 0.548 / 0.615    | 1.000 / 2.48       | 1.000 / 2.56
0.5   | 0.457 / 0.781             | 0.292 / 1.120    | 1.000 / 3.95       | 1.000 / 4.12
0.7   | 0.286 / 1.251            | 0.189 / 1.852    | 0.974 / 7.03       | 0.992 / 6.53
```

## A — Integration validity: PASSED

At every noise level the full filter tracks the true position substantially better than the
Update-only ablation (higher posterior on the true cell, lower MAP error). The closed loop
runs repeatedly without the belief detaching. **The action-conditioned Predict step
demonstrably incorporates the agent's own action and keeps the belief aligned with a state
the agent is moving** — the new capability Labs 1–3 did not contain. The ablation confirms
Predict's contribution by losing alignment when removed.

## B — Behavioral utility: did NOT materialize (honest)

Maintaining a good belief produced **no behavioral advantage** in this task. At low/mid noise
the belief agent is within noise of memoryless; **at noise 0.7 the memoryless agent is
slightly *better*** (reached 0.992 vs 0.974; 6.53 vs 7.03 steps). Not manufactured into a win.

**Why (analysis):** the task is behavior-easy. Observations arrive every step and are
informative enough that a single fresh observation usually points the right way, the corridor
is short, and wrong moves self-correct next step. So belief improves *estimation* (A) but the
*decision* barely needs it. At high noise, integrating (smoothing) can even *lag* relative to
reacting to the freshest observation — hence memoryless edging ahead. Belief helped Genesis
*know*; it did not help Genesis *act*, because acting here didn't require knowing.

## Observed limitation → what capability is actually missing

Belief becomes behaviorally load-bearing only when a single current observation is
*insufficient* for a good decision. The minimal change that creates that condition:
**sparse/intermittent observations** — the agent must act during observation gaps, forced to
decide from the *predicted* belief rather than a fresh reading. Then Predict is load-bearing
for *behavior*, not just estimation.

- **Prior-art classification:** filtering/decision under intermittent (missing) observations
  — **IMPORT** (open-loop prediction between measurements; POMDP with null observations).
  Established; not research.

## Proposed next milestone (from the evidence, not a ladder)

**Milestone 2 (candidate): the same closed loop with sparse observations** — the smallest
change that makes belief behaviorally necessary. Import (intermittent-observation filtering)
+ Build (the sparse-obs harness). No RL, planning, markets, reflexivity. To be reviewed
before build. (Alternative, larger: an uncertainty-using policy — deferred, edges toward
planning.)

## Status

No canon change. No novelty claim — established machinery integrated. Milestone 1's honest
result: **the closed loop works and the filter is validated; the belief did not yet earn its
keep behaviorally, which points directly and cheaply to Milestone 2.**
