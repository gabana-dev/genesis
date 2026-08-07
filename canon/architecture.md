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

### The pipeline (established by Laboratory 1)

Genesis has one path from idea to executable knowledge, and every future laboratory —
trading included — follows it. This *is* the deliverable of the first laboratory, more than
any single result it produces:

**Research → Architecture → Implementation → Experiment → Journal → Canon**

- **Research** discovers and compresses (`research/journal/`, `research/hypotheses/`).
- **Architecture** commits earned research to a spec (Part B), importing nothing unearned.
- **Implementation** operationalizes the spec in `src/`, adding no generality of its own.
- **Experiment** exposes it to reality (`tests/`) and records the result in
  `research/experiments/`.
- **Journal** captures what happened — including ambiguities the build exposed, which
  become new `research/questions/` and feed Research again.
- **Canon** is where a result that survives all of the above graduates into settled belief.

This is the [Epistemic Lifecycle](research-methodology.md#the-epistemic-lifecycle) made
executable — it inserts Architecture and Implementation as explicit stages between a
hypothesis and its test. The lifecycle remains the authority on what the stages *mean*;
this describes how they run in practice. **Laboratory 1 traversed the whole path except the
final step:** nothing has yet graduated to Canon. That step is the researchers' act, and
running it once would be the pipeline's first full closure.

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
