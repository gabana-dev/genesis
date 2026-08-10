"""
MEASURE-1 machinery (market/).

Covers the three data facts found during the first ingest -- each of which produced a wrong
result before it was found -- and the statistical methods against cases with known answers.

Run: .venv/bin/python tests/test_market.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import data  # noqa: E402
import stats  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


MIN = data.MINUTE_MS


def bars(n, start=1546300800000, step=MIN, price=100.0):
    """n well-formed 1-minute klines: open_time, o, h, l, c, vol, close_time, qv, trades."""
    r = np.zeros((n, 9))
    r[:, 0] = start + np.arange(n) * step
    r[:, 6] = r[:, 0] + step - 1
    r[:, 1:5] = price
    r[:, 5] = 1.0
    r[:, 7] = price
    r[:, 8] = 10
    return r


# ---- the three data facts ---------------------------------------------------------------

@check
def halt_truncated_bar_is_accepted():
    """
    Found on the first ingest: 2019-06-07 21:13 spans 13,524ms with zero volume, followed by
    61 missing bars. A genuine venue halt. The first version of the verifier rejected it.
    """
    r = bars(100)
    r[50, 6] = r[50, 0] + 13524                 # truncated at the halt
    r[51:, 0] += 61 * MIN                       # ... and 61 bars missing
    r[51:, 6] = r[51:, 0] + MIN - 1
    f = data.verify_timestamp_semantics(r)
    assert f["short_close_time_bars"] == 1 and f["of_which_precede_a_halt"] == 1, f
    return "a halt-truncated bar followed by a gap is accepted and counted"


@check
def unreliable_close_time_is_accepted():
    """
    2021-12-24 04:59 spans 54,362ms with 1,124 trades and NO following gap. `close_time` is
    simply unreliable in the bulk archives. The second version of the verifier rejected it.
    """
    r = bars(100)
    r[50, 6] = r[50, 0] + 54362                 # short, but 51 still opens on schedule
    f = data.verify_timestamp_semantics(r)
    assert f["short_close_time_bars"] == 1 and f["of_which_precede_a_halt"] == 0, f
    return "a short close_time with no gap is accepted -- the field, not the alignment, is wrong"


@check
def microsecond_archives_are_normalised():
    """
    Binance switched the archives to MICROSECOND timestamps during 2025. Concatenating both
    units unconverted would place every 2025+ bar ~50,000 years in the future.
    """
    us = "1735689600000000,1.0,1.0,1.0,1.0,1.0,1735689659999999,1.0,1\n"
    ms = "1546300800000,1.0,1.0,1.0,1.0,1.0,1546300859999,1.0,1\n"
    a = data._parse(us.encode())
    b = data._parse(ms.encode())
    assert a[0, 0] == 1735689600000, a[0, 0]
    assert b[0, 0] == 1546300800000, b[0, 0]
    assert a[0, 6] - a[0, 0] == MIN - 1 and b[0, 6] - b[0, 0] == MIN - 1
    return "microsecond archives are detected by magnitude and normalised to ms"


@check
def misalignment_still_raises():
    """The verifier must not have become permissive. Off-boundary timestamps are fatal."""
    r = bars(100)
    r[:, 0] += 137                              # no longer on a minute boundary
    r[:, 6] = r[:, 0] + MIN - 1
    try:
        data.verify_timestamp_semantics(r)
    except ValueError as e:
        assert "boundary" in str(e), e
        return "off-boundary open_time is still rejected"
    raise AssertionError("misaligned timestamps were accepted")


@check
def pervasive_short_close_times_still_raise():
    r = bars(100)
    r[:, 6] = r[:, 0] + 30000                   # every bar wrong -> not a venue quirk
    try:
        data.verify_timestamp_semantics(r)
    except ValueError as e:
        assert "too many" in str(e), e
        return "a wholesale close_time mismatch is still rejected"
    raise AssertionError("pervasive mismatch was accepted")


# ---- segmentation ------------------------------------------------------------------------

@check
def aggregation_never_spans_a_halt():
    """
    The reason segments exist. Aggregating across a halt would produce a '1-hour return'
    spanning many real hours and label it an ordinary observation.
    """
    r = bars(300)
    r[150:, 0] += 600 * MIN                     # a 10-hour halt after bar 149
    r[150:, 6] = r[150:, 0] + MIN - 1
    _, facts = _fake_load(r)
    segs = data.contiguous_segments(r, facts)
    assert len(segs) == 2 and len(segs[0]) == 150, [len(s) for s in segs]
    for s in segs:
        agg = data.aggregate(s, 60)
        gaps = np.diff(data.open_time(agg))
        assert np.all(gaps == 60 * MIN), "an aggregated block spans a halt"
    return "segments split at halts; no aggregated block spans one"


def _fake_load(rows):
    ts = data.open_time(rows)
    d = np.diff(ts).astype(np.int64)
    gap_at = np.flatnonzero(d != MIN)
    return rows, {"halt_index": gap_at.astype(np.int64).tolist()}


# ---- statistics against known answers ----------------------------------------------------

@check
def variance_ratio_is_one_for_a_random_walk():
    rng = np.random.default_rng(1)
    r = rng.normal(0, 0.01, 200_000)
    vr, z, p = stats.variance_ratio(r, 10)
    assert abs(vr - 1.0) < 0.05, vr
    assert p > 0.01, f"random walk wrongly rejected: p={p}"
    return f"VR(10) = {vr:.4f} on an IID series, not rejected"


@check
def variance_ratio_detects_mean_reversion():
    rng = np.random.default_rng(2)
    e = rng.normal(0, 0.01, 200_000)
    r = e[1:] - 0.4 * e[:-1]                    # MA(-0.4): mean-reverting
    vr, z, p = stats.variance_ratio(r, 10)
    assert vr < 0.9, vr
    assert p < 0.01, f"z2={z} p={p} -- the heteroskedastic-robust statistic failed to reject"
    return f"VR(10) = {vr:.4f}, z2 = {z:.1f} on a mean-reverting series, rejected"


@check
def variance_ratio_detects_trending():
    rng = np.random.default_rng(3)
    e = rng.normal(0, 0.01, 200_000)
    r = e[1:] + 0.4 * e[:-1]                    # MA(+0.4): trending
    vr, z, p = stats.variance_ratio(r, 10)
    assert vr > 1.1, vr
    return f"VR(10) = {vr:.4f} > 1 on a trending series"


@check
def roll_recovers_a_known_spread():
    """A pure bid-ask bounce on a constant true price must return the spread that made it."""
    rng = np.random.default_rng(4)
    true, s = 100.0, 0.02
    obs = true + (s / 2) * rng.choice([-1.0, 1.0], 100_000)
    out = stats.roll_spread(obs)
    assert out["model_applies"], out
    assert abs(out["spread_abs"] - s) < 0.002, out
    return f"Roll recovers {out['spread_abs']:.4f} from a planted {s} spread"


@check
def roll_reports_inapplicable_rather_than_clipping():
    # A random walk has ~zero covariance whose SIGN is random, so it is not a valid case.
    # A genuinely trending series is: MA(+0.5) price changes give positive autocovariance.
    rng = np.random.default_rng(5)
    e = rng.normal(0, 0.01, 50_000)
    dp = e[1:] + 0.5 * e[:-1]
    p = 100 + np.cumsum(dp)
    out = stats.roll_spread(p)
    assert not out["model_applies"] or out["spread_abs"] != out["spread_abs"], out
    return "a non-negative covariance reports model_applies=False, never a clipped zero"


@check
def breakeven_matches_the_contract_formula():
    # c = 0.0004, m = 0.017, phi = 0.5  ->  0.5 + 0.0004/(2*0.5*0.017)
    p = stats.breakeven_hit_rate(0.0004, 0.017, 0.5)
    assert abs(p - (0.5 + 0.0004 / 0.017)) < 1e-12, p
    assert stats.breakeven_hit_rate(0.02, 0.001, 1.0) != stats.breakeven_hit_rate(0.02, 0.001, 1.0), \
        "p* above 1 must be NaN, not a number above 1"
    return f"p* = {p:.4f} matches section 2, and an unreachable horizon returns NaN"


@check
def block_bootstrap_is_wider_than_iid_on_dependent_data():
    """
    The reason for the block bootstrap. On an autocorrelated series an IID bootstrap
    understates the interval; if these came out equal the block structure would be doing
    nothing.
    """
    rng = np.random.default_rng(6)
    e = rng.normal(0, 1, 20_000)
    x = np.convolve(e, np.ones(50) / 50, mode="same")     # strongly dependent
    lo_b, hi_b = stats.block_bootstrap_ci(x, np.mean, n_boot=400)
    lo_i, hi_i = stats.block_bootstrap_ci(x, np.mean, n_boot=400, block=1)
    assert (hi_b - lo_b) > 1.5 * (hi_i - lo_i), (hi_b - lo_b, hi_i - lo_i)
    return "the block bootstrap is materially wider than an IID one on dependent data"


@check
def amihud_rises_when_price_moves_more_per_dollar():
    r = np.array([0.01, -0.01, 0.01, -0.01])
    thin = stats.amihud(r, np.array([1e5] * 4))
    deep = stats.amihud(r, np.array([1e7] * 4))
    assert thin > deep * 50, (thin, deep)
    return "Amihud is higher for the thinner market"


# ---- the Book cache ------------------------------------------------------------------------
# Cached best-price invalidation is the subtlest code in market/. A bug here would not crash
# -- it would silently return a stale best price and corrupt every fill in EXEC-1. Each check
# compares the cache against a full recomputation, which is the thing it replaces.

@check
def book_cache_matches_a_full_scan_under_random_updates():
    import random
    import book as bk
    rng = random.Random(20260810)
    b = bk.Book()
    ref_bids, ref_asks = {}, {}
    for _ in range(4000):
        side = rng.choice(("bids", "asks"))
        price = round(rng.uniform(99.0, 101.0), 2)
        size = rng.choice((0.0, 0.0, rng.uniform(0.1, 10.0)))
        b.set(side, price, size)
        ref = ref_bids if side == "bids" else ref_asks
        if size <= 0:
            ref.pop(round(price, 8), None)
        else:
            ref[round(price, 8)] = size
        want_bb = max(ref_bids) if ref_bids else None
        want_ba = min(ref_asks) if ref_asks else None
        assert b.best_bid == want_bb, (b.best_bid, want_bb)
        assert b.best_ask == want_ba, (b.best_ask, want_ba)
    return "cached best matches a full scan across 4,000 random inserts and removals"


@check
def removing_the_best_level_invalidates_the_cache():
    import book as bk
    b = bk.Book()
    for p in (99.98, 99.99, 100.00):
        b.set("bids", p, 1.0)
    assert b.best_bid == 100.00
    b.set("bids", 100.00, 0.0)                 # remove the best
    assert b.best_bid == 99.99, b.best_bid
    b.set("bids", 99.98, 0.0)                  # remove a NON-best: cache must survive
    assert b.best_bid == 99.99, b.best_bid
    return "removing the best recomputes; removing any other level does not disturb the cache"


@check
def a_price_computed_by_arithmetic_hits_the_same_key():
    """
    fills.py posts at best - n*tick. If float arithmetic lands one ulp off the parsed key,
    size_at returns 0 and the order silently never fills.
    """
    import book as bk
    b = bk.Book()
    for p in ("100.00", "99.99", "99.95"):
        b.set("bids", float(p), 3.0)
    for n, want in ((0, 100.00), (1, 99.99), (5, 99.95)):
        price = round(100.00 - n * 0.01, 8)
        assert b.size_at("bids", price) == 3.0 * want, (n, price)
    return "prices derived as best - n*tick resolve to the parsed level, not to zero"


@check
def snapshot_clears_stale_levels_and_cache():
    import book as bk
    b = bk.Book()
    b.set("bids", 100.0, 1.0)
    b.set("asks", 101.0, 1.0)
    b.clear()
    assert b.best_bid is None and b.best_ask is None and not b.ready()
    b.set("bids", 50.0, 1.0)
    b.set("asks", 51.0, 1.0)
    assert b.best_bid == 50.0 and b.best_ask == 51.0 and b.ready()
    return "a snapshot clears levels and both cached bests"


# ---- book arithmetic ---------------------------------------------------------------------

@check
def sweep_cost_walks_levels_and_reports_exhaustion():
    import book as bk
    asks = {"100.0": "1.0", "101.0": "1.0", "102.0": "1.0"}
    out = bk.sweep_cost(asks, 100.0, "asks")
    assert abs(out["vwap"] - 100.0) < 1e-9 and out["touch"] == 100.0, out
    out2 = bk.sweep_cost(asks, 250.0, "asks")           # spans two levels
    assert 100.0 < out2["vwap"] < 101.0 and out2["slippage_frac"] > 0, out2
    assert bk.sweep_cost(asks, 10_000.0, "asks") is None, "depth exhaustion must return None"
    return "book walk prices across levels and refuses to extrapolate past recorded depth"


@check
def round_trip_impact_is_positive_and_grows_with_size():
    import book as bk
    bids = {"99.0": "1.0", "98.0": "10.0"}
    asks = {"100.0": "1.0", "101.0": "10.0"}
    small = bk.round_trip_impact(bids, asks, 50.0)
    large = bk.round_trip_impact(bids, asks, 600.0)
    assert small > 0 and large > small, (small, large)
    return f"round-trip cost grows with size: {small:.5f} -> {large:.5f}"


def main():
    failed = 0
    for fn in _checks:
        try:
            print(f"  ok  {fn.__name__}  --  {fn()}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"MEASURE-1 checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
