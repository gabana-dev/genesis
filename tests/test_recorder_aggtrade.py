"""
Checks for the aggTrade channel — the trade stream.

WHY IT IS BEING ADDED
    EXEC-1's largest stated limitation was that the recording carries NO trade stream, so
    every fill is inferred from book evolution and reported as a bracket rather than observed.
    Binance's archives publish historical aggTrades, but they publish no book at 500ms — so a
    joint record of book AND trades on one clock, under the recorder's own completeness
    labels, exists only if it is recorded live. It cannot be backfilled.

WHAT THESE CHECKS PIN
    The channel drops into machinery that already generalises: `dialects` reduces sequence to
    a RANGE (seq_first, seq_last) and `stream` keys sequence state by (subscription, channel,
    market). aggTrade's f/l — first and last trade id — is exactly that range, and being
    keyed by channel means depth ids and trade ids cannot collide. These checks assert both
    properties rather than assuming them, because a shared sequence space would produce a
    SEQUENCE_GAP on almost every message and the recording would look catastrophically broken
    while being fine.

    The aggressor side is taken from Binance's `m` flag, not inferred. `m` true means the
    BUYER was the maker, so the aggressor was the seller. Getting this backwards inverts
    signed order flow, which is silent and would corrupt every downstream measurement.

Fixtures are SYNTHETIC, built to Binance's documented aggTrade shape.

Run: .venv/bin/python tests/test_recorder_aggtrade.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import dialects  # noqa: E402
import events as E  # noqa: E402
from log import EventLog, read  # noqa: E402
from stream import Ingestor  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def agg_trade(agg_id=1, first=100, last=105, price="63476.05", qty="0.125",
              buyer_is_maker=True, symbol="BTCUSDT", event_ms=1_700_000_000_000):
    """Binance documented aggTrade payload."""
    return {"e": "aggTrade", "E": event_ms, "s": symbol, "a": agg_id,
            "p": price, "q": qty, "f": first, "l": last,
            "T": event_ms - 3, "m": buyer_is_maker, "M": True}


def depth_update(U=1000, u=1005, symbol="BTCUSDT"):
    return {"e": "depthUpdate", "E": 1_700_000_000_000, "s": symbol, "U": U, "u": u,
            "b": [["63476.00", "1.5"]], "a": [["63476.10", "2.0"]]}


# ---- dialect --------------------------------------------------------------------------

@check
def the_dialect_reads_aggtrade_as_a_trade_id_range(tmp):
    ex = dialects.binance_extract(agg_trade(agg_id=7, first=100, last=105))
    assert ex["channel"] == "aggTrade", ex["channel"]
    assert ex["market"] == "BTCUSDT", ex["market"]
    assert ex["seq_first"] == 100, ex["seq_first"]
    assert ex["seq_last"] == 105, ex["seq_last"]
    return "f/l map onto the existing seq_first/seq_last range"


@check
def a_depth_update_still_reads_its_own_ids(tmp):
    """The aggTrade branch must not disturb depth, which uses U/u."""
    ex = dialects.binance_extract(depth_update(U=1000, u=1005))
    assert ex["channel"] == "depthUpdate"
    assert (ex["seq_first"], ex["seq_last"]) == (1000, 1005), ex
    return "depth still reads U/u unchanged"


# ---- canonical view -------------------------------------------------------------------

@check
def the_aggressor_side_is_read_from_the_venue_not_inferred(tmp):
    """
    m=True  -> buyer was the MAKER -> the aggressor was the SELLER.
    Reversing this inverts signed order flow silently.
    """
    sell = E.canonical_view("aggTrade", agg_trade(buyer_is_maker=True))
    buy = E.canonical_view("aggTrade", agg_trade(buyer_is_maker=False))
    assert sell["aggressor_side"] == "sell", sell
    assert buy["aggressor_side"] == "buy", buy
    assert sell["buyer_is_maker"] is True and buy["buyer_is_maker"] is False
    return "m=True yields aggressor 'sell'; m=False yields 'buy'"


@check
def price_and_quantity_are_canonicalised(tmp):
    cv = E.canonical_view("aggTrade", agg_trade(price="63476.05", qty="0.125"))
    assert cv["price"] == "63476.05", cv
    assert cv["qty"] == "0.125", cv
    assert cv["agg_trade_id"] == 1, cv
    assert cv["trade_ms"] == 1_699_999_999_997, cv
    assert "invalid" not in cv, cv
    return "price, qty, id and trade time canonicalised without loss"


@check
def a_malformed_trade_is_marked_invalid_not_silently_zeroed(tmp):
    cv = E.canonical_view("aggTrade", agg_trade(price="not-a-price", qty="-1"))
    assert "invalid" in cv, cv
    fields = {i["field"] for i in cv["invalid"]}
    assert "p" in fields, fields
    return f"a bad price/qty is reported invalid: {sorted(fields)}"


@check
def an_unknown_side_flag_is_refused(tmp):
    bad = agg_trade()
    bad["m"] = "yes"
    cv = E.canonical_view("aggTrade", bad)
    assert "invalid" in cv, cv
    assert cv.get("aggressor_side") is None, cv
    return "a non-boolean maker flag yields no side, and is recorded invalid"


# ---- sequence isolation, the one that matters -----------------------------------------

@check
def depth_and_trade_sequences_do_not_collide(tmp):
    """
    THE CRITICAL CHECK. Depth update ids and aggregate trade ids are different number
    spaces on the same symbol. If sequence state were keyed by market alone, interleaving
    them would emit a SEQUENCE_GAP on nearly every message -- a recording that looked
    catastrophically broken while being perfectly fine.
    """
    path = os.path.join(tmp, "mixed.jsonl")
    ing = Ingestor(EventLog(path), dialect=dialects.BINANCE)
    ing.started("test")
    ing.connection_opened("c1", "ws://test")

    ing.observe(depth_update(U=1000, u=1005))
    ing.observe(agg_trade(agg_id=1, first=100, last=105))
    ing.observe(depth_update(U=1006, u=1010))
    ing.observe(agg_trade(agg_id=2, first=106, last=110))
    ing.observe(depth_update(U=1011, u=1011))

    gaps = [e for e in read(path) if e.get("event_type") == "SEQUENCE_GAP"]
    assert not gaps, f"interleaving depth and trades emitted {len(gaps)} spurious gap(s)"
    return "5 interleaved messages across two id spaces, 0 spurious gaps"


@check
def a_real_trade_gap_is_still_caught(tmp):
    """And the other half: the detector must not have been silenced to achieve the above."""
    path = os.path.join(tmp, "gap.jsonl")
    ing = Ingestor(EventLog(path), dialect=dialects.BINANCE)
    ing.started("test")
    ing.connection_opened("c1", "ws://test")

    ing.observe(agg_trade(agg_id=1, first=100, last=105))
    ing.observe(agg_trade(agg_id=2, first=200, last=205))     # 106..199 missing

    gaps = [e for e in read(path) if e.get("event_type") == "SEQUENCE_GAP"]
    assert len(gaps) == 1, f"expected 1 trade gap, got {len(gaps)}"
    body = gaps[0]["body"]
    assert body.get("channel") == "aggTrade", body
    return "a genuine break in trade ids is reported as a gap on the aggTrade channel"


def main():
    tmp = tempfile.mkdtemp(prefix="aggtrade-")
    failed = 0
    try:
        for fn in _checks:
            d = os.path.join(tmp, fn.__name__)
            os.makedirs(d, exist_ok=True)
            try:
                print(f"  ok  {fn.__name__}  --  {fn(d)}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL {fn.__name__}: {e}")
            except Exception as e:
                failed += 1
                print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"aggTrade checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
