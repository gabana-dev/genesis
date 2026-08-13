"""
Effective breadth of a correlated cross-section (market/breadth.py).

Every case here has an answer known by construction. The measure being computed is one whose
errors are invisible on real data: a breadth of 2.1 and a breadth of 21 both look like
plausible numbers for thirty instruments, and nothing about either says which is right.

The question it serves: MEASURE-1 §8 established that settling the daily horizon by time
series on BTCUSDT alone needs 68 years of a seven-year-old instrument, and named the escape as
"conditional, cross-sectional or event-based" evidence. The cross-sectional route has an
arithmetic precondition -- enough independent bets to be worth the trouble -- and this measures
it. A wrong breadth would either close a viable route or open a dead one.

Run: .venv/bin/python tests/test_breadth.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import breadth as B  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def equicorr(k, r):
    m = np.full((k, k), float(r))
    np.fill_diagonal(m, 1.0)
    return m


def blocks(n_per, n_blocks, within, across):
    k = n_per * n_blocks
    m = np.empty((k, k))
    for i in range(k):
        for j in range(k):
            m[i, j] = 1.0 if i == j else (within if i // n_per == j // n_per else across)
    return m


# ── The two ends of the scale ───────────────────────────────────────────────────────────

@check
def independent_instruments_give_breadth_equal_to_their_count():
    r = B.effective_breadth(np.eye(10))
    assert abs(r["breadth_equicorrelation"] - 10) < 1e-9, r
    assert abs(r["breadth_participation_ratio"] - 10) < 1e-9, r
    return "ten independent instruments give breadth 10.00 on both measures"


@check
def perfectly_correlated_instruments_are_one_bet():
    r = B.effective_breadth(equicorr(30, 0.999999))
    assert r["breadth_participation_ratio"] < 1.01, r
    assert r["breadth_equicorrelation"] < 1.01, r
    assert r["pc1_variance_share"] > 0.99, r
    return "thirty perfectly correlated instruments are one bet, however many tickers"


@check
def the_equicorrelation_formula_matches_the_hand_calculation():
    # k / (1 + (k-1)*rho) -- the number quoted in discussion before any data was fetched.
    r = B.effective_breadth(equicorr(30, 0.7))
    assert abs(r["breadth_equicorrelation"] - 30 / (1 + 29 * 0.7)) < 1e-9, r
    assert abs(r["breadth_equicorrelation"] - 1.408) < 0.001, r
    return "k=30, rho=0.7 gives 1.41, matching the hand calculation"


# ── Where the simple measure misleads ───────────────────────────────────────────────────

@check
def the_participation_ratio_sees_structure_the_average_cannot():
    # Two tight blocks of ten: the truth is about two bets. The equicorrelation formula assumes
    # every pair shares one correlation and cannot represent this; the eigenvalue measure can.
    # This is the whole reason both are reported.
    m = blocks(n_per=10, n_blocks=2, within=0.95, across=0.10)
    r = B.effective_breadth(m)
    assert 1.5 < r["breadth_participation_ratio"] < 3.0, r
    assert r["breadth_participation_ratio"] > r["breadth_equicorrelation"], r
    return "two tight blocks read ~2 on the eigenvalue measure; the average cannot see them"


@check
def removing_the_common_factor_reveals_the_residual_dimensionality():
    # A single market factor over otherwise independent instruments. Directionally this is one
    # bet; on the residual it is many. Reporting only the first number would close the
    # relative-value route on arithmetic that does not apply to it.
    k, load = 20, 0.8
    m = equicorr(k, load ** 2)
    raw = B.effective_breadth(m)["breadth_participation_ratio"]

    lam, vec = np.linalg.eigh(m)
    o = np.argsort(lam)[::-1]
    R = m - lam[o[0]] * np.outer(vec[:, o[0]], vec[:, o[0]])
    d = np.sqrt(np.clip(np.diag(R), 1e-12, None))
    res = B.effective_breadth(R / np.outer(d, d))["breadth_participation_ratio"]

    assert raw < 3.0, raw
    assert res > raw * 3, (raw, res)
    return f"one common factor: breadth {raw:.2f} raw, {res:.2f} on the residual"


# ── Guards against numbers that would mislead rather than fail ──────────────────────────

@check
def a_degenerate_correlation_does_not_produce_a_negative_breadth():
    # With rho <= -1/(k-1) the equicorrelation matrix is not positive semi-definite and the
    # formula has no meaning. A negative breadth printed into a report reads as a number.
    r = B.effective_breadth(equicorr(3, -0.49999999))
    assert r["breadth_equicorrelation"] > 0, r
    return "a degenerate correlation returns a positive or infinite breadth, never a negative one"


@check
def breadth_never_exceeds_the_instrument_count():
    for k, rho in ((5, 0.0), (12, 0.3), (33, 0.67)):
        r = B.effective_breadth(equicorr(k, rho))
        assert r["breadth_participation_ratio"] <= k + 1e-9, (k, rho, r)
        assert r["breadth_equicorrelation"] <= k + 1e-9, (k, rho, r)
    return "no configuration yields more independent bets than there are instruments"


@check
def the_variance_shares_are_a_fraction_and_ordered():
    r = B.effective_breadth(equicorr(15, 0.5))
    assert 0.0 <= r["pc1_variance_share"] <= 1.0, r
    assert r["pc1_plus_pc2_share"] >= r["pc1_variance_share"], r
    assert r["pc1_plus_pc2_share"] <= 1.0 + 1e-9, r
    return "PC1 and PC1+PC2 shares are bounded fractions, correctly ordered"


@check
def alignment_uses_the_intersection_and_never_fills_gaps():
    # Forward-filling a missing bar inserts a zero return, which drags every correlation
    # involving that instrument toward zero -- flattering the exact quantity being measured.
    src = open(os.path.join(os.path.dirname(__file__), "..", "market", "breadth.py")).read()
    assert "ffill" not in src and "fillna" not in src and "nan_to_num" not in src
    assert "common = ts if common is None else (common & ts)" in src
    return "returns are aligned on the timestamp intersection; no gap is ever filled"


@check
def the_horizon_matches_the_affordability_floor():
    # Correlation is horizon-dependent. Measured at 1m this would answer a question nobody
    # asked: MEASURE-1 put affordability at 4h, so that is where breadth must be measured.
    assert B.INTERVAL == "4h", B.INTERVAL
    return "breadth is measured at 4h, where MEASURE-1 located the affordability floor"


@check
def the_source_is_the_perpetual_futures_archive():
    # The question was asked about perps. Spot would be a different cross-section, and after
    # today's EXEC-1 finding the distinction is not a detail.
    assert "futures/um" in B.FUTURES_BASE, B.FUTURES_BASE
    return "the cross-section is USD-M perpetual futures, the market the question was about"


if __name__ == "__main__":
    failures = 0
    for fn in _checks:
        try:
            print(f"  ok  {fn.__name__}  --  {fn()}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL  {fn.__name__}  --  {e}")
    total = len(_checks)
    print(f"{'PASS' if not failures else 'FAIL'} -- {total - failures}/{total} breadth checks")
    sys.exit(1 if failures else 0)
