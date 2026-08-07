# 2026-08-07 — Laboratory 1 postmortem: the engineering wisdom

> Not an investigation — a retrospective. Reviews `canon/architecture.md` Part B, `src/`,
> and `research/experiments/0001-belief-vs-memoryless.md` together, to harvest what building
> the first laboratory taught that deriving could not. Claude authored the review under the
> researcher's direction.

## Stable (survived implementation unchanged)

- Update's signature `(state, input) → state` — held perfectly; the five invariants weren't
  even stressed (Bayesian conditioning satisfies them for free).
- Belief-state as a distribution `[p0, p1]` — the right algebra; Bayesian Update fell out in
  ~6 lines, zero friction. The algebra-unification result earned its keep.
- The environment/agent boundary (reality vs. theory) — held cleanly, feels fundamental.

## Changed

- **Reception dropped in weight.** Derived as a co-equal primitive; implemented as
  `return x`. Its dissociability stands, but the code says it is a boundary, not a
  computation. (Logged: `research/questions/reception-operation-or-boundary.md`.)
- **The `(state, input)` signature is incomplete for execution.** It cannot run without a
  third thing — the observation model. This is the largest change to what counts as earned.

## Unexpectedly simple

- The whole laboratory is ~100 lines, standard library only. Forty-odd turns of derivation
  implemented in almost nothing. That gap is a caution: either the theory is genuinely clean
  or we over-derived relative to what building needed — honestly, some of both.
- The predicted result landed with no tuning (memoryless 0.699, exactly the `1 - noise`
  ceiling).

## Unexpectedly difficult

- Almost nothing was hard to *code* — which is the finding. The only real difficulty was
  conceptual and surfaced *because* coding forced it: the observation model has nowhere to
  live. The build produced a problem the theory had not.

## Assumptions that disappeared

- That Reception and Update are equally weighty.
- That `(state, input)` is a complete account of Update — it needs a model.
- That "don't build until foundations earn it" was still binding — the foundations were more
  than enough; the caution was over-applied. A pacing lesson for future labs.

## New abstractions that emerged naturally (designed by no one, forced by the code)

- **The observation model `P(obs | hidden)`** — not state, not input, not Update; a fourth
  thing the theory has no slot for. The single most valuable harvest.
  (`research/questions/observation-model-provenance.md`.)
- **The "agent"** — the natural container bundling belief-state + Update + policy.
- **The "policy"** — the action-read (MAP), distinct from Update.

## Interfaces that now appear fundamental (reusable for every future laboratory)

- **Agent:** `observe(observation)` + act/`guess()`. Feed it observations; read a decision.
- **Environment:** `reset() → obs`, `step() → obs | None`, `reward(action)`.

These two are the most durable thing Lab 1 produced — more than the POMDP result.

## What became stronger / weaker

- Stronger: belief-necessity (now validated, not just derived); the pipeline (5 of 6 stages
  run); Update (implements cleanly).
- Weaker: Reception (revealed as thin).

## Earned vs. provisional, going forward

- **Earned** (build Lab 2 on these): agent interface, environment interface, belief-state as
  distribution, Update as Bayesian conditioning, environment/agent separation.
- **Provisional / exposed as incomplete**: where the observation model lives, the
  policy/action-read, Reception's status.

## The decision this postmortem informs

The candidate next step (Laboratory 2 = learn the observation model) directly attacks the
#1 harvest. But it is **not** the highest-leverage move yet: Lab 1's pipeline has not closed
its final stage (→ Canon). Running a second laboratory through a pipeline not yet proven
end-to-end scales an unvalidated process. Highest leverage is to **close the loop first** —
graduate belief-necessity (now derived, specified, built, and experimentally validated) into
the Canon. That is a researcher (Type-1) act, and it would be the pipeline's first full
closure. Lab 2 comes immediately after.
