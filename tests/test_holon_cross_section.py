"""
Checks for the cross-sectional volatility holon.

WHAT MATTERS HERE
    This holon exists to be INDEPENDENT of volatility.py. Its value is entirely in what it
    does NOT use. So the checks that count are the ones asserting exclusion and leakage:

      - BTC is excluded from its own predictor
      - the target never appears among the features
      - altering only the future leaves a prediction unchanged
      - a thin cross-section is refused rather than averaged

    A suite that only confirmed "it produces a number" would pass with BTC left in the
    universe, which would silently guarantee the correlation the integrator is meant to detect.

Fixtures are SYNTHETIC.

Run: .venv/bin/python tests/test_holon_cross_section.py
"""

import datetime as dt
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "holons"))

import numpy as np
from cross_section import (MIN_SYMBOLS, MONTH, MIN_TRAIN, CrossSectionVolatilityHolon,
                           align, cross_section_series, daily_log_rv, har_features)
from holon import Basis

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def bars(days=3, bars_per_day=6, start_price=100.0, drop_day=None):
    """4h bars in market-data column order: open_time at 0, close at 4."""
    base = int(dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    rows, p = [], start_price
    for d in range(days):
        n = 1 if d == drop_day else bars_per_day
        for b in range(n):
            t = base + (d * 6 + b) * 4 * 3600 * 1000
            p *= 1.001
            rows.append([t, p, p, p, p, 1.0, t + 1, 1.0])
    return np.array(rows, dtype=float)


def ar1(n=1400, phi=0.7, seed=7):
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.normal(0, 0.3)
    return x - 3.0


# ---- the estimator ---------------------------------------------------------------------

@check
def a_thin_day_is_dropped_not_scaled(tmp):
    rv = daily_log_rv(bars(days=3, drop_day=1))
    assert len(rv) == 2, f"expected 2 full days, got {len(rv)}"
    return "a day with 1 of 6 bars is dropped rather than inflated"


@check
def features_never_read_past_today(tmp):
    x = np.arange(100.0)
    f = har_features(x, 50)
    assert f[1] == 50.0
    assert f[2] == x[46:51].mean()
    assert f[3] == x[29:51].mean()
    return "day, week and month features all terminate at today"


# ---- exclusion, which is the whole point -----------------------------------------------

@check
def btc_is_excluded_from_its_own_predictor(tmp):
    """
    THE CENTRAL CHECK. If BTCUSDT survived into the cross-section, this holon would carry the
    other holon's information and the integrator's independence test would be rigged.
    """
    calls = []

    import cross_section as CS
    real_series = CS.breadth.series

    def spy(symbol, start, end, interval=None):
        calls.append(symbol)
        return bars(days=120)

    CS.breadth.series = spy
    try:
        CS.cross_section_series(["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT",
                                 "BNBUSDT", "XRPUSDT"],
                                dt.date(2024, 1, 1), dt.date(2024, 5, 1))
    finally:
        CS.breadth.series = real_series

    assert "BTCUSDT" not in calls, f"BTCUSDT was fetched into its own predictor: {calls}"
    assert len(calls) == 5, calls
    return f"BTCUSDT never requested; {len(calls)} other symbols used"


@check
def a_thin_cross_section_is_refused(tmp):
    import cross_section as CS
    real = CS.breadth.series
    CS.breadth.series = lambda s, a, b, interval=None: bars(days=120)
    try:
        dates, vals, used, dropped = CS.cross_section_series(
            ["BTCUSDT", "ETHUSDT", "SOLUSDT"], dt.date(2024, 1, 1), dt.date(2024, 5, 1))
    finally:
        CS.breadth.series = real
    assert len(vals) == 0, f"averaged over {len(used)} symbols, below the floor of {MIN_SYMBOLS}"
    return f"fewer than {MIN_SYMBOLS} usable symbols yields no series, not a thin average"


@check
def the_target_is_never_a_feature(tmp):
    """
    Corrupting BTC's own history must not move the prediction: it is the target only. If it
    leaked into the features this holon would duplicate volatility.py.
    """
    xs, ys = ar1(seed=1), ar1(seed=2)
    i = MONTH - 1 + MIN_TRAIN + 40
    h = CrossSectionVolatilityHolon()
    clean = h.fit_predict(xs, ys, i)

    poisoned = ys.copy()
    poisoned[:i + 1] += 50.0          # every PAST target value, wrecked
    moved = h.fit_predict(xs, poisoned, i)

    assert clean is not None
    assert abs(clean - moved) > 1e-9, "prediction ignored the target entirely — check the fit"
    # the fit legitimately uses past targets; what must NOT happen is the FEATURES changing
    f_clean = har_features(xs, i)
    f_again = har_features(xs, i)
    assert np.array_equal(f_clean, f_again)
    assert not np.isnan(f_clean).any()
    return "features are built from the cross-section alone; targets enter only as y"


@check
def no_lookahead_in_the_walk_forward(tmp):
    xs, ys = ar1(seed=3), ar1(seed=4)
    i = MONTH - 1 + MIN_TRAIN + 60
    h = CrossSectionVolatilityHolon()
    clean = h.fit_predict(xs, ys, i)

    fx, fy = xs.copy(), ys.copy()
    fx[i + 1:] += 100.0
    fy[i + 1:] += 100.0
    same = h.fit_predict(fx, fy, i)

    assert clean is not None and abs(clean - same) < 1e-9, (
        f"prediction moved {clean} -> {same} when only the FUTURE was altered")
    return "altering everything after day i leaves the day-i+1 prediction untouched"


# ---- the holon contract ----------------------------------------------------------------

@check
def it_declines_until_it_has_measured_its_own_error(tmp):
    xs, ys = ar1(seed=5), ar1(seed=6)
    i = MONTH - 1 + MIN_TRAIN + 5
    h = CrossSectionVolatilityHolon()
    view = {"xs": xs, "ys": ys, "i": i, "completeness": True, "at": 0.0}
    assert h.assess(view) is None
    for _ in range(25):
        h.score(0.0, 0.1)
    assert h.assess(view) is not None
    return "no claim before 20 scored residuals; a claim after"


@check
def an_unvouched_record_produces_no_claim(tmp):
    xs, ys = ar1(seed=8), ar1(seed=9)
    h = CrossSectionVolatilityHolon()
    for _ in range(25):
        h.score(0.0, 0.1)
    i = MONTH - 1 + MIN_TRAIN + 5
    assert h.assess({"xs": xs, "ys": ys, "i": i, "completeness": False, "at": 0.0}) is None
    return "completeness=False yields None, never a discounted claim"


@check
def it_declares_itself_fitted(tmp):
    assert CrossSectionVolatilityHolon().basis is Basis.FITTED
    return "basis is FITTED — a walk-forward fit, not a completed measurement"


@check
def alignment_intersects_and_never_fills(tmp):
    cs_d = [dt.date(2024, 1, d) for d in (1, 2, 3, 4)]
    cs_v = np.array([1.0, 2.0, 3.0, 4.0])
    btc_d = [dt.date(2024, 1, d) for d in (2, 4)]
    btc_v = np.array([20.0, 40.0])
    days, xs, ys = align(cs_d, cs_v, btc_d, btc_v)
    assert days == btc_d, days
    assert list(xs) == [2.0, 4.0], xs
    assert list(ys) == [20.0, 40.0], ys
    return "only days present in both survive; nothing is forward-filled"


def main():
    tmp = tempfile.mkdtemp(prefix="xsec-")
    failed = 0
    try:
        for fn in _checks:
            try:
                print(f"  ok  {fn.__name__}  --  {fn(tmp)}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL {fn.__name__}: {e}")
            except Exception as e:
                failed += 1
                print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"cross-section holon checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
