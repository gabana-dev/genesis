"""
Fill simulator. Measurement infrastructure only.

WHAT THIS IS
    Given a hypothetical resting order, replay Genesis's own recorded order book and answer
    what would have happened to it: where it would have been posted after latency, whether the
    market reached it, whether it filled, how much, what the market did around the fill, and
    how much of the maker fee advantage adverse selection took back.

WHAT THIS IS NOT
    It generates no signal, chooses no price, sizes no position, optimises nothing and computes
    no strategy P&L. Every order it evaluates is supplied by the caller. It answers "what would
    have happened to this order", never "which order should we place".

THE CENTRAL LIMITATION, STATED BEFORE ANY RESULT
    The recording carries the DEPTH stream only -- no trades. So when the displayed size at a
    price level falls, Genesis cannot tell whether it was consumed by a trade or withdrawn by a
    cancellation. Queue position depends on exactly that distinction.

    This is not resolved by assumption. Every fill is reported in three states:

      CERTAIN      price traded through our level -- the level was cleared and the book moved
                   past it. Our order filled under any queue model.
      OPTIMISTIC   every observed size decrease at our level consumed queue AHEAD of us.
                   An upper bound on fill probability.
      PESSIMISTIC  every observed size decrease was a cancellation from BEHIND us, so our
                   queue position never improved. A lower bound.

    The truth lies between OPTIMISTIC and PESSIMISTIC, and the gap between them is the cost of
    not recording trades. It is reported as a first-class number rather than buried.

    Adding an @aggTrade subscription to the recorder would collapse this ambiguity. The 7-day
    recording currently running does not have it.

LATENCY
    Applied in both directions and never merged with venue time. A decision made at t is based
    on the book as of t; the order reaches the venue at t + latency and takes the queue as it
    exists then. The gap between the two is itself a measured cost.

ADVERSE SELECTION
    Measured as markout: the mid price at t_fill + h, against the fill price, signed so that
    positive means the fill was good. A resting bid fills disproportionately when the price is
    about to fall, so the expected markout is negative. That loss is compared directly against
    the maker fee advantage it is supposed to pay for.
"""

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(__file__))

import book as bk  # noqa: E402

BUY, SELL = "buy", "sell"

# Binance USD-M futures, taker 0.05% / maker 0.02% per side. The ADVANTAGE of resting rather
# than crossing is the difference, per side. Fees are a venue fact, recorded with the date.
MAKER_FEE, TAKER_FEE = 0.0002, 0.0005
MAKER_ADVANTAGE = TAKER_FEE - MAKER_FEE          # 0.0003 = 3 bps per side
FEES_AS_OF = "2026-08-10"

MEASURED_LATENCY_MS = 291.0                      # floor, Nairobi -> Binance (BAV-1)


@dataclass
class Order:
    """A hypothetical resting order. Supplied by the caller; never chosen here."""
    order_id: str
    side: str
    size_usd: float
    decided_at_ms: float
    price: float = None                  # absolute, or None to use offset_ticks from touch
    offset_ticks: int = 0                # 0 = join the touch, 1 = one tick behind, etc.
    tick: float = 0.01
    ttl_ms: float = 60_000.0

    # filled in by the simulator
    arrives_at_ms: float = None
    posted_price: float = None
    intended_price: float = None
    queue_ahead: float = None
    consumed: float = 0.0                # cumulative observed size decreases at our level
    last_size: float = None              # last observed size at our level
    reached: bool = False
    reached_at_ms: float = None
    outcome: str = "pending"             # pending|expired|certain|optimistic_only|never_reached
    fill_price: float = None
    fill_at_ms: float = None
    fill_size_usd: float = 0.0
    markouts: dict = field(default_factory=dict)
    mid_at_decision: float = None
    mid_at_post: float = None
    mid_before_fill: float = None


def _mid(b):
    return (b.best_bid + b.best_ask) / 2.0


def simulate(path, market, orders, latency_ms=MEASURED_LATENCY_MS,
             markout_ms=(1_000, 10_000, 60_000), every_ms=0, instrument=None):
    """
    Single pass over the recorded book, tracking every supplied order to resolution.

    `orders` is a list of Order, each with `decided_at_ms` set. Nothing here decides when or
    at what price to post -- the caller does, and the caller is not this module.

    `instrument` selects one venue from a log holding several (D-6). Left None it is a no-op
    and EXEC-1's and CAP-2's behaviour is bit-identical, which tests/test_book_instrument.py
    asserts -- their published results depend on it.
    """
    orders = sorted(orders, key=lambda o: o.decided_at_ms)
    pending = list(orders)
    live = []
    filled = []
    max_markout = max(markout_ms)

    for t_iso, b in bk.stream(path, market, every_ms=every_ms, instrument=instrument):
        t = bk._ms(t_iso)
        mid = _mid(b)

        # decisions: record what the strategy WOULD have seen, then put the order in flight
        while pending and pending[0].decided_at_ms <= t:
            o = pending.pop(0)
            o.mid_at_decision = mid
            touch = b.best_bid if o.side == BUY else b.best_ask
            o.intended_price = (o.price if o.price is not None else
                                round(touch - o.offset_ticks * o.tick
                                      * (1 if o.side == BUY else -1), 8))
            o.arrives_at_ms = o.decided_at_ms + latency_ms
            live.append(o)

        for o in list(live):
            if o.posted_price is None:
                if t < o.arrives_at_ms:
                    continue
                # ARRIVAL. The book has moved during the flight; the order takes the queue as
                # it exists now, at the price it was told to post at.
                o.posted_price = o.intended_price
                o.mid_at_post = mid
                o.queue_ahead = b.size_at("bids" if o.side == BUY else "asks", o.posted_price)
                o.last_size = o.queue_ahead
                continue

            side_key = "bids" if o.side == BUY else "asks"
            here = b.size_at(side_key, o.posted_price)

            # Did the market reach our price? For a resting bid, the opposing best must come
            # down to our level. Cached best -- O(1), not a scan over ~4,800 levels.
            best_opp = b.best_ask if o.side == BUY else b.best_bid
            crossed = (best_opp <= o.posted_price) if o.side == BUY else (best_opp >= o.posted_price)
            if crossed and not o.reached:
                o.reached, o.reached_at_ms = True, t

            # CERTAIN fill: the level is gone and the book has moved past it.
            best_same = b.best_bid if o.side == BUY else b.best_ask
            traded_through = (best_same < o.posted_price) if o.side == BUY else \
                             (best_same > o.posted_price)
            if here == 0.0 and traded_through:
                _fill(o, t, mid, "certain")
                live.remove(o)
                filled.append(o)
                continue

            # Queue consumption, ambiguous by construction. Decreases are accumulated against
            # the LAST OBSERVED size, not against (queue_ahead - consumed): other traders join
            # behind us, and a refill would otherwise mask every subsequent decrease.
            if here < o.last_size:
                o.consumed += o.last_size - here
            o.last_size = here
            if o.consumed >= o.queue_ahead > 0 and o.reached:
                _fill(o, t, mid, "optimistic_only")
                live.remove(o)
                filled.append(o)
                continue

            if t - o.arrives_at_ms > o.ttl_ms:
                o.outcome = "expired" if o.reached else "never_reached"
                o.mid_before_fill = mid
                live.remove(o)

        # markouts for already-filled orders
        for o in filled:
            for h in markout_ms:
                key = f"{h}ms"
                if key not in o.markouts and t >= o.fill_at_ms + h:
                    signed = (mid - o.fill_price) if o.side == BUY else (o.fill_price - mid)
                    o.markouts[key] = signed / o.fill_price
        filled = [o for o in filled
                  if len(o.markouts) < len(markout_ms)
                  and t < o.fill_at_ms + max_markout + 1]

    # The recording ends. An order still live never resolved, and saying so is the honest
    # outcome -- leaving it "pending" would let an unresolved order vanish from every count.
    for o in pending + live:
        if o.outcome == "pending":
            o.outcome = "unresolved_at_end_of_recording" if o.posted_price else "never_posted"
    return orders


def _fill(o, t, mid, kind):
    o.outcome = kind
    o.fill_at_ms = t
    o.fill_price = o.posted_price
    o.fill_size_usd = o.size_usd
    o.mid_before_fill = mid


def summarise(orders, markout_ms=(1_000, 10_000, 60_000)):
    """
    Aggregate. Reports the fill bracket explicitly -- CERTAIN is the lower bound on fills and
    CERTAIN+OPTIMISTIC is the upper; the gap is what the missing trade stream costs.
    """
    import statistics as st

    n = len(orders)
    certain = [o for o in orders if o.outcome == "certain"]
    optimistic = [o for o in orders if o.outcome == "optimistic_only"]
    reached = [o for o in orders if o.reached]
    posted = [o for o in orders if o.posted_price is not None]

    slip = [abs(o.posted_price - o.mid_at_decision) / o.mid_at_decision
            for o in posted if o.mid_at_decision]
    latency_move = [abs(o.mid_at_post - o.mid_at_decision) / o.mid_at_decision
                    for o in posted if o.mid_at_post and o.mid_at_decision]

    out = {
        "n_orders": n,
        "n_posted": len(posted),
        "n_reached": len(reached),
        "reach_rate": len(reached) / n if n else None,
        "fills_certain": len(certain),
        "fills_optimistic_extra": len(optimistic),
        "fill_rate_lower_bound": len(certain) / n if n else None,
        "fill_rate_upper_bound": (len(certain) + len(optimistic)) / n if n else None,
        "ambiguity_width": len(optimistic) / n if n else None,
        "median_mid_move_during_latency": st.median(latency_move) if latency_move else None,
        "median_post_vs_decision_mid": st.median(slip) if slip else None,
        "markout": {}, "adverse_selection": {},
        "maker_advantage_per_side": MAKER_ADVANTAGE, "fees_as_of": FEES_AS_OF,
    }

    for pool, label in ((certain, "certain"), (certain + optimistic, "certain_plus_optimistic")):
        out["markout"][label] = {}
        for h in markout_ms:
            key = f"{h}ms"
            vals = [o.markouts[key] for o in pool if key in o.markouts]
            if not vals:
                continue
            med = st.median(vals)
            out["markout"][label][key] = {
                "n": len(vals), "median": med, "mean": st.fmean(vals),
                "median_bps": med * 1e4,
                "fraction_negative": sum(1 for v in vals if v < 0) / len(vals),
            }
        # The question the contract asks: how much of the fee advantage survives?
        longest = f"{max(markout_ms)}ms"
        m = out["markout"][label].get(longest)
        if m:
            loss = -m["median"]                      # positive when markout is adverse
            out["adverse_selection"][label] = {
                "horizon": longest,
                "median_adverse_move": loss,
                "median_adverse_bps": loss * 1e4,
                "maker_advantage_bps": MAKER_ADVANTAGE * 1e4,
                "fraction_of_advantage_lost": loss / MAKER_ADVANTAGE,
                "advantage_survives": loss < MAKER_ADVANTAGE,
            }
    return out
