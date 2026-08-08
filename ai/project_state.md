# Project state

A factual snapshot. What exists, what's in progress, what's blocked. Updated when
something meaningful changes. Not a narrative — a status board.

For milestone-level progress (what fraction of the epistemic foundation is done), see
[`../research/PROGRAM-STATUS.md`](../research/PROGRAM-STATUS.md). This file tracks the same
territory at session granularity — what changed most recently, not the overall count.

---

## Phase

**Phase 0 — building the laboratory.** See [`../canon/roadmap.md`](../canon/roadmap.md).

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

## Frozen

- `0002` Emergence, `0003` Time, `constitution.md`, `ontology.md`, the caring fork.

---

*Last updated: 2026-08-08.*
