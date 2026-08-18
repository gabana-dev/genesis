"""
The earned Genesis primitives, in code, for Laboratory 1.

This file exists to answer one question: can Reception, Update, and a
belief-state be implemented cleanly, directly from the canon, with nothing else?

Provenance (each function descends from a specific earned result):
  Reception, Update as the two irreducible primitives
    -> research/journal/2026-08-06-computational-primitives-reception-update.md
  Update signature (state, input) and its invariants
    -> research/journal/2026-08-07-update-operator-invariants.md
  Distribution-space Update == Bayesian conditioning
    -> research/journal/2026-08-07-update-algebra-unification.md
  Belief as the sufficient statistic forced by partial observability
    -> research/journal/2026-08-07-belief-derived-by-necessity.md

No abstraction beyond what these results name. Standard library only.
"""

# --- Reception -------------------------------------------------------------
# In the canon, Reception is: information not already derivable from current
# state becomes available. In code, for this laboratory, that is simply the
# arrival of an observation. Reception performs no transformation of its own --
# it is the intake point. (That it is nearly contentless in code is itself a
# finding; see the laboratory's report.)

def receive(observation):
    return observation


# --- Update ----------------------------------------------------------------
# Signature (state, input) -> state. Here the state is a belief -- a
# distribution [p0, p1] over the hidden bit -- and Update is Bayesian
# conditioning, the distribution-space form of Update.
#
# NOTE (exposed by writing this code): the observation model
# P(observation | hidden) is REQUIRED to perform the update, yet it is NOT part
# of Update's (state, input) signature. Laboratory 1 supplies it as a fixed,
# known quantity (`noise`). Where such a model comes from in general is not
# specified by the canon -- see the laboratory's findings.

def update(belief, observation, noise):
    # P(observation | hidden = h): faithful w.p. (1 - noise), corrupted w.p. noise
    likelihood = [
        (1.0 - noise) if observation == 0 else noise,   # P(obs | hidden = 0)
        (1.0 - noise) if observation == 1 else noise,    # P(obs | hidden = 1)
    ]
    unnormalized = [belief[0] * likelihood[0], belief[1] * likelihood[1]]
    total = unnormalized[0] + unnormalized[1]
    return [unnormalized[0] / total, unnormalized[1] / total]


# --- Belief-state ----------------------------------------------------------
# The sufficient statistic for the hidden cause. A uniform prior encodes
# "no information yet."

def initial_belief():
    return [0.5, 0.5]
