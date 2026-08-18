# Project state

A factual snapshot. What exists, what's in progress, what's blocked. Updated when
something meaningful changes. Not a narrative — a status board.

For milestone-level progress (what fraction of the epistemic foundation is done), see
[`../research/PROGRAM-STATUS.md`](../research/PROGRAM-STATUS.md). This file tracks the same
territory at session granularity — what changed most recently, not the overall count.

---

## Current — 2026-08-18

**The market line is where the project lives.** Everything below the "Superseded" rule is the
cognitive-architecture era, preserved rather than rewritten.

- **Code:** `recorder/` (2,605 lines) · `market/` (1,926) · `rdb/` (829) · `tests/` (4,815,
  **19 suites, all passing**) · `status.py`, the orientation layer. `src/` holds the retired
  Labs 1–3 and no longer matches its own README — recorded as C2.
- **Experiments 0006–0009 complete:** RDB-1 (closed, holdout sealed), BAV-1 (p = 0.0165),
  MEASURE-1 (structure 15m–60m; ≥4h unresolvable, 68 years needed), EXEC-1 (**60.93% of the
  maker advantage survives**, 1.828 bps).
- **Decision records to DR0006.** DR0005 authorised `status.py` — reports, may not decide.
  **DR0006: no predictive experiment is declared unless its contract names the consumer, the
  decision changed, a do-nothing baseline and a wiring kill condition.**
- **Ledger:** 27 declared, 27 recorded, 0 outstanding, chain verified.
- **Running:** 48-hour BTCUSDT recording with **book and trades on one clock**,
  `~/genesis-evidence/q4/` — a soak test of the new aggTrade path. No contract, no question.
- **Blocked on the researcher:** which direction next, and nine contradictions in
  [`../research/CURRENT-STATE-2026-08-18.md`](../research/CURRENT-STATE-2026-08-18.md) §2.

Note: the roadmap reconciliation flagged below on 2026-08-09 as "the researcher's, not done
here" is **still open nine days later**, now recorded as C6 alongside the discovery that a
second, operative phase list lives in [`current_focus.md`](current_focus.md).

---

## Superseded 2026-08-09 — the cognitive-architecture era

Preserved per DR0002 (7). Everything from here down describes the project before the market
line opened, and is retained as history.

## Phase

**Research programme: CLOSED (2026-08-09).** **Engineering: ACTIVE.**

Ratified 2026-08-09:
[`../research/decisions/0002-close-the-genesis-research-program.md`](../research/decisions/0002-close-the-genesis-research-program.md)
closes the cognitive-architecture research program (Option D, completed learning vehicle);
[`../research/decisions/0003-engineering-posture-real-data.md`](../research/decisions/0003-engineering-posture-real-data.md)
permits disciplined engineering against real, externally recorded environments, claiming no
novelty. Both facts hold simultaneously and neither may be stated without the other.

`canon/` is unchanged by both records — including
[`../canon/roadmap.md`](../canon/roadmap.md), which still reads *Phase 0 — build the laboratory
(current)*. Phases are Type-1 (researcher-authored); reconciling the roadmap with the ratified
closure is the researcher's, and is **not** done here.

## Exists

- Repository structure (`canon/`, `research/`, `ai/`, `src/`, `tests/`).
- Collaboration contract with the provenance rule (`ai/collaboration.md`).
- `canon/vision.md`, `canon/research-methodology.md`, `canon/philosophical-foundations.md`,
  `canon/epistemology.md` — **authored**.
- Canon scaffolds still awaiting authored substance: `constitution`, `ontology`,
  `architecture` (Part B).
- `research/` subfolders with their purpose-and-format READMEs.
- `research/hypotheses/` — 14-section Standard Hypothesis Structure (README).
  `0001-quality-of-knowing.md` **authored, active**. `0002`–`0005` still scaffolds.
- `research/conceptual-landscape.md` — **authored** (8-layer conceptual map, living
  document, distinct from ontology/glossary).
- `research/PROGRAM-STATUS.md` — milestone tracker, new.
- `research/explorations/` — `what-makes-a-good-hypothesis.md` and
  `patterns-emerging-across-investigations.md`, both authored.
- `research/journal/` — seven entries. Four dated 2026-08-06: the Belief/Context
  interpretive collision, the Reception/Update computational-primitives derivation, the
  reality/resistance/action thread, and the caring/regulation/optimization comparison
  (the last two both reach the same unresolved constitutive-vs-installed caring fork,
  from different directions). Three dated 2026-08-07: Update-operator invariants (four
  survivors: prior-state-dependence, formal input-capacity, well-definedness, causal
  locality; corrects the primitives entry re: blending via forward amendment, not a
  silent edit); Update-algebra unification (point-correction and population-selection
  reduce to the same Bayesian-conditioning operation over two representations; structural
  learning partly reduces too via functional-gradient/lattice views; open-ended structural
  search remains a genuine, unresolved edge); and Update-closed (signature = (state,
  input); a fifth invariant found — non-everywhere-discontinuity, grounding identity
  across updates; provenance, metadata, and uncertainty-as-required all rejected).
  **Update investigation is closed.** Previously empty; a real gap now substantially
  closed.
- Two new standing rules in `ai/current_focus.md`, adopted 2026-08-07: the Method of
  Discovery is frozen (seven steps, self-tested from eight, revise only on demonstrated
  failure), and the architectural-leverage gate (every investigation must answer what it
  unlocks, why now, what becomes possible after, and its stopping condition, or be
  deferred).
- Eighth journal entry (2026-08-07): Belief derived by necessity. Property-search did not
  converge (all candidates were structural; falsified in sequence); reframed via the
  finding that Reception+Update is closed under state-algebra choice, so no property is
  internally forced. The necessity is at the interface: partial observability + acting on
  the unobserved forces a belief-state (sufficient statistic for the hidden cause) —
  coincides with POMDP theory, recorded as convergence not novelty. Belief = necessary
  but not primitive (a forced configuration of Update, not a new operation). Unblocks
  architecture.md Part B and a first executable experiment.
- **Standing discipline, adopted 2026-08-07:** no investigation ends without a permanent
  artifact (journal entry, hypothesis revision, architecture spec, interface, code, or
  test). Conversation alone no longer counts as project progress. Work is chosen by
  project leverage (what artifact/file/downstream it produces, whether it could be tested
  instead of analyzed), not intellectual interest.
- Working-memory files in `ai/`.

## Laboratory (new — 2026-08-07)

- **Phase transition: Foundation → Laboratory 1.** Genesis now optimizes for executable
  knowledge, not more foundations. Loop: research earns architecture → architecture
  generates implementation → implementation exposes ambiguity → ambiguity generates research.
- `canon/architecture.md` Part B — written (minimal adaptive loop, earned-only,
  Claude-drafted from journal results, for researcher review).
- `src/` — first code in the project: `environment.py`, `genesis.py`
  (Reception/Update/belief-state), `agents.py`, `laboratory.py`. Standard library only.
- `tests/test_laboratory.py` — the falsifiable check; passes.
- `research/experiments/0001-belief-vs-memoryless.md` — belief 0.929 vs memoryless 0.699
  under partial observability; concepts became software; three ambiguities exposed.
- `research/questions/` — `observation-model-provenance` (narrowing), `reception-operation-or-boundary` (open).
- **Laboratory 3 (choice over information) — done, but design failed to discriminate.**
  `src/laboratory3.py`, `tests/test_laboratory3.py`, `research/experiments/0003-...`.
  Validation (per the design-review's point 5) showed the environment is
  non-discriminating: for one-step single-function equal-noise channels, info-gain is a
  monotone read of the target marginal, so pure-read ≡ simulation (proven; 0/20,000
  disagreements). Empirically pure-read = simulation > passive; simulation bought nothing.
  Compositional I1 only; I2/I3 unreachable in this regime. **No canon change; belief-necessity
  stays Working.** Finding: the deep "does agency need new machinery" question requires
  escaping the one-step/single-function regime (multi-step, joint-dependent channels, or
  intractable beliefs) — a boundary decision, not yet taken.

## Research triage (2026-08-08) — the major reframe

- A literature-reconciliation pass ([`../research/prior-art-and-opportunity-map.md`](../research/prior-art-and-opportunity-map.md))
  established that Genesis's foundations are **established science** (POMDP, Bayes/Kalman,
  Baum-Welch, filtering, active sensing, Pearl, model-based RL) — not discoveries.
- **The novel-cognitive-architecture thesis collapsed into established science.** The
  **axiology/install thesis is an old philosophical problem** (Hume's is/ought), likely
  ill-posed. The **Research OS is the strongest surviving candidate contribution** — novelty
  and value both unproven.
- New standing rule (proposed for canon, awaiting ratification): rediscovery ≠ research
  novelty; import established results, don't re-derive them as research.
- Abandoned (F): primitive-counting; the "differentiator sentence" search; the capability
  graph as a *research* roadmap (it's a dependency map now).
- **Open decision (researcher's, not made):** which project Genesis is — methodology /
  normal-research (reflexive-performative) / modest-philosophy (axiology) / completed-learning
  vehicle. To be the first `research/decisions/` entry. Drafts of that record and the canon
  rule await ratification.

## System construction — Milestone 1 (2026-08-08)

- **The first CLOSED loop.** `src/closed_loop.py`, `tests/test_closed_loop.py`,
  [`../research/experiments/0004-minimal-closed-loop.md`](../research/experiments/0004-minimal-closed-loop.md).
  1-D corridor (K=7, target 3), action-conditioned Bayes filter (Import: Thrun–Burgard–Fox;
  Åström 1965), certainty-equivalent greedy policy. Deliberately boring by contract.
- **A. Integration validity — passed.** Full filter vs Update-only ablation, 3000 episodes:
  true-posterior 0.775/0.548 (noise 0.2), 0.457/0.292 (0.5), 0.286/0.189 (0.7). Belief never
  detaches from the world across the episode.
- **B. Behavioral utility — did not materialize.** Belief vs memoryless: 2.48/2.56 steps,
  3.95/4.12, and at noise 0.7 memoryless is *better* (0.992 reached / 6.53 steps vs 0.974 /
  7.03). Reported honestly; no success narrative manufactured.
- **Observed limitation → next capability:** belief is behaviorally load-bearing only when one
  current observation cannot carry the decision. Milestone 2 candidate: sparse/intermittent
  observations. No canon change; no novelty claim.

## System construction — Milestone 2 (2026-08-08)

- **Sparse observations make belief behaviorally load-bearing.** `src/sparse_loop.py`,
  `tests/test_sparse_loop.py`,
  [`../research/experiments/0005-sparse-observation-decision-relevance.md`](../research/experiments/0005-sparse-observation-decision-relevance.md).
  Contract pre-registered *and approved* before build; nothing tuned afterwards.
- Four agents, **identical policy `π(p̂)`**, differing only in the state estimate (predictive
  belief / stale observation / null / frozen belief). Agent-owned STOP — the environment never
  detects arrival, which would have handed everyone an oracle.
- **Primary (behavioral) met:** paired belief−stale declaration accuracy +0.015 at `p=1`
  (M1 control, flat as pre-registered) → +0.572 at `p=2` → +0.810 [+0.796, +0.824] at `p=5`.
  Predicted mechanism observed exactly: the stale agent overshoots and never declares (0.000
  correct at `p=5`).
- **Secondary (mechanism) confirmed:** belief posterior flat across gap age (~0.65 at gaps 0–3);
  frozen ablation collapses to 0.13 with MAP error 4.2.
- **Slip condition inconclusive**; two conditions excluded by the pre-registered 25%
  wall-contamination rule (which fired on the artifact it was written for).
- **Unanticipated limitation:** the null "wait for evidence" agent is *more accurate* than the
  belief agent (0.889 vs 0.810) at 13.63 vs 1.95 steps. Costless waiting dominates. → M3
  candidate: a cost on time. Import + Build; no canon change, no novelty claim.

## Milestone sequence closed (2026-08-08) — DR0002 draft

- **M3 was proposed, design-reviewed, and rejected.** Draft decision
  [`../research/decisions/0002-close-the-genesis-research-program.md`](../research/decisions/0002-close-the-genesis-research-program.md).
  **Awaiting researcher review — canon untouched.**
- **Why:** the cost-of-waiting question is answered in closed form by M2's own numbers
  (`0005` §F, λ* ≈ 0.0068, recorded as **Import/Analysis, not an experiment**); the design could
  not preserve the identical-policy principle; and it would have produced a belief win by
  construction rather than by contest.
- **The pattern that stopped the sequence:** each capability Genesis added met a cheap
  environmental substitute, and the reflex was to modify the toy corridor until the substitute
  failed. Same manufactured-necessity failure mode as `0001`, displaced from capability to
  environment.
- **Proposed canon lesson (drafted, not adopted):** existence, correctness and usefulness are
  three separate claims; usefulness is only demonstrable against a cost; therefore an
  environment can always be built to make any capability useful, and building it demonstrates
  nothing.
- **Proposed environment-first gate (drafted, not adopted):** five questions ahead of the
  existing research gate — real need / why simpler strategies fail / established machinery /
  what remains unresolved / does it test that or demonstrate imports. Applied to Genesis's own
  market goal it returns **no justified environment**.
- **Phase options in DR0002:** (A, recommended) deploy the machinery against a real environment
  — PsTally console monitoring is an M2-shaped problem in the wild — labelled engineering, not
  research; (B) pursue reflexivity, likely blocked by scale; (C) close the program and preserve
  the method as the artifact. A and C are compatible.
- **Not a failure.** The milestones established that the machinery works and exposed where the
  program was manufacturing necessity.

## Ratified, and RDB-1 (2026-08-09)

- **DR0002 ratified**, including three narrow amendments made in draft the same day: point (6)
  narrowed to withdraw *PsTally* specifically rather than real environments in general; point (8)
  now states no *research* direction is selected while engineering is active; a scope note
  records that the environment-first gate ruled on **Genesis-authored simulators** and never
  ruled on externally recorded data.
- **DR0003 ratified** — the engineering posture. Externally recorded environments permitted;
  authored simulators barred; classification stated before each run; no novelty claimable; no
  retrospective promotion of engineering into research; no pre-authorized sequence of milestones.
- **RDB-1 development period complete** —
  [`../research/experiments/0006-rdb-1-real-data-bridge.md`](../research/experiments/0006-rdb-1-real-data-bridge.md).
  Public AEMO NSW1 demand, 140,256 obs, 729 daily origins, 48-step horizon, both training-slice
  arms. Code in `rdb/`, per-origin records in `rdb_data/results/`, analysis in `rdb/report.py`.
- **Result:** adaptation matters (+101.59 MAE for rolling over expanding, boot95
  [+65.20, +141.72], stable across years and seasons); the model is **indistinguishable from
  persistence** at its best (−15.96, [−49.32, +19.51]); slice governs accuracy, specification
  governs calibration; both arms carry a fat-tail miscalibration signature on an easy series.
- **Holdout unopened.** 2023-01 → 2026-06 not downloaded; `rdb_data/DESIGN_FROZEN` absent;
  `ingest`/`series` raise `HoldoutLocked`.
- **Not decided:** whether to open the holdout; what the next capability is. Both the
  researcher's, one step at a time, chosen from evidence.

## Frozen

- `0002` Emergence, `0003` Time, `constitution.md`, `ontology.md`, the caring fork.

---

*Last updated: 2026-08-09.*
