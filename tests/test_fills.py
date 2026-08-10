"""
The fill simulator (market/fills.py).

Built against synthetic books with hand-constructed answers, because a simulator validated
only on real data is validated against nothing -- there is no ground truth in the recording to
check it with.

Run: .venv/bin/python tests/test_fills.py
"""

import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import dialects  # noqa: E402
import fills as F  # noqa: E402
from log import EventLog  # noqa: E402
from stream import Ingestor  # noqa: E402

SYM = "BTCUSDT"
T0 = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)
_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def at(ms):
    return (T0 + timedelta(milliseconds=ms)).isoformat()


def ms_of(offset):
    return (T0 + timedelta(milliseconds=offset)).timestamp() * 1000.0


_n = [0]


def build(tmp, frames, name=None):
    """
    frames: list of (offset_ms, bids, asks) given as FULL book states, which is how they read.

    The depth dialect uses absolute per-level assignment and removes a level only on size 0,
    so consecutive states are diffed here and the disappearing levels are explicitly zeroed.
    Writing the frames as if they were deltas silently left stale levels in the book.
    """
    # A fresh log per call: EventLog RESUMES an existing chain, so a shared filename made
    # every test append to the previous test's book.
    _n[0] += 1
    path = os.path.join(tmp, name or f"b{_n[0]}.jsonl")

    def diff(prev, cur):
        out = [[p, s] for p, s in cur]
        have = {float(p) for p, _ in cur}
        out += [[p, "0"] for p, _ in prev if float(p) not in have]
        return out

    path_ = path
    with EventLog(path_) as log:
        i = Ingestor(log, dialect=dialects.BINANCE)
        i.connection_opened("c1", "wss://x")
        off0, b0, a0 = frames[0]
        i.observe({"lastUpdateId": 1, "bids": b0, "asks": a0},
                  request={"symbol": SYM, "role": "anchor"}, received_at=at(off0))
        u = 2
        pb, pa = b0, a0
        for off, b, a in frames[1:]:
            i.observe({"e": "depthUpdate", "E": 1, "s": SYM, "U": u, "u": u,
                       "b": diff(pb, b), "a": diff(pa, a)}, received_at=at(off))
            pb, pa = b, a
            u += 1
    return path_


def order(**kw):
    d = {"order_id": "o1", "side": F.BUY, "size_usd": 1000.0,
         "decided_at_ms": ms_of(0), "offset_ticks": 0, "tick": 0.01, "ttl_ms": 60_000.0}
    d.update(kw)
    return F.Order(**d)


# ---- latency ----------------------------------------------------------------------------

@check
def order_takes_the_queue_as_it_exists_on_arrival(tmp):
    """
    The point of modelling latency at all. The decision is made against one book; the order
    arrives 291ms later against a different one.
    """
    path = build(tmp, [
        (0,    [["100.00", "5"]], [["100.01", "5"]]),
        (100,  [["100.00", "9"]], [["100.01", "5"]]),      # queue grows while we are in flight
        (400,  [["100.00", "9"]], [["100.01", "5"]]),
    ])
    o = order(price=100.00)
    F.simulate(path, SYM, [o], latency_ms=291.0)
    assert o.arrives_at_ms == o.decided_at_ms + 291.0
    assert o.queue_ahead == 9 * 100.00, o.queue_ahead
    return "queue is measured on arrival (900), not at decision time (500)"


@check
def mid_move_during_flight_is_recorded(tmp):
    path = build(tmp, [
        (0,   [["100.00", "5"]], [["100.01", "5"]]),
        (400, [["100.10", "5"]], [["100.11", "5"]]),       # market moved during the flight
        (500, [["100.10", "5"]], [["100.11", "5"]]),
    ])
    o = order(price=100.00)
    F.simulate(path, SYM, [o], latency_ms=291.0)
    assert o.mid_at_decision == 100.005, o.mid_at_decision
    assert abs(o.mid_at_post - 100.105) < 1e-9, o.mid_at_post
    s = F.summarise([o])
    assert s["median_mid_move_during_latency"] > 0.0009, s
    return "the book moved 0.1% while the order was in flight, and that is recorded"


# ---- the three fill states ----------------------------------------------------------------

@check
def price_trading_through_is_a_certain_fill(tmp):
    """The one case no queue model can dispute: our level is gone and the book moved past it."""
    path = build(tmp, [
        (0,    [["100.00", "5"], ["99.99", "5"]], [["100.01", "5"]]),
        (400,  [["100.00", "5"], ["99.99", "5"]], [["100.00", "5"]]),   # ask reaches our bid
        (600,  [["100.00", "0"], ["99.99", "5"]], [["99.99", "5"]]),    # level cleared, through
        (700,  [["99.99", "5"]],                  [["99.99", "5"]]),
    ])
    o = order(price=100.00)
    F.simulate(path, SYM, [o], latency_ms=291.0, markout_ms=(100,))
    assert o.outcome == "certain", o.outcome
    assert o.reached and o.fill_price == 100.00, o
    return "a level cleared and traded through fills under any queue model"


@check
def queue_never_consumed_does_not_fill(tmp):
    path = build(tmp, [
        (0,     [["100.00", "5"]], [["100.01", "5"]]),
        (400,   [["100.00", "5"]], [["100.01", "5"]]),
        (70000, [["100.00", "5"]], [["100.01", "5"]]),     # nothing ever happens
    ])
    o = order(price=100.00, ttl_ms=10_000.0)
    F.simulate(path, SYM, [o], latency_ms=291.0)
    assert o.outcome == "never_reached", o.outcome
    assert o.fill_price is None
    return "an order the market never reached does not fill"


@check
def the_ambiguous_case_is_labelled_not_guessed(tmp):
    """
    Size at our level fell while the market was at our price. That is either a trade that
    consumed the queue ahead of us or a cancellation from behind. The simulator must not
    pretend to know.
    """
    # 400 of queue vanishes, the level is refilled by traders joining BEHIND us, then another
    # 400 vanishes. Cumulatively that is 800 against a queue of 500, so under the optimistic
    # model we are through -- but the level never emptied, so nothing is certain.
    path = build(tmp, [
        (0,    [["100.00", "5"]], [["100.01", "5"]]),
        (400,  [["100.00", "5"]], [["100.00", "5"]]),      # market at our price, queue 500
        (600,  [["100.00", "1"]], [["100.00", "5"]]),      # -400: trade or cancel?
        (800,  [["100.00", "5"]], [["100.00", "5"]]),      # refilled from behind
        (1000, [["100.00", "1"]], [["100.00", "5"]]),      # -400 again, cumulative 800 > 500
        (1100, [["100.00", "1"]], [["100.00", "5"]]),
    ])
    o = order(price=100.00)
    F.simulate(path, SYM, [o], latency_ms=291.0, markout_ms=(50,))
    assert o.outcome == "optimistic_only", o.outcome
    s = F.summarise([o], markout_ms=(50,))
    assert s["fill_rate_lower_bound"] == 0.0, s
    assert s["fill_rate_upper_bound"] == 1.0, s
    assert s["ambiguity_width"] == 1.0, s
    return "an ambiguous fill widens the bracket instead of being resolved by assumption"


@check
def the_bracket_is_reported_as_a_pair(tmp):
    path_certain = build(tmp, [
        (0,   [["100.00", "5"]], [["100.01", "5"]]),
        (400, [["100.00", "5"]], [["100.00", "5"]]),
        (600, [["100.00", "0"]], [["99.99", "5"]]),
        (700, [["99.99", "5"]],  [["99.99", "5"]]),
    ])
    a = order(price=100.00)
    F.simulate(path_certain, SYM, [a], latency_ms=291.0, markout_ms=(50,))
    s = F.summarise([a], markout_ms=(50,))
    assert s["fill_rate_lower_bound"] == 1.0 and s["fill_rate_upper_bound"] == 1.0
    assert s["ambiguity_width"] == 0.0, s
    return "an unambiguous fill closes the bracket to zero width"


# ---- adverse selection --------------------------------------------------------------------

@check
def adverse_selection_is_measured_as_signed_markout(tmp):
    """
    A resting bid that fills just before the price falls has been adversely selected. The
    markout must be negative, and it must be negative for the BUY sign convention.
    """
    path = build(tmp, [
        (0,    [["100.00", "5"], ["99.00", "50"]], [["100.01", "5"]]),
        (400,  [["100.00", "5"], ["99.00", "50"]], [["100.00", "5"]]),
        (600,  [["100.00", "0"], ["99.00", "50"]], [["99.50", "5"]]),   # filled, then falls
        (2000, [["99.00", "50"]],                  [["99.02", "5"]]),
    ])
    o = order(price=100.00)
    F.simulate(path, SYM, [o], latency_ms=291.0, markout_ms=(1000,))
    assert o.outcome == "certain", o.outcome
    mk = o.markouts["1000ms"]
    assert mk < 0, mk
    assert abs(mk - ((99.01 - 100.00) / 100.00)) < 1e-9, mk
    return f"a bid filled before a fall shows markout {mk*1e4:.0f} bps -- adverse"


@check
def a_good_fill_shows_positive_markout(tmp):
    path = build(tmp, [
        (0,    [["100.00", "5"], ["99.00", "50"]], [["100.01", "5"]]),
        (400,  [["100.00", "5"], ["99.00", "50"]], [["100.00", "5"]]),
        (600,  [["100.00", "0"], ["99.00", "50"]], [["99.99", "5"]]),
        (2000, [["100.50", "5"]],                  [["100.52", "5"]]),   # price rose after
    ])
    o = order(price=100.00)
    F.simulate(path, SYM, [o], latency_ms=291.0, markout_ms=(1000,))
    assert o.markouts["1000ms"] > 0, o.markouts
    return "a bid filled before a rise shows positive markout"


@check
def sell_side_sign_is_inverted(tmp):
    """A resting ask is adversely selected when the price RISES after the fill."""
    path = build(tmp, [
        (0,    [["99.99", "5"]], [["100.00", "5"], ["101.00", "50"]]),
        (400,  [["100.00", "5"]], [["100.00", "5"], ["101.00", "50"]]),
        (600,  [["100.01", "5"]], [["100.00", "0"], ["101.00", "50"]]),
        (2000, [["100.98", "5"]], [["101.00", "50"]]),                  # rose after our sell
    ])
    o = order(order_id="s1", side=F.SELL, price=100.00)
    F.simulate(path, SYM, [o], latency_ms=291.0, markout_ms=(1000,))
    assert o.outcome == "certain", o.outcome
    assert o.markouts["1000ms"] < 0, o.markouts
    return "a resting ask filled before a rise is adverse, with the sign handled correctly"


@check
def fee_advantage_accounting_is_arithmetic_not_judgement(tmp):
    """
    The contract's question: what portion of the maker advantage is lost to adverse selection?
    3 bps advantage against a 5 bps adverse move means the advantage is gone.
    """
    o = order()
    o.outcome, o.fill_price, o.fill_at_ms = "certain", 100.0, 0.0
    o.markouts = {"1000ms": -0.0005}                      # -5 bps
    s = F.summarise([o], markout_ms=(1000,))
    a = s["adverse_selection"]["certain"]
    assert abs(a["median_adverse_bps"] - 5.0) < 1e-9, a
    assert abs(a["maker_advantage_bps"] - 3.0) < 1e-9, a
    assert abs(a["fraction_of_advantage_lost"] - 5.0 / 3.0) < 1e-9, a
    assert a["advantage_survives"] is False, a
    return "5 bps of adverse selection against a 3 bps advantage: 167% lost, does not survive"


@check
def a_small_adverse_move_leaves_the_advantage_intact(tmp):
    o = order()
    o.outcome, o.fill_price, o.fill_at_ms = "certain", 100.0, 0.0
    o.markouts = {"1000ms": -0.0001}                      # -1 bp
    a = F.summarise([o], markout_ms=(1000,))["adverse_selection"]["certain"]
    assert a["advantage_survives"] is True and abs(a["fraction_of_advantage_lost"] - 1/3) < 1e-9
    return "1 bp against 3 bps leaves two thirds of the advantage standing"


@check
def no_signal_or_sizing_logic_exists():
    """
    A structural check against scope creep. This module must not acquire the ability to choose
    what to trade -- it answers only what would have happened to an order it was handed.
    """
    src = open(os.path.join(os.path.dirname(__file__), "..", "market", "fills.py")).read()
    banned = ("def signal", "def strategy", "def optimi", "def size_position",
              "def choose", "sharpe", "pnl", "def backtest")
    hit = [b for b in banned if b in src.lower()]
    assert not hit, f"scope creep: {hit}"
    assert "orders" in F.simulate.__code__.co_varnames, "orders must be supplied by the caller"
    return "no signal, sizing, optimisation or P&L entered the simulator"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-fills-")
    failed = 0
    try:
        for fn in _checks:
            try:
                n = fn.__code__.co_argcount
                print(f"  ok  {fn.__name__}  --  {fn(tmp) if n else fn()}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL {fn.__name__}: {e}")
            except Exception as e:
                failed += 1
                print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"fill-simulator checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
