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

## Current — 2026-08-18

**Research programme CLOSED (DR0002); engineering ACTIVE (DR0003).** No research direction is
selected. Every market result classifies itself as *import* or *engineering* — there are no
research findings claimed.

**Completed since the market line opened:**

| | | |
|---|---|---|
| [BAV-1](experiments/0007-bav-1-book-agreement-validation.md) | 2026-08-10 | The recorder's completeness label **predicts** agreement with an independent channel, p = 0.0165. Fidelity and self-knowledge measured separately. |
| [MEASURE-1](experiments/0008-measure-1-cost-of-being-right.md) | 2026-08-10 | Linear structure at 15m–60m, well-powered; affordability begins at 4h. **§8 retracted the overlap claim**: at ≥4h the test was blind, and 80% power at daily scale would need **68 years**. |
| [EXEC-1](experiments/0009-exec-1-maker-advantage.md) | 2026-08-17 | **60.93% of the 3 bps maker advantage survives** adverse selection at the touch at 60s (1.828 bps). Kill condition not triggered. 580,658 events, 0 sequence gaps. X3/X4/X6/X7 nulls are **structural** — the 0–5 tick grid spans 151× less than the effect it was built to modulate. |

**Decision records:** DR0004 closed RDB-1 and sealed the holdout · DR0005 authorised the
orientation layer (`status.py`), which reports and may not decide · **DR0006 requires every
predictive experiment's contract to name its consumer, the decision it changes, a do-nothing
baseline and a wiring kill condition** — or it is not declared.

**Ledger:** 27 declared, 27 recorded, **0 outstanding**, chain verified.

**Running now:** a 48-hour BTCUSDT recording carrying **book *and* trades** on one clock
(`~/genesis-evidence/q4/`), the first to include the aggTrade stream. It is a soak test of new
code and carries no contract and no question — per DR0006 nothing predictive may be declared
against it.

**Open and the researcher's:** which direction, if any, comes next — and nine documented
contradictions between what this repository claims and what it contains, listed in
[`CURRENT-STATE-2026-08-18.md`](CURRENT-STATE-2026-08-18.md) §2. None have been silently
resolved.

---

## Superseded 2026-08-09 — the RDB-1 phase

Preserved rather than rewritten, per DR0002 (7). **This described the state on 9 August and was
already superseded when written; RDB-1 was closed by DR0004 on 2026-08-10.**

Both decision records were ratified
2026-08-09: [`decisions/0002-close-the-genesis-research-program.md`](decisions/0002-close-the-genesis-research-program.md)
(closure) and [`decisions/0003-engineering-posture-real-data.md`](decisions/0003-engineering-posture-real-data.md)
(engineering posture).

Active engineering at that time: **RDB-1**,
[`experiments/0006-rdb-1-real-data-bridge.md`](experiments/0006-rdb-1-real-data-bridge.md) —
import + build, no novelty claimed, development period complete, holdout unopened. Adaptation
returned a large stable positive for the rolling window; the model is indistinguishable from
persistence at its best.

Undecided at that time: whether to open the holdout — **since decided, it stays sealed
(DR0004)** — and what the next capability is. No sequence of milestones is pre-authorized
(DR0003 §10).

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
