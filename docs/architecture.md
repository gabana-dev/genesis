# Architecture

> Structure and links maintained by AI. The architecture of the *mind* is authored by the
> researchers — see [`../ai/collaboration.md`](../ai/collaboration.md).

**Purpose:** How things are built. Two parts, deliberately separate: the architecture of
the **laboratory** (this repository and its workflow, which exists now) and the
architecture of the **mind** (deferred until the foundations earn it).

---

## Part A — The laboratory

*(Descriptive: how the research OS is currently organized. This describes what exists.)*

- **`docs/`** — the canon. Slow-changing, authoritative. What we currently believe
  (`vision`, `ontology`), how we govern the work (`constitution`), where we're headed
  (`roadmap`), and how it's built (this file).
- **`research/`** — the living record, append-mostly:
  - `journal/` — chronological thinking.
  - `decisions/` — decision records (what was chosen and why).
  - `experiments/` — things tried and what they showed.
  - `external_ideas/` — imported ideas, marked unadopted until the researchers decide.
  - `questions/` — open problems.
- **`ai/`** — working memory for AI collaborators; state that survives a session boundary.
- **`src/`, `tests/`** — implementation and its validation. Empty by design until the
  foundations are ready.

The flow: thinking accumulates in `research/`; when something stabilizes and the
researchers adopt it, it graduates into the `docs/` canon; only what the canon supports
becomes `src/`.

---

## Part B — The mind

> Deferred. The cognitive architecture is not designed here yet, by rule. When the
> foundations in `docs/` and `research/` are ready, its design is authored by the
> researchers in this section.

_(unwritten — see the one rule in the root [`README`](../README.md))_
