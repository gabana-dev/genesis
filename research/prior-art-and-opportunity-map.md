# Prior-Art & Opportunity Map

> **Claude-authored director analysis, provisional — not canon, not a researcher claim.**
> Produced during the 2026-08-07/08 research-triage turns, at the researcher's direction to
> stop treating independent rediscovery of established science as research progress. It maps
> Genesis's work against prior art and classifies what, if anything, remains worth
> researching. The researcher has not yet ratified the direction this implies. Living doc.

## The rule this map enforces

Before Genesis designs a laboratory around a capability, identify the established literature
and determine whether the capability is already solved. If so, import it, name the prior art,
implement the minimum needed as a *dependency*, and move on. First-principles derivation
remains useful for understanding, verification, and exposing assumptions — but is **no longer
counted as research novelty.** (Proposed for canon; awaiting researcher ratification.)

## Foundations — Genesis result → established concept → prior art → what Genesis adds

| Genesis result | Established concept | Prior art | Net-new |
|---|---|---|---|
| Belief under partial observability | POMDP belief-state | Åström 1965; Kaelbling–Littman–Cassandra 1998 | none (pedagogical ownership) |
| Update / recursive updating | Recursive Bayesian estimation | Bayes; Kalman 1960 | none |
| Observation-model learning (Lab 2) | Emission-model / system ID | Baum-Welch; Rabiner 1989 | none (supervised = trivial case) |
| Dynamic filtering / "Predict" | Predict-update filtering | Kalman; Chapman–Kolmogorov | none |
| Active sensing / info-gain (Lab 3) | Bayesian experimental design | Lindley 1956; MacKay 1992; BALD 2011 | none (rediscovered a special-case collapse) |
| Interventional competence | do-calculus; obs ≠ interventional | Pearl 2009 | none |
| Closed-loop / model-based agency | POMDP planning; model-based RL | Bellman; Sutton & Barto | none |
| Compression / "belief re-targeting" | Hierarchical Bayes; MDL | Rissanen; probabilistic-programming stance | framing, not results |

**Foundations verdict: the cognitive-architecture thesis collapses into established science.**
Net-new cognitive science ≈ zero.

## Axiology / the install problem

The question: can an objective arise from a system's organization rather than being externally
selected or *relocated* into another assumed premise? Every approach relocates the evaluative
premise; none removes it — reward/IRL/RLHF (external), curiosity/intrinsic motivation (chosen
drive), empowerment (stipulated imperative), active inference/FEP (preferred states + Markov
blanket, i.e. reward renamed), autopoiesis/enactivism (presupposed self), homeostatic value
(setpoints), evolution (tautology or chosen selection environment).

**The install problem is the is/ought gap (Hume) in an engineering costume.** The only rescue
is the neo-Aristotelian/enactivist bridge (Foot; M. Thompson), itself a contested, unresolved
metaethics dispute. **Verdict: E — philosophically unresolved, possibly ill-posed. Not novel
to Genesis; an old problem rediscovered.** Marginal tractable sliver: operationalizing *where*
the premise enters — probably a restatement of no-free-lunch-for-values.

## Research OS — prior-art audit

Closest work: autonomous discovery (Sakana AI Scientist 2024; Coscientist 2023; Google AI
co-scientist 2025 — these *automate*, Genesis inverts), experiment tracking/provenance (MLflow,
W&B, DVC, W3C PROV), open science (OSF, Registered Reports), human-AI collaboration
(mixed-initiative, Horvitz 1999; co-writing 2023–25), knowledge/argumentation (Zettelkasten,
IBIS, Toulmin). Plausibly-novel sliver: the **enforced form/substance governance contract**
(AI as consistency-maintainer forbidden to author substance) + provenance-of-reasoning
sustaining a long-horizon human-led program without drift.

**Verdict: C — candidate contribution, novelty unvalidated, value unproven.** Needs a real
CSCW/HCI + AI-agents prior-art review; its first output was re-derivation; it can only prove
value on a genuine frontier. Real open sub-question (D): *does the form/substance contract
measurably reduce drift/hallucinated-substance vs. unconstrained collaboration?* — Genesis's
most tractable open question, but a methodology-evaluation question, not cognitive science.

## One genuinely-open, tractable, adjacent problem

**Reflexive / performative decision-making (D).** Where the agent's actions change the
distribution it models — exactly where Genesis's Bayesian/causal machinery breaks (modularity
fails). Young, unsolved: performative prediction (Perdomo et al. 2020), strategic ML (Hardt et
al.), reflexivity/performativity (Soros; MacKenzie). Sits on Genesis's stated domain (markets).
Honest caveat: crowded, and Genesis has **no special advantage** — normal research, not a
founding contribution.

## Opportunity map (A–F)

- **A — Import:** belief states, Bayesian/recursive updating, obs-model learning, dynamic
  filtering, active sensing, causal/interventional reasoning, closed-loop/model-based RL.
- **B — Engineering validation only:** minimal implementations of the above *if* needed as
  dependencies.
- **C — Genesis-specific candidate (validate novelty):** the Research OS.
- **D — Genuinely unresolved & researchable:** (i) the Research-OS drift-reduction study;
  (ii) reflexive/performative decision-making (adjacent, crowded).
- **E — Philosophically unresolved / possibly ill-posed:** the axiology/install problem.
- **F — Abandon:** primitive-counting (proven description-relative); the "differentiator
  sentence" search; re-deriving established estimation/control theory as if it were discovery;
  the capability graph *as a research roadmap*.

## Bottom line (director, not protecting Genesis)

- As a bid for a **novel cognitive architecture / artificial mind:** essentially nothing
  survives — it is established science.
- As a bid to **solve axiology:** nothing survives as tractable research — it is deep,
  likely-ill-posed philosophy.
- **What survives is narrow:** the Research OS as a *methodology* candidate (unvalidated), and
  the option of *normal* research on reflexive/performative decision-making.

Genesis is, at present, **a research method in search of a problem worthy of it.** The honest
open decision is no longer "which lab next" but "which project is Genesis" — a methodology
project, a normal research project, a modest philosophy project, or a completed learning
vehicle. That decision is the researcher's, recorded in `research/decisions/`.
