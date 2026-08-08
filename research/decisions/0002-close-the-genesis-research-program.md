# 0002 — Close the Genesis cognitive-architecture research program

**Date:** 2026-08-08
**Status:** **draft — awaiting researcher ratification.** Nothing here is written into `canon/`.
**Reversibility:** one-way in practice. Reopening would require a genuine research problem
arriving from outside, not a decision to resume.
**Closes:** the open direction question in [`0001`](0001-research-triage-reframe.md) — **Option
D, completed learning vehicle**, is selected.
**Supersedes:** this record's own earlier draft (the toy-milestone closure and its Option A
recommendation), preserved in git history at `85a8c5e` under the filename
`0002-close-the-toy-milestone-sequence.md`.

---

> **Genesis reached the point where continuing the original research program would require
> manufacturing novelty rather than discovering it. Therefore the program is deliberately
> closed.**

That sentence is the decision. Everything below is the reasoning and the record.

## Context

[`0001`](0001-research-triage-reframe.md) established that Genesis's foundations were
established science and left one question deliberately open: *which project Genesis now is.*
Four options were named; none was selected. The immediate next action was to keep building and
see what the evidence forced.

What followed was three milestones and two audits:

- **M1** ([`../experiments/0004-minimal-closed-loop.md`](../experiments/0004-minimal-closed-loop.md))
  — the closed loop was built and the action-conditioned predict/update machinery validated.
  The belief tracked a state the agent was itself moving. It produced **no behavioral
  advantage**.
- **M2** ([`../experiments/0005-sparse-observation-decision-relevance.md`](../experiments/0005-sparse-observation-decision-relevance.md))
  — sparse observations made the belief behaviorally load-bearing (+0.810 [+0.796, +0.824] at
  gap 5 against a stale-observation agent running an identical policy). Then a throwaway agent
  that simply waited for evidence proved **more accurate still**, because nothing in the
  environment charged for time.
- **M3** — proposed, design-reviewed, **rejected**. The question was answerable in closed form
  from M2's own data (λ* ≈ 0.0068), the design could not preserve the identical-policy
  principle, and it would have produced a belief win by construction rather than by contest.
- **The environment audit** — applying an environment-first test to Genesis's own market goal
  returned *no justified environment*. Reflexivity needs unreachable scale; a hand-built market
  simulator would rediscover the price-impact function that was typed into it.
- **The PsTally problem-first audit** (external; lives in the PsTally repo, not here) — a real
  deployed system produced four genuine operational problems, and **every one was solved by
  established engineering**. The problem that most resembled M2's structure was best served by
  debouncing, not by belief machinery.

The pattern across all of it is the finding that closes the program:

> **Every time Genesis added a capability, the environment offered a cheap substitute for it —
> and the available response was always to modify the environment until the substitute failed.**

That is the [`0001`](0001-research-triage-reframe.md) failure mode — manufacturing necessity
around imported machinery — displaced from the *capability* onto the *environment*. Recognising
it a second time, in a different disguise, is what makes closure the honest move rather than a
mood.

## Decision

1. **The cognitive-architecture thesis is retired.** Its foundations — belief states, recursive
   Bayesian updating, observation-model learning, filtering, active sensing, closed-loop
   model-based agency — are established science. Genesis re-derived them independently. That
   built real understanding; it did not produce a new architecture, and no such claim is made.
2. **The axiology / install question is unresolved philosophy, not a Genesis engineering
   objective.** It is the is/ought gap. It is not Genesis's to solve, and it is not held open as
   a pending work item.
3. **The Research OS is useful but not an established novel contribution.** It demonstrably
   worked *here* — pre-registration, ablations, pre-committed contamination thresholds, and a
   program willing to reject its own next milestone. Its novelty against existing research-
   methodology systems was never validated, and this record does not claim it.
4. **The toy-milestone sequence is closed at M2.** No M3. The corridor is not modified further
   to make an imported capability look necessary.
5. **PsTally is explicitly not a Genesis phase.** It is a real product, and the fixes identified
   by its audit (debounce/hysteresis; alert thresholds and feedback instrumentation; the
   hardware/session reconciliation; fleet networking) proceed as ordinary product engineering,
   tracked in PsTally. Genesis does not own PsTally, did not produce those findings, and takes
   no credit for them.
6. **DR0002's earlier Option A is superseded.** "Deploy the Genesis machinery against a real
   environment" is withdrawn as a Genesis phase, for the reason in (5).
7. **Genesis's experiments, journals, and methodological lessons are preserved in full** — the
   negative results especially. Nothing is deleted or retrospectively smoothed.
8. **No new research direction is selected.** Not to keep the project alive, not as a gesture,
   not as a placeholder. The absence of a next direction is the accurate state, and it is
   recorded as such.

## What Genesis established

Stated plainly, without inflation. These are the outputs, and they are enough:

- **A working understanding of the estimation/control machinery** it reconstructed — belief
  states, the Update algebra, action-conditioned prediction, and the closed perception→action
  loop, validated in code with ablations rather than asserted.
- **The distinction between capability, correctness, and usefulness** as three separate claims —
  and the corollary that usefulness is only demonstrable against a cost, so an environment can
  always be built in which any capability looks necessary. Building that environment
  demonstrates nothing.
- **An honest record of where its supposed discoveries were prior art**, produced by the project
  itself rather than imposed from outside.
- **A research process capable of detecting its own false novelty** — twice, in two different
  forms, the second time faster than the first.
- **A demonstrated reason not to manufacture experiments around imported capabilities**, which
  is the practical result most likely to change future behaviour.

## Reasoning

Measured against prior art, the thesis does not survive. Measured against real environments, the
machinery is not the bottleneck. Measured against its own milestone sequence, each new capability
met a cheap substitute, and the only way forward was to author environments that punished the
substitute — which is engineering a conclusion, not testing one.

A research program is justified by an unresolved question, not by momentum, sunk effort, or the
discomfort of stopping. Genesis currently has no unresolved question that it is positioned to
answer. Continuing under those conditions would mean searching for a reason to continue, which is
the definition of manufacturing novelty.

Closing is therefore not a verdict that the work failed. It is the same standard the project
applied to M3 and to the PsTally audit, applied one level up — to itself.

## What we gave up

> The prospect that Genesis would produce a novel cognitive architecture, a new primitive, or a
> publishable research contribution.

Also given up: the capability ladder as a source of direction, and the assumption that a
sufficiently clever environment could turn imported machinery into a discovery.

Kept: the understanding, the code, the negative results, the method, and the record of how a
project talked itself out of two false claims of novelty.

## What would reopen this

Nothing internal. Not a new capability, not a new environment, not a new toy laboratory.

Only this: **a genuinely unresolved problem arriving from real system constraints**, surviving
the prior-art gate, and demanding something no established method supplies. If that happens,
Genesis has a method ready for it. If it does not happen, the program stays closed, and that is
an acceptable outcome.

## Preserved from the earlier draft — the environment-first gate (NOT canon)

Retained as a methodological artifact, deliberately not promoted. The standing instruction is
that a lesson learned during Genesis is not automatically a canonical principle; it must be seen
to govern real decisions before elevation. It has governed exactly two so far (rejecting M3;
framing the PsTally audit), which is not yet enough.

> **The environment-first gate.** Before the research gate is applied to a proposed capability,
> the environment must be justified:
>
> 1. What real problem or system requirement creates the need?
> 2. Why can a simpler established strategy not solve it?
> 3. What established machinery already addresses it?
> 4. What specifically remains unresolved?
> 5. Does the proposed experiment test that unresolved question, or merely demonstrate imported
>    machinery?
>
> If **(4)** is *"nothing unresolved"*, the work is integration or validation, labelled as
> engineering, claiming nothing. If **(5)** is *"merely demonstrate imported machinery"*, no
> laboratory is warranted unless the demonstration is itself an explicit engineering objective.
> **If the environment must be altered to make the capability necessary, the alteration is the
> claim under examination — and it is almost certainly a manufactured one.**

## Status of the repository after ratification

`canon/` unchanged. `research/` and `src/` preserved as a completed record. The roadmap and the
`ai/` trackers to be updated to reflect closure — **on ratification, not before.**

## Source

[`0001`](0001-research-triage-reframe.md); experiments
[`0004`](../experiments/0004-minimal-closed-loop.md) and
[`0005`](../experiments/0005-sparse-observation-decision-relevance.md); journal entries
[`2026-08-08-first-closed-loop-belief-without-behavior`](../journal/2026-08-08-first-closed-loop-belief-without-behavior.md)
and
[`2026-08-08-sparse-observation-the-patient-agent-wins`](../journal/2026-08-08-sparse-observation-the-patient-agent-wins.md);
[`../prior-art-and-opportunity-map.md`](../prior-art-and-opportunity-map.md);
[`../system-roadmap.md`](../system-roadmap.md). The PsTally audit is external to this repository
by decision (5).
