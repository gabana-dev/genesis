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

**Next:** Milestone 2 — the same loop with **sparse observations**, chosen from M1's observed
limitation: belief only becomes behaviorally load-bearing when a single current observation is
insufficient to decide. Intermittent-observation filtering = Import; harness = Build. Awaiting
researcher approval before build. Still no RL, planning, market data, trading, or reflexivity.

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
