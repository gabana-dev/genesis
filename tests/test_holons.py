"""
Checks for the holon contract and the integrator.

The central ones are the DETECTION cases. A test that only confirms independent holons
combine cleanly would pass with the correlation machinery entirely removed -- which is the
same shape as the variance-ratio bug that could only ever find nothing. So the tests that
matter here are the ones where failing to notice the correlation is the failure.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "holons"))

import numpy as np
from holon import Basis, Claim, Holon
from integrate import Integrator

CHECKS = []
def check(fn):
    CHECKS.append(fn)
    return fn


def mk(name, est, unc=1.0, at=0.0, basis=Basis.FITTED, complete=True, q="rv_next", h=3600.0):
    return Claim(holon=name, quantity=q, horizon_s=h, estimate=est, uncertainty=unc,
                 basis=basis, completeness=complete, at=at,
                 evidence="test" if basis is Basis.MEASURED else "")


def feed(itg, names, data, unc=1.0, q="rv_next", h=3600.0):
    """data: (n_obs, k) array of past estimates."""
    for i, row in enumerate(data):
        itg.observe([mk(n, float(v), unc, at=float(i), q=q, h=h) for n, v in zip(names, row)])


# ---- the Claim contract ---------------------------------------------------------------

@check
def a_claim_without_uncertainty_is_refused():
    for bad in (0.0, -1.0):
        try:
            mk("v", 1.0, bad)
        except ValueError:
            continue
        raise AssertionError(f"uncertainty={bad} was accepted")
    return "zero and negative uncertainty are both refused at construction"


@check
def a_measured_claim_must_name_its_evidence():
    try:
        Claim(holon="v", quantity="rv_next", horizon_s=60.0, estimate=1.0, uncertainty=1.0,
              basis=Basis.MEASURED, completeness=True, at=0.0)
    except ValueError:
        return "MEASURED without evidence is refused; provenance is not optional"
    raise AssertionError("a MEASURED claim with no evidence was accepted")


@check
def untested_and_unvouched_claims_carry_no_weight():
    assert mk("a", 1.0, basis=Basis.UNTESTED).admissible is False
    assert mk("b", 1.0, complete=False).admissible is False
    assert mk("c", 1.0).admissible is True
    return "untested basis and unvouched record are both inadmissible"


@check
def a_holon_may_decline_to_speak():
    class Quiet(Holon):
        quantity = "rv_next"
        def assess(self, view):
            return None
    assert Quiet("quiet").assess(object()) is None
    return "assess() returning None is a legal outcome, not an error"


# ---- the integrator: refusal ------------------------------------------------------------

@check
def the_integrator_refuses_before_it_has_history():
    itg = Integrator()
    out = itg.combine([mk("a", 1.0, at=0.0), mk("b", 1.2, at=0.0)])
    assert out["claim"] is None, "combined on empty history"
    assert "insufficient" in out["refused"]
    return "no combined claim until the correlation estimate is supportable"


@check
def inadmissible_claims_are_counted_not_silently_dropped():
    itg = Integrator()
    itg.observe([mk("a", 1.0, complete=False), mk("b", 1.0, basis=Basis.UNTESTED)])
    r = itg.refusals()
    assert r.get(("a", "incomplete_record")) == 1, r
    assert r.get(("b", "untested_basis")) == 1, r
    return "refusals are recorded by holon and reason"


@check
def combining_different_quantities_is_refused():
    itg = Integrator()
    try:
        itg.combine([mk("a", 1.0, q="rv_next"), mk("b", 1.0, q="residual_return")])
    except ValueError:
        return "mixing quantities raises rather than averaging a category error"
    raise AssertionError("two different quantities were combined")


# ---- the integrator: DETECTION ----------------------------------------------------------

@check
def independent_holons_show_full_breadth_and_no_inflation():
    rng = np.random.default_rng(20260817)
    itg = Integrator()
    names = ["a", "b", "c"]
    feed(itg, names, rng.normal(0, 1, (400, 3)))
    out = itg.combine([mk(n, 1.0, 1.0, at=999.0) for n in names])
    assert out["claim"] is not None, out
    br = out["breadth"]["breadth_participation_ratio"]
    assert br > 2.7, f"three independent holons read as BR={br:.2f}"
    assert abs(out["variance_inflation"] - 1.0) < 0.1, out["variance_inflation"]
    return f"three independent holons: BR={br:.2f}, inflation={out['variance_inflation']:.2f}x"


def correlated_pair(rho, n=400, seed=20260817):
    rng = np.random.default_rng(seed)
    f = rng.normal(0, 1, n)
    a = f * np.sqrt(rho) + rng.normal(0, 1, n) * np.sqrt(1 - rho)
    b = f * np.sqrt(rho) + rng.normal(0, 1, n) * np.sqrt(1 - rho)
    return np.column_stack([a, b])


@check
def near_duplicate_holons_are_refused_not_combined():
    """
    THE CENTRAL CHECK. Two holons at rho=0.9 are one opinion, and the integrator must decline
    rather than combine them. This is the case that failed in the first draft: breadth was
    measured correctly at 1.13 and then ignored, and the resulting combination scored worse
    out of sample than the better holon alone.
    """
    itg = Integrator()
    feed(itg, ["a", "b"], correlated_pair(0.9))
    out = itg.combine([mk("a", 1.0, 1.0, at=999.0), mk("b", 1.0, 1.0, at=999.0)])
    br = out["breadth"]["breadth_participation_ratio"]
    assert out["claim"] is None, f"combined two holons at BR={br:.2f}"
    assert "one opinion" in out["refused"], out["refused"]
    assert br < 1.35, f"rho=0.9 read as BR={br:.2f}; correlation was not seen"
    return f"rho=0.9 -> BR={br:.2f}, refused rather than combined"


@check
def moderately_correlated_holons_still_combine_but_pay_for_it():
    """The path that must stay open: real but partial overlap combines, with the penalty."""
    itg = Integrator()
    feed(itg, ["a", "b"], correlated_pair(0.5))
    out = itg.combine([mk("a", 1.0, 1.0, at=999.0), mk("b", 1.0, 1.0, at=999.0)])
    assert out["claim"] is not None, out
    br = out["breadth"]["breadth_participation_ratio"]
    infl = out["variance_inflation"]
    assert br > 1.35, br
    assert infl > 1.2, f"inflation {infl:.2f}x; the overlap was not charged for"
    assert out["claim"].uncertainty > np.sqrt(0.5), "error bar ignores the correlation"
    return f"rho=0.5 -> BR={br:.2f}, combined with {infl:.2f}x variance inflation"


@check
def identical_holons_are_refused():
    """Six copies of one opinion must not read as six bets. The degenerate limit."""
    rng = np.random.default_rng(20260817)
    x = rng.normal(0, 1, 400)
    itg = Integrator()
    feed(itg, ["a", "b"], np.column_stack([x, x]))
    out = itg.combine([mk("a", 1.0, 1.0, at=999.0), mk("b", 1.0, 1.0, at=999.0)])
    assert out["claim"] is None, "two identical holons produced a combined claim"
    assert out["breadth"]["breadth_participation_ratio"] == 1.0
    return "perfectly correlated holons are refused, never pseudo-inverted"


@check
def the_combination_beats_its_parts_when_they_genuinely_differ():
    rng = np.random.default_rng(20260817)
    itg = Integrator()
    feed(itg, ["a", "b"], rng.normal(0, 1, (400, 2)))
    out = itg.combine([mk("a", 1.0, 1.0, at=999.0), mk("b", 1.0, 1.0, at=999.0)])
    u = out["claim"].uncertainty
    assert u < 1.0, f"combining two independent holons did not tighten the estimate ({u})"
    assert abs(u - np.sqrt(0.5)) < 0.05, u
    return f"two independent unit-sigma holons combine to sigma={u:.3f} (theory {np.sqrt(0.5):.3f})"


@check
def a_hole_in_one_holons_history_is_not_filled():
    rng = np.random.default_rng(20260817)
    itg = Integrator()
    data = rng.normal(0, 1, (40, 2))
    for i, row in enumerate(data):
        cl = [mk("a", float(row[0]), at=float(i))]
        if i % 2 == 0:                       # b speaks only half the time
            cl.append(mk("b", float(row[1]), at=float(i)))
        itg.observe(cl)
    out = itg.combine([mk("a", 1.0, 1.0, at=999.0), mk("b", 1.0, 1.0, at=999.0)])
    assert out["n_obs"] == 20, f"aligned on {out['n_obs']} rows; holes were filled"
    return "alignment uses only decision times where every holon spoke"


@check
def the_weakest_basis_governs_the_combination():
    rng = np.random.default_rng(20260817)
    itg = Integrator()
    feed(itg, ["a", "b"], rng.normal(0, 1, (400, 2)))
    out = itg.combine([mk("a", 1.0, 1.0, at=999.0, basis=Basis.MEASURED),
                       mk("b", 1.0, 1.0, at=999.0, basis=Basis.FITTED)])
    assert out["claim"].basis is Basis.FITTED, out["claim"].basis
    return "a measured claim combined with a fitted one yields a fitted claim"


if __name__ == "__main__":
    failed = 0
    for fn in CHECKS:
        try:
            print(f"  ok   {fn.__name__}: {fn()}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(CHECKS) - failed} of {len(CHECKS)} checks passed")
    sys.exit(1 if failed else 0)
