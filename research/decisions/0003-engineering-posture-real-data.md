# 0003 — Engineering posture for real, externally recorded environments

**Date:** 2026-08-09
**Status:** **RATIFIED by the researcher, 2026-08-09.** Nothing here is written into `canon/`.
**Reversibility:** reversible. This record governs how work is *labelled and bounded*, not what
is believed. It can be narrowed, widened or withdrawn without loss.
**Depends on:** [`0002`](0002-close-the-genesis-research-program.md), as amended 2026-08-09.
**Does not modify:** any conclusion of `0001` or `0002`. The research program stays closed.

---

> **The research program is closed. The laboratory remains capable of doing disciplined
> engineering.**

That sentence is the decision. Everything below bounds it so it cannot quietly become
something else.

## Why this record exists separately

[`0002`](0002-close-the-genesis-research-program.md) answers one question — *is Genesis a
research program?* — and answers it **no**. RDB-1 raises a different question that `0002` did
not consider, because RDB-1 was built after `0002` was drafted: *may a closed research program
keep doing engineering against real data, and under what constraints?*

Folding that into `0002` would make one record answer two questions and blur what "closed"
means. It is kept separate so that closure remains unambiguous and this posture remains
independently revisable.

## Context

Three facts, all established elsewhere:

1. `0002`'s environment audit assessed a **Genesis-authored market simulator** and returned *no
   justified environment*. Its recorded objection — that a hand-built simulator "would
   rediscover the price-impact function that was typed into it" — depends on Genesis authoring
   the environment. It did not rule on externally recorded data. (Scope note now in `0002`;
   reasoning in [`../journal/2026-08-09-real-data-is-not-a-simulator.md`](../journal/2026-08-09-real-data-is-not-a-simulator.md).)
2. **RDB-1 exists and has produced results** — [`../experiments/0006-rdb-1-real-data-bridge.md`](../experiments/0006-rdb-1-real-data-bridge.md).
   Public AEMO NSW1 data, frozen protocol, 729 origins, both training-slice arms complete,
   holdout unopened.
3. **Its results claim nothing novel.** The adaptation test returned a large, stable positive
   for the rolling window (+101.59 MAE, block-bootstrap 95% [+65.20, +141.72]); the model was
   *indistinguishable from persistence* at its best; calibration was governed by the
   specification rather than the training slice. All established method.

## Decision

1. **Engineering against real, externally recorded environments is permitted**, and is not a
   resumption of the research program. It is labelled engineering, it claims nothing, and it is
   tracked as such.
2. **"Externally recorded" is the qualifying property, and it is narrow.** An environment
   qualifies only if Genesis did not author its dynamics, cannot tune them, and cannot make the
   task easier by wanting it to be. Public recorded observations qualify. **Genesis-authored
   simulators do not, and the `0002` gate continues to bar them at full force.** A dataset does
   not become externally recorded because it is realistic; it qualifies because its generating
   process is outside Genesis's control.
3. **Every real-data milestone carries an explicit classification** — import, build, or both —
   stated before it runs. RDB-1 is **import + build**. A milestone that cannot state its
   classification in advance does not start.
4. **What this work may claim.** That established machinery was correctly implemented; that it
   was evaluated under a protocol fixed in advance; that it did or did not beat named baselines
   on a named dataset; that a measured property (accuracy, calibration, stability, cost) took a
   measured value. Negative and null results are first-class outputs and are not rescued.
5. **What this work may not claim.** Novelty of any kind. A new architecture, primitive,
   capability or mechanism. Research standing. Generality beyond the dataset and protocol
   evaluated. Superiority not supported by a paired interval on per-origin records. **Nor may
   accumulated engineering be retrospectively recast as research** — if that case is ever to be
   made, it is made by a new decision record arguing it explicitly, never by drift.
6. **The prior-art gate applies first and unchanged.** Anything classified import (A) in
   [`../prior-art-and-opportunity-map.md`](../prior-art-and-opportunity-map.md) gets no
   laboratory. Import it, validate it, label it, move on.
7. **The environment-first gate applies, with its answers permitted to differ.** For engineering
   the honest answer to question (4) is routinely *"nothing unresolved"* — which the gate
   already handles: the work is integration or validation, labelled as engineering, claiming
   nothing. That is a legitimate pass, not a failure.
8. **The environment may not be altered to make a capability look necessary.** This is the
   `0002` finding and it survives intact. Choosing a *harder recorded target* is permitted;
   authoring dynamics, tuning a corridor, or selecting a subset until a method wins is not.
   Target selection is recorded with its reason before the run.
9. **Protocol discipline is retained in full** — pre-declared contract, snapshot with checksums,
   leakage controls, rolling-origin evaluation, serious baselines, paired intervals on
   per-origin records, technical holdout locks, and disclosure of which analysis choices were
   fixed when. This discipline is the reason the work is worth doing at all, and it is not
   relaxed because the stakes are labelled engineering.
10. **One step at a time, chosen from evidence.** No sequence of future milestones is adopted in
    advance. Each milestone is chosen from what the previous one exposed. A pre-planned
    technology roadmap is the capability-graph failure mode `0001` classified **F — abandon**,
    and it stays abandoned.

## What "better" means here

Recorded because the obvious metric is the wrong one. A milestone succeeds when the system
becomes **more capable, more adaptive, more measurable, or more grounded in reality** — not
when a score improves. A well-measured failure that exposes a real limitation is a success under
this definition. A score improvement obtained by choosing a friendlier target is not.

## What would reopen the research program

Nothing in this record, and nothing that follows from it. The `0002` reopening clause stands
unchanged and unweakened: only a genuinely unresolved problem, arriving from real constraints,
surviving the prior-art gate, and demanding something no established method supplies.

**Engineering results do not accumulate into that.** Ten disciplined milestones are ten
disciplined milestones. If such a problem ever does arrive, it will be recognisable because
established methods will visibly fail on it — not because enough engineering has been done to
make a research claim feel earned.

## Status of the repository

`canon/` unchanged. `rdb/` and `rdb_data/` are engineering artifacts governed by this record,
not part of the preserved research record under `0002`. The `ai/` trackers must state both facts
together — research closed, engineering active. **Done on ratification, 2026-08-09.**

## Source

[`0002`](0002-close-the-genesis-research-program.md) (as amended 2026-08-09) and its
environment-first gate; [`0001`](0001-research-triage-reframe.md);
[`../experiments/0006-rdb-1-real-data-bridge.md`](../experiments/0006-rdb-1-real-data-bridge.md);
[`../journal/2026-08-09-real-data-is-not-a-simulator.md`](../journal/2026-08-09-real-data-is-not-a-simulator.md);
[`../prior-art-and-opportunity-map.md`](../prior-art-and-opportunity-map.md);
[`0005`](../experiments/0005-sparse-observation-decision-relevance.md) §E on costless
environments.
