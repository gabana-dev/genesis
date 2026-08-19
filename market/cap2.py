"""
CAP-2: the declared grid from CONTRACT-capacity-2.md, run against the size-aware instrument.

Contract frozen 2026-08-19 at sha256
9b06777e0071e750155b8d4fb95b02c55853524ad07d675b3bb0312a7c26d5df.

This module chooses nothing. Sizes, offsets, latency, TTL and decision times are copied from
the contract, which copied all but the size from CAP-1, which copied it from EXEC-1.

WHY THE REPLAY LOOP IS HERE AND NOT REUSED FROM fills.py
    `fills.simulate` resolves an order the moment `consumed >= queue_ahead` and then removes it
    -- correct for a size-blind model, wrong here, because that is exactly the instant our own
    size STARTS filling rather than finishes. A sized order must keep observing the level until
    it is fully filled, expires, or the level clears.

    `fills.py` is not modified: EXEC-1 and BAV-1 were validated against it.

UNITS -- D-CAP2-1, AND THE REASON THIS DOCSTRING ONCE SAID THE OPPOSITE
    `book.size_at()` returns **notional in quote currency**: it computes `q * p` internally.
    Order size must therefore be carried in NOTIONAL too. `SizedOrder` is unit-agnostic -- it
    only requires that `size` and the values passed to `observe_level` share a unit.

    The first version of this module converted the grid's notional to base units at post time
    (`size_usd / price`) and compared that against the book's notional. Every order was
    therefore ~64,000x too small: a $1,000,000 order was simulated as $15.60. Fill rate came
    out near-identical across a 1,000x size range, and BOTH kill conditions passed -- K2's
    anchor because reach does not depend on size, and K3 because a 0.005 spread of pure
    floating-point and rounding noise cleared its 0.001 threshold.

    K3 tests whether the INSTRUMENT is size-blind. It cannot test whether the CALLER handed it
    the wrong units, and it did not. Recorded in research/cap-2-units-defect.md.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import book as bk  # noqa: E402
import exec1 as X  # noqa: E402
import sized_fills as SF  # noqa: E402

CONTRACT = "market/CONTRACT-capacity-2.md"
CONTRACT_SHA256 = "9b06777e0071e750155b8d4fb95b02c55853524ad07d675b3bb0312a7c26d5df"

# Section 4. CAP-1's grid, with the TTL stated outright rather than inheriting D-C1.
SIZES_USD = (1_000.0, 10_000.0, 100_000.0, 1_000_000.0)
OFFSET_TICKS = X.OFFSET_TICKS               # (0, 1, 5)
SIDES = X.SIDES                             # ("buy", "sell")
TICK = X.TICK
LATENCY_MS = 291.0
TTL_MS = 300_000.0                          # EXEC-1's actual value
DECISION_EVERY_MS = X.DECISION_EVERY_MS
BOOK_SAMPLE_MS = X.BOOK_SAMPLE_MS

ANCHOR_SIZE_USD = 10_000.0
EXEC1_REACH_RATE = 0.6529                   # K2
ANCHOR_TOLERANCE = 0.05
MIN_ORDERS = 200                            # K1
SIZE_BLIND_EPS = 0.001                      # K3

DECLARED_CELLS = len(SIZES_USD) * len(OFFSET_TICKS)   # 12


class Resting(SF.SizedOrder):
    """A SizedOrder plus the flight and lifecycle state the replay needs."""

    def __init__(self, order_id, side, size_usd, offset_ticks, decided_at_ms):
        super().__init__(order_id=order_id, side=side, size=0.0, price=None)
        self.size_usd = size_usd
        self.offset_ticks = offset_ticks
        self.decided_at_ms = decided_at_ms
        self.arrives_at_ms = None
        self.intended_price = None
        self.reached = False
        self.expired = False
        self.depth_at_post = None
        self.resolved = False


def build_orders(start_ms, end_ms):
    out = []
    for t in X.decision_times(start_ms, end_ms, DECISION_EVERY_MS):
        for size in SIZES_USD:
            for side in SIDES:
                for off in OFFSET_TICKS:
                    out.append(Resting(f"{int(size)}|{side}|{off}|{int(t)}",
                                       side, size, off, t))
    return out


def simulate(path, market, orders, every_ms=BOOK_SAMPLE_MS):
    """
    One pass over the recorded book.

    Differs from fills.simulate in exactly one way that matters: an order is not resolved when
    the queue ahead clears. That is when it BEGINS to fill. It keeps observing until fully
    filled, expired, or the level clears outright.
    """
    orders = sorted(orders, key=lambda o: o.decided_at_ms)
    pending, live = list(orders), []

    for t_iso, b in bk.stream(path, market, every_ms=every_ms):
        t = bk._ms(t_iso)

        while pending and pending[0].decided_at_ms <= t:
            o = pending.pop(0)
            touch = b.best_bid if o.side == SF.BUY else b.best_ask
            if touch is None:
                continue
            o.intended_price = round(
                touch - o.offset_ticks * TICK * (1 if o.side == SF.BUY else -1), 8)
            o.arrives_at_ms = o.decided_at_ms + LATENCY_MS
            live.append(o)

        for o in list(live):
            side_key = "bids" if o.side == SF.BUY else "asks"

            if o.price is None:
                if t < o.arrives_at_ms:
                    continue
                # ARRIVAL. Size stays in NOTIONAL, because that is what size_at returns.
                # See D-CAP2-1 in the module docstring.
                o.price = o.intended_price
                o.size = o.size_usd
                depth = b.size_at(side_key, o.price)
                o.depth_at_post = depth
                o.observe_level(depth)          # sets queue_ahead and last_size
                continue

            here = b.size_at(side_key, o.price)

            best_opp = b.best_ask if o.side == SF.BUY else b.best_bid
            if best_opp is not None:
                crossed = (best_opp <= o.price) if o.side == SF.BUY else (best_opp >= o.price)
                if crossed:
                    o.reached = True

            best_same = b.best_bid if o.side == SF.BUY else b.best_ask
            if best_same is not None:
                through = (best_same < o.price) if o.side == SF.BUY else (best_same > o.price)
                if here == 0.0 and through:
                    o.level_cleared()
                    o.resolved = True
                    live.remove(o)
                    continue

            o.observe_level(here)

            # Resolve only when OUR OWN size is exhausted, not when the queue ahead clears.
            if o.reached and o.optimistic_fill() >= o.size > 0:
                o.resolved = True
                live.remove(o)
                continue

            if t - o.arrives_at_ms > TTL_MS:
                o.expired = True
                o.resolved = True
                live.remove(o)

    for o in pending + live:
        o.expired = o.price is not None
    return orders


def cell_key(o):
    return f"{int(o.size_usd)}|{o.offset_ticks}"


def report(orders):
    posted = [o for o in orders if o.price is not None]
    cells = {}
    for o in posted:
        cells.setdefault(cell_key(o), []).append(o)

    out = {"contract": CONTRACT, "contract_sha256": CONTRACT_SHA256,
           "grid": {"sizes_usd": list(SIZES_USD), "offsets": list(OFFSET_TICKS),
                    "latency_ms": LATENCY_MS, "ttl_ms": TTL_MS,
                    "declared_cells": DECLARED_CELLS},
           "n_orders": len(orders), "n_posted": len(posted), "cells": {}}

    for key, os_ in sorted(cells.items()):
        s = SF.summarise(os_)
        enough = len(os_) >= MIN_ORDERS
        ratios = [SF.depth_ratio(o.size, o.depth_at_post) for o in os_]
        ratios = [r for r in ratios if r is not None]
        classes = [SF.classify_size(o.size, o.depth_at_post) for o in os_]
        import statistics as st
        out["cells"][key] = {
            "n_orders": len(os_),
            "sufficient": enough,
            "excluded_reason": None if enough else f"K1: {len(os_)} against {MIN_ORDERS}",
            "reach_rate": sum(1 for o in os_ if o.reached) / len(os_),
            "fill_rate_upper_bound": s["fill_rate_upper_bound"],
            "fill_rate_lower_bound": s["fill_rate_lower_bound"],
            "median_ambiguity_fraction": s["median_ambiguity_fraction"],
            "n_partial_optimistic": s["n_partial_optimistic"],
            "n_traded_through": s["n_traded_through"],
            "median_depth_ratio": st.median(ratios) if ratios else None,
            "dominant_fraction": classes.count("dominant") / len(classes) if classes else None,
            "size_class_counts": {c: classes.count(c) for c in set(classes)},
        }

    # ---- kill conditions, checked here so no result can be read without them ----
    by_size = {}
    for key, c in out["cells"].items():
        if c["sufficient"] and c["fill_rate_upper_bound"] is not None:
            by_size.setdefault(int(key.split("|")[0]), []).append(c["fill_rate_upper_bound"])
    means = {s: sum(v) / len(v) for s, v in by_size.items()}

    # K3 -- the exact failure that blocked CAP-1, checked rather than assumed fixed.
    #
    # "COULD NOT CHECK" IS NOT "FAILED". With fewer than two sufficient size groups there is
    # no spread to measure, and reporting size-blindness then would void a run for having too
    # little data rather than for the defect K3 exists to catch. health.py learned this the
    # hard way: it once "verified" 3.4 GB in 0.3 seconds while reading nothing.
    if len(means) < 2:
        out["K3_size_blind"] = {
            "fill_rate_by_size": means, "spread": None,
            "evaluable": False,
            "reason": "fewer than two size groups met K1; there is no spread to measure",
            "instrument_still_size_blind": None,
        }
    else:
        spread = max(means.values()) - min(means.values())
        out["K3_size_blind"] = {
            "fill_rate_by_size": means, "spread": spread, "evaluable": True,
            "instrument_still_size_blind": bool(spread < SIZE_BLIND_EPS),
            "consequence": ("K3: if size-blind, the run is VOID and no cell may be "
                            "interpreted -- this is the failure that blocked CAP-1"),
        }

    # K2 -- the anchor.
    anchor = [c for k, c in out["cells"].items()
              if k.startswith(f"{int(ANCHOR_SIZE_USD)}|") and c["sufficient"]]
    obs = (sum(c["reach_rate"] for c in anchor) / len(anchor)) if anchor else None
    out["K2_anchor"] = {
        "expected_reach_rate": EXEC1_REACH_RATE, "observed": obs,
        "tolerance": ANCHOR_TOLERANCE,
        # Same distinction as K3: an absent anchor is unevaluable, not failed.
        "evaluable": obs is not None,
        "passes": (None if obs is None
                   else bool(abs(obs - EXEC1_REACH_RATE) <= ANCHOR_TOLERANCE)),
        "reason": None if obs is not None else "no $10,000 cell met K1",
        "consequence": "K2: if the anchor FAILS the re-simulation is defective and nothing "
                       "else is interpreted; if it is UNEVALUABLE that is a data shortfall, "
                       "not a defect",
    }
    return out


def run(path, market, start_ms, end_ms, every_ms=BOOK_SAMPLE_MS):
    orders = build_orders(start_ms, end_ms)
    simulate(path, market, orders, every_ms=every_ms)
    return orders, report(orders)
