# 2026-08-08 — Belief earned its keep, and then an agent that does nothing beat it

> Milestone 2. Contract pre-registered and approved before the build:
> [`../experiments/0005-sparse-observation-decision-relevance.md`](../experiments/0005-sparse-observation-decision-relevance.md).
> Code: `src/sparse_loop.py`. Check: `tests/test_sparse_loop.py`.
> Continues [`2026-08-08-first-closed-loop-belief-without-behavior.md`](2026-08-08-first-closed-loop-belief-without-behavior.md).

## The thing we set out to do, we did

Milestone 1 ended with a clean split: the filter worked, the belief was useless for acting.
The diagnosis was that observations arrived every step, so the freshest reading was always a
good enough decision input. Milestone 2 removed exactly that and nothing else.

It worked, and the mechanism was the predicted one. Under an observation period of 5, the
stale-observation agent — same policy, same environment, same random draws, differing only in
that its position estimate is an old reading rather than a propagated belief — **declares
arrival in 24% of episodes and is correct in none of them.** It walks past the target and
oscillates until the step budget runs out. The belief agent declares in 100% of episodes, after
1.95 steps, correct 81% of the time.

That is not "belief is faster." It is the categorical thing we predicted in the design review:
**the predictive agent knows when to stop because it knows what it did.** The stale agent
cannot detect its own arrival, and no amount of memory fixes that — only propagation does.
The paired advantage is +0.810 [+0.796, +0.824] at `p=5` and +0.015 at `p=1`, which is the
Milestone 1 replication control coming out flat exactly as pre-registered.

The mechanism evidence is equally clean: the full filter's posterior on the true cell is *flat*
across gap age (0.65 at gap 0, 0.65 at gap 3) while the frozen-belief ablation collapses within
a single unobserved step (0.455 → 0.133) and its MAP error grows to 4.2 cells. Predict is
carrying the estimate across the gap, and the estimate is carrying the decision.

## And then the agent that does nothing won

The `null` agent was in the design as a weak reference — the throwaway. It acts only when it
has fresh evidence and holds still otherwise. It has no memory, no propagation, no state.

It is the most accurate agent in almost every condition. At `p=5`, noise 0.2: **0.889 versus
the belief agent's 0.810.**

It takes 13.63 steps to the belief agent's 1.95.

Nothing in the environment charges for time. No step cost, no deadline, no target that moves,
and a 40-step budget a patient agent can spend freely. Under those conditions the optimal
strategy is to refuse to act until the world tells you where you are — and the belief agent's
entire advantage, that it can act *before* evidence arrives, is worth precisely nothing.

I did not foresee this in the design review. It is not a bug, and per the standing rule it was
not tuned away after the fact. It is the environment's next resistance, and it arrived the
moment the previous one was removed.

## The shape of this is worth noticing

M1 built an environment that tested whether the agent can *know*. It did not test whether
knowing *matters*, so belief looked useless.

M2 made knowing matter — and immediately exposed that the environment does not test whether
knowing *sooner* matters, so speed looks useless.

Each milestone's environment has been generous in exactly the dimension that makes the new
capability unnecessary. That is not bad luck. A deliberately boring environment is boring in
some specific way, and the specific way it is boring is what silently sets the ceiling on what
any capability can be shown to be worth. The environment is not the backdrop to the
experiment; it *is* the experiment's claim about what competence consists of.

Stated as the lesson: **capability is only demonstrable against a cost.** Estimation could not
show its value until observations were scarce. Prediction cannot show its value until *time*
is scarce.

## The wall rule earned its place

The pre-registered contamination threshold — 25% of an agent's correct declarations being
wall-assisted — fired on the `p=3` conditions, where the stale agent's clamp-share hit 0.688
and 0.739. Roughly 70% of its apparent successes there were the corridor boundary repositioning
it onto a known cell, not competence.

Those cells are also the ones that break the otherwise increasing sequence of the belief
advantage. Without the threshold fixed in advance, there would have been an obvious temptation:
look at the broken trend, notice the wall artifact, and exclude `p=3` *after* seeing that
excluding it produces a monotone result. The threshold made that decision before the data
existed, which is the only thing that makes the exclusion honest rather than convenient.

One flaw in my own rule, recorded rather than patched: it says "any agent", so the `p=1`
noise-0.2 condition was flagged on the strength of the frozen *ablation*, an agent not in the
primary comparison, while belief and stale sat at 0.045. The flag stands as written. The fix
belongs in the next contract, not in this one.

## What I am not claiming

Nothing here is a discovery about Bayesian filtering. Filtering across missing observations is
decades old (Sinopoli 2004; dead reckoning between fixes). The claim is bounded to exactly
this: predictive state maintenance became behaviorally useful when observations were
intermittent, and that usefulness was isolated from merely having memory by a baseline running
the identical policy. Import + Build. No canon change, no new primitive, no architecture claim.

The secondary slip condition should also be recorded honestly as a non-result: with unreliable
motion, the advantage did not survive at short gaps (the one clean cell had the stale agent
slightly *ahead*), and every large-gap cell where belief dominated was wall-contaminated. That
condition is inconclusive. It was left inconclusive.

## What comes next is not mine to decide

The observed limitation is specific: **the environment does not charge for time.** The smallest
change consistent with it is a cost on time — a step cost, a deadline, or a target that does
not wait — which would make acting under uncertainty strictly better than waiting for
certainty, and would put the belief agent's 1.95 steps against the null agent's 13.63 in a
setting where that difference means something.

That is a candidate for review, not a plan. The rule holds: the next milestone comes from the
resistance the last one exposed.
