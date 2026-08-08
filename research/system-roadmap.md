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
- **Milestone 2 — candidate: the same loop with sparse observations.** Chosen from Milestone
  1's observed limitation: belief is behaviorally load-bearing only when a single current
  observation is insufficient to decide. Intermittent-observation filtering is **Import**;
  the harness is **Build**. Awaiting researcher approval before build.
- **Milestone 3+ —** determined from Milestone 2's observed limitation. Not pre-specified.

## Historical record (preserved, not the plan)

Labs 0001–0003 and their results, the primitives/Update/belief work, the compression and
re-targeting principles, and the retired capability graph are kept as **evidence of what
Genesis learned** — established science independently re-derived, plus one clean negative
(primitive-counting is description-relative). They are history, not the roadmap.
