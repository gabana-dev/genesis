"""
D-6: a log holding two venues under one ticker.

q5 records Binance spot and USD-M perp together and both call the symbol BTCUSDT. Filtering on
`market_ticker` alone merges them — perp depth applied to the spot book — producing a
reconstruction of a venue that never existed. COND-1's conditioner A is the SPREAD between
those two books, so it cannot be computed at all until the reader can tell them apart.

The recorder has carried `instrument` on the observation side since the D-4 fix. This reader
never read it.

Run: .venv/bin/python tests/test_book_instrument.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import book as bk  # noqa: E402
import dialects  # noqa: E402
from log import EventLog  # noqa: E402
from stream import Ingestor  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def snapshot(bid, ask, sym="BTCUSDT"):
    """A REST depth snapshot in Binance's shape: no `e`, no symbol in the payload."""
    return {"lastUpdateId": 1, "bids": [[str(bid), "5.0"]], "asks": [[str(ask), "5.0"]]}


def two_venue_log(path):
    """One log, two instruments, one ticker — and deliberately different prices."""
    with EventLog(path) as log:
        spot = Ingestor(log, dialect=dialects.BINANCE, instrument="binance_spot")
        perp = Ingestor(log, dialect=dialects.BINANCE_FUTURES, instrument="binance_futures")
        spot.connection_opened("s1", "wss://spot/ws")
        spot.subscription_changed(["depth"], ["BTCUSDT"])
        perp.connection_opened("p1", "wss://perp/ws")
        perp.subscription_changed(["depth"], ["BTCUSDT"])
        req = {"url": "https://example/depth", "symbol": "BTCUSDT"}
        spot.observe(snapshot(100.0, 101.0), request=req)
        perp.observe(snapshot(200.0, 201.0), request=req)


@check
def unfiltered_streaming_merges_two_venues():
    """
    The defect, demonstrated — and it is worse than "the books interleave".

    A depth SNAPSHOT clears the book before applying, so the second venue does not blend with
    the first, it REPLACES it wholesale. Ask for the spot book from a two-venue log and you
    silently receive the perp book, at perp prices, with nothing anywhere saying so.
    """
    d = tempfile.mkdtemp(prefix="d6-")
    try:
        p = os.path.join(d, "two.log")
        two_venue_log(p)
        mids = [(b.best_bid, b.best_ask) for _, b in bk.stream(p, "BTCUSDT", every_ms=0)]
        assert mids, "no frames"
        bid, ask = mids[-1]
        assert (bid, ask) == (200.0, 201.0), (bid, ask)
        return (f"asked for spot, silently got perp: {bid}/{ask} — the snapshot cleared the "
                f"spot book and replaced it")
    finally:
        shutil.rmtree(d, ignore_errors=True)


@check
def filtering_by_instrument_separates_them():
    d = tempfile.mkdtemp(prefix="d6-")
    try:
        p = os.path.join(d, "two.log")
        two_venue_log(p)
        got = {}
        for inst in ("binance_spot", "binance_futures"):
            frames = [(b.best_bid, b.best_ask)
                      for _, b in bk.stream(p, "BTCUSDT", every_ms=0, instrument=inst)]
            assert frames, f"no frames for {inst}"
            got[inst] = frames[-1]
        assert got["binance_spot"] == (100.0, 101.0), got
        assert got["binance_futures"] == (200.0, 201.0), got
        return "spot reads 100/101 and perp reads 200/201, as recorded"
    finally:
        shutil.rmtree(d, ignore_errors=True)


@check
def the_basis_is_now_computable():
    """
    COND-1's conditioner A. Before this fix the quantity could not be formed at all, because
    both mids came from the same corrupted book.
    """
    d = tempfile.mkdtemp(prefix="d6-")
    try:
        p = os.path.join(d, "two.log")
        two_venue_log(p)
        mid = {}
        for inst in ("binance_spot", "binance_futures"):
            _, b = list(bk.stream(p, "BTCUSDT", every_ms=0, instrument=inst))[-1]
            mid[inst] = (b.best_bid + b.best_ask) / 2
        basis = (mid["binance_futures"] - mid["binance_spot"]) / mid["binance_spot"]
        assert abs(basis - (200.5 - 100.5) / 100.5) < 1e-9, basis
        return f"basis forms cleanly: {basis:.4f} from two separate books"
    finally:
        shutil.rmtree(d, ignore_errors=True)


@check
def omitting_instrument_preserves_prior_behaviour_exactly():
    """
    Every existing caller -- exec1, cap2, fills -- passes no instrument. Their logs hold one
    venue, so the filter must be a no-op there or EXEC-1's and CAP-2's results silently change.
    """
    d = tempfile.mkdtemp(prefix="d6-")
    try:
        p = os.path.join(d, "one.log")
        with EventLog(p) as log:
            ing = Ingestor(log, dialect=dialects.BINANCE)      # no instrument, as before
            ing.connection_opened("c1", "wss://spot/ws")
            ing.subscription_changed(["depth"], ["BTCUSDT"])
            ing.observe(snapshot(100.0, 101.0),
                        request={"url": "https://example/depth", "symbol": "BTCUSDT"})
        frames = [(b.best_bid, b.best_ask) for _, b in bk.stream(p, "BTCUSDT", every_ms=0)]
        assert frames and frames[-1] == (100.0, 101.0), frames
        # And an instrument filter finds nothing, because none was ever recorded.
        none = list(bk.stream(p, "BTCUSDT", every_ms=0, instrument="binance_spot"))
        assert not any(b.ready() for _, b in none), "unlabelled events matched a label"
        return "single-venue logs stream identically; an unset label matches nothing"
    finally:
        shutil.rmtree(d, ignore_errors=True)


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
          f"D-6 instrument-separation checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
