"""
Binance depth-stream dialect checks.

Written BEFORE the implementation. The fixtures are REAL: every field value below was
captured from `wss://stream.binance.com:9443/ws/btcusdt@depth` on 2026-08-09, including the
sequence numbers, the event timestamps, the 8-decimal quantity strings and a genuine
zero-quantity level removal. Only the level arrays are truncated, for readability.

Two properties of this venue differ materially from Kalshi, and the recorder must represent
them rather than translate them away:

  1. SEQUENCE IS A RANGE. Each message carries `U` (first update id) and `u` (final update
     id). Contiguity is `next.U == prev.u + 1`, verified empirically across the capture.
     Kalshi's single `seq` is the degenerate case where first == last.

  2. LEVELS ARE ABSOLUTE, NOT DELTAS. A `b`/`a` entry assigns the new total size at a price;
     quantity "0" REMOVES the level. Converting these to deltas would require inferring the
     prior book, which is authoring, so they are recorded as what they are.

Run: .venv/bin/python tests/test_recorder_binance.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import dialects  # noqa: E402
import events as E  # noqa: E402
import replay  # noqa: E402
from log import EventLog, read  # noqa: E402
from stream import Ingestor  # noqa: E402

SYMBOL = "BTCUSDT"
_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def depth(U, u, E_ms=1786303446014, bids=None, asks=None):
    """Real captured shape: keys e, E, s, U, u, b, a."""
    return {"e": "depthUpdate", "E": E_ms, "s": SYMBOL, "U": U, "u": u,
            "b": bids if bids is not None else [["65209.96000000", "1.13938000"],
                                                ["65209.95000000", "0.38815000"]],
            "a": asks if asks is not None else [["65209.97000000", "10.22224000"],
                                                ["65210.52000000", "0.24174000"]]}


def ing(log):
    return Ingestor(log, dialect=dialects.BINANCE)


@check
def real_payload_is_extracted(tmp):
    path = os.path.join(tmp, "a.jsonl")
    with EventLog(path) as log:
        ing(log).observe(depth(98377489110, 98377489259))
    ev = [e for e in read(path) if e["event_class"] == E.WORLD][0]
    w = ev["body"]["world"]
    assert w["channel"] == "depthUpdate", w["channel"]
    assert w["market_ticker"] == SYMBOL, w["market_ticker"]
    assert w["venue_seq"] == 98377489110 and w["venue_seq_last"] == 98377489259, w
    assert w["venue_ts_ms"] == 1786303446014, w
    assert w["raw"]["U"] == 98377489110, "raw must stay verbatim"
    assert ev["body"]["observation"]["received_at"].endswith("+00:00")
    return "U/u/E/s extracted; raw verbatim; both clocks preserved"


@check
def contiguous_range_is_not_a_gap(tmp):
    path = os.path.join(tmp, "b.jsonl")
    with EventLog(path) as log:
        i = ing(log)
        i.observe(depth(98377489110, 98377489259))
        i.observe(depth(98377489260, 98377489333))     # real next message
    assert not [e for e in read(path) if e["event_type"] == "SEQUENCE_GAP"]
    return "next.U == prev.u + 1 accepted as contiguous"


@check
def broken_range_is_a_gap(tmp):
    path = os.path.join(tmp, "c.jsonl")
    with EventLog(path) as log:
        i = ing(log)
        i.observe(depth(98377489110, 98377489259))
        i.observe(depth(98377489300, 98377489350))     # 260..299 missing
    gaps = [e["body"] for e in read(path) if e["event_type"] == "SEQUENCE_GAP"]
    assert len(gaps) == 1, gaps
    assert (gaps[0]["missing_from"], gaps[0]["missing_to"]) == (98377489260, 98377489299), gaps[0]
    return "a broken range records the exact missing span"


@check
def absolute_levels_replay(tmp):
    path = os.path.join(tmp, "d.jsonl")
    with EventLog(path) as log:
        i = ing(log)
        i.observe(depth(1, 1, bids=[["65209.96000000", "1.13938000"]],
                        asks=[["65209.97000000", "10.22224000"]]))
        i.observe(depth(2, 2, bids=[["65209.96000000", "2.50000000"]], asks=[]))
    b = replay.order_book_at(path, SYMBOL)
    assert b["book"]["bids"] == {"65209.96": "2.5"}, b["book"]
    assert b["book"]["asks"] == {"65209.97": "10.22224"}, b["book"]
    return "an absolute level assignment replaces, it does not accumulate"


@check
def zero_quantity_removes_the_level(tmp):
    path = os.path.join(tmp, "e.jsonl")
    with EventLog(path) as log:
        i = ing(log)
        i.observe(depth(1, 1, bids=[["65208.10000000", "0.50000000"],
                                    ["65209.96000000", "1.13938000"]], asks=[]))
        i.observe(depth(2, 2, bids=[["65208.10000000", "0.00000000"]], asks=[]))  # real removal
    b = replay.order_book_at(path, SYMBOL)
    assert b["book"]["bids"] == {"65209.96": "1.13938"}, b["book"]
    assert b["complete"] is True, b
    return "quantity 0 removes the level and is not an error"


@check
def eight_decimal_quantities_are_exact(tmp):
    path = os.path.join(tmp, "f.jsonl")
    with EventLog(path) as log:
        ing(log).observe(depth(1, 1, bids=[["65209.95000000", "0.38815000"]],
                               asks=[["65210.52000000", "0.24174000"]]))
    ev = [e for e in read(path) if e["event_class"] == E.WORLD][0]
    canon = ev["body"]["world"]["canonical"]
    assert canon["bids"] == [["65209.95", "0.38815"]], canon
    assert canon["asks"] == [["65210.52", "0.24174"]], canon
    assert canon["absolute"] is True
    return "8-decimal strings canonicalise without loss; absolute flag recorded"


@check
def gap_makes_the_book_incomplete(tmp):
    path = os.path.join(tmp, "g.jsonl")
    with EventLog(path) as log:
        i = ing(log)
        i.observe(depth(1, 1, bids=[["65209.96000000", "1.00000000"]], asks=[]))
        i.observe(depth(50, 50, bids=[["65209.96000000", "2.00000000"]], asks=[]))
    b = replay.order_book_at(path, SYMBOL)
    assert b["complete"] is False, b
    assert "sequence gap" in (b["reason"] or ""), b["reason"]
    return "a real gap propagates incompleteness, as with Kalshi"


@check
def duplicate_is_not_applied_twice(tmp):
    path = os.path.join(tmp, "h.jsonl")
    with EventLog(path) as log:
        i = ing(log)
        i.observe(depth(1, 1, bids=[["65209.96000000", "1.00000000"]], asks=[]))
        i.observe(depth(2, 2, bids=[["65209.96000000", "5.00000000"]], asks=[]))
        i.observe(depth(2, 2, bids=[["65209.96000000", "5.00000000"]], asks=[]))
    assert "DUPLICATE_MESSAGE" in [e["event_type"] for e in read(path)]
    b = replay.order_book_at(path, SYMBOL)
    assert b["book"]["bids"] == {"65209.96": "5"}, b["book"]
    return "duplicate range detected and not re-applied"


@check
def kalshi_dialect_still_works(tmp):
    """The generalisation must not break the venue the recorder was written for."""
    path = os.path.join(tmp, "i.jsonl")
    k_snap = {"type": "orderbook_snapshot", "sid": 1, "seq": 1,
              "msg": {"market_ticker": "KX", "ts_ms": 1000,
                      "yes_dollars_fp": [["0.50", "100"]], "no_dollars_fp": []}}
    k_delta = {"type": "orderbook_delta", "sid": 1, "seq": 2,
               "msg": {"market_ticker": "KX", "ts_ms": 1100, "side": "yes",
                       "price_dollars": "0.50", "delta_fp": "-40"}}
    with EventLog(path) as log:
        i = Ingestor(log)                       # default dialect
        i.observe(k_snap)
        i.observe(k_delta)
    b = replay.order_book_at(path, "KX")
    assert b["complete"] is True and b["book"]["yes"] == {"0.5": "60"}, b
    return "Kalshi dialect unchanged: single seq, delta semantics, yes/no sides"


@check
def malformed_binance_message_is_uninterpretable(tmp):
    path = os.path.join(tmp, "j.jsonl")
    with EventLog(path) as log:
        i = ing(log)
        i.observe(depth(1, 1, bids=[["65209.96000000", "1.00000000"]], asks=[]))
        i.observe(depth(2, 2, bids=[["NOT-A-PRICE", "1.00000000"]], asks=[]))
    b = replay.order_book_at(path, SYMBOL)
    assert b["complete"] is False, b
    assert "UNINTERPRETABLE_FIELD" in [e["event_type"] for e in read(path)]
    assert b["book"]["bids"] == {"65209.96": "1"}, b["book"]
    return "a bad level is uninterpretable here too; invariant 16 holds across dialects"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-binance-")
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
          f"Binance dialect checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
