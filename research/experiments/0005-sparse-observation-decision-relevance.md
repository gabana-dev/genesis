# 0005 — Sparse observation: does maintaining a belief change what the agent does? (Milestone 2)

**Date:** 2026-08-08
**Status:** contract pre-registered and approved to build (rulings 1–9 incorporated below).
Code: [`../../src/sparse_loop.py`](../../src/sparse_loop.py); check:
[`../../tests/test_sparse_loop.py`](../../tests/test_sparse_loop.py).

Follows [`0004-minimal-closed-loop.md`](0004-minimal-closed-loop.md). Milestone 1 established
that the closed loop tracks a state the agent is itself moving (integration validity), and
that better estimation bought **no** behavioral advantage in that environment. The finding
that governs this design:

> **Belief quality and decision utility are distinct.** The Milestone 1 environment tested
> whether the agent can know its moving state. It did not test whether knowing it matters.

Milestone 2 is designed around that exact resistance and nothing else.

---

## 1. Why sparse observation is the minimum change needed

Milestone 1's belief was decision-irrelevant for one identifiable reason: **an informative
observation arrived on every single step**, so the freshest reading was always an adequate
decision input. Everything else about the environment (size, noise, transition determinism,
policy) was downstream of that fact. Removing observations attacks the mechanism directly.

It is minimal in a strict sense: it introduces **one new environment parameter** (the
observation schedule), **no new agent machinery**, **no new action semantics beyond stopping**
(§6), and leaves the state space, transition model, policy, and reward untouched. The Predict
step that already exists becomes load-bearing for behavior instead of only for estimation,
because during a gap the predicted belief is the *only* estimate that exists.

Alternatives considered and rejected as non-minimal or non-discriminating:

| Candidate change | Why rejected |
|---|---|
| Longer corridor / larger state space | Harder, but an observation still arrives every step — the redundancy that killed M1's advantage survives untouched. Difficulty ≠ decision-relevance. |
| More observation noise | M1 measured this: at noise 0.7 the memoryless agent got *better* relative to belief, because integration lags reaction. Pushing noise pushes the wrong way. |
| Stochastic transitions alone | Degrades tracking without changing the decision input. Belief gets worse; the fresh observation stays sufficient. |
| Movement cost / step penalty | Makes the task an optimization problem and invites planning. Scope violation. |
| Perceptual aliasing (ambiguous observations) | Would work, but requires a new observation model and reasoning about identity — larger change, more machinery, harder to attribute a result to. |
| Active sensing (agent chooses when to look) | Explicitly out of scope: that is information-seeking behavior, i.e. planning. Also the exact regime Laboratory 3 already failed to discriminate. |

Sparse observation is the only candidate that removes the specific sufficiency condition M1
identified while adding no capability the system does not already have.

## 2. The exact capability being tested

**Can the agent act competently during intervals in which it receives no evidence, by acting
on a belief propagated through its own actions?**

Precisely: whether `Predict(action)` — already validated as an *estimator* component in M1 —
is sufficient to carry **decision-making** across observation gaps. The capability is
open-loop state propagation between measurements, consumed by a policy.

This is deliberately *not* a test of whether the filter is correct (M1 settled that), and not
a test of whether a cleverer policy helps (the policy is held fixed, §4).

## 3. Expected behavioral distinction

All agents run the **identical policy function** `π(p̂) = +1 if p̂ < target, −1 if p̂ > target,
STOP if p̂ == target`. The *only* difference between agents is what is passed as `p̂`. This is
the core design property: any behavioral difference is attributable to the state estimate and
to nothing else.

The predicted mechanism is **overshoot and failure to stop**:

- The **belief agent** knows its position during a gap because it knows what it did — its
  posterior is propagated by its own actions. It stops when it believes it has arrived, and
  that belief is well-founded.
- The **stale-observation agent** keeps executing the direction implied by an old reading. It
  cannot detect arrival, so it walks past the target and oscillates or clamps against a wall.

So the expected distinction is *not* "belief is a bit faster." It is: **belief-based agents
know when to stop; agents without propagation do not.** That is a categorical behavioral
difference, not a marginal efficiency one, and it should grow monotonically with gap length.

At observation period `p = 1` the environment reduces exactly to Milestone 1, and the
prediction is **no advantage** — this is a pre-registered null control (§5).

## 4. Baselines and confounds

**Agents (same policy, different `p̂`):**

1. **belief** — full action-conditioned filter; Update on observation steps, Predict every
   step; `p̂ = MAP(belief)`.
2. **stale-observation** — no filter; `p̂ =` most recent observation, held constant through
   the gap. **This is the load-bearing baseline.** It has memory but no propagation, so the
   comparison isolates *Predict* rather than the trivial fact of having any memory.
3. **null-memoryless** — acts only on observation steps, holds still during gaps. Continuity
   with M1's baseline; the weak baseline.
4. **no-Predict ablation** — Update on observation steps, belief frozen during gaps. Secondary
   diagnostic for §5B.

Beating (3) alone would be uninformative. **The milestone's claim rests on belief vs (2).**

**Confounds, each with its control:**

| Confound | Why it corrupts the result | Control |
|---|---|---|
| **Oracle termination** — environment declares success when true position == target | Leaks the hidden state for free and hands every agent perfect arrival detection, destroying the very distinction being measured | The **agent must declare arrival** (STOP action). The episode ends on declaration; success is scored afterwards. Non-negotiable. |
| **Weak baseline** | "Belief beats an agent that does nothing" is not a finding | Stale-observation is the primary baseline; report all three |
| **Determinism makes Predict exact** | With deterministic moves and known actions the belief is *analytically* exact during gaps, so the advantage is guaranteed by algebra rather than demonstrated | Report `p=1` null control; **recommend** an action-slip robustness sweep (§6) so belief degrades with gap length rather than being trivially perfect |
| **Wall clamping as free information** | Moves clamp at cells 0 and K−1, so an agent pressing into a wall converges to a known position without observing — this silently *helps* the baselines | Record wall-contact frequency per agent and report it; keep target central so wall-collapse is not the dominant path |
| **Unpaired randomness** | Different start positions / observation schedules across agents inflate or mask differences | Common random numbers: identical starts, noise draws, and observation schedules across all four agents per episode |
| **Step budget interacts with sparsity** | Agents that move only on observation steps traverse less of the budget | Fixed `MAX_STEPS` for all agents; report timeout rate separately from wrong-place declarations |
| **Metric conflation** | M1's lesson | Belief-quality and behavior metrics recorded and reported separately, never combined |

## 5. Success criteria (pre-registered)

**A. Decision utility — PRIMARY** (the inverse of Milestone 1, deliberately: integration is
already established, so this milestone stands or falls on behavior)

> The belief agent's **declaration accuracy** — fraction of episodes ending in a STOP issued
> at the true target — exceeds the stale-observation baseline's, by a margin that is ≈ 0 at
> `p = 1` and **grows with observation period `p`**.

The pattern across `p ∈ {1, 2, 3, 5}` is the criterion, not any single number, and the `p = 1`
null control must come out flat or the harness is wrong.

**Phrasing of the trend (per ruling 4).** Monotonicity is predicted **of the underlying
mechanism**, not required of the finite-sample estimates. The comparison is paired
(common random numbers, §4) and reported as a per-episode mean difference with a 95%
confidence interval at every condition. A non-monotonic empirical sequence whose intervals
overlap is *consistent* with the prediction and will be reported as such; a non-monotonic
sequence with separated intervals is evidence *against* it. **No result will be presented as
monotonic if the data are not.**

**B. Belief quality under gaps — SECONDARY** (mechanism evidence, reported separately)

> Posterior on the true position and MAP error, **bucketed by steps-since-last-observation**
> (0, 1, 2, … , p−1), for the full filter vs the no-Predict ablation. Expected: the full
> filter stays flat or degrades gracefully with gap age; the frozen belief degrades sharply.

**Also recorded, not scored:** steps-to-declaration, timeout rate, wrong-cell declaration
distance, wall-contact frequency.

**C. Wall-contamination threshold — PRE-REGISTERED BEFORE THE RUN (ruling 7)**

A **clamped step** is one where the agent's chosen move would leave `[0, K−1]` and the position
is clamped instead. Clamping delivers implicit position information without an observation, and
it *helps the baselines*, so it must be bounded in advance rather than assessed after seeing the
results.

> **A condition is declared CONTAMINATED — and its primary comparison inconclusive — if more
> than 25% of any agent's *correct declarations* in that condition were clamp-assisted** (i.e.
> preceded by at least one clamped step in that episode).

Fixed now, before any run. If a condition trips it, the condition is reported as inconclusive.
The threshold will not be moved, and the corridor will not be redesigned to rescue a result.

## 6. Smallest environment that can discriminate

Unchanged from Milestone 1 wherever possible:

- 1-D corridor, **K = 7**, target = 3 (central), deterministic ±1 moves, clamped at walls.
- Observation model unchanged: correct with probability `1 − noise`, else uniform over the
  other cells. Noise ∈ {0.2, 0.5}. (0.7 dropped — M1 showed it measures smoothing lag, not
  this question.)
- **New: observation period `p` ∈ {1, 2, 3, 5}.** An observation arrives on steps where
  `t mod p == 0`; no observation otherwise. `p = 1` is the M1 null control.
- **New: STOP action**, required by §4. This is the only action-set change and it exists
  solely to remove the oracle-termination confound.
- `MAX_STEPS = 40` (raised from 30 because gaps slow every agent equally).
- 3000 episodes per cell, common random numbers across agents.

Why K = 7 still suffices: discrimination depends on the ratio of gap length to corridor
length, not on absolute size. At `p = 3` a stale agent starting 2–3 cells from target will
overshoot before its next reading — the failure mode appears inside a 7-cell corridor. A
longer corridor would add runtime and no discriminating power.

**Action slip (approved, ruling 6):** `s ∈ {0, 0.1}`, where a movement action fails and the
agent stays put. STOP is never slipped.

- **Primary condition: `s = 0`.** Deterministic motion. The predictive belief is then
  *analytically exact* during a gap, so this condition is a **clean demonstration of the
  decision mechanism, not a difficult research test** (ruling 5) — stated plainly here and in
  the write-up. That is acceptable because M2 is an Import + Build integration milestone.
- **Secondary condition: `s = 0.1`.** Tests whether the advantage survives when the predictive
  belief is genuinely uncertain rather than exact. The agent's transition model knows the slip
  probability (models are known by contract). Kept clearly secondary; it must not turn M2 into
  a stochastic-filtering research experiment. **Surprising behavior here is recorded, not
  redesigned around** (ruling 6).

## 7. Prior-art classification

**IMPORT + BUILD. No research component. No novelty claim.**

- **Import — filtering under intermittent observations.** Standard: Kalman filtering with
  intermittent observations (Sinopoli et al., 2004); POMDP with null/empty observations;
  dead reckoning between position fixes in robotics (odometry between GPS/landmark updates,
  Thrun–Burgard–Fox 2005). Prediction between measurements is textbook, decades old.
- **Import — certainty-equivalent control.** The policy is unchanged from M1 and is trivial.
- **Build — the harness only:** observation scheduler, STOP action and declaration scoring,
  gap-age-bucketed metrics, paired-RNG comparison across four agents.
- **Research — none.** Explicitly confirmed against the six-way gate: this capability meets no
  unresolved problem. If the experiment produces a surprising result, the surprise is about
  *our environment design*, not about the state of the art.

## 8. Deliberately excluded

Reinforcement learning; learned or optimized policies; planning or lookahead of any depth;
active sensing / choosing when to observe (this is the Laboratory 3 trap and it is planning);
uncertainty-thresholded stopping rules (`stop when P(target) > θ`) — the policy stays
certainty-equivalent on the MAP so that policy is held identical across agents; model
learning; causal inference; multi-dimensional or continuous state; multiple agents; market
data; trading; reflexivity/performativity; self-improvement; axiology work; any architectural
novelty claim; any canon change.

If the design tempts an addition because it would make the demonstration more impressive, that
is the signal to refuse it.

## 9. What counts as failure or inconclusive

**Failure (a real, reportable negative):** no behavioral separation between belief and the
stale-observation baseline at any sparsity level. This would mean the diagnosis carried out of
Milestone 1 was wrong — that observation sparsity is *not* what makes belief decision-relevant
— and the correct response is to re-examine the diagnosis, **not** to add machinery until a
difference appears.

**Inconclusive (design failed to discriminate — the Laboratory 3 failure mode):**

- Belief beats only the null-memoryless agent, not stale-observation → the result measures
  "having any memory", not propagation.
- The advantage does not scale with `p` → the effect is an artifact of the harness rather than
  of gap length.
- Wall clamping dominates: most episodes resolve by an agent grinding into a boundary → the
  corridor, not the belief, is doing the work.
- Declaration accuracy is at ceiling or floor for all agents → the parameter grid is wrong.
- With `s = 0` only: a belief win that is fully predicted by the exactness of Predict → this is
  a demonstration, not evidence, and must be labelled so.

**Mixed result to be reported without smoothing:** belief declares correctly more often but
takes substantially longer, or is more accurate at high `p` and worse at low `p`. Milestone 1's
standard applies — the split is the finding, and it is not to be collapsed into a verdict.

---

## 10. Narrow interpretation (ruling 8) — fixed in advance

If the experiment succeeds, the claim is exactly this and no more:

> Predictive state maintenance can become behaviorally useful when direct observations are
> intermittent, and that usefulness can be isolated from merely having memory by comparison
> with a stale-observation agent running the same policy.

It is **not** a discovery about Bayesian filtering, not evidence for a new cognitive primitive,
not evidence of a novel architecture, not evidence about general intelligence, not evidence
about trading, and not evidence about axiology. Prior-art classification stays **Import +
Build**.

## 11. Standing methodological constraint on the run

**No post-hoc tuning.** Environment parameters, policy, agent definitions, the wall threshold,
and the success criteria are fixed by this document before execution. If the design fails to
discriminate, that is recorded as an experiment-design failure or an interesting negative
result. Parameters will not be adjusted until an expected result appears.

---

# RESULTS (3000 episodes/condition, seed 7, run 2026-08-08)

Nothing below was tuned after seeing results. Parameters, agents, criteria and the wall
threshold are exactly as pre-registered above.

## A. PRIMARY — declaration accuracy, belief vs stale (paired, 95% CI)

**Deterministic (`s = 0`, primary condition):**

| noise | p | belief | stale | null | frozen | paired belief−stale [95% CI] | max clamp-share | contaminated |
|---|---|---|---|---|---|---|---|---|
| 0.2 | 1 | 0.921 | 0.906 | 0.906 | 0.561 | **+0.015** [+0.006, +0.024] | 0.376 (frozen) | YES |
| 0.2 | 2 | 0.852 | 0.281 | 0.907 | 0.118 | **+0.572** [+0.552, +0.591] | 0.042 | no |
| 0.2 | 3 | 0.831 | 0.702 | 0.902 | 0.389 | +0.129 [+0.108, +0.150] | 0.688 (stale) | YES |
| 0.2 | 5 | 0.810 | 0.000 | 0.889 | 0.000 | **+0.810** [+0.796, +0.824] | 0.035 | no |
| 0.5 | 1 | 0.678 | 0.627 | 0.627 | 0.291 | **+0.052** [+0.034, +0.070] | 0.198 | no |
| 0.5 | 2 | 0.563 | 0.164 | 0.624 | 0.092 | **+0.399** [+0.379, +0.419] | 0.147 | no |
| 0.5 | 3 | 0.537 | 0.628 | 0.598 | 0.310 | −0.091 [−0.115, −0.067] | 0.739 (stale) | YES |
| 0.5 | 5 | 0.508 | 0.000 | 0.514 | 0.000 | **+0.508** [+0.490, +0.526] | 0.078 | no |

**The primary criterion is met in every uncontaminated condition.** The advantage is ≈0 at the
`p = 1` null control (+0.015 / +0.052) and large under gaps (+0.399 to +0.810), with intervals
far from zero. Sanity check passed: at `p = 1` the stale and null agents are numerically
identical, as they must be when every step carries an observation.

**On monotonicity (per ruling 4):** among the uncontaminated conditions the ordering is
increasing in `p` at both noise levels (0.2: +0.015 → +0.572 → +0.810; 0.5: +0.052 → +0.399 →
+0.508). The `p = 3` cells break the sequence, but they are excluded by the pre-registered wall
rule, not by preference. **This is reported as "consistent with the predicted mechanism", not
as a demonstrated monotonic law.**

**Mechanism confirmed as predicted:** the stale agent fails by *not knowing when to stop*. At
`p = 5` it declares in only 24% of episodes and is correct in 0.000 of them (avg 34.5 steps —
it overshoots, oscillates, and times out). The belief agent declares in 100% of episodes after
1.95 steps. The predicted failure mode is exactly the observed one.

## B. SECONDARY — belief quality by gap age (mechanism evidence)

`s = 0`, noise 0.2, `p = 5`; posterior on the true cell / MAP error:

| gap age | belief | frozen (ablation) |
|---|---|---|
| 0 | 0.655 / 0.529 | 0.455 / 2.618 |
| 1 | ~0.66 / ~0.50 | 0.133 / 3.268 |
| 2 | ~0.66 / ~0.49 | 0.101 / 3.763 |
| 3 | ~0.65 / ~0.52 | 0.095 / 4.211 |

The full filter's alignment is **flat across gap age**; the frozen belief collapses within one
step of losing observations and its MAP error grows without bound. Predict is load-bearing for
estimation across gaps, which is the mechanism the primary result depends on.

## C. Wall contamination — the pre-registered rule fired

Three `s = 0` conditions tripped the 25% threshold. Reported with the decomposition the rule
itself does not make:

- **`p = 3` (both noise levels): flagged by the `stale` agent** (0.688, 0.739) — an agent *in
  the primary comparison*, so these conditions are genuinely inconclusive. The artifact is real
  and explains the broken sequence: holding a reading for 3 steps in a 7-cell corridor drives
  the stale agent into a boundary, and clamping repositions it onto a known cell. Roughly 70%
  of its "successes" there are wall-assisted, not evidence of competence.
- **`p = 1`, noise 0.2: flagged by the `frozen` ablation** (0.376) while belief and stale sit at
  0.045 / 0.042. The rule as written says "any agent", so the flag stands as pre-registered —
  but it is driven by an agent that is not part of the primary comparison. **Recommendation for
  the director (not applied here):** scope the rule to the primary pair in future contracts.
  The threshold has not been moved and no condition has been reinstated.

## D. Secondary slip condition (`s = 0.1`) — largely inconclusive

| noise | p | belief | stale | null | paired [95% CI] | contaminated |
|---|---|---|---|---|---|---|
| 0.2 | 1 | 0.888 | 0.895 | 0.895 | −0.007 [−0.015, +0.001] | YES (frozen) |
| 0.2 | 2 | 0.779 | 0.802 | 0.896 | −0.023 [−0.042, −0.005] | no |
| 0.2 | 3 | 0.725 | 0.778 | 0.894 | −0.053 [−0.073, −0.032] | YES |
| 0.2 | 5 | 0.663 | 0.162 | 0.869 | +0.501 [+0.479, +0.523] | YES (stale 0.579) |
| 0.5 | 1 | 0.605 | 0.615 | 0.615 | −0.010 [−0.027, +0.007] | no |
| 0.5 | 2 | 0.495 | 0.466 | 0.609 | +0.029 [+0.007, +0.052] | YES |
| 0.5 | 3 | 0.456 | 0.548 | 0.576 | −0.092 [−0.116, −0.069] | YES |
| 0.5 | 5 | 0.423 | 0.076 | 0.491 | +0.346 [+0.326, +0.367] | YES |

**When motion is unreliable, the advantage does not survive at short gaps** — at `p = 2` (the
only clean short-gap cell) the stale agent is slightly *better* (−0.023, CI excludes zero). The
large-gap cells where belief still dominates are all wall-contaminated. So the honest verdict on
the secondary condition is: **inconclusive, with a small negative signal at short gaps.** No
redesign was attempted, per ruling 6.

## E. The result the design did not anticipate — waiting is free

The `null` agent — the reference that was supposed to be weak, which acts only when it has fresh
evidence and holds still otherwise — **is the most accurate agent in almost every condition**,
including `p = 5` where it beats the belief agent 0.889 vs 0.810 (noise 0.2).

It does so at **13.63 steps versus 1.95** — roughly 7× slower.

Nothing in this environment charges for time. There is no step cost, no deadline, no moving
target, and a 40-step budget that a patient agent can spend freely. Under those conditions
"do nothing until the world tells you where you are" is close to optimal, and the belief agent's
speed earns it nothing. This was not foreseen in the design and it is not a bug to tune away:
**the environment made estimation decision-relevant (as intended) but left inaction costless,
so it rewards patience rather than knowledge.**

## Verdict

- **Primary criterion: MET** in all uncontaminated conditions — a predictive belief produces
  materially better termination decisions than a stale observation under the same policy, with
  the advantage ≈0 when observations are dense and large when they are sparse.
- **Mechanism: CONFIRMED** — belief alignment flat across gaps, ablation collapses; the stale
  agent fails specifically by overshooting and never declaring.
- **Secondary slip condition: INCONCLUSIVE**, with a small negative signal at short gaps.
- **Two conditions inconclusive by the pre-registered wall rule**, one of them driven by an
  agent outside the primary comparison.
- **A limitation was exposed that the contract did not anticipate:** costless waiting dominates
  both agents.

Interpretation stays narrow per §10: predictive state maintenance became behaviorally useful
when observations were intermittent, isolated from mere memory by the stale baseline. Nothing
here is a discovery about filtering, a new primitive, or evidence about anything beyond this
corridor. **Import + Build.** No canon change.

## What limitation this actually exposes

M1: belief was not decision-relevant. M2 fixed that — and revealed the next resistance
immediately behind it: **the environment does not charge for time, so knowing sooner is worth
nothing.** The belief agent's real advantage over the null agent is that it can act *before*
evidence arrives; the task gives that no value.

Any next milestone should be justified by that observation. The smallest change consistent with
it is a **cost on time** (a step cost, a deadline, or a target that does not wait), which would
make acting under uncertainty strictly better than waiting for certainty. That is a candidate,
not a decision — to be reviewed before any build, per the standing rule.

## Rulings incorporated (all approved)

1. STOP action — approved, structurally necessary; success scored after declaration.
2. Stale-observation as the load-bearing baseline; null agent secondary reference only.
3. Criterion inversion — behavior primary, belief quality mechanism evidence.
4. Gap sweep `p ∈ {1,2,3,5}`, `p=1` as null control; monotonicity predicted of the mechanism,
   estimates reported with uncertainty.
5. Deterministic motion primary, labelled a clean demonstration rather than a research test.
6. Action slip secondary robustness only.
7. Wall contacts recorded; contamination threshold pre-registered above.
8. Interpretation kept narrow (§10).
9. Approved to build; no further scope expansion.
