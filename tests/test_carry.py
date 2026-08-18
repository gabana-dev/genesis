"""
CARRY-1 arithmetic, checked against synthetic series with hand-computed answers.

Written because RDB-1 lost a week to a variance-ratio statistic carrying a stray factor of n:
on real data it looked plausible and nothing about the number said it was wrong. These checks
exist so a sign error in the basis term cannot survive contact with real prices, where every
value is plausible.

Run: .venv/bin/python tests/test_carry.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import carry1 as K  # noqa: E402

_checks = []
BPS = 1e-4
H8 = 8 * 3600 * 1000


def check(fn):
    _checks.append(fn)
    return fn


def series(n, rate, basis, spot=100_000.0):
    """n settlements. `rate` and `basis` may be scalars or per-index callables."""
    rows = []
    for i in range(n):
        r = rate(i) if callable(rate) else rate
        b = basis(i) if callable(basis) else basis
        s = spot(i) if callable(spot) else spot
        rows.append({"t": i * H8, "rate": r, "perp": s * (1 + b), "spot": s, "basis": b})
    return rows


@check
def funding_accrues_over_held_intervals_only():
    """
    Entry is decided on the rate at t and taken after it, so the position receives t+1..t+H.
    Collecting the entry settlement would pay for a position not yet held.
    """
    rows = series(60, 0.0001, 0.0)            # 1 bp per interval, flat basis
    trips, _ = K.round_trips(rows, hold_days=1, threshold=0.0, maker_perp=0.0, fee_spot=0.0)
    assert trips, "no round trips"
    # 1 day = 3 settlements held, at 1 bp each.
    assert abs(trips[0]["funding"] - 0.0003) < 1e-15, trips[0]["funding"]
    return "1 day at 1 bp/interval accrues exactly 3 bps, entry settlement excluded"


@check
def flat_basis_means_net_is_funding_minus_fees():
    """The clean case with a hand-computed answer: nothing to earn or lose on the basis."""
    rows = series(60, 0.0001, 0.0)
    trips, _ = K.round_trips(rows, 1, 0.0, maker_perp=0.0002, fee_spot=0.0010)
    t = trips[0]
    assert abs(t["basis_pnl"]) < 1e-15, t["basis_pnl"]
    assert abs(t["fees"] - 0.0024) < 1e-15, t["fees"]          # 2x10 + 2x2 bps
    assert abs(t["net"] - (0.0003 - 0.0024)) < 1e-15, t["net"]
    return "3 bps funding - 24 bps fees = -21 bps, exactly"


@check
def narrowing_basis_pays_a_short_perp():
    """
    THE SIGN CHECK. Short perp + long spot profits when the premium converges. If this is
    backwards every result inverts and every number still looks plausible.
    """
    rows = series(60, 0.0, lambda i: 0.002 if i < 3 else 0.0)   # 20 bps premium -> 0
    trips, _ = K.round_trips(rows, 1, 0.0, 0.0, 0.0)
    assert not trips, "threshold 0 must still require rate > 0"
    rows = series(60, 0.0001, lambda i: 0.002 if i < 3 else 0.0)
    trips, _ = K.round_trips(rows, 1, 0.0, 0.0, 0.0)
    t = trips[0]
    assert t["basis_pnl"] > 0, f"narrowing basis must PAY a short perp, got {t['basis_pnl']}"
    # (S_x/S_e)(b_e - b_x)/(1+b_e) with flat spot = 0.002/1.002
    assert abs(t["basis_pnl"] - 0.002 / 1.002) < 1e-12, t["basis_pnl"]
    return "20 bps premium converging pays +19.96 bps, matching the closed form"


@check
def widening_basis_costs_a_short_perp():
    rows = series(60, 0.0001, lambda i: 0.0 if i < 3 else 0.002)
    t = K.round_trips(rows, 1, 0.0, 0.0, 0.0)[0][0]
    assert t["basis_pnl"] < 0, t["basis_pnl"]
    assert abs(t["basis_pnl"] + 0.002) < 1e-12, t["basis_pnl"]
    return "the mirror case costs -20 bps, and the two are not symmetric by accident"


@check
def negative_funding_is_never_entered():
    """Contract section 5: the mirror needs a spot borrow Genesis does not have."""
    rows = series(60, -0.0001, 0.0)
    assert K.round_trips(rows, 1, 0.0, 0.0, 0.0)[0] == []
    mixed = series(60, lambda i: 0.0001 if i % 2 == 0 else -0.0001, 0.0)
    trips, _ = K.round_trips(mixed, 1, 0.0, 0.0, 0.0)
    assert trips and all(t["funding"] != 0 or True for t in trips)
    entered = {t["entry_t"] // H8 for t in trips}
    assert all(i % 2 == 0 for i in entered), "entered on a negative-funding settlement"
    return "no position is ever opened on negative funding"


@check
def threshold_filters_entries():
    rows = series(60, lambda i: 0.00005 if i % 2 else 0.0003, 0.0)
    loose, _ = K.round_trips(rows, 1, 0.0, 0.0, 0.0)
    tight, _ = K.round_trips(rows, 1, 0.0002, 0.0, 0.0)
    assert len(tight) < len(loose), (len(tight), len(loose))
    assert all(r["rate"] >= 0.0002 for r in rows
               for t in tight if t["entry_t"] == r["t"])
    return f"threshold >=2bp admits {len(tight)} of {len(loose)} entries"


@check
def longer_holds_accrue_proportionally_more_funding():
    """Y2's mechanism: fees are paid once per round trip, funding accrues per interval."""
    rows = series(200, 0.0001, 0.0)
    got = {h: K.round_trips(rows, h, 0.0, 0.0002, 0.0010)[0][0] for h in (1, 3, 7, 14)}
    assert all(abs(got[h]["funding"] - 0.0001 * 3 * h) < 1e-15 for h in got)
    assert all(abs(got[h]["fees"] - 0.0024) < 1e-15 for h in got)
    nets = [got[h]["net"] for h in (1, 3, 7, 14)]
    assert nets == sorted(nets), nets
    return "14d accrues 42 bps against the same 24 bps of fees; net is monotone in hold"


@check
def missing_legs_are_excluded_not_interpolated():
    """K5. A P&L computed from an invented price is a fabricated observation."""
    funding = [(0, 0.0001), (H8, 0.0001), (2 * H8, 0.0001)]
    perp = {0: 100_100.0, 2 * H8: 100_100.0}          # H8 absent
    spot = {0: 100_000.0, H8: 100_000.0, 2 * H8: 100_000.0}
    rows, missing = K.align(funding, perp, spot)
    assert missing == 1, missing
    assert [r["t"] for r in rows] == [0, 2 * H8]
    return "a settlement missing one leg is dropped and counted, never filled in"


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
          f"CARRY-1 arithmetic checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
