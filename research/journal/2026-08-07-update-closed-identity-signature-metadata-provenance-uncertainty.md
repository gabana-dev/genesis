# 2026-08-07 — Update closed: signature, metadata, uncertainty, provenance, and a fifth invariant

> Captured retroactively from conversation. Applies the frozen seven-step Method of
> Discovery (see [`2026-08-07-update-operator-invariants.md`](2026-08-07-update-operator-invariants.md)
> and [`2026-08-07-update-algebra-unification.md`](2026-08-07-update-algebra-unification.md))
> to the five remaining Update questions, per the researcher's explicit instruction to use
> the method rather than continue refining it. Claude performed the derivation. The method
> required no changes anywhere in this pass — every finding below came from the existing
> seven steps, run as already stood.

## Signature — does provenance survive as a required third argument?

Tested whether Update's signature needs to be (state, input, provenance) rather than just
(state, input), where provenance distinguishes exogenously-received content from
internally-derived content. Definitional precision passed — there's a genuine negative
case in both directions (a single-channel sensor system where the tag is trivially
constant; a closed-loop reflective system where it's the other constant), not an
unfalsifiable stretch. Necessity failed: a system that updates identically regardless of
provenance — feeding its own prior inferences back in as if they were fresh evidence —
remains a legitimate Update instance. It becomes prone to a specific failure (confidence
inflation from double-counting its own conclusions), but that's the same quality-not-
definitional category that already rejected convergence-guarantees and single-step
boundedness. **Provenance is rejected as a required signature element; the signature
stands as (state, input).**

## Metadata — must Update output anything beyond the new state?

Deletion decisive on its own: the simplest legitimate implementations (raw exponential
smoothing) output nothing but the new value and still satisfy the target. Checked whether
this is secretly required by the refusal-conditions material — deciding whether to update
needs some internal discrepancy computation — but that internal computation, where it
exists, doesn't need to be exposed externally, and isn't universal across implementations
regardless (blending computes no explicit discrepancy at all). **Rejected as necessary.**
Optional design choice, not an operator property.

## Uncertainty — where, if anywhere, does it enter?

Same pattern. A bare point-estimate update carries no uncertainty representation and
remains a fully legitimate point-correction instance — rejected as a required component.
Where it does legitimately show up: the algebra-unification result already established
that distribution-space state representations carry uncertainty automatically, as part of
what a distribution is — nothing extra required. Point-estimate and lattice
representations have no such structure by default; adding one (a Kalman filter's variance
term) is a design choice about the state's own algebra, not a requirement of Update
itself. **Resolved as an automatic consequence of choosing a distributional state
algebra, not a separate required element.**

## Identity across updates — the one that produced something new, not just a rejection

Tested the sharpest adversarial construction available: an update rule that formally
satisfies prior-state-dependence (the first invariant) but scrambles the state completely
every cycle — new state as a cryptographic-style hash of (old state, input). Technically
depends on prior state. Still felt wrong to call adaptive, which needed an actual
argument, not just intuition.

First candidate explanation — continuity is required — fails immediately, since
continuity was already tested and correctly rejected (threshold-gated updates are
legitimately discontinuous at their decision boundary). The hash case isn't discontinuous
*at* a boundary, though — it's discontinuous *everywhere*, with no smooth region
anywhere in its domain. That's a different, more precise claim than the one already
rejected, and it survives construction: no legitimate adaptive system could be built on a
nowhere-continuous update rule, because such a rule has no fixed points and no basin of
attraction — nothing about repeated similar experience could ever cause behavior to
settle toward anything, which is close to what "adaptive" means in the first place.

**Fifth invariant, new: Update must be well-behaved — continuous or structured — on at
least some non-trivial region of its domain. It may be sharply discontinuous at isolated
decision boundaries (threshold and selection mechanisms remain fully legitimate) but
cannot be discontinuous everywhere.** This is what grounds identity across updates — not
that state never changes sharply, but that somewhere nearby, similar states and inputs
produce recognizably related outputs, which is what makes state at time t and state at
time t+1 the same evolving thing rather than arbitrary, unrelated values.

## Status

Update is closed. Signature: (state, input). Five invariants total — the original four
plus this one. Provenance, metadata, and uncertainty all resolved as rejected-but-
reclassified rather than left open. The frozen method needed no modification anywhere in
this pass.

Per the leverage rule adopted this session, this was explicitly gating both `0005` and
the Belief/Context resolution. Both are now unblocked.
