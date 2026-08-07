# Is Reception a computational operation, or a boundary condition?

**Status:** open
**Weight:** medium — it does not block the next laboratory, but it questions one of the two foundational primitives.

Surfaced by Laboratory 1 ([`../experiments/0001-belief-vs-memoryless.md`](../experiments/0001-belief-vs-memoryless.md)).

## Why it matters

The primitives investigation
([`../journal/2026-08-06-computational-primitives-reception-update.md`](../journal/2026-08-06-computational-primitives-reception-update.md))
established Reception and Update as two co-equal, irreducible primitives, dissociable in both
directions. But when implemented, Reception was `receive(x) = x` — no computation, only the
marking of an intake boundary. Update, by contrast, carried the entire Bayesian mechanism.
The asymmetry in implementation weight raises the question the derivation did not: is Reception
an *operation the system performs*, or the *interface condition* under which Update becomes
meaningful?

## What we know so far

- Reception's dissociability from Update stands regardless of implementation size — decay
  gives Update without Reception, the refractory case gives Reception without Update. That
  argument does not depend on Reception doing visible computation.
- Yet a primitive that is always the identity function in code invites the suspicion that its
  content is entirely relational (a boundary) rather than operational.
- Possible resolution: Reception's real content is *selection* — which of the available
  boundary signals is admitted at all (attention/filtering) — which was never implemented in
  Laboratory 1 because that environment delivers exactly one observation with no choice about
  what to receive. If so, Reception only shows its computational substance in an environment
  where the system must choose what to attend to.

## What would move it

A laboratory where the agent must *select* what to receive from multiple available channels
under a bandwidth limit — testing whether Reception acquires real computational content there,
or remains an identity boundary even then.
