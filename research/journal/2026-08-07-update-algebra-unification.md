# 2026-08-07 — The algebra of Update: one operation, or three families?

> Captured retroactively from conversation. Continues directly from
> [`2026-08-07-update-operator-invariants.md`](2026-08-07-update-operator-invariants.md).
> The researcher explicitly challenged a claim raised in conversation — never persisted to
> the repository — that point-correction, population-selection, and structural learning
> are three irreducible families of Update, and proposed instead that they might be one
> operation over three different state algebras. Instructed Claude to try hard to falsify
> the three-families framing rather than defend it. This entry supersedes that unpersisted
> framing before it was ever committed, not something already on record.

## The challenge

Maybe "family" was the wrong unit of analysis. Maybe what actually differs across
point-correction, population-selection, and structural learning isn't the *operation*
Update performs, but the *algebraic structure* the state happens to live in — with Update
itself staying constant: combine prior state with new information, using whatever
combination the state's own algebra provides.

## Point-correction and population-selection: a real, not forced, reduction

A population of weighted particles is a numerical approximation to a probability
distribution. Particle filters are understood in the estimation-theory literature as
approximating Bayesian conditioning — this is an established result, not a novel claim
made here. Point-correction (a Kalman filter, e.g.) updates a distribution parametrically
— mean and variance, closed form. Population-selection updates the same kind of object —
a distribution over hypotheses — empirically, via resampling a sample cloud instead of
computing a formula. Both compute something like "reweight the distribution by how well
each hypothesis explains the new input." Representation differs; the operation doesn't.

## Structural learning: tested against the hardest case first

Gradient boosting fits each new tree to the residual — the discrepancy — between the
current ensemble's predictions and the target, then adds it in with a weight:
`F_new = F_old + lr · h_new`. Identical additive discrepancy-correction form as
point-correction, with state living in a function space rather than a finite vector, and
each correction term happening to be a whole tree rather than a scalar nudge. Structural
complexity by itself doesn't escape the unification.

Pushed further, to classical concept learning: version-space algorithms maintain a
boundary in a lattice of hypotheses ordered by generality, updating via meet/join as new
examples arrive — refining the boundary, not blending it numerically. A third genuinely
different algebra — not a vector space, not a distribution space, a partial order — and
it still fits the same shape. Meet/join is that algebra's combination operator, the way
weighted sum is a vector space's.

## Where the unification stops, honestly

Open-ended structural search — free-form program synthesis, architecture search, anything
without a natural lattice ordering compatible with the search process — doesn't obviously
fit any of the three algebras found. No fourth algebra was found to close this gap, and
none was manufactured to force a tidy total unification. This is the genuine remaining
edge, left open rather than smoothed over.

## Revised position

Not "three irreducible families of Update." Update may be a single operation whose
apparent variety comes entirely from which algebra the state lives in — vector spaces get
weighted sum, distribution spaces get Bayesian reweighting (provably the same update
whether represented parametrically or empirically), lattices get meet/join. A deeper
unification than three families, going further than expected for two of the original
three candidates, with one honestly unresolved edge: unstructured, open-ended search.

## Status

Nothing here is settled — the state-algebra reframing is a strong candidate, not a
conclusion, and the open-ended-search gap is a real limit on how far it currently reaches,
not a footnote to be explained away later.
