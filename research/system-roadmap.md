# System-Construction Roadmap (current working roadmap)

> **Transition marker.** This roadmap records Genesis's shift from
> **foundational / primitive research** (deriving cognitive machinery from scratch) to
> **literature-grounded system construction** (importing established machinery and building
> the shortest honest path to the system goal). It supersedes
> [`architectural-roadmap.md`](architectural-roadmap.md) (now retired as a roadmap; kept as
> historical record). Claude-drafted; accepted by the researcher as the working direction.
> The *formal* project-direction decision remains open in
> [`decisions/0001-research-triage-reframe.md`](decisions/0001-research-triage-reframe.md).

## System goal (intact)

A belief-maintaining, learning, acting, adapting agent that can eventually operate in a
domain such as markets/trading. This is an engineering target reached by integration, not a
claim to novel science.

## Binding methodological constraints

1. Established capabilities are **imported**, not rediscovered.
2. First-principles implementations may be written for understanding, verification, or
   integration — but they are **not research laboratories and not counted as discoveries.**
3. Every proposed capability passes the six-way research gate
   ([`../canon/research-methodology.md`](../canon/research-methodology.md)) and is classified
   **Import / Build / Research / Dependency / Blocker.**
4. No experiment is justified merely because it demonstrates an established result.
5. Research begins only where an established capability meets a genuinely unresolved problem
   relevant to the system goal.
6. The **installed objective** is kept explicitly distinct from the **unresolved philosophical
   question** of whether an objective can be non-installed.

## Capability path — classified

| Capability | Class |
|---|---|
| Belief / state estimation | **Import** |
| Dynamic environments (predict + update) | **Import** |
| Decision-making (machinery) | **Import** |
| Planning | **Import** (deferred; optional) |
| Learning from action (RL) | **Import** |
| Causal / interventional reasoning | **Dependency** (optional; undercut by reflexivity) |
| Market reflexivity / performative prediction | **Research + Blocker** (the one genuine open edge, at scale) |
| Objective / axiology | **Build (installed, documented)** + **Research (open, unclaimed)** |
| Self-improvement | **Import** (online adaptation) + **Research** (open-ended; deferred) |
| Trading | **Build + Dependency**; where the reflexivity blocker and market-difficulty blocker live |

**Blockers, honestly:** (a) reflexivity/performativity at non-trivial scale; (b) the
non-installed-objective question (bypassed by installing one, documented as such); (c) market
difficulty itself (low SNR, nonstationarity, adversariality) — a *domain* blocker to
*profitability*, not an architecture problem, and the most likely practical failure mode.

## Construction approach

Build **upward from a working minimal system**, importing established machinery whenever it
exists. Do **not** replay the old lab sequence or follow a pre-planned capability ladder.
Each milestone establishes the smallest working increment; the *next* capability is chosen
from the **observed limitation** of the previous one, not from a roadmap of ambitions.

## Milestones

- **Milestone 1 — the minimal closed agent loop. DONE.**
  [`experiments/0004-minimal-closed-loop.md`](experiments/0004-minimal-closed-loop.md).
  Established `environment → observation → belief → decision → action → transition → new
  observation` with an action-conditioned Predict step and a trivial greedy policy.
  **A. Integration validity: passed** — the belief tracks a state the agent is itself moving;
  an Update-only ablation loses alignment at every noise level. **B. Behavioral utility: did
  not materialize** — the memoryless baseline matches the belief agent (and slightly beats it
  at noise 0.7). Reported, not rewritten into a win.
- **Milestone 2 — sparse observations. DONE.**
  [`experiments/0005-sparse-observation-decision-relevance.md`](experiments/0005-sparse-observation-decision-relevance.md).
  Contract pre-registered and approved before build. **Primary criterion met:** with an
  identical policy and paired randomness, the predictive belief beats the stale-observation
  agent on declaration accuracy by +0.810 [+0.796, +0.824] at `p=5`, and by +0.015 at the
  `p=1` null control. Mechanism confirmed — belief alignment flat across gap age, frozen
  ablation collapses; the stale agent fails specifically by overshooting and never declaring.
  **Slip condition inconclusive.** Two conditions excluded by the pre-registered
  wall-contamination rule.
  **Unanticipated limitation exposed:** a null agent that simply waits for fresh evidence is
  *more accurate* than the belief agent (0.889 vs 0.810) at 7× the steps — nothing in this
  environment charges for time.
- **Milestone 3 — PROPOSED AND REJECTED. The milestone sequence is closed at M2.**
  The candidate (a cost on time) was design-reviewed and declined: the answer is available in
  closed form from M2's own data (`experiments/0005-...` §F, crossover λ* ≈ 0.0068), the design
  could not preserve the identical-policy principle, and it would have made the belief agent win
  by construction rather than by contest. Draft decision:
  [`decisions/0002-close-the-genesis-research-program.md`](decisions/0002-close-the-genesis-research-program.md)
  (awaiting review; canon untouched).
- **No further milestone by default.** The pattern M1→M2→M3 exposed a second manufactured-
  necessity failure mode: each added capability met a cheap environmental substitute, and the
  reflex was to modify the environment until the substitute failed. A proposed
  **environment-first gate** now precedes the research gate — the environment must be justified
  before the capability is. Applied to Genesis's own market goal, it currently returns *no
  justified environment*, so the laboratory sequence stops rather than manufacturing one.

## Historical record (preserved, not the plan)

Labs 0001–0003 and their results, the primitives/Update/belief work, the compression and
re-targeting principles, and the retired capability graph are kept as **evidence of what
Genesis learned** — established science independently re-derived, plus one clean negative
(primitive-counting is description-relative). They are history, not the roadmap.
