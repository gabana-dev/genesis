"""
The Hyperliquid aggressor rule.

There is exactly one thing that must not be wrong here. Every wallet-toxicity method scores
AGGRESSIVE orders, so mislabelling the taker inverts every score -- and an inverted score is
still a plausible-looking number. These checks pin the rule established from `userFills`.

Run: .venv/bin/python tests/test_hyperliquid.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import dialects  # noqa: E402
import hyperliquid as HL  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


BUYER, SELLER = "0xbuyer", "0xseller"


def trade(side):
    return {"coin": "BTC", "side": side, "px": "64000.0", "sz": "0.01",
            "tid": 1, "users": [BUYER, SELLER]}


@check
def buyer_aggresses_when_side_is_B():
    t, m = HL.taker_of(trade("B"))
    assert (t, m) == (BUYER, SELLER), (t, m)
    return "side=B -> users[0], the buyer, crossed"


@check
def seller_aggresses_when_side_is_A():
    t, m = HL.taker_of(trade("A"))
    assert (t, m) == (SELLER, BUYER), (t, m)
    return "side=A -> users[1], the seller, crossed"


@check
def the_two_cases_are_not_the_same_wallet():
    """The failure that would silently invert everything: returning a fixed slot."""
    tb, _ = HL.taker_of(trade("B"))
    ta, _ = HL.taker_of(trade("A"))
    assert tb != ta, "taker_of returns the same slot regardless of side"
    return "the taker depends on `side`, not on list position"


@check
def malformed_trades_return_nothing_rather_than_a_guess():
    assert HL.taker_of({"side": "B", "users": ["0xa"]}) == (None, None)
    assert HL.taker_of({"side": "X", "users": [BUYER, SELLER]}) == (None, None)
    assert HL.taker_of({"users": [BUYER, SELLER]}) == (None, None)
    return "one user, unknown side, or missing side all yield (None, None)"


@check
def the_dialect_claims_no_sequence():
    """
    tid is not a stream position. If a sequence were ever set here, the generic contiguity
    check would emit a gap on nearly every message -- and worse, an absence of gaps would read
    as verified continuity when the check is simply impossible.
    """
    ex = dialects.HYPERLIQUID["extract"]({"channel": "trades", "data": [trade("B")]})
    assert ex["seq_first"] is None and ex["seq_last"] is None, ex
    assert ex["channel"] == "hl_trades"
    return "no sequence claimed, so no false continuity is implied"


@check
def raw_payload_is_preserved_verbatim():
    t = trade("B")
    ex = dialects.HYPERLIQUID["extract"]({"channel": "trades", "data": [t]})
    assert ex["msg"]["data"][0] is t, "the dialect rewrote the payload"
    return "the venue's own bytes survive into the record"


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
          f"Hyperliquid aggressor checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
