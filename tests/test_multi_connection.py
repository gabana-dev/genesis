"""
Regression checks for D-4 -- one Ingestor per connection -- and for the instrument
dimension that makes a two-venue log possible.

Written AFTER the defect was demonstrated in a real 90-second futures recording, and each
check asserts the property that recording showed was missing. The demonstration is recorded
in research/binance-futures-stream-availability.md; the defect is that two concurrent
connections sharing one Ingestor

  * cleared EVERY stream's sequence state whenever ANY connection opened, and
  * attributed every lifecycle event to whichever connection opened most recently.

Fixtures are SYNTHETIC, built to the documented Binance payload shapes, and live here rather
than in the `recorder` package so fabricated data cannot reach a real log.

Run: .venv/bin/python tests/test_multi_connection.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import dialects  # noqa: E402
import events as E  # noqa: E402
from log import EventLog, read, verify  # noqa: E402
from stream import Ingestor  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def spot_depth(U, u, sym="BTCUSDT"):
    return {"e": "depthUpdate", "s": sym, "U": U, "u": u, "E": 1_787_000_000_000,
            "b": [["100.0", "1.0"]], "a": [["101.0", "1.0"]]}


def perp_depth(pu, u, sym="BTCUSDT"):
    return {"e": "depthUpdate", "s": sym, "pu": pu, "U": pu + 1, "u": u,
            "E": 1_787_000_000_000, "b": [["100.0", "1.0"]], "a": [["101.0", "1.0"]]}


def events_of(path, typ):
    return [e for e in read(path) if e.get("event_type") == typ]


@check
def one_venue_log_is_unchanged(tmp):
    """
    The instrument dimension must be invisible when unset. Every prior recording, and BAV-1's
    validated behaviour, depends on the sequence key and the observation body being exactly
    what they were.
    """
    path = os.path.join(tmp, "single.log")
    with EventLog(path) as log:
        ing = Ingestor(log, dialect=dialects.BINANCE)
        assert ing._seq_key(None, "depthUpdate", "BTCUSDT") == ("cm", "depthUpdate", "BTCUSDT")
        assert ing._seq_key(7, "depthUpdate", "BTCUSDT") == ("sid", 7)
        ing.connection_opened("c1", "wss://example/ws")
        ing.observe(spot_depth(1, 5))
    obs = [e for e in read(path) if e.get("event_class") == E.WORLD]
    assert len(obs) == 1
    assert "instrument" not in obs[0]["body"]["observation"], \
        "an unset instrument must not appear in the body at all"
    return "unset instrument leaves keys and bodies byte-identical"


@check
def shared_symbol_across_venues_does_not_collide(tmp):
    """
    THE CORE OF T0.2. Spot and perp both call it BTCUSDT, and their update ids are unrelated
    number spaces. Without the instrument dimension the two share one sequence key and the
    recorder reports a gap on nearly every message -- a healthy recording that looks destroyed.
    """
    path = os.path.join(tmp, "twovenue.log")
    with EventLog(path) as log:
        spot = Ingestor(log, dialect=dialects.BINANCE, instrument="binance_spot")
        perp = Ingestor(log, dialect=dialects.BINANCE_FUTURES, instrument="binance_futures")
        spot.connection_opened("spot-1", "wss://spot/ws")
        perp.connection_opened("perp-1", "wss://perp/ws")
        # Interleaved, on one clock, in one chain -- and numerically far apart, as two
        # independent venues always are.
        spot.observe(spot_depth(1000, 1001))
        perp.observe(perp_depth(50, 51))
        spot.observe(spot_depth(1002, 1003))
        perp.observe(perp_depth(51, 52))
        spot.observe(spot_depth(1004, 1005))
        perp.observe(perp_depth(52, 53))

    gaps = events_of(path, "SEQUENCE_GAP")
    assert not gaps, f"two venues collided on the sequence key: {gaps}"
    obs = [e for e in read(path) if e.get("event_class") == E.WORLD]
    assert len(obs) == 6, f"expected 6 observations, got {len(obs)}"
    labels = [e["body"]["observation"]["instrument"] for e in obs]
    assert labels == ["binance_spot", "binance_futures"] * 3, labels
    ok, problems = verify(path)
    assert ok, problems
    return "6 interleaved observations, 0 false gaps, chain verified"


@check
def a_real_gap_is_still_caught_per_instrument(tmp):
    """
    Separating the key spaces must not cost detection. A gap on one venue is still a gap, and
    must not be masked by the other venue's traffic.
    """
    path = os.path.join(tmp, "gap.log")
    with EventLog(path) as log:
        spot = Ingestor(log, dialect=dialects.BINANCE, instrument="binance_spot")
        perp = Ingestor(log, dialect=dialects.BINANCE_FUTURES, instrument="binance_futures")
        spot.connection_opened("spot-1", "wss://spot/ws")
        perp.connection_opened("perp-1", "wss://perp/ws")
        spot.observe(spot_depth(1000, 1001))
        perp.observe(perp_depth(50, 51))
        spot.observe(spot_depth(1500, 1501))          # <- a real hole on spot
        perp.observe(perp_depth(51, 52))              # <- perp remains continuous

    gaps = events_of(path, "SEQUENCE_GAP")
    assert len(gaps) == 1, f"expected exactly one gap, got {len(gaps)}"
    assert gaps[0]["body"]["market_ticker"] == "BTCUSDT"
    return "the spot gap is reported; the continuous perp stream is not implicated"


@check
def one_connection_opening_does_not_blind_another(tmp):
    """
    D-4, first half. `connection_opened` clears sequence state -- correctly, for ITS OWN
    connection. When two connections shared an Ingestor it cleared both, so a reconnect on
    the liquidation feed silently disabled gap detection on the depth feed. Loss of
    detection, reported as health, which is the failure class this recorder exists to prevent.
    """
    path = os.path.join(tmp, "blind.log")
    with EventLog(path) as log:
        book = Ingestor(log, dialect=dialects.BINANCE_FUTURES, instrument="binance_futures")
        liq = Ingestor(log, dialect=dialects.BINANCE_FUTURES, instrument="binance_futures")
        book.connection_opened("book-1", "wss://perp/public")
        liq.connection_opened("liq-1", "wss://perp/market")
        book.observe(perp_depth(50, 51))
        liq.connection_opened("liq-2", "wss://perp/market")   # the other feed reconnects
        book.observe(perp_depth(900, 901))                    # a hole, straight afterwards

    gaps = events_of(path, "SEQUENCE_GAP")
    assert len(gaps) == 1, \
        f"the book's gap was masked by the liquidation feed's reconnect: {len(gaps)} gaps"
    return "a reconnect on one connection does not blind another"


@check
def lifecycle_events_are_attributed_to_their_own_connection(tmp):
    """
    D-4, second half, and the one that produced a false record rather than a missing one. A
    90-second futures recording logged BOTH CONNECTION_CLOSED events against the depth
    connection and none against the liquidation connection: a log stating that one connection
    closed twice and the other never closed.
    """
    path = os.path.join(tmp, "attrib.log")
    with EventLog(path) as log:
        book = Ingestor(log, dialect=dialects.BINANCE_FUTURES, instrument="binance_futures")
        liq = Ingestor(log, dialect=dialects.BINANCE_FUTURES, instrument="binance_futures")
        book.connection_opened("book-1", "wss://perp/public")
        liq.connection_opened("liq-1", "wss://perp/market")
        book.subscription_changed(["depth", "trade"], ["BTCUSDT"])
        liq.subscription_changed(["!forceOrder@arr"], [])
        book.connection_closed("stop_after reached")
        liq.connection_closed("stop_after reached")

    closed = [e["body"]["connection_id"] for e in events_of(path, "CONNECTION_CLOSED")]
    assert sorted(closed) == ["book-1", "liq-1"], f"misattributed closes: {closed}"
    subs = {e["body"]["connection_id"]: e["body"]["channels"]
            for e in events_of(path, "SUBSCRIPTION_CHANGED")}
    assert subs["book-1"] == ["depth", "trade"], subs
    assert subs["liq-1"] == ["!forceOrder@arr"], subs
    return "each connection's closes and subscriptions are its own"


@check
def resume_does_not_borrow_the_other_instrument_state(tmp):
    """
    An Ingestor rebuilds sequence state from the existing log at construction. In a shared
    log it must resume ONLY its own instrument, or it keys another venue's numbers under its
    own label -- reintroducing at startup the exact collision the instrument prevents.
    """
    path = os.path.join(tmp, "resume.log")
    with EventLog(path) as log:
        spot = Ingestor(log, dialect=dialects.BINANCE, instrument="binance_spot")
        perp = Ingestor(log, dialect=dialects.BINANCE_FUTURES, instrument="binance_futures")
        spot.connection_opened("spot-1", "wss://spot/ws")
        perp.connection_opened("perp-1", "wss://perp/ws")
        spot.observe(spot_depth(1000, 1001))
        perp.observe(perp_depth(50, 51))

    # Restart: a fresh perp Ingestor over the same log must carry perp's 51, not spot's 1001.
    with EventLog(path) as log:
        perp2 = Ingestor(log, dialect=dialects.BINANCE_FUTURES, instrument="binance_futures")
        resumed = perp2._last_seq.get(("binance_futures", "cm", "depthUpdate", "BTCUSDT"))
        assert resumed == 51, f"resumed the wrong instrument's sequence: {resumed}"
        assert not any(k[0] == "binance_spot" for k in perp2._last_seq), \
            "perp resumed spot's state"
        perp2.connection_opened("perp-2", "wss://perp/ws")
        perp2.observe(perp_depth(51, 52))

    assert not events_of(path, "SEQUENCE_GAP"), "resume produced a false gap"
    return "each instrument resumes only its own sequence state"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-multiconn-")
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
          f"D-4 multi-connection checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
