# Current focus

**One thing at a time. This file names it.**

---

## Now

**The research program is closed. The laboratory remains capable of doing disciplined
engineering.**

Two decision records were ratified on 2026-08-09 and together they define the whole of the
current state:

- [`../research/decisions/0002-close-the-genesis-research-program.md`](../research/decisions/0002-close-the-genesis-research-program.md)
  — **RATIFIED.** The cognitive-architecture thesis is retired (established science,
  independently re-derived); the axiology/install question is retired as philosophy, not a
  Genesis objective; the Research OS is useful but its novelty is unvalidated and unclaimed; the
  toy-milestone sequence is closed at M2; PsTally is not a Genesis phase. **No research
  direction is selected.** Reopening requires a genuinely unresolved problem arriving from real
  constraints and surviving the prior-art gate — nothing internal reopens it.
- [`../research/decisions/0003-engineering-posture-real-data.md`](../research/decisions/0003-engineering-posture-real-data.md)
  — **RATIFIED.** Engineering against real, *externally recorded* environments is permitted,
  labelled as engineering, claiming nothing. Genesis-authored simulators remain barred. Every
  milestone states its import/build classification before it runs. Accumulated engineering is
  never retrospectively recast as research.

**Active work: RDB-1**, the real-data bridge.
[`../research/experiments/0006-rdb-1-real-data-bridge.md`](../research/experiments/0006-rdb-1-real-data-bridge.md).
Classification **import + build, no novelty claimed**. Public AEMO NSW1 data under a frozen
protocol. Development period complete; **the holdout is unopened.**

## What RDB-1 established (development period only)

- **Adaptation matters, decisively.** Rolling 26 weeks beats an expanding window by +101.59 MAE,
  block-bootstrap 95% [+65.20, +141.72]. Stable across every year and season; largest in summer.
- **The model does not reliably beat "yesterday at this clock time."** Rolling vs persistence
  straddles zero (−15.96, [−49.32, +19.51]). Expanding fails to beat seasonal-naive at all.
- **Slice and specification are separable.** The training slice moved accuracy ~24% and moved
  calibration essentially not at all. Both arms carry the same fat-tail signature: intervals too
  wide at 50%, too narrow at 95% — on a smooth, well-behaved series.
- **Nothing consumes the forecast.** No cost, no decision, no consequence for being wrong — the
  condition [`0005`](../research/experiments/0005-sparse-observation-decision-relevance.md) §E
  identified as making usefulness undemonstrable.

## Open — the researcher's, not yet decided

1. **Whether to open the RDB-1 holdout** (2023-01 → 2026-06). One-way in practice. The lock is
   technical: the months are not downloaded and `ingest`/`series` raise `HoldoutLocked` unless
   `rdb_data/DESIGN_FROZEN` exists.
2. **What the next capability is.** Chosen from what the evidence exposed, one step at a time.
   **No sequence is pre-authorized** — DR0003 (10) forbids adopting a roadmap of future
   milestones in advance, and DR0001 classifies the capability graph as **F — abandon**.

An environment distinction is on record but selects nothing:
[`../research/journal/2026-08-09-real-data-is-not-a-simulator.md`](../research/journal/2026-08-09-real-data-is-not-a-simulator.md)
notes that the environment-first gate ruled on Genesis-*authored* simulators and never ruled on
externally recorded data. DR0003 permits considering a harder recorded target; **it selects
none.**

## What "better" means

A milestone succeeds when the system becomes **more capable, more adaptive, more measurable, or
more grounded in reality** — not when a score improves. A well-measured failure exposing a real
limitation is a success. A score improvement obtained by choosing a friendlier target is not.
(DR0003, "What better means here".)

## Standing rules still in force

- **Prior-art gate first.** Anything classified import (A) in
  [`../research/prior-art-and-opportunity-map.md`](../research/prior-art-and-opportunity-map.md)
  gets no laboratory.
- **Environment-first gate** (DR0002, preserved there, deliberately **not canon**). Full force
  against any environment Genesis would author.
- **Protocol discipline**, undiminished for engineering: contract fixed in advance, checksummed
  snapshots, leakage controls, serious baselines, paired intervals on per-origin records,
  technical holdout locks, and disclosure of which analysis choices were fixed when.
- **The form/substance boundary** ([`collaboration.md`](collaboration.md)). Unchanged by any of
  the above. Claude does not author substance or set direction.

## Superseded, kept on record

The capability-construction gate and the frozen Method of Discovery remain in the history
(journal entries of 2026-08-07 and the `0001` triage) but no longer govern selection: the
prior-art rule subsumes them, and no laboratory runs for anything classified import.

## Not in focus

- **Abandoned (F):** primitive-counting; the "differentiator sentence" search; re-deriving
  established estimation/control theory as discovery; the capability graph as a research roadmap.
- **Import if needed (A), never as research:** dynamic-state filtering, unsupervised
  observation-model learning, closed-loop RL, causal inference.
- **Frozen:** `0002` Emergence, `0003` Time, `constitution.md`, `ontology.md`, the caring fork.
- **Open but unchosen (D/E):** Research-OS validation; reflexive/performative decision-making;
  the axiology/install problem. Retired as Genesis objectives by DR0002.

---

*Last updated: 2026-08-09.*
