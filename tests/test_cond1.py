"""
COND-1 arithmetic, checked against synthetic cases with hand-computed answers, BEFORE q5
closes and the real data exists.

That ordering is the point. Every one of these could be written after the recording lands, and
every arbitrary choice would then be made with a result visible.

Run: .venv/bin/python tests/test_cond1.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import cond1 as C  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


@check
def the_family_is_exactly_twenty_nine():
    """The contract fixes it. If the grid drifts, the correction is wrong."""
    n = C.check_family()
    cs = C.cells()
    by = {}
    for cond, _, _ in cs:
        by[cond] = by.get(cond, 0) + 1
    assert n == 29, n
    assert by == {"reference": 5, "A": 8, "B": 4, "C": 4, "D": 8}, by
    return f"29 cells: A=8 B=4 C=4 D=8 reference=5"


@check
def cell_keys_are_unique():
    """Two cells sharing a key would silently overwrite one another in the report."""
    keys = [k for _, k, _ in C.cells()]
    assert len(keys) == len(set(keys)), [k for k in keys if keys.count(k) > 1]
    return f"{len(keys)} distinct cell keys"


@check
def basis_buckets_partition_by_magnitude_and_sign():
    b = np.array([0.2, -0.2, 1.0, -1.0, 2.0, 5.0, -5.0])
    pos_narrow = C.a_mask(b, "positive", 0.0, 0.5)
    neg_narrow = C.a_mask(b, "negative", 0.0, 0.5)
    assert list(pos_narrow) == [True, False, False, False, False, False, False]
    assert list(neg_narrow) == [False, True, False, False, False, False, False]
    wide = C.a_mask(b, "positive", 3.0, float("inf"))
    assert list(wide) == [False] * 5 + [True, False]
    # Every observation lands in exactly one (sign, bucket) cell.
    total = np.zeros(len(b), dtype=int)
    for s in C.BASIS_SIGNS:
        for lo, hi in C.BASIS_BUCKETS_BPS:
            total += C.a_mask(b, s, lo, hi).astype(int)
    assert list(total) == [1] * len(b), total
    return "sign and magnitude partition cleanly; every point lands in exactly one cell"


@check
def cancellation_subtracts_trades_rather_than_assuming_none():
    """
    The whole reason q5 records trades alongside depth. Size that left a level is only a
    CANCELLATION to the extent it was not traded.
    """
    r = C.cancellation_ratio(removed_size=[10.0, 10.0, 10.0],
                             traded_size=[0.0, 10.0, 4.0],
                             visible_depth=[20.0, 20.0, 20.0])
    assert np.allclose(r, [0.5, 0.0, 0.3]), r
    assert list(C.b_mask(r, 0.25)) == [True, False, True]
    return "10 removed with 4 traded on depth 20 is a 0.30 cancel ratio, not 0.50"


@check
def cancellation_never_goes_negative_or_divides_by_zero():
    r = C.cancellation_ratio([5.0, 5.0], [9.0, 0.0], [10.0, 0.0])
    assert r[0] == 0.0, r
    assert not np.isfinite(r[1]), r
    assert list(C.b_mask(r, 0.25)) == [False, False]
    return "more traded than removed clamps to 0; zero depth yields NaN, never inf"


@check
def precision_is_the_declared_primary_and_recall_is_not_computed():
    """
    forceOrder publishes only the largest liquidation per symbol per 1000ms, so absence is not
    evidence of absence and the negative cell of a 2x2 is unreliable. Only precision is clean.
    """
    fired = [True, True, True, False, False]
    key = [True, False, True, True, False]
    p = C.precision_against_key(fired, key)
    assert abs(p - 2 / 3) < 1e-12, p
    assert C.precision_against_key([False, False], [True, True]) is None
    return "2 of 3 fires confirmed -> 0.667; no fires -> None rather than a fabricated 0"


@check
def sweeps_break_on_id_gap_side_change_and_time_gap():
    ids = [1, 2, 3, 10, 11, 12, 13]
    sides = ["B", "B", "B", "B", "B", "S", "S"]
    times = [0, 1, 2, 3, 4, 5, 400]
    sizes = [1, 1, 1, 2, 2, 3, 3]
    sw = C.reconstruct_sweeps(ids, sides, times, sizes, max_gap_ms=50)
    got = [(s["first"], s["last"], s["side"], s["size"]) for s in sw]
    assert got == [(1, 3, "B", 3.0), (10, 11, "B", 4.0), (12, 12, "S", 3.0),
                   (13, 13, "S", 3.0)], got
    return "id gap, side change and a 395ms pause each end a sweep"


@check
def a_contiguous_run_is_one_sweep_not_many():
    """The point of D: aggTrade would report this as five records; the parent is one order."""
    sw = C.reconstruct_sweeps([5, 6, 7, 8, 9], ["B"] * 5, [0, 1, 2, 3, 4], [2.0] * 5,
                              max_gap_ms=50)
    assert len(sw) == 1, sw
    assert sw[0]["size"] == 10.0
    return "five contiguous prints reconstruct to a single 10 BTC sweep"


@check
def thin_cells_are_reported_not_merged():
    rep = C.cell_report(np.full(C.MIN_FILLS - 1, -1e-4), "thin", "A")
    assert rep["sufficient"] is False
    assert "median_markout_bps" not in rep
    assert str(C.MIN_FILLS) in rep["excluded_reason"]
    return f"{C.MIN_FILLS - 1} fills -> insufficient, and no statistic exposed"


@check
def k5_voids_only_conditioner_A():
    ok = C.k5_clock([0, 10, 20], [5, 15, 25])
    bad = C.k5_clock([0, 10, 20], [200, 210, 220])
    assert ok["A_void"] is False and bad["A_void"] is True
    return "50ms threshold: 5ms disagreement passes, 200ms voids A and only A"


@check
def k4_requires_reporting_not_silent_restriction():
    lo = C.k4_window(0.10)
    hi = C.k4_window(0.40)
    assert lo["restricted_to_complete_intervals"] is False
    assert hi["restricted_to_complete_intervals"] is True
    assert hi["must_be_reported_on_every_result"] is True
    return "above 25% incomplete, restriction is flagged for reporting on every result"


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
          f"COND-1 arithmetic checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
