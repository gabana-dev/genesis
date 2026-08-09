"""
Regression checks for audit defects D1-D5: uninterpretable and invalid numeric fields.

Written BEFORE the fixes. Each check corresponds to a defect demonstrated by an audit probe:

  D1  an unparseable PRICE in a delta was silently discarded, book reported complete
  D2  an unparseable QUANTITY in a delta became a zero delta, silently
  D3  an unparseable SNAPSHOT size became a phantom zero level that persisted
  D4  "-0.00" canonicalised to "-0", a distinct key from "0"
  D5  prices and quantities shared identical (absent) validity rules, so a negative
      resting size was accepted as book state

The governing principle is the one the recorder already enforces elsewhere: a value the
recorder cannot interpret must make the projection INCOMPLETE. It must never be dropped,
defaulted, or rounded into something plausible.

Fixtures are SYNTHETIC. Run: .venv/bin/python tests/test_recorder_validity.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import events as E  # noqa: E402
import health  # noqa: E402
import replay  # noqa: E402
from log import EventLog, read  # noqa: E402
from stream import Ingestor  # noqa: E402

T = "KXBTC15M-26AUG091045-45"
_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def snap(seq=1, yes=None, no=None):
    return {"type": "orderbook_snapshot", "sid": 1, "seq": seq,
            "msg": {"market_ticker": T, "ts_ms": 1786293000000,
                    "yes_dollars_fp": yes if yes is not None else [["0.50", "100"]],
                    "no_dollars_fp": no if no is not None else []}}


def dl(seq, price, amount, side="yes"):
    return {"type": "orderbook_delta", "sid": 1, "seq": seq,
            "msg": {"market_ticker": T, "ts_ms": 1786293000000 + seq, "side": side,
                    "price_dollars": price, "delta_fp": amount}}


@check
def d1_unparseable_price_marks_incomplete(tmp):
    path = os.path.join(tmp, "d1.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap())
        i.observe(dl(2, "NOT-A-PRICE", "-40"))
    b = replay.order_book_at(path, T)
    assert b["complete"] is False, b
    assert "uninterpretable" in (b["reason"] or "").lower(), b["reason"]
    assert b["book"]["yes"] == {"0.5": "100"}, "the bad delta must not be applied"
    types = [e["event_type"] for e in read(path)]
    assert "UNINTERPRETABLE_FIELD" in types, types
    return "unparseable price: not applied, anomaly recorded, book incomplete"


@check
def d2_unparseable_quantity_marks_incomplete(tmp):
    path = os.path.join(tmp, "d2.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap())
        i.observe(dl(2, "0.50", "NOT-A-QTY"))
    b = replay.order_book_at(path, T)
    assert b["complete"] is False, b
    assert b["book"]["yes"] == {"0.5": "100"}, "must not apply a zero delta"
    return "unparseable quantity: no silent zero delta, book incomplete"


@check
def d3_unparseable_snapshot_size_marks_incomplete(tmp):
    path = os.path.join(tmp, "d3.jsonl")
    with EventLog(path) as log:
        Ingestor(log).observe(snap(yes=[["0.50", "100"], ["0.60", "BAD"]]))
    b = replay.order_book_at(path, T)
    assert b["complete"] is False, b
    assert "0.6" not in b["book"]["yes"], f"phantom level: {b['book']['yes']}"
    assert b["book"]["yes"] == {"0.5": "100"}, b["book"]["yes"]
    return "bad snapshot level: no phantom zero, book incomplete"


@check
def d3b_zero_size_level_is_not_a_level(tmp):
    path = os.path.join(tmp, "d3b.jsonl")
    with EventLog(path) as log:
        Ingestor(log).observe(snap(yes=[["0.50", "100"], ["0.60", "0"]]))
    b = replay.order_book_at(path, T)
    assert b["complete"] is True, b
    assert b["book"]["yes"] == {"0.5": "100"}, b["book"]["yes"]
    return "a zero-size snapshot level is dropped, matching delta pop-at-zero"


@check
def d4_negative_zero_collapses(tmp):
    assert E.canon_decimal("-0.00") == "0", E.canon_decimal("-0.00")
    assert E.canon_decimal("0.00") == "0"
    assert E.canon_decimal(-0.0) == "0"
    path = os.path.join(tmp, "d4.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(yes=[["0.50", "5"]]))
        i.observe(dl(2, "0.50", "-5"))          # exactly zero -> level removed
    b = replay.order_book_at(path, T)
    assert b["book"]["yes"] == {}, b["book"]
    return "'-0.00', '0.00' and -0.0 all canonicalise to '0'; no split key"


@check
def d5_negative_price_is_invalid(tmp):
    assert E.canon_price("-0.50") is None, E.canon_price("-0.50")
    assert E.canon_price("0.50") == "0.5"
    path = os.path.join(tmp, "d5a.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap())
        i.observe(dl(2, "-0.50", "10"))
    b = replay.order_book_at(path, T)
    assert b["complete"] is False, b
    assert b["book"]["yes"] == {"0.5": "100"}, b["book"]["yes"]
    return "a negative price is invalid, not a book key"


@check
def d5_negative_resting_size_is_invalid(tmp):
    assert E.canon_size("-100") is None
    assert E.canon_size("100") == "100"
    path = os.path.join(tmp, "d5b.jsonl")
    with EventLog(path) as log:
        Ingestor(log).observe(snap(yes=[["0.50", "-100"]]))
    b = replay.order_book_at(path, T)
    assert b["complete"] is False, b
    assert b["book"]["yes"] == {}, b["book"]["yes"]
    return "a negative resting size is rejected, never booked"


@check
def d5_negative_delta_remains_valid(tmp):
    assert E.canon_qty("-40") == "-40", "a delta may reduce a level"
    path = os.path.join(tmp, "d5c.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(yes=[["0.50", "100"]]))
        i.observe(dl(2, "0.50", "-40"))
    b = replay.order_book_at(path, T)
    assert b["complete"] is True and b["book"]["yes"] == {"0.5": "60"}, b
    return "price and size are non-negative; a delta amount is signed -- rules differ by role"
@check
def unknown_side_in_delta_marks_incomplete(tmp):
    path = os.path.join(tmp, "side.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap())
        i.observe(dl(2, "0.50", "-10", side="maybe"))
    b = replay.order_book_at(path, T)
    assert b["complete"] is False, b
    assert b["book"]["yes"] == {"0.5": "100"}, b["book"]["yes"]
    return "an unrecognised side is uninterpretable, not silently ignored"


@check
def health_surfaces_uninterpretable_fields(tmp):
    path = os.path.join(tmp, "h.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.started({"markets": [T]})
        i.observe(snap(), received_at="2026-08-09T10:00:00+00:00")
        i.observe(dl(2, "BAD", "-1"), received_at="2026-08-09T10:00:10+00:00")
    rep = health.report(path)
    assert rep["uninterpretable_fields"], rep.get("uninterpretable_fields")
    assert any(iv["reason"].startswith("uninterpretable")
               for iv in rep["incomplete_intervals"]), rep["incomplete_intervals"]
    assert "uninterpretable" in health.render(rep).lower()
    return "uninterpretable fields counted and shown as an incomplete interval"


@check
def valid_traffic_is_unaffected(tmp):
    path = os.path.join(tmp, "ok.jsonl")
    real_yes = [["0.0570", "0.01"], ["0.0580", "5.01"]]
    real_no = [["0.9380", "191.00"]]
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(yes=real_yes, no=real_no))
        i.observe(dl(2, "0.0570", "0.02"))
    b = replay.order_book_at(path, T)
    assert b["complete"] is True, b
    assert b["book"]["yes"] == {"0.057": "0.03", "0.058": "5.01"}, b["book"]["yes"]
    assert b["book"]["no"] == {"0.938": "191"}, b["book"]["no"]
    assert not [e for e in read(path) if e["event_type"] == "UNINTERPRETABLE_FIELD"]
    return "real fractional traffic still replays clean, no false anomalies"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-validity-")
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
          f"D1-D5 validity checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
