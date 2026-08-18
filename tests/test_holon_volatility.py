"""
Checks for the volatility holon.

Two of these are the ones that matter. `har_finds_nothing_in_white_noise` is the reverse-
detection case: a model that reports skill on a series with none is worse than useless, and a
suite that only checks it succeeds on predictable data would pass with a look-ahead bug in
place. `no_lookahead_in_the_walk_forward` guards the RDB-1 error class directly -- treating
information from day i+1 as available at day i inflates every figure downstream and does not
crash.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "holons"))

import numpy as np
from holon import Basis
from volatility import (MONTH, MIN_TRAIN, VolatilityHolon, har_features, oos_r2,
                       realized_vol_daily, walk_forward)

CHECKS = []
def check(fn):
    CHECKS.append(fn)
    return fn


def ar1_log_rv(n=1600, phi=0.73, seed=20260817):
    """Log RV with the autocorrelation the exploration measured at lag 1 (+0.730)."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.normal(0, 0.3)
    return x - 3.0


@check
def har_recovers_structure_in_a_series_built_to_have_it():
    log_rv = ar1_log_rv()
    rec = walk_forward(log_rv, VolatilityHolon())
    r2 = oos_r2(rec)
    assert r2 > 0.35, f"HAR found only R2={r2:.4f} in a series with rho_1 = 0.73"
    return f"AR(1) phi=0.73 -> OOS R2 = {r2:+.4f} across {len(rec)} predictions"


@check
def har_finds_nothing_in_white_noise():
    """THE REVERSE CASE. Skill reported here means a leak, not a discovery."""
    rng = np.random.default_rng(20260817)
    log_rv = rng.normal(-3.0, 0.3, 1600)
    rec = walk_forward(log_rv, VolatilityHolon())
    r2 = oos_r2(rec)
    assert r2 < 0.05, f"HAR reported R2={r2:+.4f} on white noise; something leaks"
    return f"white noise -> OOS R2 = {r2:+.4f} (no skill claimed)"


@check
def no_lookahead_in_the_walk_forward():
    """
    Corrupt the future only, refit, and require the prediction to be unchanged. If any
    information from day i+1 onward reaches the fit for day i+1, this moves.
    """
    log_rv = ar1_log_rv()
    i = MONTH - 1 + MIN_TRAIN + 100
    h = VolatilityHolon()
    clean = h.fit_predict(log_rv, i)

    poisoned = log_rv.copy()
    poisoned[i + 1:] += 100.0
    same = h.fit_predict(poisoned, i)

    assert clean is not None and abs(clean - same) < 1e-9, (
        f"prediction moved {clean} -> {same} when only the FUTURE was altered")
    return "altering every value after day i leaves the day-i+1 prediction untouched"


@check
def features_never_read_past_today():
    log_rv = np.arange(100.0)
    f = har_features(log_rv, 50)
    assert f[1] == 50.0
    assert f[2] == log_rv[46:51].mean()
    assert f[3] == log_rv[29:51].mean()
    return "day, week and month features all terminate at today's close"


@check
def the_holon_declines_until_it_has_measured_its_own_error():
    log_rv = ar1_log_rv()
    h = VolatilityHolon()
    i = MONTH - 1 + MIN_TRAIN + 5
    assert h.assess({"log_rv": log_rv, "i": i, "completeness": True, "at": 0.0}) is None
    for _ in range(25):
        h.score(0.0, 0.1)
    c = h.assess({"log_rv": log_rv, "i": i, "completeness": True, "at": 0.0})
    assert c is not None, "still silent after 25 scored errors"
    return "no claim before 20 scored residuals; a claim after"


@check
def an_unvouched_record_produces_no_claim():
    log_rv = ar1_log_rv()
    h = VolatilityHolon()
    for _ in range(25):
        h.score(0.0, 0.1)
    i = MONTH - 1 + MIN_TRAIN + 5
    assert h.assess({"log_rv": log_rv, "i": i, "completeness": False, "at": 0.0}) is None
    return "completeness=False yields None, never a discounted claim"


@check
def uncertainty_widens_when_the_model_degrades():
    log_rv = ar1_log_rv()
    h = VolatilityHolon()
    i = MONTH - 1 + MIN_TRAIN + 5
    for _ in range(30):
        h.score(0.0, 0.02)
    tight = h.assess({"log_rv": log_rv, "i": i, "completeness": True, "at": 0.0}).uncertainty
    for _ in range(60):
        h.score(0.0, np.random.default_rng(1).normal(0, 0.5))
    wide = h.assess({"log_rv": log_rv, "i": i, "completeness": True, "at": 0.0})
    assert wide is None or wide.uncertainty > tight, "error bar did not respond to worse misses"
    return "self-measured sigma tracks recent walk-forward residuals"


@check
def it_declares_itself_fitted_not_measured():
    assert VolatilityHolon().basis is Basis.FITTED
    return "basis is FITTED until the committed figures are reproduced and recorded"


@check
def partial_days_are_dropped_not_scaled():
    import datetime as dt
    base = int(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    rows = []
    for d in range(3):
        n = 1440 if d != 1 else 500          # day 1 is short
        for m in range(n):
            t = base + (d * 1440 + m) * 60_000
            rows.append((t, 100.0, 100.0, 100.0, 100.0 + 0.01 * m, 1.0, t + 59_999, 1.0))
    arr = np.array(rows, dtype=float)
    out = realized_vol_daily(arr)
    assert len(out) == 2, f"expected 2 full days, got {len(out)}"
    return "a day missing 65% of its minutes is dropped rather than inflated"


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
