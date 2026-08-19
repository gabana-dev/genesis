"""
Size-aware fill simulation. Measurement infrastructure only.

WHY THIS IS A NEW MODULE AND NOT A CHANGE TO fills.py
    `fills.py` is what EXEC-1 and BAV-1 were validated against. Changing it would silently
    alter the provenance of every result already recorded from it. It stays exactly as it is.

WHAT fills.py COULD NOT DO, AND WHY IT MATTERED
    `size_usd` appeared in exactly one operative line of it: `o.fill_size_usd = o.size_usd`.
    A label copied onto the result. It never entered queue position, never entered the fill
    condition, and there were no partial fills -- so a $1,000,000 order filled at the same
    instant as a $1,000 one. Demonstrated: a 1,000x size range produced identical reach
    (0.8833) and identical fill counts (159).

    CAP-1 was frozen against that simulator and would have returned twelve identical numbers
    with a clean kill-condition pass, readable as "no capacity constraint detected". See
    research/cap-1-blocked-size-blind-simulator.md.

THE MODEL

    An order rests at a price with `queue_ahead` of displayed size in front of it. As size
    leaves that level, the queue in front is consumed first; only once it is exhausted does
    our own order begin to fill.

        filled = clip(consumed - queue_ahead, 0, our_size)

    Full fill requires `consumed >= queue_ahead + our_size`. That single `+ our_size` is the
    whole difference from fills.py, and it is why a large order is not a small one.

THE AMBIGUITY, WHICH SIZE MAKES WORSE RATHER THAN BETTER
    The depth stream cannot distinguish a trade from a cancellation, so an observed decrease at
    our level has two readings:

      OPTIMISTIC    every decrease was a trade consuming the queue AHEAD of us.
                    Maximum fill.
      PESSIMISTIC   every decrease was a cancellation from BEHIND us. Our queue position never
                    improves, so we fill nothing.
      CERTAIN       the price traded THROUGH our level -- the level cleared and the book moved
                    past it. Everything resting there filled, including all of our size,
                    whatever the queue model.

    With size the answer is no longer a yes/no but a FILL-SIZE BRACKET
    [pessimistic, optimistic]. A larger order sits further from certainty, so the bracket
    widens with size. That is a real property of the market being measured, not a defect of
    the instrument, and it is reported as a first-class number.

MARKET IMPACT IS NOT MODELLED, AND THIS IS A CEILING
    A resting order that fills does not move the book here. At small size that is close to
    true; at size comparable to displayed depth it is optimistic. **Every result from this
    module is an UPPER BOUND on fill and therefore on the edge**, and the overshoot grows with
    size. It is stated here rather than discovered in a result.
"""

from dataclasses import dataclass, field

BUY, SELL = "buy", "sell"


@dataclass
class SizedOrder:
    """A hypothetical resting order. Supplied by the caller; nothing here chooses one."""
    order_id: str
    side: str
    size: float                          # in base units, at the posted price
    price: float

    # observed state, filled in by the simulator
    queue_ahead: float = None            # displayed size at our price when we arrived
    last_size: float = None
    consumed: float = 0.0                # cumulative observed decreases at our level
    traded_through: bool = False         # the price cleared and the book moved past it

    def observe_level(self, size_now: float):
        """
        One observation of the displayed size at our price.

        Consumption is measured against the LAST OBSERVED size, not against
        (queue_ahead - consumed). Other traders join the queue behind us and their arrival
        raises the displayed size; measuring against the original anchor would read that as
        negative consumption and silently credit us with a fill.
        """
        if self.last_size is None:
            self.last_size = size_now
            if self.queue_ahead is None:
                self.queue_ahead = size_now
            return
        if size_now < self.last_size:
            self.consumed += self.last_size - size_now
        self.last_size = size_now

    def level_cleared(self):
        """The price traded through. Everything resting filled, ours included."""
        self.traded_through = True

    # ---- the bracket -------------------------------------------------------------------

    def optimistic_fill(self) -> float:
        """Every observed decrease consumed the queue ahead of us. Maximum fill."""
        if self.traded_through:
            return self.size
        if self.queue_ahead is None:
            return 0.0
        return _clip(self.consumed - self.queue_ahead, 0.0, self.size)

    def pessimistic_fill(self) -> float:
        """
        Every observed decrease was a cancellation from behind us, so our position in the
        queue never improved and nothing of ours traded. Only a level that cleared outright
        fills us.
        """
        return self.size if self.traded_through else 0.0

    def certain_fill(self) -> float:
        """The lower bound that requires no queue assumption at all."""
        return self.size if self.traded_through else 0.0

    def bracket(self) -> dict:
        lo, hi = self.pessimistic_fill(), self.optimistic_fill()
        return {
            "order_id": self.order_id, "side": self.side, "size": self.size,
            "price": self.price,
            "queue_ahead": self.queue_ahead, "consumed": self.consumed,
            "traded_through": self.traded_through,
            "pessimistic_fill": lo,
            "optimistic_fill": hi,
            "certain_fill": self.certain_fill(),
            # Reported as a first-class number: it IS the cost of not recording trades.
            "ambiguity": hi - lo,
            "ambiguity_fraction": (hi - lo) / self.size if self.size > 0 else 0.0,
            "fully_filled_optimistic": hi >= self.size,
            "partial": 0.0 < hi < self.size,
        }


def _clip(x, lo, hi):
    return lo if x < lo else (hi if x > hi else x)


# ---------------------------------------------------------------------------------------
# Depth-relative sizing
# ---------------------------------------------------------------------------------------

def depth_ratio(order_size: float, displayed_depth: float):
    """
    Our order as a fraction of the depth already resting at that price.

    K4 of CAP-1 anticipated this and called it "partially fillable". A ratio above 1 means we
    are larger than everything in front of us, so the level must be consumed more than twice
    over before we are done -- and the market-impact ceiling in the module docstring binds
    hardest exactly there.
    """
    if displayed_depth is None or displayed_depth <= 0:
        return None
    return order_size / displayed_depth


def classify_size(order_size: float, displayed_depth: float) -> str:
    r = depth_ratio(order_size, displayed_depth)
    if r is None:
        return "unknown_depth"
    if r <= 0.1:
        return "small"          # impact assumption roughly safe
    if r <= 1.0:
        return "material"       # impact unmodelled and starting to matter
    return "dominant"           # larger than the resting queue; the ceiling binds hard


# ---------------------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------------------

def summarise(orders) -> dict:
    """
    Aggregate a set of resolved orders.

    Fill RATE is reported in base units rather than in order counts, because with partial
    fills an order is no longer a yes/no. Counting orders would report a 1% fill and a 100%
    fill as the same event, which is exactly the blindness this module exists to remove.
    """
    import statistics as st

    n = len(orders)
    if n == 0:
        return {"n_orders": 0}
    brs = [o.bracket() for o in orders]
    requested = sum(b["size"] for b in brs)
    opt = sum(b["optimistic_fill"] for b in brs)
    pes = sum(b["pessimistic_fill"] for b in brs)
    amb = [b["ambiguity_fraction"] for b in brs]
    return {
        "n_orders": n,
        "requested_size": requested,
        "optimistic_filled_size": opt,
        "pessimistic_filled_size": pes,
        "fill_rate_upper_bound": opt / requested if requested else None,
        "fill_rate_lower_bound": pes / requested if requested else None,
        "median_ambiguity_fraction": st.median(amb),
        "n_partial_optimistic": sum(1 for b in brs if b["partial"]),
        "n_traded_through": sum(1 for b in brs if b["traded_through"]),
        "note": ("fill rates are in BASE UNITS, not order counts, because partial fills make "
                 "an order-count rate meaningless. Market impact is not modelled, so both "
                 "bounds are ceilings and the overshoot grows with size."),
    }
