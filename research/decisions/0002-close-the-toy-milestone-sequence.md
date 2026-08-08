# 0002 — Close the toy-milestone sequence; adopt an environment-first gate

**Date:** 2026-08-08
**Status:** **DRAFT — awaiting researcher review. Not canon. Nothing here has been written into
`canon/`.**
**Reversibility:** cheap to reverse as a plan; costly as a self-conception (it names a second
manufactured-necessity failure mode, after [`0001`](0001-research-triage-reframe.md)).

## Context

Three milestones and one design review, in sequence:

- **M1** ([`../experiments/0004-minimal-closed-loop.md`](../experiments/0004-minimal-closed-loop.md))
  — closed-loop integration demonstrated. The action-conditioned predict/update machinery works
  while the agent moves the very state it tracks. Behavioral advantage did not materialize.
- **M2** ([`../experiments/0005-sparse-observation-decision-relevance.md`](../experiments/0005-sparse-observation-decision-relevance.md))
  — under sparse observations the maintained belief became behaviorally load-bearing
  (+0.810 [+0.796, +0.824] at gap 5 vs a stale-observation agent on an identical policy). But a
  throwaway agent that simply waits for fresh evidence was *more accurate still*, because
  nothing in the environment charged for time.
- **M3 design review** — adding a cost of waiting would invoke established optimal-stopping /
  decision-theoretic machinery, would answer a question already available in closed form
  (§F of `0005`: crossover λ* ≈ 0.0068), and could not preserve the identical-policy principle.
  It would have produced a belief win *by construction rather than by contest*.

The pattern across all three is the finding:

> **Every time Genesis added a capability, the environment offered a cheap substitute for it —
> and the proposed response was always to modify the environment until the substitute failed.**

That is capability-demonstration engineering, not research. It is the same failure mode as
[`0001`](0001-research-triage-reframe.md) — manufacturing necessity around imported machinery —
displaced from the *capability* onto the *environment*.

## Decision (proposed)

1. **The toy-corridor milestone sequence is closed at M2.** No M3. The corridor is not modified
   further to make an imported capability look necessary.
2. **The λ-crossover result is recorded as Import/Analysis**, a consequence of M2 — not a new
   experiment, milestone, or finding (`0005` §F).
3. **Adopt the environment-first gate** (drafted below) as a precondition on any future
   experiment, sitting *in front of* the existing research gate in
   [`../../canon/research-methodology.md`](../../canon/research-methodology.md).
4. **Do not propose an experiment merely because a capability has not been demonstrated yet.**
   An experiment requires a concrete problem that needs the capability *and* a genuine question
   prior art does not already answer.
5. **This is not a failure.** The milestones did their job: they established that the machinery
   works, and they exposed where the research program was manufacturing necessity.

## The general lesson (proposed for canon)

> **Existence, correctness, and usefulness are three separate claims.**
>
> That a capability exists says nothing about whether an implementation is correct. That an
> implementation is correct says nothing about whether it is useful. Usefulness is a claim about
> a *relationship between a capability and an environment*, and it is only demonstrable against
> a cost — some consequence for not using the capability.
>
> Therefore an environment can always be built in which any capability is useful. **Building
> that environment demonstrates nothing.** Genesis does not manufacture an environment in order
> to make a capability look necessary.

## Draft canon amendment — the environment-first gate

*Proposed insertion into `canon/research-methodology.md`, immediately before "The research gate
(mandatory)". Wording is a draft for review, not adopted text.*

> #### The environment-first gate (mandatory, precedes the research gate)
>
> Before the research gate is applied to a proposed capability, the *environment* must be
> justified. Five questions, answered in order:
>
> 1. **What real problem or system requirement creates the need?**
> 2. **Why can a simpler established strategy not solve it?**
> 3. **What established machinery already addresses it?**
> 4. **What specifically remains unresolved?**
> 5. **Does the proposed experiment test that unresolved question, or merely demonstrate
>    imported machinery?**
>
> Dispositions:
>
> - If **(4)** is *"nothing unresolved"*, the work is **integration or validation**. It may
>   still be worth doing, but it is labelled as engineering and claims nothing.
> - If **(5)** is *"merely demonstrate imported machinery"*, **no laboratory is warranted** —
>   unless the demonstration is itself an explicit engineering objective, stated as such.
> - If the environment must be altered to make the capability necessary, the alteration is the
>   claim under examination, and it is almost certainly a manufactured one.
>
> The environment is not the backdrop to an experiment. It *is* the experiment's claim about
> what competence consists of, and it silently sets the ceiling on what any capability can be
> shown to be worth.

## Applying the gate to Genesis's own system goal

The stated goal: *a belief-maintaining, learning, acting, adapting agent that can eventually
operate in a domain such as markets/trading.* Run honestly through the gate:

1. **What real problem creates the need?** — None currently. There is no capital at risk, no
   deployment, no user, no stakeholder. The need is self-generated by the roadmap.
2. **Why can a simpler established strategy not solve it?** — For trading, simpler strategies
   largely *can*. The binding difficulty is signal-to-noise, nonstationarity, adversariality and
   costs — a **domain** difficulty, not an architecture gap. A closed-loop belief agent is not
   the bottleneck.
3. **What established machinery addresses it?** — Effectively all of it: filtering, POMDPs, RL,
   execution algorithms, sequential decision theory.
4. **What remains unresolved?** — Only what
   [`../system-roadmap.md`](../system-roadmap.md) already flagged: reflexivity/performativity at
   non-trivial scale, and the non-installed-objective question (philosophical). Both are
   recorded as **blockers**, and the first requires an agent large enough to move the market it
   predicts — unreachable at this scale.
5. **Does an experiment test that, or demonstrate imports?** — Any market simulator Genesis
   builds would need a handcrafted price-impact function, i.e. the reflexivity being
   "discovered" would be the reflexivity that was typed in. **That is the corridor mistake
   again, at higher cost.**

**Conclusion: no environment is currently justified for a research laboratory. Per the
researcher's own instruction, the laboratory sequence stops rather than manufacturing one.**

## Recommendation for the next phase — three honest options

The decision is the researcher's. Stated plainly, with the recommendation first.

### Option A (recommended) — deploy against a real environment; call it engineering, not research

The one class of environment available to this researcher whose difficulty is **intrinsic** —
not installed by design — is the live systems already running: PsTally, Stoka. These contain
genuine partially-observed closed-loop problems with real costs for being wrong, real
intermittency, and no designer able to tune the difficulty. **PsTally's console monitoring is
literally an M2-shaped problem occurring in the wild**: a hidden state (is a console in use),
intermittent and unreliable observation (UDP discovery that genuinely fails on some gateways),
a real cost to waiting (unbilled minutes), and a real cost to acting wrongly (ghost alerts).

Under the gate this is honestly classified: **integration/engineering, Import + Build, no
research novelty claimed.** That is not a demotion — it is the first environment in this project
whose difficulty Genesis did not author. It would test whether the imported machinery survives
contact with a world that was not designed to accommodate it.

### Option B — pursue the one genuinely open question, and accept it is likely blocked

Reflexivity/performativity is the surviving open edge from `0001`. It needs scale Genesis does
not have. Pursuing it would be theoretical or literature work, not laboratory work, with a high
probability of terminating in "correctly identified as out of reach."

### Option C — close the research program and preserve it as a record

Declare the arc complete: a self-directed program that derived established cognitive machinery
from first principles, then correctly identified that it had done so, twice. The artifact of
value is the **method** — the pre-registration discipline, the ablation habit, the pre-committed
contamination thresholds, the willingness to publish a negative result and reject its own
proposed next milestone. `0001` already named the Research OS as the strongest surviving
candidate contribution; its novelty remains unvalidated, but its *use* here is demonstrated.

**A and C are compatible** — C preserves the record, A gives the machinery a real environment.

## What this decision explicitly does not claim

Not that the milestones failed. Not that belief maintenance is useless. Not that the machinery
is wrong — M1 and M2 both validated it. Not that no future experiment could be justified; only
that none currently is, and that the burden now sits with the environment rather than the
capability.

## Requested

Review of (a) the draft canon amendment and (b) the phase recommendation. Canon remains
untouched until ratified.
