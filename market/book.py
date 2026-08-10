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


class Book:
    """
    A live order book kept in float form, with the best price cached.

    The recorder's canonical decimal strings are the record; this is a working view of them.
    Conversion happens once per LEVEL UPDATE rather than once per query, which is the whole
    point: a frame touches a handful of levels but the book holds ~4,800 of them, so
    re-parsing on read costs three orders of magnitude more than re-parsing on write.

    Prices are rounded to 8dp on both insertion and lookup so that a price computed
    arithmetically (best - n*tick) lands on the same key as one parsed from the venue.
    """

    __slots__ = ("bids", "asks", "_bb", "_ba")

    def __init__(self):
        self.bids, self.asks = {}, {}
        self._bb = self._ba = None

    def clear(self):
        self.bids.clear()
        self.asks.clear()
        self._bb = self._ba = None

    def set(self, side, price, size):
        levels = self.bids if side == "bids" else self.asks
        p = round(price, 8)
        if size <= 0:
            if levels.pop(p, None) is not None:
                # Only invalidate when the level removed WAS the best; otherwise the cache
                # is still correct and recomputing would cost a full scan.
                if side == "bids" and p == self._bb:
                    self._bb = None
                elif side == "asks" and p == self._ba:
                    self._ba = None
            return
        levels[p] = size
        if side == "bids":
            if self._bb is not None and p > self._bb:
                self._bb = p
        elif self._ba is not None and p < self._ba:
            self._ba = p

    @property
    def best_bid(self):
        if self._bb is None and self.bids:
            self._bb = max(self.bids)
        return self._bb

    @property
    def best_ask(self):
        if self._ba is None and self.asks:
            self._ba = min(self.asks)
        return self._ba

    def size_at(self, side, price):
        """O(1). Notional at a price level, in quote currency."""
        p = round(price, 8)
        q = (self.bids if side == "bids" else self.asks).get(p)
        return q * p if q else 0.0

    def ready(self):
        return bool(self.bids) and bool(self.asks)


def stream(path, market, every_ms=1000, complete_only=True):
    """
    Stream the log, yielding (received_at, Book) at most every `every_ms`.

    The Book is LIVE and reused between yields -- it is never copied, because copying ~4,800
    levels per frame dominated everything else. A consumer that needs to retain a frame must
    copy it deliberately.

    `complete_only` restricts sampling to intervals the recorder itself vouches for. BAV-1
    established that this label predicts agreement with an independent channel, so applying it
    here is using a measured property, not an assumption.
    """
    fast = Book()
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
            fast.clear()
            for side in ("bids", "asks"):
                for price, size in canon.get(side) or []:
                    v = float(size)
                    if v > 0:
                        fast.set(side, float(price), v)
        elif typ == DEPTH:
            for side in ("bids", "asks"):
                for price, size in canon.get(side) or []:
                    fast.set(side, float(price), float(size))
        else:
            continue

        if complete_only and not complete:
            continue
        if not fast.ready():
            continue

        t = replay._ts(ev)          # Genesis receipt time, never venue time
        ms = _ms(t)
        if last_emit is not None and ms - last_emit < every_ms:
            continue
        last_emit = ms
        yield t, fast


def walk(path, market, every_ms=1000, complete_only=True):
    """
    Compatibility view over `stream`: yields (received_at, bids, asks) as plain float-keyed
    dicts. One book implementation, two views -- two implementations of one idea always drift,
    which is the lesson `completeness.py` was consolidated to record.
    """
    for t, b in stream(path, market, every_ms, complete_only):
        yield t, b.bids, b.asks


_TS_CACHE = {}


def _ms(iso):
    from datetime import datetime
    v = _TS_CACHE.get(iso)
    if v is None:
        if len(_TS_CACHE) > 4096:
            _TS_CACHE.clear()
        v = _TS_CACHE[iso] = datetime.fromisoformat(iso).timestamp() * 1000.0
    return v


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
