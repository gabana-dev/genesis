# Architecture

> Maintained by Claude per the
> [Governing Principle](../ai/collaboration.md#governing-principle). **Type: mixed** — Part A
> (the repository/workflow) is Type-2, Claude-authored and factual. Part B is now split: the
> **minimal adaptive loop** below is an engineering spec that *composes already-earned
> research results* (Type-2/3, Claude-drafted, researcher-reviewed) — it introduces no new
> substance, only what the journal already earned. The architecture of the **eventual full
> system / mind** remains Type-1, deferred, and is not written here.

**Purpose:** How things are built. The architecture of the **repository** (Part A, exists
now), the **minimal adaptive loop** that earned research now supports and that Laboratory 1
implements (Part B), and the **full system** (still deferred until further foundations earn
it).

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

### The pipeline (two parallel streams)

Genesis turns ideas into executable knowledge along one path, run as **two independent
streams that do not block each other** — production creates confidence, governance records
it:

- **Production:** Research → Architecture → Implementation → Experiment
- **Governance:** Experiment → Postmortem → Canon

Production discovers, commits earned research to an architecture spec (Part B, below),
builds it in `src/`, and exposes it to reality in `tests/` and `research/experiments/`. Governance takes a completed experiment,
harvests its lessons in a postmortem (`research/journal/`), and — only once the result has
earned it — graduates it into the Canon. The two run concurrently: a new laboratory can begin
in production while the previous one is still moving through governance. Neither is the
other's critical path.

**The bar for Canon is not "survived one implementation."** It is *an architectural contract
with demonstrated stability under variation* — the same invariant surviving a different
implementation, a different environment, or a different representation. One successful build
is evidence; it is not yet stability. A result therefore graduates carrying an honest
confidence level (cf. the ontology entry statuses: proposed / working / stable), reaching
**stable** only after variation confirms the invariant is not an accident of one
implementation.

This is the [Epistemic Lifecycle](research-methodology.md#the-epistemic-lifecycle) made
executable — production inserts Architecture and Implementation as explicit stages;
governance is the lifecycle's Reflection → Decision → Canon tail. The lifecycle remains the
authority on what the stages *mean*.

---

## Part B — The minimal adaptive loop

*Conservative by intent. This specifies only what earned research supports, and exists so
that implementation descends from the canon rather than from assumptions. It should stay
boring; excitement belongs in `research/`, not here.*

The loop, for an agent acting in a partially observable world:

```
Reception  →  Update(state)  →  read state to act  →  Action  →  world  →  Reception  →  …
```

Each element descends from a specific earned result:

- **Reception** — intake of information not already derivable from current state.
  *(research/journal/2026-08-06-computational-primitives-reception-update.md)*
- **State = a belief-state** — when the world is partially observable and the agent must
  act on what it cannot directly observe, the state is forced to be a *sufficient statistic
  for the hidden cause*, not a record of observations.
  *(research/journal/2026-08-07-belief-derived-by-necessity.md)*
- **Update** — signature `(state, input) → state`, satisfying the five invariants. In a
  distribution-valued state, Update is Bayesian conditioning.
  *(research/journal/2026-08-07-update-operator-invariants.md,
  research/journal/2026-08-07-update-algebra-unification.md)*
- **Action** — a *read* of the state, not a separate primitive; the read whose output is
  coupled to the world. *(primitives entry: "Emission" reclassified as Update's output
  externally coupled.)*

**Deliberately not specified here** (kept out to stay earned-only):

- Where the observation model (the likelihood `P(observation | hidden)`) comes from —
  assumed given for now; learning it is future work.
- Any multi-level / holon structure — frozen speculation.
- How the action policy is chosen beyond "a function of state."
- Anything about the eventual full system. Deferred.

**What Laboratory 1 validates:** that Reception, Update, and a belief-state can be
implemented *cleanly and directly from this spec* — i.e., that the canon is precise enough
to become software. It lives in [`../src/`](../src/) with its check in
[`../tests/`](../tests/). Its purpose is architectural validation, not performance.
