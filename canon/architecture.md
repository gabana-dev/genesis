# Architecture

> Maintained by Claude (form only) per the
> [Governing Principle](../ai/collaboration.md#governing-principle). **Type: mixed** — Part A
> (the laboratory) is Type-2, Claude-authored and factual; Part B (the architecture of the
> system) is Type-1, authored by the researchers.

**Purpose:** How things are built. Two parts, deliberately separate: the architecture of
the **laboratory** (this repository and its workflow, which exists now) and the
architecture of the **system** (deferred until the foundations earn it).

---

## Part A — The laboratory

*(Descriptive: how the research OS is currently organized. This describes what exists.)*

- **`canon/`** — the canon. Slow-changing, authoritative. What we currently believe
  (`vision`, `philosophical-foundations`, `epistemology`, `ontology`), how we govern the
  work (`constitution`), how the lab reasons (`research-methodology`), where we're headed
  (`roadmap`), and how it's built (this file).
- **`research/`** — the living record, append-mostly:
  - `journal/` — chronological thinking.
  - `hypotheses/` — what we suspect but haven't tested (distinct from decisions).
  - `decisions/` — decision records (what was chosen and why).
  - `experiments/` — things tried and what they showed.
  - `external_ideas/` — imported ideas, marked unadopted until the researchers decide.
  - `questions/` — open problems.
  - [`conceptual-landscape.md`](../research/conceptual-landscape.md) — the living map of
    how Genesis's concepts relate; discovery, not definition (those stay in the canon).
  - `explorations/` — investigations into how Genesis should research, not what it
    should believe. E.g. [`what-makes-a-good-hypothesis.md`](../research/explorations/what-makes-a-good-hypothesis.md),
    [`patterns-emerging-across-investigations.md`](../research/explorations/patterns-emerging-across-investigations.md).
- **`ai/`** — working memory for AI collaborators; state that survives a session boundary.
- **`src/`, `tests/`** — implementation and its validation. Empty by design until the
  foundations are ready.

The flow: thinking accumulates in `research/`; when something stabilizes and the
researchers adopt it, it graduates into the `canon/`; only what the canon supports
becomes `src/`.

---

## Part B — The system

> Deferred. The cognitive architecture is not designed here yet, by rule. When the
> foundations in `canon/` and `research/` are ready, its design is authored by the
> researchers in this section.

_(unwritten — see the one rule in the root [`README`](../README.md))_
