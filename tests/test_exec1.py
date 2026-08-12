"""
The EXEC-1 grid and aggregations (market/exec1.py).

Every answer here is known by construction. That is the point: on the real recording nothing
tells you a grouping dropped a third of its orders or that a horizon key silently missed, and
the numbers look reasonable either way. RDB-1's variance-ratio statistic carried a stray factor
of n and read VR 0.38 at p = 0.86 on real data for a week; a synthetic series with a known
answer caught it immediately.

Run: .venv/bin/python tests/test_exec1.py
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import exec1 as E  # noqa: E402
import fills as F  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def ms(y, mo, d, h=0, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=timezone.utc).timestamp() * 1000.0


def order(side="buy", off=0, at=0.0, outcome="certain", markouts=None):
    o = F.Order(order_id=f"{side}@{off}t|{int(at)}", side=side, size_usd=E.SIZE_USD,
                decided_at_ms=at, offset_ticks=off, tick=E.TICK, ttl_ms=E.TTL_MS)
    o.outcome = outcome
    o.markouts = markouts or {}
    return o


# ── The grid is what the contract says it is ────────────────────────────────────────────

@check
def the_grid_matches_the_frozen_contract():
    assert E.SIDES == ("buy", "sell")
    assert E.OFFSET_TICKS == (0, 1, 5)
    assert E.SIZE_USD == 10_000.0
    assert E.DECISION_EVERY_MS == 60_000.0
    assert E.TTL_MS == 300_000.0
    assert E.LATENCY_ARMS_MS == (291.0, 650.0)
    assert E.MARKOUT_MS == (1_000, 10_000, 60_000, 300_000)
    assert E.BOOK_SAMPLE_MS == 500
    return "every grid parameter matches CONTRACT-execution.md §4"


@check
def there_are_exactly_six_cells():
    ks = [c.key for c in E.cells()]
    assert len(ks) == 6 and len(set(ks)) == 6, ks
    assert ks == ["buy@0t", "buy@1t", "buy@5t", "sell@0t", "sell@1t", "sell@5t"], ks
    return "six cells per decision time, in a fixed order"


@check
def decision_times_are_a_fixed_cadence_not_a_choice():
    t0 = ms(2026, 8, 10, 12, 0)
    ts = E.decision_times(t0, t0 + 5 * 60_000)
    assert len(ts) == 5, len(ts)
    assert all(b - a == 60_000 for a, b in zip(ts, ts[1:]))
    return "one decision every 60s, evenly spaced"


@check
def the_end_of_the_window_is_excluded():
    # An order decided at the last instant could never resolve; including it would put an
    # unresolved order in all six cells for nothing.
    t0 = ms(2026, 8, 10, 12, 0)
    assert E.decision_times(t0, t0) == []
    assert E.decision_times(t0, t0 + 60_000) == [t0]
    return "half-open window: an order that could never resolve is never created"


@check
def the_order_set_is_six_per_decision_time():
    t0 = ms(2026, 8, 10, 12, 0)
    os_ = E.build_orders(t0, t0 + 10 * 60_000)
    assert len(os_) == 60, len(os_)
    assert len({o.order_id for o in os_}) == 60, "order ids must be unique"
    assert all(o.ttl_ms == E.TTL_MS and o.size_usd == E.SIZE_USD for o in os_)
    assert {o.offset_ticks for o in os_} == {0, 1, 5}
    return "10 decision times x 6 cells = 60 orders, uniquely identified"


# ── Groupings partition; they never drop or duplicate ───────────────────────────────────

@check
def every_grouping_is_a_partition():
    # The failure this guards against is silent: a grouping that drops orders produces a
    # smaller, cleaner-looking sample and says nothing about it.
    t0 = ms(2026, 8, 10, 0, 0)
    os_ = E.build_orders(t0, t0 + 60 * 60_000)          # 24h of nothing but decisions
    n = len(os_)
    for name, g in (("cell", E.group_by_cell(os_)), ("offset", E.group_by_offset(os_)),
                    ("day", E.group_by_day(os_)), ("session", E.group_by_session(os_))):
        total = sum(len(v) for v in g.values())
        assert total == n, f"{name}: {total} != {n}"
        seen = [o.order_id for v in g.values() for o in v]
        assert len(set(seen)) == n, f"{name}: duplicated orders"
    return "cell, offset, day and session groupings each partition the set exactly"


@check
def days_are_split_on_the_decision_time():
    # Keyed on the fill time instead, an order decided at 23:59 and filled at 00:01 would land
    # in a day whose conditions had nothing to do with it.
    a = order(at=ms(2026, 8, 10, 23, 59))
    b = order(at=ms(2026, 8, 11, 0, 1))
    g = E.group_by_day([a, b])
    assert list(g) == ["2026-08-10", "2026-08-11"], list(g)
    return "an order belongs to the day it was decided in"


@check
def the_x5_windows_are_the_declared_ones():
    quiet = order(at=ms(2026, 8, 11, 4, 0))
    us = order(at=ms(2026, 8, 11, 15, 0))
    neither = order(at=ms(2026, 8, 11, 9, 0))
    g = E.group_by_session([quiet, us, neither])
    assert len(g["quiet"]) == 1 and len(g["us_session"]) == 1 and len(g["other"]) == 1
    return "03:00-06:00 UTC vs US session, with the remainder kept separate not folded in"


@check
def hours_outside_both_windows_are_never_compared():
    # X5 names two windows. Folding 09:00 UTC into either would answer a different question.
    assert 9 not in E.QUIET_HOURS_UTC and 9 not in E.US_SESSION_UTC
    assert set(E.QUIET_HOURS_UTC).isdisjoint(E.US_SESSION_UTC)
    return "the two X5 windows are disjoint and do not cover the day"


# ── E3 arithmetic ───────────────────────────────────────────────────────────────────────

@check
def e3_reports_the_fraction_of_the_advantage_lost():
    # 1.5 bps of adverse move against a 3 bps advantage is exactly half.
    os_ = [order(markouts={"60000ms": -0.00015}) for _ in range(5)]
    got = E.advantage_lost(os_, horizon_ms=60_000)
    assert abs(got - 0.5) < 1e-9, got
    return "1.5 bps lost against a 3 bps advantage reads as 0.50"


@check
def the_kill_condition_is_a_number_not_a_judgement():
    # §6: above 1.0, resting is worse than crossing after costs.
    os_ = [order(markouts={"60000ms": -0.00040}) for _ in range(5)]
    got = E.advantage_lost(os_, horizon_ms=60_000)
    assert got > 1.0, got
    return "4 bps against 3 bps crosses the kill threshold at 1.33"


@check
def a_favourable_markout_does_not_read_as_a_loss():
    os_ = [order(markouts={"60000ms": +0.00015}) for _ in range(5)]
    got = E.advantage_lost(os_, horizon_ms=60_000)
    assert got < 0, got
    return "a positive markout gives a negative fraction lost -- the advantage grew"


@check
def the_two_fill_pools_are_reported_separately():
    # The bracket exists because there is no trade stream. Collapsing it would hide exactly
    # what the missing data costs.
    certain = [order(outcome="certain", markouts={"60000ms": -0.00015}) for _ in range(4)]
    optimistic = [order(outcome="optimistic_only", markouts={"60000ms": -0.00060}) for _ in range(4)]
    lo = E.advantage_lost(certain + optimistic, pool="certain")
    hi = E.advantage_lost(certain + optimistic, pool="certain_plus_optimistic")
    assert abs(lo - 0.5) < 1e-9, lo
    assert hi > lo, (lo, hi)
    return "certain and certain+optimistic give different answers, and both are available"


@check
def markout_series_respects_the_pool():
    certain = [order(outcome="certain", markouts={"60000ms": -0.0001}) for _ in range(3)]
    optimistic = [order(outcome="optimistic_only", markouts={"60000ms": -0.0009}) for _ in range(2)]
    both = certain + optimistic
    assert len(E.markout_series(both, 60_000, "certain")) == 3
    assert len(E.markout_series(both, 60_000, "certain_plus_optimistic")) == 5
    return "the raw series for bootstrapping matches the pool it claims to describe"


@check
def a_missing_horizon_is_absent_not_zero():
    # A zero here would read as "no adverse selection", which is the most dangerous possible
    # way for a missing measurement to fail.
    os_ = [order(markouts={"1000ms": -0.0002}) for _ in range(3)]
    assert E.markout_series(os_, 300_000) == []
    assert E.advantage_lost(os_, horizon_ms=300_000) is None
    return "an unmeasured horizon returns None/empty, never a comforting zero"


@check
def unfilled_orders_never_enter_a_markout():
    os_ = ([order(outcome="never_reached") for _ in range(5)] +
           [order(outcome="expired") for _ in range(5)] +
           [order(outcome="certain", markouts={"60000ms": -0.0003}) for _ in range(2)])
    assert len(E.markout_series(os_, 60_000)) == 2
    return "reach and fill are separate facts; only fills carry a markout"


# ── The report is facts, not verdicts ───────────────────────────────────────────────────

@check
def the_report_carries_every_declared_breakdown():
    t0 = ms(2026, 8, 10, 12, 0)
    os_ = E.build_orders(t0, t0 + 10 * 60_000)
    for o in os_:
        o.outcome = "certain"
        o.markouts = {f"{h}ms": -0.00015 for h in E.MARKOUT_MS}
        o.reached = True
    r = E.report(os_)
    for k in ("grid", "pooled", "by_cell", "by_offset", "by_day", "by_session"):
        assert k in r, k
    assert set(r["by_cell"]) == {c.key for c in E.cells()}
    assert r["grid"]["contract"].endswith("CONTRACT-execution.md")
    return "pooled, per-cell, per-offset, per-day and per-session all present"


@check
def the_report_states_no_verdict_on_any_prediction():
    # X1-X7 are adjudicated deliberately, in the ledger, as counted trials. A report that
    # printed "X2 holds" would make every reading of it an untracked test.
    t0 = ms(2026, 8, 10, 12, 0)
    os_ = E.build_orders(t0, t0 + 2 * 60_000)
    for o in os_:
        o.outcome = "certain"
        o.markouts = {f"{h}ms": -0.00015 for h in E.MARKOUT_MS}
    text = repr(E.report(os_)).lower()
    for banned in ("falsified", "confirmed", "holds", "p_value", "significant", "reject"):
        assert banned not in text, f"report leaked a verdict: {banned}"
    return "the report contains measurements only -- no prediction is adjudicated by printing it"


@check
def no_selection_logic_exists_in_the_grid():
    src = open(os.path.join(os.path.dirname(__file__), "..", "market", "exec1.py")).read().lower()
    # "optimi" was too loose: it matches optimistic_only, which is a FILL OUTCOME, not
    # optimisation. A guard that fires on correct code gets deleted, and then it guards nothing.
    for banned in ("if signal", "predict(", "best_offset", "optimise", "optimize",
                   "pnl", "profit", "sharpe"):
        assert banned not in src, f"exec1.py contains selection logic: {banned}"
    return "no signal, sizing, optimisation or P&L entered the grid"


if __name__ == "__main__":
    failures = 0
    for fn in _checks:
        try:
            note = fn()
            print(f"  ok  {fn.__name__}  --  {note}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL  {fn.__name__}  --  {e}")
    total = len(_checks)
    print(f"{'PASS' if not failures else 'FAIL'} -- {total - failures}/{total} EXEC-1 grid checks")
    sys.exit(1 if failures else 0)
