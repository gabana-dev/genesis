"""
LIQ-2 map arithmetic, checked against hand-built snapshots.

Two errors in this module would be invisible on real data. The first is the forced direction:
a short liquidates by BUYING and a long by SELLING, and inverting that flips the entire map
while leaving every number plausible. The second is coverage, which is the exact defect that
killed LIQ-1 -- a scan set holding 5.8% of open interest produced a map that looked complete.

Run: .venv/bin/python tests/test_liqmap.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import liqmap as L  # noqa: E402

_checks = []
SPOT = 100_000.0


def check(fn):
    _checks.append(fn)
    return fn


def pos(szi, lpx, withdrawable="0", maint="1000", wallet="0xa"):
    """One position as `scan` would emit it."""
    return {"wallet": wallet, "szi": szi, "liquidationPx": lpx,
            "forced_side": "buy" if szi < 0 else "sell",
            "forced_notional": abs(szi) * lpx,
            "withdrawable": withdrawable, "maint_margin": maint}


def snap(positions, oi=1_000_000.0, tier="deep"):
    return {"t": 0, "spot": SPOT, "oi_usd": oi, "tier": tier, "scanned": len(positions),
            "with_position": len(positions), "positions": positions, "throttled": 0}


@check
def shorts_are_forced_buyers_above_spot():
    r = L.bucketise2(snap([pos(-1.0, 102_000.0)]))
    assert r["forced_buy_5pct"] == 102_000.0, r["forced_buy_5pct"]
    assert r["forced_sell_5pct"] == 0.0, r["forced_sell_5pct"]
    return "short liquidating at +2% is a forced buy"


@check
def longs_are_forced_sellers_below_spot():
    r = L.bucketise2(snap([pos(1.0, 98_000.0)]))
    assert r["forced_sell_5pct"] == 98_000.0, r["forced_sell_5pct"]
    assert r["forced_buy_5pct"] == 0.0, r["forced_buy_5pct"]
    return "long liquidating at -2% is a forced sell"


@check
def imbalance_sign_follows_buy_pressure():
    r = L.bucketise2(snap([pos(-1.0, 102_000.0), pos(1.0, 98_000.0, wallet="0xb")]))
    # 102,000 forced buy against 98,000 forced sell
    assert r["imbalance"] > 0, r["imbalance"]
    assert abs(r["imbalance"] - (102_000 - 98_000) / 200_000) < 1e-12, r["imbalance"]
    return f"imbalance {r['imbalance']:.4f}"


@check
def imbalance_is_none_when_nothing_is_in_range():
    r = L.bucketise2(snap([pos(1.0, 80_000.0)]))
    assert r["imbalance"] is None, r["imbalance"]
    assert r["forced_sell_10pct"] == 0.0, r["forced_sell_10pct"]
    return "-20% is outside the +/-10% map entirely"


@check
def range_boundary_excludes_beyond_ten_percent():
    inside = L.bucketise2(snap([pos(1.0, 90_500.0)]))["forced_sell_10pct"]
    outside = L.bucketise2(snap([pos(1.0, 89_000.0)]))["forced_sell_10pct"]
    assert inside == 90_500.0, inside
    assert outside == 0.0, outside
    return "-9.5% in, -11% out"


@check
def coverage_is_scanned_notional_over_open_interest():
    r = L.bucketise2(snap([pos(1.0, 98_000.0)], oi=980_000.0))
    assert abs(r["coverage"] - 0.10) < 1e-12, r["coverage"]
    return f"coverage {r['coverage']:.2%}"


@check
def coverage_counts_positions_outside_the_map():
    # A position 20% away is not in any bucket but its notional is still open interest we hold.
    r = L.bucketise2(snap([pos(1.0, 80_000.0)], oi=800_000.0))
    assert r["forced_sell_10pct"] == 0.0
    assert abs(r["coverage"] - 0.10) < 1e-12, r["coverage"]
    return "coverage measures the scan set, not the map"


@check
def credible_weight_is_full_without_free_collateral():
    p = pos(1.0, 98_000.0, withdrawable="0", maint="5000")
    assert L.credible_notional(p) == p["forced_notional"]
    return "no escape capacity, full weight"


@check
def credible_weight_falls_with_free_collateral():
    p = pos(1.0, 98_000.0, withdrawable="45000", maint="5000")  # 9x buffer -> 1/10
    assert abs(L.credible_notional(p) - 9800.0) < 1e-9, L.credible_notional(p)
    return "9x maintenance buffer discounts to a tenth"


@check
def credible_weight_falls_back_to_raw_on_missing_fields():
    for bad in ({"forced_notional": 1.0, "withdrawable": None, "maint_margin": None},
                {"forced_notional": 1.0, "withdrawable": "x", "maint_margin": "5"},
                {"forced_notional": 1.0, "withdrawable": "5", "maint_margin": "0"}):
        assert L.credible_notional(bad) == 1.0, bad
    return "unparseable collateral never silently zeroes a position"


@check
def credible_map_never_exceeds_raw_map():
    ps = [pos(-1.0, 102_000.0, withdrawable="20000", maint="4000"),
          pos(1.0, 98_000.0, withdrawable="0", maint="4000", wallet="0xb")]
    r = L.bucketise2(snap(ps))
    assert r["credible_buy_5pct"] < r["forced_buy_5pct"]
    assert r["credible_sell_5pct"] == r["forced_sell_5pct"]
    return "weighting only ever discounts"


@check
def ranking_is_by_notional_and_deduplicates_wallets():
    ps = [pos(0.1, 100_000.0, wallet="0xsmall"),
          pos(5.0, 100_000.0, wallet="0xbig"),
          pos(1.0, 100_000.0, wallet="0xbig"),
          pos(-2.0, 100_000.0, wallet="0xshort")]
    assert L.rank_by_notional(ps, n=3) == ["0xbig", "0xshort", "0xsmall"]
    return "shorts rank by absolute size; one entry per wallet"


@check
def ranking_respects_the_cap():
    ps = [pos(float(i + 1), 100_000.0, wallet=f"0x{i}") for i in range(10)]
    assert len(L.rank_by_notional(ps, n=3)) == 3
    return "top-N cap holds"


@check
def largest_bucket_share_is_a_fraction_of_its_own_side():
    ps = [pos(9.0, 98_000.0), pos(1.0, 95_000.0, wallet="0xb")]
    r = L.bucketise2(snap(ps))
    assert abs(r["largest_bucket_share_sell"] - (9 * 98_000) / (9 * 98_000 + 95_000)) < 1e-12
    assert r["largest_bucket_share_buy"] is None
    return f"{r['largest_bucket_share_sell']:.3f} of the sell side"


@check
def nearest_dense_ignores_buckets_under_the_threshold():
    # Both shorts: liquidation above spot is a forced buy. A long liquidating above spot is
    # not a thing, and constructing one puts notional in a bucket the dense search never reads.
    ps = [pos(-0.001, 101_000.0),                       # $101, far under $1M
          pos(-50.0, 104_000.0, wallet="0xb")]          # $5.2M
    r = L.bucketise2(snap(ps))
    assert abs(r["nearest_dense_above"] - 0.04) < 1e-12, r["nearest_dense_above"]
    assert r["nearest_dense_below"] is None
    return "nearest dense cluster is +4%, not +1%"


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
          f"LIQ-2 map checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
