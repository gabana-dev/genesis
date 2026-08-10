"""
Spread and slippage from Genesis's own recordings (MEASURE-1 sections 4C, 4D, 4E).

Reuses the recorder's reconstruction semantics rather than re-implementing them: absolute
level assignment, size 0 removes the level, canonical decimal prices, and the same
anti-circularity rule that keeps BAV-1 comparison probes out of the book they were used to
evaluate. What is new here is only that the walk STREAMS -- `replay.order_book_at` re-reads
the whole log for a single timestamp, which is O(n) per sample and unusable for a sweep.

Slippage (4D) is arithmetic on observed depth, not a simulation. It answers "what would a
market order of size Q have paid against the book as recorded" and nothing more. In
particular it assumes the book is available at the recorded instant, which it is not -- by
~291 ms. That gap is a Q3 question and is out of scope for MEASURE-1 (contract section 1).
"""

import os
import sys
from collections import defaultdict
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import completeness as C  # noqa: E402
import events as E  # noqa: E402
import replay  # noqa: E402
from log import read  # noqa: E402

DEPTH, DEPTH_SNAP = "depthUpdate", "depthSnapshot"


def walk(path, market, every_ms=1000, complete_only=True):
    """
    Stream the log, yielding (received_at, bids, asks) snapshots at most every `every_ms`.

    `complete_only` restricts sampling to intervals the recorder itself vouches for. BAV-1
    established that this label predicts agreement with an independent channel, so applying it
    here is using a measured property, not an assumption.
    """
    book = {"bids": defaultdict(lambda: Decimal("0")), "asks": defaultdict(lambda: Decimal("0"))}
    rule = C.CompletenessRule()
    complete = False
    last_emit = None

    for ev in read(path):
        outcome = rule.observe(ev)
        if C.affects(outcome, market):
            complete = False
        elif outcome["restores"] in (market, C.ALL) and outcome["restores"] is not None:
            complete = True

        if ev["event_class"] != E.WORLD:
            continue
        body = ev.get("body", {})
        world = body.get("world", {})
        request = body.get("observation", {}).get("request") or {}
        if request.get("probe_id"):                      # anti-circularity
            continue
        named = world.get("market_ticker")
        if named != market and not (named is None and request.get("symbol") == market):
            continue

        typ = ev["event_type"]
        msg = (world.get("raw") or {}).get("msg") or {}
        canon = world.get("canonical") or E.canonical_view(typ, msg)
        if canon.get("invalid"):
            continue

        if typ == DEPTH_SNAP:
            book = {"bids": defaultdict(lambda: Decimal("0")),
                    "asks": defaultdict(lambda: Decimal("0"))}
            for side in ("bids", "asks"):
                for price, size in canon.get(side) or []:
                    v = E.to_decimal(size)
                    if v > 0:
                        book[side][price] = v
        elif typ == DEPTH:
            for side in ("bids", "asks"):
                for price, size in canon.get(side) or []:
                    v = E.to_decimal(size)
                    if v <= 0:
                        book[side].pop(price, None)
                    else:
                        book[side][price] = v
        else:
            continue

        if complete_only and not complete:
            continue
        if not (book["bids"] and book["asks"]):
            continue

        t = replay._ts(ev)          # Genesis receipt time, never venue time
        ms = _ms(t)
        if last_emit is not None and ms - last_emit < every_ms:
            continue
        last_emit = ms
        yield t, dict(book["bids"]), dict(book["asks"])


def _ms(iso):
    from datetime import datetime
    return datetime.fromisoformat(iso).timestamp() * 1000.0


def best(bids, asks):
    bb = max(float(p) for p in bids)
    ba = min(float(p) for p in asks)
    return bb, ba


def spread(bids, asks):
    """Absolute and fractional spread against the mid."""
    bb, ba = best(bids, asks)
    mid = (bb + ba) / 2.0
    return {"bid": bb, "ask": ba, "mid": mid, "abs": ba - bb, "frac": (ba - bb) / mid}


def sweep_cost(levels, notional_usd, side):
    """
    Walk one side of the book for `notional_usd` and return the volume-weighted execution
    price and the slippage against the touch.

    Returns None when the recorded depth is insufficient -- reported as insufficient, never
    extrapolated. Extrapolating past the last recorded level would invent liquidity.
    """
    order = sorted(((float(p), float(q)) for p, q in levels.items()),
                   reverse=(side == "bids"))
    touch = order[0][0]
    spent = filled = 0.0
    for price, qty in order:
        avail = price * qty
        take = min(avail, notional_usd - spent)
        if take <= 0:
            break
        spent += take
        filled += take / price
        if spent >= notional_usd - 1e-9:
            break
    if spent < notional_usd - 1e-9:
        return None                                   # depth exhausted
    vwap = spent / filled
    slip = (vwap - touch) / touch if side == "asks" else (touch - vwap) / touch
    return {"vwap": vwap, "touch": touch, "slippage_frac": slip, "levels_used": len(order)}


def round_trip_impact(bids, asks, notional_usd):
    """
    Cost of buying then selling `notional_usd` immediately, as a fraction, EXCLUDING fees.
    This is the spread + impact terms of `c = fees + spread + impact` (contract section 3).
    """
    buy = sweep_cost(asks, notional_usd, "asks")
    sell = sweep_cost(bids, notional_usd, "bids")
    if buy is None or sell is None:
        return None
    mid = (buy["touch"] + sell["touch"]) / 2.0
    return (buy["vwap"] - sell["vwap"]) / mid
