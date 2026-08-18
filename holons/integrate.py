"""
The integrating holon: combine claims WITHOUT assuming the claimants are independent.

PROPOSAL -- not adopted. Tests no hypothesis; combining claims is not itself a trial.

THE FAILURE THIS EXISTS TO PREVENT
    The cross-section study measured 33 liquid perps and found the first principal component
    takes 69% of all variance -- roughly TWO independent bets, not 33. Holding thirty
    altcoins is one position with extra fees.

    Six sensing holons are the same trap one level up. If they read overlapping evidence --
    and they will, since they all consume L0 -- then averaging them, or combining them by
    inverse variance, silently claims an independence they do not have. The combined error
    bar comes out too tight, position sizing reads it as confidence, and the system stakes
    real capital on six copies of one opinion.

    So this module's job is NOT to average. It is to measure how independent its children
    actually are, and to combine them correctly given the answer.

THE ARITHMETIC
    For estimators with covariance Sigma, the minimum-variance unbiased combination is

        w = Sigma^-1 . 1 / (1' . Sigma^-1 . 1)         combined var = 1 / (1' Sigma^-1 1)

    which is exact and needs no breadth fudge factor -- the correlation is already in Sigma.
    Effective breadth is then a DIAGNOSTIC rather than an input: it says how many independent
    opinions were present, and `variance_inflation` says how badly the naive independent
    combination would have flattered itself. That ratio is the number worth watching.

WHY IT REFUSES TO SPEAK
    A correlation matrix over k holons estimated from a handful of observations is noise
    shaped like a matrix, and inverting it amplifies exactly that noise. Below the history
    floor the integrator returns diagnostics and NO combined claim, which is the same
    "no opinion" property the sensing holons have. An integrator that always produces a
    number is the thing being guarded against.
"""

import os
import sys
from collections import defaultdict, deque

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))
sys.path.insert(0, os.path.dirname(__file__))

import breadth  # noqa: E402

from holon import Basis, Claim  # noqa: E402

# A k x k correlation matrix needs far more than k observations before its inverse means
# anything. 5k is the conventional floor and 30 keeps small k honest; both are arbitrary in
# the same way a significance level is, and both are stated rather than buried.
MIN_OBS_PER_HOLON = 5
MIN_OBS_FLOOR = 30

# Above this condition number the holons are collinear enough that the inverse is dominated
# by numerical noise. Reported as degenerate rather than pseudo-inverted, because a
# pseudo-inverse here silently invents an independence that the data denies.
MAX_CONDITION = 1e6

# Effective breadth below this means the holons are one opinion wearing several names, and the
# combination is not worth making whatever the condition number says.
#
# This gate was MISSING in the first draft, and the omission is instructive: the breadth
# diagnostic was computed correctly, printed, and then ignored by the code that acted on it.
# Two real volatility holons measured rho = 0.969 and BR = 1.03 -- one opinion -- and the
# integrator combined them anyway, producing GLS weights of -0.78 / +1.78 and an out-of-sample
# R-squared of +0.44 against +0.56 for the better holon used alone. The combination was worse
# than either input. Condition number was 64, nowhere near the 1e6 refusal.
#
# At rho = 0.97 an 11% precision edge is enough to drive the weaker holon to a negative
# weight: the combination stops averaging and starts extrapolating the difference between two
# nearly identical estimates, which is the least reliable quantity available.
MIN_BREADTH = 1.35


class Integrator:
    """
    L2. Holds claim history, measures inter-holon correlation, combines by GLS.

    Groups by (quantity, horizon_s): a volatility forecast and a spread-capture forecast are
    different quantities and combining them is a category error, not a diversification.
    """

    def __init__(self, history=512):
        self._hist = defaultdict(lambda: deque(maxlen=history))
        self._refused = defaultdict(int)

    def observe(self, claims):
        """Record a decision-time slice of claims. Inadmissible ones are counted, not weighted."""
        for c in claims:
            if not c.admissible:
                reason = "incomplete_record" if not c.completeness else "untested_basis"
                self._refused[(c.holon, reason)] += 1
                continue
            self._hist[(c.quantity, c.horizon_s, c.holon)].append((c.at, c.estimate))

    def combine(self, claims):
        """
        Combine one decision-time slice. Returns a dict of diagnostics, with `claim` set to
        a Claim when the history supports a combination and None when it does not.
        """
        adm = [c for c in claims if c.admissible]
        if not adm:
            return {"claim": None, "refused": "no admissible claims", "n_holons": 0}

        groups = defaultdict(list)
        for c in adm:
            groups[(c.quantity, c.horizon_s)].append(c)
        if len(groups) > 1:
            raise ValueError(
                f"combine() takes one (quantity, horizon) group; got {sorted(groups)}. "
                f"Combining different quantities is a category error, not diversification")

        (quantity, horizon), group = next(iter(groups.items()))
        group.sort(key=lambda c: c.holon)
        names = [c.holon for c in group]
        k = len(group)

        if k == 1:
            c = group[0]
            return {"claim": c, "n_holons": 1, "note": "single holon; nothing to integrate"}

        aligned, n_obs = self._aligned_history(quantity, horizon, names)
        need = max(MIN_OBS_FLOOR, MIN_OBS_PER_HOLON * k)
        if n_obs < need:
            return {"claim": None, "n_holons": k, "n_obs": n_obs, "n_obs_required": need,
                    "refused": "insufficient aligned history to estimate correlation"}

        corr = np.corrcoef(aligned, rowvar=False)
        corr = np.nan_to_num(corr, nan=0.0)
        np.fill_diagonal(corr, 1.0)

        br = breadth.effective_breadth(corr)
        if br["breadth_participation_ratio"] < MIN_BREADTH:
            return {"claim": None, "n_holons": k, "n_obs": n_obs, "breadth": br,
                    "refused": (f"effective breadth {br['breadth_participation_ratio']:.2f} "
                                f"< {MIN_BREADTH}; these holons are one opinion")}

        sd = np.array([c.uncertainty for c in group], dtype=float)
        est = np.array([c.estimate for c in group], dtype=float)
        sigma = corr * np.outer(sd, sd)

        cond = float(np.linalg.cond(sigma))
        if not np.isfinite(cond) or cond > MAX_CONDITION:
            return {"claim": None, "n_holons": k, "n_obs": n_obs, "condition": cond,
                    "breadth": br,
                    "refused": "holons are collinear; the combination is not identified"}

        ones = np.ones(k)
        inv = np.linalg.inv(sigma)
        denom = float(ones @ inv @ ones)
        if denom <= 0:
            return {"claim": None, "n_holons": k, "breadth": br,
                    "refused": "non-positive-definite covariance"}

        w = (inv @ ones) / denom
        combined = float(w @ est)
        var = 1.0 / denom
        naive_var = 1.0 / float((1.0 / sd ** 2).sum())

        # The WEAKEST basis governs. Basis is ordered strongest-first, so this is max(), and
        # the obvious min() is wrong in the dangerous direction: it would let one MEASURED
        # holon launder authority onto a combination that rests partly on a fitted one.
        basis = max((c.basis for c in group), key=lambda b: list(Basis).index(b))
        merged = Claim(
            holon="integrator",
            quantity=quantity,
            horizon_s=horizon,
            estimate=combined,
            uncertainty=float(np.sqrt(var)),
            basis=basis,
            completeness=True,
            at=max(c.at for c in group),
            notes=(f"GLS over {k} holons; BR_eff="
                   f"{br['breadth_participation_ratio']:.2f}; "
                   f"variance inflation {var / naive_var:.2f}x vs independence"),
            evidence="; ".join(sorted({c.evidence for c in group if c.evidence})),
        )

        return {
            "claim": merged,
            "n_holons": k,
            "n_obs": n_obs,
            "holons": names,
            "weights": dict(zip(names, (float(x) for x in w))),
            "breadth": br,
            "variance_inflation": float(var / naive_var),
            "condition": cond,
        }

    def _aligned_history(self, quantity, horizon, names):
        """
        Only decision times where EVERY holon in the group spoke. A holon returning "no
        opinion" creates a hole, and filling it would manufacture agreement that never
        happened.
        """
        series = [dict(self._hist[(quantity, horizon, n)]) for n in names]
        common = set(series[0])
        for s in series[1:]:
            common &= set(s)
        ts = sorted(common)
        if not ts:
            return np.empty((0, len(names))), 0
        return np.array([[s[t] for s in series] for t in ts], dtype=float), len(ts)

    def refusals(self):
        """Why claims were dropped, by holon. A rising count is a holon in trouble."""
        return dict(self._refused)
