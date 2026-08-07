# 2026-08-07 — What must every Update operator satisfy? Four survivors, a long list of rejections

> Captured retroactively from conversation. Continues directly from
> [`2026-08-06-computational-primitives-reception-update.md`](2026-08-06-computational-primitives-reception-update.md).
> The researcher set the instruction explicitly: forget Genesis, treat Update as a
> mathematical operator, derive properties by deletion/reduction/counterexample rather
> than intuition, and test each candidate on whether it's necessary, whether it reduces to
> another property, whether a counterexample survives without it, and whether it's a
> property of the operator itself or of one implementation. Claude did the derivation.
> This entry preserves two live self-corrections rather than smoothing them into a clean
> final answer, per the same discipline the entry itself ends up deriving.

## First, a correction to the prior entry

The primitives entry claimed discrepancy-driven correction and blending were two separate
families of Update — one computing an explicit comparison against expectation, the other
just a weighted average with no such structure. That's wrong. Exponential smoothing,
`state_new = (1-a)·state_old + a·input`, rearranges algebraically to
`state_new = state_old + a·(input − state_old)` — the identical error-correction form,
with a fixed weight instead of an adaptive one. Blending isn't a separate family; it's the
simplest member of the discrepancy-driven family, computing the same discrepancy without
ever materializing it as a named intermediate. Not rewriting the earlier entry to fix this
quietly — adding a note there pointing here instead, the same way a superseded Decision
gets marked and linked forward rather than deleted.

## What survives

**Prior-state-dependence.** The operator's output must be capable of depending on prior
state — delete this and you get a stateless map, which can't be adaptive at all (already
established). Not reducible to anything else. About the type of the operator, not any one
instance's behavior.

**Formal capacity for input-dependence, without requiring actual dependence.** Decay
changes state with zero informational content in the input at all — so no instance is
required to actually use the input, only the operator class must be capable of taking it
as an argument.

**Well-definedness, not determinism.** Determinism fails directly — stochastic update
rules (sampling-based, dropout-style) are legitimate and common. What survives underneath
it: the operator's output, deterministic or not, must be a determinate function or
determinate distribution of its inputs. Genuine unspecifiable arbitrariness isn't allowed;
well-defined randomness is fine.

**Causal locality.** An update applied at time *t* can only be a function of information
available up to and including *t* — never of inputs that haven't arrived yet. Close to
trivial to state, not trivial to have named explicitly, and it rules out something real —
future information illegitimately leaking into a past update.

## What was tested and rejected, with the specific counterexample that killed each one

- **Boundedness of single-step change** — a strongly informative Bayesian likelihood can
  legitimately move a posterior almost arbitrarily far in one step.
- **No-op under redundant input** — decay changes state with zero new information;
  the intuitively "obvious" property is directly falsified by the simplest family member.
- **Guaranteed convergence under a stationary environment** — a badly-tuned rule can
  oscillate forever and remain a legitimate, if poor, instance. Flagged explicitly as a
  *quality* property, not a *definitional* one — several rejected candidates on this list
  are properties of *good* Update operators, not of Update as such, and that distinction
  matters more than any single item here.
- **Order-independence — rejected, and reversed mid-derivation.** First instinct was the
  opposite: that order-*dependence* should be required, since an operator blind to
  sequence can't track timing or trend. Testing it against a concrete case broke that —
  simple unweighted running-mean averaging is genuinely order-independent (the mean of a
  set doesn't depend on arrival order), and it's a completely legitimate family member
  alongside recency-weighted smoothing, which *is* order-dependent. Neither direction is
  required; it's a real, free parameter. The first instinct was wrong and only got caught
  by actually constructing the counterexample rather than reasoning about it abstractly.
- **Monotonic confidence-increase under repeated consistent evidence** — a sophisticated
  system can legitimately grow *more* suspicious of suspiciously perfect repetition
  (identical readings every time suggests a stuck sensor, not confirmation).
- **Normalization (weights summing to a fixed total)** — only meaningful for probabilistic
  representations, meaningless for others (a raw scalar has nothing to normalize). Fails
  the operator-vs-implementation test directly.
- **Invertibility** — many legitimate updates are deliberately lossy; a running average
  destroys the individual data points that produced it. Non-invertibility is often a
  feature, not a defect.
- **Continuity** — threshold-gated updates are discontinuous by construction, and that
  discontinuity is exactly what prevents chasing noise. Desirable, not merely tolerated.
- **Bounded growth in state complexity** — rejected as a *mathematical* invariant
  (nothing forbids a state that grows without bound), retained only as a *real-world*
  constraint once finite memory is assumed. A fact about implementation, not the operator.
- **Immutable historical logging** — proposed, then retracted under the operator-vs-
  implementation test. An Update operator with no logging at all is still a legitimate
  Update operator; keeping an untamperable record is a choice some *systems* make around
  Update, not a property Update itself has.

## Status

Four survivors, considerably fewer than the mechanism-level richness explored in the
prior entry might have suggested. The gap between how much felt like it should be a law
and how little actually was one, once tested against real counterexamples rather than
intuition, may be the more useful finding than any single item on either list.
