"""
Cascade arithmetic, against hand-built books with hand-computed answers.

A cascade model is trusted precisely when nobody can check it, which is why every number here is
one that can be worked out on paper. Two properties matter more than the rest:

  1. it must NEVER invent liquidity past the recorded book -- exhaustion is an answer, not a gap
     to fill with an extrapolation
  2. evaporation must make the cascade travel FURTHER, never less; a sign error would produce a
     comforting number and an inverted one

Run: .venv/bin/python tests/test_cascade.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import cascade as C  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def flat_bids(top=100.0, step=1.0, size=10.0, n=20):
    """
    A bid ladder descending from `top`, `size` base units at each of `n` levels.

    NOTE THE UNITS. `size` is base units, so a level holds size*price in NOTIONAL -- about
    $1,000 at the top. Sweeping $500 never leaves the first level and the price does not move.
    Three tests were written against $500 and failed for exactly that reason: the arithmetic was
    wrong in the test, not the model. Reaching level 97 takes roughly $3,950.
    """
    return {top - i * step: size for i in range(n)}


@check
def reach_is_the_last_price_touched_not_the_vwap(tmp=None):
    """The model bug this test exists for: vwap understates cascade reach."""
    lv = flat_bids()
    r = C.sweep_to_price(lv, 5000.0, "bids", 1.0)
    assert r["last_price"] < r["vwap"] < r["touch"], r
    return f"touch {r['touch']:.0f}, vwap {r['vwap']:.2f}, reached {r['last_price']:.0f}"


@check
def sweep_with_no_evaporation_matches_the_primitive(tmp=None):
    import book as BK
    lv = flat_bids()
    a = BK.sweep_cost(lv, 500.0, "bids")
    b = C.sweep_with_evaporation(lv, 500.0, "bids", evaporation=1.0)
    assert a["vwap"] == b["vwap"], (a, b)
    return "evaporation=1.0 is the untouched book"


@check
def evaporation_makes_price_travel_further(tmp=None):
    lv = flat_bids()
    full = C.sweep_with_evaporation(lv, 5000.0, "bids", 1.0)
    thin = C.sweep_with_evaporation(lv, 5000.0, "bids", 0.5)
    assert thin["vwap"] < full["vwap"], (full["vwap"], thin["vwap"])
    return f"vwap {full['vwap']:.2f} -> {thin['vwap']:.2f} at half depth"


@check
def exhausted_book_reports_exhaustion_not_a_number(tmp=None):
    lv = flat_bids(n=3)                      # ~3 levels of depth only
    r = C.cascade(lv, "bids", 1_000_000.0, [], 100.0)
    assert r["exhausted"] is True, r
    assert r["final_price"] is None and r["moved_pct"] is None, r
    return "no extrapolation past the recorded book"


@check
def no_clusters_means_one_round(tmp=None):
    lv = flat_bids()
    r = C.cascade(lv, "bids", 5000.0, [], 100.0)     # ~5 levels deep
    assert r["rounds"] == 1 and r["clusters_triggered"] == 0, r
    assert r["moved_pct"] > 0, r
    return f"single sweep, moved {r['moved_pct']:.3f}%"


@check
def a_cluster_inside_the_sweep_is_triggered(tmp=None):
    lv = flat_bids()
    # ~$3,950 reaches level 97, so a cluster triggering at 97.5 is inside the first sweep
    r = C.cascade(lv, "bids", 5000.0, [(97.5, 400.0)], 100.0)
    assert r["clusters_triggered"] == 1, r
    assert r["total_notional"] == 5400.0, r
    return "cluster added to the swept notional"


@check
def a_cluster_outside_the_sweep_is_not_triggered(tmp=None):
    lv = flat_bids()
    r = C.cascade(lv, "bids", 2000.0, [(50.0, 999.0)], 100.0)
    assert r["clusters_triggered"] == 0, r
    assert r["total_notional"] == 2000.0, r
    return "a cluster far below is left alone"


@check
def a_cluster_is_never_counted_twice(tmp=None):
    lv = flat_bids(n=40)
    r = C.cascade(lv, "bids", 5000.0, [(97.5, 300.0), (95.5, 300.0)], 100.0)
    assert r["clusters_triggered"] <= 2, r
    assert r["total_notional"] <= 5000.0 + 600.0 + 1e-9, r
    return "triggered set prevents double counting across rounds"


@check
def the_iteration_terminates(tmp=None):
    lv = flat_bids(n=60)
    # a dense ladder of clusters all the way down -- must stop, not spin
    cl = [(100.0 - i, 50.0) for i in range(1, 50)]
    r = C.cascade(lv, "bids", 8000.0, cl, 100.0)
    assert r["rounds"] <= C.MAX_ROUNDS, r
    assert r["rounds"] > 1, "a dense cluster ladder must actually iterate"
    return f"converged in {r['rounds']} rounds"


@check
def forced_buying_moves_price_up(tmp=None):
    asks = {100.0 + i: 10.0 for i in range(20)}
    r = C.cascade(asks, "asks", 5000.0, [], 100.0)
    assert r["moved_pct"] > 0, r
    assert r["final_price"] > 100.0, r
    return "asks side moves up, sign is not inverted"


@check
def bracket_orders_pessimistic_further_than_optimistic(tmp=None):
    # A FINE ladder. With $1 steps both sweeps land on the same level and the bracket collapses
    # -- true of the model and useless as a test. Real books are finely priced; the fixture
    # should be too.
    lv = flat_bids(top=100.0, step=0.01, size=1.0, n=400)
    b = C.bracket(lv, "bids", 2000.0, [(99.90, 500.0)], 100.0,
                  evaporation_optimistic=1.0, evaporation_pessimistic=0.72)
    o, p = b["optimistic"]["moved_pct"], b["pessimistic"]["moved_pct"]
    assert p > o, (o, p)
    assert b["ambiguity_pct"] > 0
    return f"optimistic {o:.3f}% vs pessimistic {p:.3f}%, ambiguity {b['ambiguity_pct']:.3f}pp"


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
          f"cascade checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
