"""
Cascade depth: if forced flow of size S hits at price P, where does it stop?

Nobody sells this. Every liquidation product on the market shows WHERE clusters sit and stops
there -- Coinglass's own documentation calls its heatmap a probability map and attaches no
probability, and no provider checked (Tardis, QuickNode, 0xArchive, PurrData, HyperTracker,
HyperPerps) publishes how far a cascade would travel.

WHAT THIS DOES NOT INVENT
    The book walk is `book.sweep_cost`, built for MEASURE-1's cost model and already tested. It
    returns None when recorded depth is exhausted rather than extrapolating past the last level,
    which is the single most important property here: a cascade model that invents liquidity
    beyond the book produces a comfortable number and a false one.

WHAT IS NEW
    Two things on top of that primitive:

      1. ITERATION. Sweeping to depth d may drag in clusters between the start price and d.
         Those add forced size, which sweeps further, which may drag in more. A fixed point.
      2. EVAPORATION. The book does not stand still while this happens. Depth is scaled down as
         the move grows, using the factor measured from three years of Binance bookDepth.

    Both are declared parameters, never hidden constants.

THE ASSUMPTION THIS CARRIES
    Evaporation is calibrated on Binance and applied to Hyperliquid. That is untested and
    load-bearing -- see research/ASSUMPTION-binance-physics-may-not-transfer.md. `hl2` is
    recording Hyperliquid book depth to settle it. Until it does, any Hyperliquid cascade figure
    must be reported with that caveat on its face.

REPORTED AS A BRACKET, NEVER A POINT
    Following sized_fills, which treats the gap between optimistic and pessimistic as a
    first-class number rather than something to average away. A cascade depth of "1.1% to 1.9%"
    is honest; "1.4%" is a guess wearing a decimal point.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import book as BK  # noqa: E402

MAX_ROUNDS = 20          # a fixed point that has not converged in 20 rounds has diverged

# MEASURED, not assumed. Binance USD-M BTCUSDT, 1,324 days, 3,733,943 snapshots, 0 missing.
# research/evaporation-result.md; finding F-0002.
#
# Depth after / depth before in the near book (+/-0.2-1%) during the LARGEST move bucket, with
# the p25 as the stressed case. Horizon matters more than expected: liquidity leaves over
# minutes, not on impact, so a fast cascade meets a nearly full book and a slow one does not.
#
#   horizon   quiet    median (large move)   p25
#   1m        1.0003   0.9773                0.8700
#   5m        1.0015   0.8462                0.6573
#   15m       1.0030   0.8586                0.6646
#
# CARRIES F-0006: measured on Binance, applied to Hyperliquid is ASSUMED and untested.
EVAPORATION = {
    1:  {"quiet": 1.000, "stress": 0.9773, "tail": 0.8700},
    5:  {"quiet": 1.000, "stress": 0.8462, "tail": 0.6573},
    15: {"quiet": 1.000, "stress": 0.8586, "tail": 0.6646},
}


def evaporation_for(horizon_min, case="stress"):
    """
    Measured depth ratio for a horizon. Raises rather than interpolating an unmeasured horizon --
    inventing a number between measured ones is how a calibration becomes a guess.
    """
    if horizon_min not in EVAPORATION:
        raise ValueError(f"no measurement at {horizon_min}m; have {sorted(EVAPORATION)}")
    return EVAPORATION[horizon_min][case]


def clusters_between(clusters, lo, hi):
    """Forced notional with a trigger price in (lo, hi]. `clusters` is [(price, notional), ...]."""
    return sum(n for p, n in clusters if lo < p <= hi)


def sweep_to_price(levels, notional_usd, side, evaporation=1.0):
    """
    Walk the ladder and return BOTH the last price touched and the volume-weighted price.

    THE DISTINCTION IS THE WHOLE MODEL. `book.sweep_cost` returns VWAP, which is the right
    answer for execution COST and the wrong one for cascade REACH:

        sweeping $5,000 through a ladder from 100 gives vwap 97.94 but touches 95

    Further liquidations trigger at the price the market actually reached, not at the average
    paid to get there. Using vwap as the reach understates every cascade -- in the comforting
    direction, which is the one to be suspicious of.

    `book.sweep_cost` is left untouched: it is tested, it is used by MEASURE-1's cost model, and
    it answers its own question correctly.
    """
    order = sorted(((float(p), float(q) * evaporation) for p, q in levels.items()),
                   reverse=(side == "bids"))
    spent = filled = 0.0
    last = order[0][0]
    for price, qty in order:
        avail = price * qty
        take = min(avail, notional_usd - spent)
        if take <= 0:
            break
        spent += take
        filled += take / price
        last = price
        if spent >= notional_usd - 1e-9:
            break
    if spent < notional_usd - 1e-9:
        return None
    return {"last_price": last, "vwap": spent / filled, "touch": order[0][0]}


def sweep_with_evaporation(levels, notional_usd, side, evaporation=1.0):
    """
    `book.sweep_cost` with every level's size scaled by `evaporation`.

    evaporation = 1.0 is the static book every commercial heatmap assumes.
    evaporation = 0.89 is the measured behaviour during a 0.5-1.3% move.

    Scaling sizes rather than prices is deliberate: liquidity thinning means less size resting
    at the same prices, not the same size at worse prices.
    """
    if evaporation >= 1.0:
        scaled = levels
    else:
        scaled = {p: q * evaporation for p, q in levels.items()}
    return BK.sweep_cost(scaled, notional_usd, side)


def cascade(levels, side, initial_notional, clusters, start_price,
            evaporation=1.0, max_rounds=MAX_ROUNDS):
    """
    Iterate forced flow against the book until no further clusters are triggered.

    `side`      "bids" for forced SELLING (longs liquidating hit bids), "asks" for forced BUYING.
    `clusters`  [(trigger_price, forced_notional)] -- the map.
    Returns the final price, total notional swept, rounds, and whether the book was exhausted.

    EXHAUSTION IS NOT FAILURE, it is the answer "further than the recorded book can say". It is
    returned as a flag rather than as a number, because filling that gap with an extrapolation is
    how a cascade estimate becomes fiction.
    """
    total = float(initial_notional)
    price = float(start_price)
    triggered = set()
    rounds = 0

    for rounds in range(1, max_rounds + 1):
        r = sweep_to_price(levels, total, side, evaporation)
        if r is None:
            return {"final_price": None, "total_notional": total, "rounds": rounds,
                    "exhausted": True, "moved_pct": None,
                    "note": "recorded depth exhausted; the book cannot answer beyond this"}
        new_price = r["last_price"]      # reach, not average cost -- see sweep_to_price
        lo, hi = (new_price, price) if side == "bids" else (price, new_price)
        add = 0.0
        for p, n in clusters:
            if (p, n) in triggered:
                continue
            if lo < p <= hi:
                add += n
                triggered.add((p, n))
        if add <= 0:
            price = new_price
            break
        total += add
        price = new_price

    moved = (float(start_price) - price) / float(start_price) if side == "bids" \
        else (price - float(start_price)) / float(start_price)
    return {"final_price": price, "total_notional": total, "rounds": rounds,
            "exhausted": False, "moved_pct": moved * 100.0,
            "clusters_triggered": len(triggered)}


def bracket(levels, side, initial_notional, clusters, start_price,
            evaporation_optimistic=1.0, evaporation_pessimistic=None, horizon_min=5):
    """
    The declared range.

    OPTIMISTIC assumes a static book -- what every published heatmap implicitly claims, and what
    the measurement says is correct to four decimals in QUIET markets and wrong by 15% during
    large moves.
    PESSIMISTIC applies the measured ratio for the horizon.

    The gap between them is reported as `ambiguity_pct` and is a first-class output: it is the
    cost of not knowing how the book behaves, and it is exactly the quantity a competitor hides
    by quoting a single number.
    """
    if evaporation_pessimistic is None:
        evaporation_pessimistic = evaporation_for(horizon_min, "stress")
    hi = cascade(levels, side, initial_notional, clusters, start_price,
                 evaporation=evaporation_optimistic)
    lo = cascade(levels, side, initial_notional, clusters, start_price,
                 evaporation=evaporation_pessimistic)
    out = {"optimistic": hi, "pessimistic": lo,
           "evaporation_optimistic": evaporation_optimistic,
           "evaporation_pessimistic": evaporation_pessimistic,
           "horizon_min": horizon_min,
           "evaporation_source": "measured, Binance 1,324d (F-0002); applied to Hyperliquid "
                                 "is ASSUMED (F-0006)"}
    if hi.get("moved_pct") is not None and lo.get("moved_pct") is not None:
        out["ambiguity_pct"] = abs(lo["moved_pct"] - hi["moved_pct"])
    return out
