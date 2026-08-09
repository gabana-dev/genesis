"""
NF-1 regression: Kalshi quantities are decimal strings, not integers.

The shapes below are taken from a REAL public REST response observed 2026-08-09 for
`KXBTC15M-26AUG091045-45`:

    {"orderbook_fp": {"no_dollars":  [["0.9380","191.00"],["0.9390","33.00"],["0.9400","298.18"]],
                      "yes_dollars": [["0.0570","0.01"],  ["0.0580","5.01"], ["0.0590","9.01"]]}}

with market metadata `"price_level_structure": "tapered_deci_cent"` and tick steps of 0.0010
below $0.10 and above $0.90.

PROVENANCE, kept explicit:
  * the fractional decimal-string quantity is OBSERVED REST evidence;
  * the WebSocket payload (`yes_dollars_fp`, `delta_fp`) is UNOBSERVED;
  * that the two share the representation is INFERRED from the shared `_fp` convention;
  * these fixtures therefore mirror the observed REST quantities into the documented WS
    envelope. They are SYNTHETIC WS messages carrying REAL quantity shapes, and prove only
    that the recorder handles that shape -- not that the WS sends it.

Run: .venv/bin/python tests/test_recorder_decimal_qty.py
"""

import json
import os
import shutil
import sys
import tempfile
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import events as E  # noqa: E402
import replay  # noqa: E402
from log import EventLog, read, verify  # noqa: E402
from stream import Ingestor  # noqa: E402

T = "KXBTC15M-26AUG091045-45"
_checks = []


def check(fn):
    _checks.append(fn)
    return fn


REAL_YES = [["0.0570", "0.01"], ["0.0580", "5.01"], ["0.0590", "9.01"]]
REAL_NO = [["0.9380", "191.00"], ["0.9390", "33.00"], ["0.9400", "298.18"]]


def snap(seq=1, ts=1786293000000, yes=None, no=None):
    return {"type": "orderbook_snapshot", "sid": 1, "seq": seq,
            "msg": {"market_ticker": T, "ts_ms": ts,
                    "yes_dollars_fp": yes if yes is not None else REAL_YES,
                    "no_dollars_fp": no if no is not None else REAL_NO}}


def dl(seq, ts, price, delta, side="yes"):
    return {"type": "orderbook_delta", "sid": 1, "seq": seq,
            "msg": {"market_ticker": T, "ts_ms": ts, "side": side,
                    "price_dollars": price, "delta_fp": delta}}


@check
def real_snapshot_replays(tmp):
    path = os.path.join(tmp, "a.jsonl")
    with EventLog(path) as log:
        Ingestor(log).observe(snap())
    b = replay.order_book_at(path, T)
    assert b["complete"] is True, b
    assert b["book"]["yes"] == {"0.057": "0.01", "0.058": "5.01", "0.059": "9.01"}, b["book"]
    assert b["book"]["no"] == {"0.938": "191", "0.939": "33", "0.94": "298.18"}, b["book"]
    return "real fractional snapshot replays exactly; no int coercion"


@check
def fractional_delta_arithmetic_is_exact(tmp):
    path = os.path.join(tmp, "b.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap())
        i.observe(dl(2, 1786293001000, "0.0570", "0.02"))     # 0.01 + 0.02 = 0.03
        i.observe(dl(3, 1786293002000, "0.0590", "-9.005"))   # 9.01 - 9.005 = 0.005
        i.observe(dl(4, 1786293003000, "0.9400", "-0.18", side="no"))
    b = replay.order_book_at(path, T)
    assert b["book"]["yes"]["0.057"] == "0.03", b["book"]["yes"]
    assert b["book"]["yes"]["0.059"] == "0.005", b["book"]["yes"]
    assert b["book"]["no"]["0.94"] == "298", b["book"]["no"]
    # exactness: binary float would give 0.030000000000000002 / 9.004999999999999
    assert Decimal(b["book"]["yes"]["0.057"]) == Decimal("0.03")
    return "fractional deltas accumulate exactly; no binary-float drift"


@check
def level_removed_only_at_exactly_zero(tmp):
    path = os.path.join(tmp, "c.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(yes=[["0.0570", "0.01"]], no=[]))
        i.observe(dl(2, 1786293001000, "0.0570", "-0.009"))   # 0.001 remains
    b = replay.order_book_at(path, T)
    assert b["book"]["yes"] == {"0.057": "0.001"}, b["book"]
    with EventLog(path) as log:
        Ingestor(log).observe(dl(3, 1786293002000, "0.0570", "-0.001"))  # exactly zero
    b2 = replay.order_book_at(path, T)
    assert b2["book"]["yes"] == {}, b2["book"]
    return "a sub-cent residue survives; exact zero removes the level"


@check
def canonical_quantity_recorded_at_ingestion(tmp):
    path = os.path.join(tmp, "d.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(yes=[["0.0570", "191.00"]], no=[]))
        i.observe(dl(2, 1786293001000, "0.0580", "5.010"))
    evs = [e for e in read(path) if e["event_class"] == E.WORLD]
    assert evs[0]["body"]["world"]["canonical"]["yes"] == [["0.057", "191"]], evs[0]["body"]
    assert evs[0]["body"]["world"]["raw"]["msg"]["yes_dollars_fp"] == [["0.0570", "191.00"]], \
        "raw must stay verbatim"
    assert evs[1]["body"]["world"]["canonical"]["delta_fp"] == "5.01", evs[1]["body"]
    assert evs[1]["body"]["world"]["raw"]["msg"]["delta_fp"] == "5.010"
    return "quantities canonicalised at ingestion; raw untouched"


@check
def equivalent_quantity_spellings_agree(tmp):
    path = os.path.join(tmp, "e.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(yes=[["0.0570", "5.00"]], no=[]))
        i.observe(dl(2, 1786293001000, "0.0570", 5))        # numeric int
        i.observe(dl(3, 1786293002000, "0.0570", "5.0"))    # string with trailing zero
    b = replay.order_book_at(path, T)
    assert b["book"]["yes"] == {"0.057": "15"}, b["book"]
    return "'5.00', 5 and '5.0' all add identically"


@check
def account_arithmetic_exact_with_fractional_counts(tmp):
    path = os.path.join(tmp, "f.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.intent(client_order_id="o1", market_ticker=T, side="yes", action="buy",
                 count="0.03", price_dollars="0.0570", order_type="limit")
        i.execution(kind="partial_fill", market_ticker=T, raw={}, received_at=E.now(),
                    client_order_id="o1", side="yes", action="buy", count="0.01",
                    price_dollars="0.0570", fee_dollars="0.0001")
    s = replay.account_state_at(path)
    assert s["positions"] == {f"{T}|yes": "0.01"}, s["positions"]
    # 0.01 * 0.057 = 0.00057, plus fee 0.0001 -> -0.00067 exactly
    assert Decimal(s["cash_dollars"]) == Decimal("-0.00067"), s["cash_dollars"]
    assert s["open_orders"]["o1"]["filled"] == "0.01", s["open_orders"]
    assert Decimal(s["reserved_collateral_dollars"]) == Decimal("0.00114"), \
        s["reserved_collateral_dollars"]
    assert s["complete"] is True, s["reasons"]
    return "fractional fill arithmetic exact; reserved collateral on the unfilled remainder"


@check
def fractional_settlement_clears_position(tmp):
    path = os.path.join(tmp, "g.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.intent(client_order_id="o1", market_ticker=T, side="no", action="buy",
                 count="191.00", price_dollars="0.9380", order_type="limit")
        i.execution(kind="fill", market_ticker=T, raw={}, received_at=E.now(),
                    client_order_id="o1", side="no", action="buy", count="191.00",
                    price_dollars="0.9380", fee_dollars="0")
        i.execution(kind="settlement", market_ticker=T, raw={}, received_at=E.now(),
                    side="no", count="191.00", price_dollars="1.0000", fee_dollars="0")
    s = replay.account_state_at(path)
    assert s["positions"] == {}, s["positions"]
    # 191 * (1 - 0.938) = 11.842
    assert Decimal(s["cash_dollars"]) == Decimal("11.842"), s["cash_dollars"]
    assert s["settlements"][0]["independently_verified"] is False
    return "fractional-count settlement clears exactly; still OBSERVED only"


@check
def serialisation_stays_strict_and_deterministic(tmp):
    path = os.path.join(tmp, "h.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap())
        i.observe(dl(2, 1786293001000, "0.0570", "-0.005"))
    for line in open(path).read().splitlines():
        json.loads(line, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    ok, problems = verify(path)
    assert ok and not problems, problems
    a = replay.order_book_at(path, T)
    b = replay.order_book_at(path, T)
    assert a == b, "replay must stay deterministic"
    assert json.dumps(a, sort_keys=True), "projection must be JSON-serialisable"
    return "strict JSON preserved, chain verifies, replay deterministic and serialisable"


@check
def float_quantity_does_not_leak_binary_error(tmp):
    path = os.path.join(tmp, "i.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(yes=[["0.0570", 0.1]], no=[]))
        i.observe(dl(2, 1786293001000, "0.0570", 0.2))
    b = replay.order_book_at(path, T)
    assert b["book"]["yes"] == {"0.057": "0.3"}, b["book"]
    return "float 0.1 + 0.2 recorded as exactly 0.3, not 0.30000000000000004"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-nf1-")
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
          f"NF-1 decimal-quantity checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
