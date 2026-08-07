# Program Status

Not philosophy. Not research. Navigation — so that months from now, with a much larger
repository, orientation is instant.

Maintained by Claude as a factual snapshot (Type-2), same as
[`../ai/project_state.md`](../ai/project_state.md) but at milestone granularity rather than
session granularity. Update it whenever a milestone completes.

Project phases are defined once, authoritatively, in
[`../canon/roadmap.md`](../canon/roadmap.md). This document does not define phases — it
drills into the milestones of whichever phase is current.

---

## Current Phase

**Laboratory 1** — transitioned 2026-08-07 from the Foundation phase. Genesis now optimizes
for turning earned foundations into executable knowledge, not for deriving more foundations.
The loop from here: research earns architecture → architecture generates implementation →
implementation exposes ambiguity → ambiguity generates research.

## Milestone: Epistemic Foundation — complete; Laboratory 1 — complete

The Foundation milestone (canon + primitives + the Update/Belief theory) is done. As of
2026-08-07 the first executable laboratory exists and ran: Reception, Update, and a
belief-state implemented cleanly from the canon; belief-state agent 0.929 vs memoryless
0.699 under partial observability. Concepts became software. See
[`experiments/0001-belief-vs-memoryless.md`](experiments/0001-belief-vs-memoryless.md).

## Status

`15 / 18 milestones complete` *(frozen items excluded from the count)*

```
████████░░ 83%
```

*(Derived from the counts below — completed ÷ (completed + remaining). Not a fixed figure;
recompute when the lists change. The high number reflects the Foundation phase being nearly
done — it does not mean Genesis is nearly done; the Laboratory and Product phases are almost
entirely ahead.)*

## Completed — Research OS

- [x] Collaboration Contract (`ai/collaboration.md`)
- [x] Guardian (role defined in `ai/collaboration.md`)
- [x] Research Methodology (`canon/research-methodology.md`)
- [x] Program Status (this document)
- [x] Conceptual Landscape (`research/conceptual-landscape.md`)
- [x] Hypothesis Framework (`research/hypotheses/README.md`)
- [x] Explorations Framework (`research/explorations/README.md`) — a category added
  after the Research OS was first marked complete; see note below

## Completed — Genesis Theory

- [x] Vision (`canon/vision.md`)
- [x] Philosophical Foundations (`canon/philosophical-foundations.md`)
- [x] Epistemology (`canon/epistemology.md`)
- [x] 0001 · Quality of Knowing (`research/hypotheses/0001-quality-of-knowing.md`) — active
- [x] Primitives (Reception, Update) + Update invariants + algebra unification (journal)
- [x] Belief-necessity (partial observability forces a belief-state) (journal)

## Completed — Architecture & Laboratory

- [x] Architecture Part B — the minimal adaptive loop, earned-only (`canon/architecture.md`)
- [x] The pipeline, two streams — Production + Governance, with the variation bar for Canon
  (`canon/architecture.md` Part A)
- [x] Laboratory 1 — belief-state vs memoryless (`research/experiments/0001-...`)
- [x] Laboratory 1 postmortem (`research/journal/2026-08-07-laboratory-1-postmortem.md`)
- [x] Laboratory 2 — learned observation model; variation test passed
  (`research/experiments/0002-learned-observation-model.md`). Belief-necessity survived one
  variation (representation); observation model shown to be a second Update loop.

## Governance stream (in progress)

- [ ] Belief-necessity → Canon. Derived, built, validated (Lab 1), survived learned-model
  variation (Lab 2). Awaiting researcher ratification into `canon/epistemology.md` at
  confidence "working" (one variation survived; environment variation still pending "stable").
  Draft prepared; Claude does not author canon.

## In Progress

- [ ] 0002 · Emergence — one seed captured (`Current Observations`: the holon/heterarchy
  candidate framing), 13 of 14 fields still unwritten. Not yet a formed hypothesis.

## Completed — Explorations

*Neither Research OS nor Genesis Theory — explorations investigate method, not belief.
Not tracked as required milestones the way canon docs and hypotheses are; listed here for
visibility since they're real, finished artifacts.*

- [x] What Makes a Good Hypothesis (`research/explorations/what-makes-a-good-hypothesis.md`)

## Remaining

*Selection is now by laboratory leverage: what unlocks the next executable laboratory or
improves one that exists. Not by intellectual interest, not by list order.*

- [ ] Laboratory 2 — candidate: the agent must *learn* its observation model rather than be
  given it (opened by `research/questions/observation-model-provenance.md`)
- [ ] 0004 · Context / 0005 · Belief Revision — reframed: what algebra the belief-state lives
  in; may now be informed by building rather than more analysis
- [ ] Ontology (`canon/ontology.md`) — still to be *earned* from results, not authored ahead

**Frozen** (nothing depends on them now): `0002` Emergence, `0003` Time, constitutional
principles (`constitution.md`), the caring fork, method/family meta-work.

> Note: the Research OS was marked complete before `explorations/` existed as a category.
> Explorations don't fit cleanly into the Research OS / Genesis Theory split — they're
> about how Genesis researches, not what it believes or how the lab is structured.
> Left as a visible third grouping rather than force-fit into either track; the
> researchers may want to formalize that split explicitly.

---

*Last updated: 2026-08-06.*
