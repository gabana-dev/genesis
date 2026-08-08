# Current focus

**One thing at a time. This file names it.**

---

## Now

**Research triage — a turning point, not a lab.** A literature-reconciliation pass
(2026-08-08) established that Genesis's foundations are established science, not discoveries.
See [`../research/prior-art-and-opportunity-map.md`](../research/prior-art-and-opportunity-map.md).
The capability-construction phase is **over**; we do not climb the POMDP/RL ladder as research.

**The honest state, plainly:** the novel-cognitive-architecture thesis collapsed into
established science; the axiology/install thesis is an old philosophical problem (Hume's
is/ought), likely ill-posed; the **Research OS is the strongest surviving candidate
contribution, but its novelty and value are both unproven.**

**Open decision (the researcher's, not yet made):** which project is Genesis now —
(1) a methodology project (validate the Research OS), (2) a normal research project
(reflexive/performative decision-making, adjacent, crowded), (3) a modest philosophy project
(axiology, likely non-resolving), or (4) a completed learning vehicle. To be recorded as the
first entry in `research/decisions/`.

## The research cycle

Every cycle now follows:

```
Question → Contemplation (researchers + Claude) → Draft (researchers) →
Guardian Review (Claude) → Revision → Accepted Research
```

Claude's role in Contemplation is to sharpen and pressure-test — surface tensions,
point at what the conceptual landscape or canon already implies, check whether a
question is well-formed. Not to steer toward an answer. That boundary is the same
form/substance line as always ([`collaboration.md`](collaboration.md)), extended one
step earlier in the cycle than before.

## How the next question is chosen — superseded, see below

The uncertainty-reduction criterion above is superseded by the leverage rule adopted
2026-08-07. It's not wrong, just subsumed: leverage is uncertainty-reduction made
concrete against the remaining architecture, rather than assessed in the abstract.

## Phase: capability construction (recognized 2026-08-07)

Genesis has left the foundations-validation phase. The pipeline is proven (belief-necessity
travelled it end-to-end into canon). The question is no longer "is the theory true enough to
build on" but **"which experiment permanently adds the next architectural capability?"** We
are assembling the architecture of Genesis one earned capability at a time — each earned
through experiment before it becomes permanent. This is a research-guided engineering
project now, not a validation project.

## Standing rule: the capability-construction gate (adopted 2026-08-07, supersedes the leverage gate)

Every proposed laboratory must answer, explicitly, before it proceeds:

1. **What hypothesis does it test?**
2. **What uncertainty does it eliminate?**
3. **What permanent architectural capability does it earn?** — *paired with a compression
   check:* is this capability new machinery, or the belief-core re-aimed at a new target
   (per the [architectural roadmap](../research/architectural-roadmap.md))? If it claims to
   be new machinery, it carries the Architectural Compression Principle's burden of proof.
   Most labs earn a validated *application/reach*, not a new primitive.
4. **Which future laboratories become possible because this capability now exists?** —
   *the primary question.* A capability compounds; choose the one that unlocks the most.

A laboratory must earn a permanent capability (or genuinely falsify an accepted one). If it
only re-validates something already stable without earning new reach, defer it.

## Standing rule: the Method of Discovery is frozen (adopted 2026-08-07)

Seven steps, self-tested down from an original eight, documented across
[`../research/journal/2026-08-07-update-operator-invariants.md`](../research/journal/2026-08-07-update-operator-invariants.md)
and the entries around it. Treat it as stable. Don't refine it in isolation — use it on
real architectural questions. Only revise it if a concrete investigation exposes a
genuine failure in practice.

## Immediate next step

**Transitioned to literature-grounded system construction** (2026-08-08). The system goal is
intact (belief → learn → act → adapt → eventually markets); it is reached by *importing*
established machinery, not rediscovery. Working roadmap:
[`../research/system-roadmap.md`](../research/system-roadmap.md). Old capability graph retired.

**Milestone 1 — DONE** (2026-08-08):
[`../research/experiments/0004-minimal-closed-loop.md`](../research/experiments/0004-minimal-closed-loop.md),
`src/closed_loop.py`, `tests/test_closed_loop.py`. The first closed loop Genesis has built —
belief → action → changed world → new evidence → updated belief. Integration validity
**passed** (the action-conditioned Predict keeps the belief on a state the agent is moving;
the Update-only ablation loses alignment). Behavioral utility **did not materialize** — the
memoryless baseline matches it, and beats it slightly at noise 0.7. Recorded as a split
result, not a win.

**Milestone 2 — DONE** (2026-08-08):
[`../research/experiments/0005-sparse-observation-decision-relevance.md`](../research/experiments/0005-sparse-observation-decision-relevance.md),
`src/sparse_loop.py`, `tests/test_sparse_loop.py`. Sparse observations made belief
behaviorally load-bearing: the predictive agent beats a stale-observation agent running the
*identical* policy by +0.810 [+0.796, +0.824] at gap 5, ≈0 at the p=1 control. It fails as
predicted — the stale agent cannot detect its own arrival, overshoots, and never declares.
Slip condition inconclusive; p=3 excluded by the pre-registered wall rule.

**But:** the throwaway null agent — waits for fresh evidence, holds still otherwise — is *more
accurate* than the belief agent (0.889 vs 0.810) at 7× the steps. Nothing charges for time, so
patience beats knowledge.

**Milestone 3 — proposed, design-reviewed, REJECTED. The toy sequence is closed at M2.**
A cost on time would have answered a question already available in closed form from M2's data
(λ* ≈ 0.0068), could not preserve the identical-policy principle, and would have made belief win
by construction. Draft decision:
[`../research/decisions/0002-close-the-toy-milestone-sequence.md`](../research/decisions/0002-close-the-toy-milestone-sequence.md)
— **awaiting review; canon deliberately untouched.**

**The lesson that closed the sequence:** every capability Genesis added met a cheap
environmental substitute, and the reflex was to modify the environment until the substitute
failed. That is capability-demonstration engineering, not research — the `0001`
manufactured-necessity failure mode displaced from the capability onto the environment.
**Existence, correctness and usefulness are three separate claims**, and usefulness is only
demonstrable against a cost, so an environment can always be built to make any capability look
necessary. Building it demonstrates nothing.

**Next:** no experiment by default. A drafted **environment-first gate** now precedes the
research gate (environment justified before capability). Applied to Genesis's own market goal it
returns *no justified environment* — so the laboratory sequence stops. Three phase options are
on the table in `0002` (recommended: deploy the machinery against a real environment and label
it engineering, not research). **Researcher's decision; nothing proceeds until it is made.**

DR0001's formal direction decision remains open; this construction direction is the accepted
*working* posture, not a formal closure of that decision.

Note: the capability-construction gate above and the Method-of-Discovery freeze remain on
record as history, but the gate is now subordinate to the prior-art rule — *no laboratory at
all* for anything classified as import (A) in the opportunity map.

## Not in focus right now — abandoned or frozen

- **Abandoned (F):** primitive-counting; the "differentiator sentence" search; re-deriving
  established estimation/control theory as if it were discovery; the capability graph as a
  *research* roadmap (it is a dependency map).
- **Import if needed (A), never as research:** dynamic-state filtering (was "Lab 3"),
  unsupervised obs-model, closed-loop RL, causal inference.
- **Frozen:** `0002` Emergence, `0003` Time, `constitution.md`, `ontology.md`.
- **Open but unchosen (D/E):** Research-OS validation; reflexive/performative decision-making;
  the axiology/install problem.

---

*Last updated: 2026-08-08.*
