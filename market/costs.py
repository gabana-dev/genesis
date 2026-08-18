"""
The cost model. Measurement infrastructure only -- it prices, it does not decide.

WHY THIS EXISTS
    EXEC-1 measured that 1.828 bps of a 3.000 bps maker advantage survives adverse selection,
    and that number has since been quoted as though it were profit. It is not. It is the
    amount by which POSTING beats CROSSING, per side, for a trade you were going to do anyway.

    This module exists to keep two questions apart that have been running together:

      EXECUTION   Given that Genesis wants to trade, is it cheaper to post than to cross?
                  Measured per side, against the alternative of crossing. This is what
                  EXEC-1's 1.83 bps answers.

      MARKET MAKING   Ignoring any directional view, does quoting both sides earn money from
                  the spread? Measured per round trip, against doing nothing at all. EXEC-1
                  does NOT answer this, and the answer is not close.

    Conflating them is how a cost reduction becomes an imaginary revenue.

WHAT IT DOES NOT DO
    No signal, no sizing, no policy, no P&L for a strategy that does not exist. Every input is
    supplied by the caller and every fee is a recorded venue fact with a date.
"""

# ---------------------------------------------------------------------------------------
# Venue facts. Recorded with a date because a fee schedule is a claim about the world that
# expires. Source: binance.com/en/fee/futureFee and the spot schedule, checked 2026-08-18.
# ---------------------------------------------------------------------------------------

FEES_AS_OF = "2026-08-18"

# (maker, taker) as fractions of notional, per side.
FEE_TIERS = {
    # USD-M perpetual futures.
    "futures_vip0": (0.00020, 0.00050),   # 2.0 / 5.0 bps -- the default, and what EXEC-1 used
    "futures_vip9": (0.00000, 0.00017),   # 0.0 / 1.7 bps -- the best publicly listed tier
    # Spot.
    "spot_vip0":    (0.00100, 0.00100),   # 10.0 / 10.0 bps
}

# Paying fees in BNB takes 10% off USD-M futures fees. Applied only when asked for.
BNB_DISCOUNT = 0.10

# Perpetual funding is exchanged every 8 hours between longs and shorts. Positive rate: longs
# pay shorts. It is a REAL cash flow on held inventory, it is published in advance, and until
# now Genesis's cost model did not contain it at all.
#
# Imported from Pindza & Bambe Moutsinga (2026), J. Finance and Data Science 12, 100197, which
# reports annualised funding impact exceeding 10% of position value in stressed periods. The
# mechanism is a venue fact; the paper is what prompted its inclusion. No novelty claimed.
FUNDING_INTERVAL_HOURS = 8.0


def fees(tier: str, bnb: bool = False):
    """(maker, taker) for a tier, as fractions per side."""
    m, t = FEE_TIERS[tier]
    if bnb and tier.startswith("futures"):
        m, t = m * (1 - BNB_DISCOUNT), t * (1 - BNB_DISCOUNT)
    return m, t


# ---------------------------------------------------------------------------------------
# Question 1 -- EXECUTION. Per side, against crossing.
# ---------------------------------------------------------------------------------------

def maker_advantage(tier: str, bnb: bool = False) -> float:
    """
    What posting saves over crossing, per side, BEFORE adverse selection.

    This is a fee difference and nothing else. It is not revenue, and it exists only for a
    trade that was going to happen regardless.
    """
    m, t = fees(tier, bnb)
    return t - m


def execution_saving(adverse_selection: float, tier: str = "futures_vip0",
                     bnb: bool = False) -> dict:
    """
    EXEC-1's question. `adverse_selection` is the measured markout cost of resting, as a
    positive fraction (EXEC-1 at 60 s: 1.1871 bps = 0.00011871).

    Returns the net saving per side. Negative means crossing is cheaper -- posting can lose
    to crossing when the market picks you off harder than the fee discount is worth.
    """
    adv = maker_advantage(tier, bnb)
    return {
        "maker_advantage": adv,
        "adverse_selection": adverse_selection,
        "net_saving_per_side": adv - adverse_selection,
        "surviving_fraction": (adv - adverse_selection) / adv if adv else float("nan"),
        "tier": tier, "bnb": bnb, "fees_as_of": FEES_AS_OF,
    }


# ---------------------------------------------------------------------------------------
# Question 2 -- MARKET MAKING. Per round trip, against doing nothing.
# ---------------------------------------------------------------------------------------

def market_making_pnl(spread: float, adverse_selection: float, tier: str = "futures_vip0",
                      bnb: bool = False, funding: float = 0.0,
                      inventory_cost: float = 0.0) -> dict:
    """
    One complete round trip: buy at the bid, sell at the ask.

    `spread` is the FULL spread as a fraction of price -- what a round trip captures if both
    sides fill at the touch. `funding` is signed: positive means Genesis PAID it.

        net = spread - 2*maker_fee - adverse_selection - funding - inventory_cost

    Two fills, so the maker fee is paid twice. This is the calculation that decides whether
    quoting is a business, and it is the one EXEC-1 never performed.
    """
    m, _ = fees(tier, bnb)
    costs = 2 * m + adverse_selection + funding + inventory_cost
    net = spread - costs
    return {
        "spread_captured": spread,
        "maker_fees_round_trip": 2 * m,
        "adverse_selection": adverse_selection,
        "funding": funding,
        "inventory_cost": inventory_cost,
        "total_cost": costs,
        "net": net,
        "viable": net > 0,
        "cost_to_spread_ratio": costs / spread if spread else float("inf"),
        "tier": tier, "bnb": bnb, "fees_as_of": FEES_AS_OF,
    }


def breakeven_spread(adverse_selection: float, tier: str = "futures_vip0", bnb: bool = False,
                     funding: float = 0.0, inventory_cost: float = 0.0) -> float:
    """
    How wide the spread must be for quoting to break even. Compare against the MEASURED
    spread, never against an assumed one.
    """
    m, _ = fees(tier, bnb)
    return 2 * m + adverse_selection + funding + inventory_cost


# ---------------------------------------------------------------------------------------
# Funding
# ---------------------------------------------------------------------------------------

def funding_cost(rate_per_interval: float, hours_held: float, side: str) -> float:
    """
    Cash exchanged on inventory held across funding timestamps, as a signed fraction of
    notional. Positive means Genesis paid.

    A positive rate means longs pay shorts. So a SHORT inventory under positive funding
    RECEIVES -- which is why this term can improve a market maker's economics rather than
    only worsen them, and why leaving it out is not conservative.

    Only whole intervals crossed are charged. Funding is exchanged at the timestamp or not at
    all; a position held for seven hours and fifty minutes pays nothing.
    """
    if side not in ("long", "short"):
        raise ValueError(f"side must be long or short, got {side!r}")
    intervals = int(hours_held // FUNDING_INTERVAL_HOURS)
    paid = rate_per_interval * intervals
    return paid if side == "long" else -paid


def annualised_funding(rate_per_interval: float) -> float:
    """A per-interval rate as an annual fraction. 3 intervals a day, 365 days."""
    return rate_per_interval * 3 * 365


# ---------------------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------------------

def inventory_cost(position_notional: float, volatility: float, hours_held: float,
                   risk_aversion: float) -> float:
    """
    The risk cost of holding inventory, as a fraction of the position, in the
    Avellaneda-Stoikov form: gamma * sigma^2 * tau, scaled by position.

    `volatility` is per-hour, as a fraction. `risk_aversion` is gamma and is a CHOICE, not a
    measurement -- it is a parameter of whoever is quoting, so it is required rather than
    defaulted. A default here would smuggle a preference into a cost model.

    This prices RISK, not realised loss. Realised inventory P&L is a separate term and
    belongs in the edge autopsy (T3.3), not here.
    """
    if position_notional < 0:
        raise ValueError("position_notional is a magnitude; pass abs()")
    return risk_aversion * (volatility ** 2) * hours_held * position_notional
