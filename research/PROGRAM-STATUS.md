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

## Current Phase — superseded 2026-08-09

**Research programme CLOSED; engineering ACTIVE.** Both decision records were ratified
2026-08-09: [`decisions/0002-close-the-genesis-research-program.md`](decisions/0002-close-the-genesis-research-program.md)
(closure) and [`decisions/0003-engineering-posture-real-data.md`](decisions/0003-engineering-posture-real-data.md)
(engineering posture). The research-triage phase described below is history; it is preserved
rather than rewritten, per DR0002 (7).

Active engineering: **RDB-1**,
[`experiments/0006-rdb-1-real-data-bridge.md`](experiments/0006-rdb-1-real-data-bridge.md) —
import + build, no novelty claimed, development period complete, holdout unopened. Adaptation
returned a large stable positive for the rolling window; the model is indistinguishable from
persistence at its best.

Undecided and the researcher's: whether to open the holdout, and what the next capability is.
No sequence of milestones is pre-authorized (DR0003 §10).

## Superseded — the research-triage phase

**Research triage (2026-08-08).** Not a laboratory phase. A literature-reconciliation pass
([`prior-art-and-opportunity-map.md`](prior-art-and-opportunity-map.md)) established that
Genesis's foundations are established science, and re-founded how work is chosen: no lab for
anything already solved in the literature. The milestone counter below is **retired** — it
measured progress up a capability ladder that turned out to be import, not research, so the
percentage was measuring the wrong thing.

## The honest status

- Labs 1–3 ran (belief-necessity validated → canon Working; observation-model learnable;
  choice-over-information — a clean *negative* that exposed primitive-counting as
  description-relative).
- **The novel-cognitive-architecture thesis has collapsed into established science.**
- **The axiology/install thesis is an old philosophical problem** (Hume's is/ought), likely
  ill-posed.
- **The Research OS is the strongest surviving candidate contribution** — novelty and value
  both still unproven.
- **Open decision (researcher's):** which project Genesis now is. See
  [`../ai/current_focus.md`](../ai/current_focus.md) and the opportunity map.

## Retired milestone counter

The former "15/18, 83%" figure is retired. It counted rungs of a POMDP/RL capability ladder
now classified as *import*, so it overstated research progress. Progress is no longer
measured by capability rungs; it is measured by whether Genesis produces something the
literature does not already have — which the triage found it has not yet done.

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

## Governance stream

- [x] **Belief-necessity → Canon (2026-08-07).** Ratified by the researcher into
  `canon/epistemology.md` as "Necessity of Internal State under Partial Observability" at
  status **Working**. Generalized on ratification: canon preserves the invariant (maintained
  internal state under partial observability), with the belief-state as *one realization* —
  not the implementation. **This is the pipeline's first full closure:** an idea travelled
  Research → Architecture → Implementation → Experiment → Postmortem → Canon end-to-end.
  Promotion to *Stable* pending environment variation.

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
