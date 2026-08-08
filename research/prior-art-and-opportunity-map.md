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

## Research OS — deeper prior-art audit

Component-by-component, nearly everything is established practice:

| Component | Closest prior art | Established? |
|---|---|---|
| Decision records (`decisions/`) | Architecture Decision Records (Nygard 2011); design rationale (IBIS) | yes |
| Pre-registered experiment contracts | Registered Reports; preregistration (OSF) | yes |
| Provenance (claim→source) | W3C PROV; design rationale | yes |
| Guardian (drift/dup/orphan/broken-link checks) | linters, CI, dead-link checkers | yes |
| Canon vs. record + linked structure | Zettelkasten; semantic wikis | yes |
| Epistemic status (Working/Stable) | evidence grading (GRADE); maturity ladders | yes |
| AI barred from authoring substance | author/editor distinction; AI-not-author norms (ICMJE 2023); mixed-initiative (Horvitz 1999) | *stance* yes; enforced+tooled discipline not found as a named system |

Field context: autonomous AI-scientists (Sakana 2024; Google co-scientist 2025) push toward
AI *automating* research; Genesis inverts this — the AI does heavy work but is barred from
substance. The live, unsolved problem that inversion targets is **AI substance-capture /
drift** in AI-assisted research.

**Recorded status (precise):**
- **Research OS as a whole: Import + Engineering validation.** Established components
  assembled into a coherent workflow.
- **Form/substance governance: Potentially novel, pending stronger prior-art verification.**
  Do not call it novel.
- **Demonstrated property: epistemic honesty / anti-self-deception about novelty.** Strongest
  evidence is internal — the OS's own provenance + literature-reconciliation caused Genesis to
  detect and formally acknowledge (Decision 0001) that much of its supposed architectural
  research was established science. *This is evidence of usefulness, NOT of novelty.*
- **Controlled superiority claim: Open question.** Difficult to test at solo scale; heavily
  confounded by the established components (preregistration already reduces error; ADRs
  already improve auditability).
- **Contribution category: methodology / HCI / CSCW — not cognitive science.**

**The four-level distinction, applied honestly:** (1) established components — yes, all of
them; (2) a potentially distinctive *combination* — yes, evidence for this; (3) a genuinely
new *mechanism* — **no**; on scrutiny the "mechanism" reduces to the author/editor
relationship + linting + citation discipline, all established; (4) demonstrated empirical
advantage — only a *small* internal piece (it caught our own false-novelty claim); the broader
comparative claim is untested. **Genesis has (2) and a small piece of (4); not (3); broader (4)
untested.**

Guard against circularity: the OS exposing our earlier mistake is evidence the *method works*,
**not** evidence the method is *novel*. Using internal success as a novelty substitute is
itself the error the "Rediscovery Is Not Discovery" rule forbids.

**Verdict: primarily Import + Engineering validation, with a Potentially-novel governance
sliver that has not cleared the bar for a new mechanism.** Do not manufacture a study to
validate it. Best treated, if pursued at all, as a *documentable methodology artifact*, not a
research program.

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
- **C — Genesis-specific candidate:** the Research OS — but the deeper audit narrows this to
  *Import + Engineering validation* overall, with only a *Potentially-novel* form/substance
  governance sliver that has **not** cleared the bar for a new mechanism. Best treated as a
  documentable methodology artifact, not a research program.
- **D — Genuinely unresolved & researchable:** reflexive/performative decision-making
  (adjacent, crowded). (The Research-OS controlled-superiority study is *open* but likely
  impractical at solo scale and confounded — not recommended as a research target.)
- **E — Philosophically unresolved / possibly ill-posed:** the axiology/install problem.
- **F — Abandon:** primitive-counting (proven description-relative); the "differentiator
  sentence" search; re-deriving established estimation/control theory as if it were discovery;
  the capability graph *as a research roadmap*.

## Bottom line (director, not protecting Genesis)

- As a bid for a **novel cognitive architecture / artificial mind:** essentially nothing
  survives — it is established science.
- As a bid to **solve axiology:** nothing survives as tractable research — it is deep,
  likely-ill-posed philosophy.
- **What survives is narrow:** the Research OS as a *documentable methodology artifact*
  (strong synthesis; one demonstrated benefit — anti-self-deception; no new mechanism
  identified), and the option of *normal* research on reflexive/performative decision-making.

Genesis is, at present, **a research method in search of a problem worthy of it.** The honest
open decision is no longer "which lab next" but "which project is Genesis" — a methodology
project, a normal research project, a modest philosophy project, or a completed learning
vehicle. That decision is the researcher's, recorded in `research/decisions/`.
