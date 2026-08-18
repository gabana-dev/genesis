"""
The holon contract: what a sensing agent owes downward, and what it owes upward.

PROPOSAL -- not adopted. Nothing here is canon, no research direction is implied, and this
module tests no hypothesis. It defines the shape a multi-agent layer would have IF Genesis
goes that way; that decision belongs to the researcher.

WHY A CONTRACT RATHER THAN AN INTERFACE
    A module becomes a holon when it is a whole at its own level and a part at the level
    above. Both halves have to be enforced or the word is decoration:

      Downward (a whole): it owns its state, its own tests, and its OWN estimate of its own
      error -- and it may decline to speak. `assess()` returning None is a first-class
      outcome, not a failure. A component that must always emit a number is a subroutine
      wearing a costume, and an agent that cannot say "this month is a random walk, I have
      nothing" will invent structure to fill the silence.

      Upward (a part): it emits one common currency -- a Claim -- never a raw signal and
      never an instruction. The layer above cannot weigh "buy" against "0.7".

WHY `basis` AND `completeness` ARE FIELDS
    These are the two that make this Genesis's rather than a generic ensemble.

    `completeness` carries the L0 invariant into every claim: BAV-1 established that the
    recorder's completeness label predicts agreement with an independent channel
    (p = 0.0165), so a claim resting on an unvouched record is a different kind of object
    from one that does not. It is refused at the integrator rather than silently discounted.

    `basis` prevents the failure this project has hit repeatedly in other forms: an untested
    thing being treated as a measured one because both arrive as floats. UNTESTED claims are
    collected and scored but contribute zero weight, which is the burn-in an unvalidated
    holon has to serve before it can move anything.
"""

from dataclasses import dataclass, field
from enum import Enum


class Basis(Enum):
    """
    Where a claim's authority comes from. Ordered by how much it has survived.

    MEASURED  a completed Genesis measurement stands behind it (an experiment record, an
              exploration with committed evidence). The estimator itself has been tested
              against series whose answer was known in advance.
    FITTED    parameters fitted to data and evaluated out of sample, walk-forward. Honest,
              and weaker than MEASURED because the fit is a search.
    UNTESTED  no validation yet. Admitted to the log, weighted zero, scored until it earns
              a promotion the researcher grants explicitly.
    """

    MEASURED = "measured"
    FITTED = "fitted"
    UNTESTED = "untested"


@dataclass(frozen=True, slots=True)
class Claim:
    """
    One holon's opinion about one quantity over one horizon, with its own error bar.

    Frozen because a claim is a record of what was believed at a moment. A layer that can
    edit its children's claims can rewrite history to suit a combination it prefers.
    """

    holon: str
    quantity: str          # what is predicted: "rv_next", "residual_return", "spread_capture"
    horizon_s: float       # seconds; the risk layer checks this against the measured cost floor
    estimate: float
    uncertainty: float     # this holon's own 1-sigma, in the units of `estimate`
    basis: Basis
    completeness: bool     # was the underlying record vouched for by the completeness rule
    at: float              # decision time, epoch seconds -- claims align on this
    notes: str = ""
    evidence: str = ""     # path or commit backing a MEASURED claim

    def __post_init__(self):
        # Boundary validation only. These are the conditions under which the arithmetic
        # downstream stops meaning anything, not defensive decoration.
        if self.uncertainty <= 0:
            raise ValueError(
                f"{self.holon}: uncertainty must be positive; a claim with none is not an "
                f"estimate, and inverse-variance weighting divides by it")
        if self.horizon_s <= 0:
            raise ValueError(f"{self.holon}: horizon_s must be positive")
        if not self.quantity:
            raise ValueError(f"{self.holon}: quantity is required and is never inferred")
        if self.basis is Basis.MEASURED and not self.evidence:
            raise ValueError(
                f"{self.holon}: a MEASURED claim must name its evidence. Provenance is the "
                f"whole difference between measured and asserted")

    @property
    def z(self) -> float:
        """Signal strength in its own units of uncertainty. Comparable across holons."""
        return self.estimate / self.uncertainty

    @property
    def admissible(self) -> bool:
        """
        May this claim carry weight? Untested claims and claims resting on an unvouched
        record are logged and scored, never weighted.
        """
        return self.completeness and self.basis is not Basis.UNTESTED


class Holon:
    """
    Base contract. A subclass measures exactly one thing and knows how badly it does it.

    Subclasses implement `assess`. Returning None means "no opinion" and is expected --
    the structure holon should return None for most of 2022 onward, because that is what
    the variance ratio actually says now.
    """

    quantity = ""
    basis = Basis.UNTESTED

    def __init__(self, name):
        self.name = name
        if not self.quantity:
            raise ValueError(f"{name}: a holon must declare the quantity it measures")

    def assess(self, view) -> "Claim | None":
        """
        Look at the world and either form a claim or decline. `view` is whatever L0 hands
        down -- a Book, a window of returns, a completeness label.
        """
        raise NotImplementedError

    def __repr__(self):
        return f"<{type(self).__name__} {self.name} {self.quantity} {self.basis.value}>"
