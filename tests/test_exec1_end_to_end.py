"""
EXEC-1 end to end: the declared grid driven through the real simulator, on a synthetic
recording whose answer is known by construction.

WHY THIS EXISTS SEPARATELY FROM test_exec1.py
    That suite checks the grid and the groupings with hand-made Order objects. It never calls
    fills.simulate, so it cannot catch the joins between them -- and those joins are where the
    contract's own parameters live. Two of them are exercised by NO other test in the
    repository: the 300 s markout horizon and 500 ms book sampling. A missing 300 000 ms key
    would not raise; it would quietly drop X1's longest horizon and leave every other number
    looking healthy.

    This is the last chance to find that before 2026-08-17, on data that only exists once.

Run: .venv/bin/python tests/test_exec1_end_to_end.py
"""

import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import dialects  # noqa: E402
import exec1 as E  # noqa: E402
import fills as F  # noqa: E402
from log import EventLog  # noqa: E402
from stream import Ingestor  # noqa: E402

SYM = "BTCUSDT"
T0 = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)
_checks = []
_n = [0]


def check(fn):
    _checks.append(fn)
    return fn


def at(ms_off):
    return (T0 + timedelta(milliseconds=ms_off)).isoformat()


def ms_of(off):
    return (T0 + timedelta(milliseconds=off)).timestamp() * 1000.0


def build(tmp, frames):
    """Same construction as tests/test_fills.py: frames are FULL book states, diffed here."""
    _n[0] += 1
    path = os.path.join(tmp, f"e2e{_n[0]}.jsonl")

    def diff(prev, cur):
        out = [[p, s] for p, s in cur]
        have = {float(p) for p, _ in cur}
        out += [[p, "0"] for p, _ in prev if float(p) not in have]
        return out

    with EventLog(path) as log:
        i = Ingestor(log, dialect=dialects.BINANCE)
        i.connection_opened("c1", "wss://x")
        off0, b0, a0 = frames[0]
        i.observe({"lastUpdateId": 1, "bids": b0, "asks": a0},
                  request={"symbol": SYM, "role": "anchor"}, received_at=at(off0))
        u, pb, pa = 2, b0, a0
        for off, b, a in frames[1:]:
            i.observe({"e": "depthUpdate", "E": 1, "s": SYM, "U": u, "u": u,
                       "b": diff(pb, b), "a": diff(pa, a)}, received_at=at(off))
            pb, pa = b, a
            u += 1
    return path


def flat_book(px=100.0, size="50"):
    bids = [[f"{px - 0.01 * k:.2f}", size] for k in range(6)]
    asks = [[f"{px + 0.01 * (k + 1):.2f}", size] for k in range(6)]
    return bids, asks


def steady(minutes, step_ms=500, px=100.0):
    """A book that does nothing, sampled every 500 ms for `minutes`."""
    b, a = flat_book(px)
    return [(t, b, a) for t in range(0, int(minutes * 60_000) + 1, step_ms)]


@check
def the_grid_runs_end_to_end_and_resolves_every_order(tmp):
    """
    Nothing may be left "pending". An unresolved order that keeps its initial state would
    vanish from every count without appearing in any failure total.
    """
    path = build(tmp, steady(12))
    start = ms_of(0)
    orders, rep = E.run_arm(path, SYM, start, start + 5 * 60_000,
                            latency_ms=E.LATENCY_ARMS_MS[0])
    assert len(orders) == 5 * 6, len(orders)
    assert all(o.outcome != "pending" for o in orders), "an order was left pending"
    assert rep["pooled"]["n_orders"] == 30
    return "5 decision times x 6 cells resolved through the real simulator, none left pending"


def falling_book(tmp, drop_at_ms=30_000, to_px=99.90, minutes=14):
    """
    A book that sits still, then steps DOWN once. The step takes the ask below a resting bid,
    which is a price trading through -- the one unambiguous fill in a recording with no trade
    stream. Everything after the step is flat, so the markout at every horizon past the step is
    exactly the size of the step.
    """
    b1, a1 = flat_book(100.0)
    b2, a2 = flat_book(to_px)
    frames = [(t, b1, a1) for t in range(0, drop_at_ms + 1, 500)]
    frames += [(t, b2, a2) for t in range(drop_at_ms + 500, int(minutes * 60_000) + 1, 500)]
    return build(tmp, frames)


@check
def a_steady_book_produces_no_fills_at_all(tmp):
    """
    The null case, and a stronger statement than "markout is zero": with no trade stream, a
    fill is inferred from the queue ahead being consumed. A book whose sizes never change has
    consumed nothing, so claiming ANY fill would mean the simulator was inventing them.

    Asserted as an emptiness, not guarded by `if fills:` -- a guarded assertion passes
    vacuously on zero fills, which is precisely the failure it is supposed to catch.
    """
    path = build(tmp, steady(12))
    start = ms_of(0)
    orders = E.build_orders(start, start + 60_000)
    F.simulate(path, SYM, orders, latency_ms=E.LATENCY_ARMS_MS[0],
               markout_ms=E.MARKOUT_MS, every_ms=E.BOOK_SAMPLE_MS)
    filled = [o for o in orders if o.outcome in ("certain", "optimistic_only")]
    assert not filled, f"a motionless book invented {len(filled)} fills"
    assert E.markout_series(orders, 60_000, "certain_plus_optimistic") == []
    return "a book that never trades produces no fills and no markouts -- none are invented"


@check
def the_three_hundred_second_horizon_actually_produces_a_number(tmp):
    """
    The horizon X1 turns on, and the one no other test in the repository touches. A silently
    missing 300 000 ms key would drop X1's longest horizon and leave every other number
    looking perfectly healthy.
    """
    path = falling_book(tmp)
    start = ms_of(0)
    orders = E.build_orders(start, start + 1000)       # one decision time, six cells
    F.simulate(path, SYM, orders, latency_ms=E.LATENCY_ARMS_MS[0],
               markout_ms=E.MARKOUT_MS, every_ms=E.BOOK_SAMPLE_MS)
    filled = [o for o in orders if o.outcome in ("certain", "optimistic_only")]
    assert filled, "fixture produced no fills -- the test would pass vacuously"
    for h in E.MARKOUT_MS:
        n = sum(1 for o in filled if f"{h}ms" in o.markouts)
        assert n, f"no fill carries the {h}ms markout"
    return f"all four declared horizons present on {len(filled)} fills, including 300 s"


@check
def a_falling_book_costs_a_resting_bid_its_advantage(tmp):
    """
    Known answer by construction: the mid steps down 10 bps and stays there, so a filled BUY
    reads -10 bps at every horizon past the step. Against a 3 bps advantage that is 3.33x
    lost -- comfortably past the §6 kill threshold.
    """
    path = falling_book(tmp)
    start = ms_of(0)
    orders = E.build_orders(start, start + 1000)
    F.simulate(path, SYM, orders, latency_ms=E.LATENCY_ARMS_MS[0],
               markout_ms=E.MARKOUT_MS, every_ms=E.BOOK_SAMPLE_MS)
    buys = [o for o in orders if o.side == "buy" and "60000ms" in o.markouts]
    assert buys, "no filled buy orders -- the test would pass vacuously"
    worst = min(o.markouts["60000ms"] for o in buys)
    assert worst < -0.0009, f"a 10 bps fall should read near -10 bps, got {worst}"
    lost = E.advantage_lost(buys, horizon_ms=60_000, pool="certain_plus_optimistic")
    assert lost is not None and lost > 1.0, lost
    return f"a 10 bps fall reads {worst * 1e4:.1f} bps adverse; {lost:.2f}x the advantage lost"


@check
def a_rising_book_is_not_read_as_adverse_for_a_bid(tmp):
    """
    Sign discipline. If the sign convention were inverted anywhere in this path, the falling
    -book test above would still pass and E3 would report the exact opposite of the truth --
    a market that pays makers would look like one that punishes them.
    """
    path = falling_book(tmp, to_px=100.10)         # steps UP instead
    start = ms_of(0)
    orders = E.build_orders(start, start + 1000)
    F.simulate(path, SYM, orders, latency_ms=E.LATENCY_ARMS_MS[0],
               markout_ms=E.MARKOUT_MS, every_ms=E.BOOK_SAMPLE_MS)
    sells = [o for o in orders if o.side == "sell" and "60000ms" in o.markouts]
    assert sells, "no filled sell orders -- the test would pass vacuously"
    worst = min(o.markouts["60000ms"] for o in sells)
    assert worst < -0.0009, f"a resting ask filled before a 10 bps rise is adverse, got {worst}"
    return f"the mirrored case is adverse for the ask, at {worst * 1e4:.1f} bps"


@check
def the_two_latency_arms_are_independent_populations(tmp):
    """
    E5 compares two complete passes. If one arm's state leaked into the other, the comparison
    would be against a mixture and the difference would be diluted toward zero.
    """
    path = build(tmp, steady(12))
    start = ms_of(0)
    fast, _ = E.run_arm(path, SYM, start, start + 3 * 60_000, latency_ms=291.0)
    slow, _ = E.run_arm(path, SYM, start, start + 3 * 60_000, latency_ms=650.0)
    assert len(fast) == len(slow) == 18
    assert fast[0] is not slow[0], "the two arms share Order objects"
    for a, b in zip(fast, slow):
        assert a.arrives_at_ms is None or b.arrives_at_ms is None or \
            b.arrives_at_ms >= a.arrives_at_ms, "the slow arm arrived earlier than the fast arm"
    return "each latency arm is a separate order population; the slow arm never arrives first"


@check
def a_recording_that_ends_early_marks_orders_unresolved_not_filled(tmp):
    """
    The recording has a last frame. An order still live at that point must say so -- counting
    it as expired (or worse, as filled) would let the end of the file look like an outcome.
    """
    path = build(tmp, steady(2))                   # only 2 minutes of book
    start = ms_of(0)
    orders, _ = E.run_arm(path, SYM, start, start + 2 * 60_000,
                          latency_ms=E.LATENCY_ARMS_MS[0])
    kinds = {o.outcome for o in orders}
    assert "pending" not in kinds
    assert any("unresolved" in k or k in ("expired", "certain", "optimistic_only",
                                          "never_reached", "never_posted") for k in kinds), kinds
    return f"orders past the end of the recording are labelled honestly: {sorted(kinds)}"


if __name__ == "__main__":
    tmp = tempfile.mkdtemp(prefix="exec1-e2e-")
    failures = 0
    try:
        for fn in _checks:
            try:
                note = fn(tmp)
                print(f"  ok  {fn.__name__}  --  {note}")
            except AssertionError as e:
                failures += 1
                print(f"  FAIL  {fn.__name__}  --  {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = len(_checks)
    print(f"{'PASS' if not failures else 'FAIL'} -- {total - failures}/{total} EXEC-1 end-to-end checks")
    sys.exit(1 if failures else 0)
