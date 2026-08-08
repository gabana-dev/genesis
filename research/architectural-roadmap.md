# Architectural Roadmap — the Genesis capability graph

> **Claude-drafted director analysis, provisional — not canon.** Produced at the
> researchers' direction to plan Genesis as a long-term program. It makes architectural
> *claims* (below) that are candidates for adoption, not settled belief. Living document:
> updated as laboratories confirm or revise it. The researchers decide what graduates from
> here into canon or architecture.
>
> **RETIRED as a roadmap (2026-08-08). Preserved as historical record — do not delete.**
> Superseded by [`system-roadmap.md`](system-roadmap.md) (the current working roadmap) and
> [`prior-art-and-opportunity-map.md`](prior-art-and-opportunity-map.md). The
> literature-reconciliation pass established that this capability graph is almost entirely
> **established science to be imported** (POMDP → RL → causal inference), not a research
> roadmap. It survives only as (a) a dependency map and (b) a record of how Genesis once
> imagined its own progression. It is no longer a statement of research direction.

**Purpose:** the smallest capability graph that could plausibly grow into the Genesis of
[`../canon/vision.md`](../canon/vision.md). Plan in terms of *capability acquisition*, not
laboratories — a laboratory exists only to validate the next required capability.

---

## Core discovery: expansion by re-targeting

Most apparent "new capabilities" are not new machinery. They are the single belief-core
(Reception + Update maintaining internal state) **pointed at a new target**:

| Lab / step | Target of belief | Status |
|---|---|---|
| Lab 1 | the world's hidden **state** | canon (Working) |
| Lab 2 | the **sensor** (observation model) | done — *proved to compress into Update* |
| Lab 3 | the world's **dynamics** (transition) | next |
| Lab 4 | **action → consequence** (value) | frontier |
| later | the system **itself** (metacognition) | postponed |
| later | **other agents** (theory of mind) | postponed |

This is a candidate principle, as load-bearing as the Architectural Compression Principle
and of the same kind:

> **Capability Expansion = Belief Re-targeting.** The architecture grows chiefly by aiming
> the belief-core at successively richer objects — world → sensor → dynamics → action-value
> → self → others — not by accreting new primitives. *Candidate; each future lab either
> fits (compresses into belief-about-a-new-target) or reveals a genuinely new capability.*

## Two kinds of node

- **Belief-targets** (the core re-aimed): state, sensor, dynamics, action-value, self,
  other-agents. Most of the graph.
- **Genuinely-new capabilities** (do not compress into belief):
  1. **Objective / value (axiology)** — what counts as good. Belief says what *is*; this
     says what is *worth doing*. This is the frozen "caring fork."
  2. **Action-selection** — reading belief *under* an objective to choose (a "read," as MAP
     was).
  3. **Composition** — organizing many belief-processes into a coherent whole (the frozen
     emergence / holon question). A *phase*, not a target.

## The graph

```
        Reception + Update            C0 · have
               |
               v
      Belief: state under            C1 · CANON, foundational
      partial observability
        |        |        |
        v        v        v
     sensor   dynamics   self         C2 have · C3 next · C7 metacognition
     model     belief    belief
        |        |
        +---+----+
            v
   ===== AGENCY GATE =====            phase transition: passive knower -> actor
   action->consequence belief (C5)    requires C3 dynamics + C4 OBJECTIVE (frozen)
   + objective (C4) + selection (C6)            + C6 selection
            |
            v
     closed action loop               actions change future observations
            |
   +--------+--------+---------+
   v        v        v         v
 active   other-  composition causal/        postponable: C7,C8,C9,C10
 inquiry  agents  /emergence  structured
 (C7)     (C8)    (C9)        belief (C10)
            |
            v
   continual improvement across changing
   environments, among many decision-makers   -> vision.md
```

## Foundational / pivot / postponable

- **Foundational** (all else depends): Reception + Update; belief-about-state. Both held.
- **The pivot:** the **agency gate** — crossing from knower to actor. It *forces* axiology
  (C4). This is the single most important transition in the graph.
- **Postponable without slowing progress:** theory-of-mind (C8), composition / emergence
  (C9), structured-causal explanation (C10), and the *deep origin* of value (install an
  objective for the first closed loop; derive it later).

## Missing capabilities this analysis surfaced

1. **Axiology is a hole.** Genesis has a rich epistemology and no theory of value. Every
   passive laboratory hid this by letting an external supervisor define "good." The closed
   loop cannot be entered without an objective. Biggest structural gap; currently frozen.
2. **The reflexive/recursive class** — belief turned on itself (metacognition: confidence,
   ignorance) and on others (theory of mind). The core aimed at minds, including its own.
3. **Multi-timescale belief hierarchy** — touched already (Lab 2's within-episode vs
   across-episode loops) but unnamed as a capability. `vision.md`'s "multiple timescales"
   lives here: nested beliefs at different forgetting rates.

## Where the next laboratory sits

**Lab 3 (dynamics belief) completes the passive-knower stack** (state + sensor + dynamics),
the last purely-epistemic capability before the agency gate. After it, the only things
between Genesis and its first action are the objective (a *decision* — install one — not a
lab) and selection (a read). Lab 3 is therefore the final rung of the knowing phase, chosen
by capability progression, not by laboratory sequence. It also re-tests the re-targeting
principle (does the filtering predict-step compress into Update-with-null-observation?).

## Status

Living and provisional. The re-targeting principle and the axiology gap are the two claims
most worth confirming or breaking as laboratories proceed.
