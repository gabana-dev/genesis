"""
The fee map: what a round trip costs at each reachable venue and tier, and what break-even
hit rate that implies.

WHY THIS IS A MODULE AND NOT A NOTE
    Every Genesis result so far has been measured against ONE cost assumption -- Binance USD-M
    VIP 0, 2 bps maker, 4 bps round trip. That number produced the 52.81% bar that DIR-1 and
    DIR-2 were judged against, and DIR-2 missed it by 0.4 points.

    The bar is not a property of the market. It is a property of the ACCOUNT. This module makes
    that dependency explicit and computable, so no future contract can quietly inherit a cost
    assumption without stating it.

WHAT IT IS NOT
    Not a recommendation and not a result. It prices hypothetical round trips from published
    schedules. Whether a signal measured on one venue exists on another is a separate question
    that this module cannot answer and must not be read as answering.

    Fee schedules expire. Every figure carries the date it was read.
"""

# Break-even: p* = 0.5 + c / (2 * phi * m)      -- CONTRACT-measurement.md section 2
# where c is round-trip cost as a fraction, m the median absolute move, phi the capture.
MEDIAN_ABS_MOVE = {"1d": 0.01425, "3d": 0.02643}     # MEASURE-1, measured
BPS = 1e-4

# What Genesis actually measured, for comparison against every bar below.
DIR2_ACCURACY_1D = 0.5242
DIR2_CI_1D = (0.5063, 0.5404)

READ_ON = "2026-08-19"

# ---------------------------------------------------------------------------------------
# Published schedules. Maker fee per side, as a fraction. Round trip for a directional
# strategy is TWO maker fills -- in and out -- so cost = 2 * maker.
#
# CONFIDENCE is recorded per row, because these were not all obtained the same way.
#   "verified"   read from the venue's own published page on the date above
#   "reported"   from secondary sources; the venue's own table required a login
# ---------------------------------------------------------------------------------------
TIERS = [
    # (venue, tier label, maker per side, requirement, confidence)
    ("Binance USD-M", "VIP 0", 0.000200, "none", "verified"),
    ("Binance USD-M", "VIP 0 + BNB", 0.000180, "hold BNB, pay fees in it (-10%)", "verified"),
    ("Binance USD-M", "VIP 9", 0.000000, "institutional 30d volume", "reported"),

    # Hyperliquid: hyperliquid.gitbook.io/hyperliquid-docs/trading/fees, read 2026-08-19.
    # Tier 0 (no volume requirement) across the staking-discount columns.
    ("Hyperliquid perp", "Tier 0 base", 0.000150, "none", "verified"),
    ("Hyperliquid perp", "Tier 0 Wood", 0.000143, "stake >10 HYPE", "verified"),
    ("Hyperliquid perp", "Tier 0 Bronze", 0.000135, "stake >100 HYPE", "verified"),
    ("Hyperliquid perp", "Tier 0 Silver", 0.000128, "stake >1,000 HYPE", "verified"),
    ("Hyperliquid perp", "Tier 0 Gold", 0.000120, "stake >10,000 HYPE", "verified"),
    ("Hyperliquid perp", "Tier 0 Platinum", 0.000105, "stake >100,000 HYPE", "verified"),
    ("Hyperliquid perp", "Tier 0 Diamond", 0.000090, "stake >500,000 HYPE", "verified"),
    ("Hyperliquid perp", "Tier 3 base", 0.000040, ">$100M 14d volume", "verified"),
    ("Hyperliquid perp", "Tier 4+ base", 0.000000, ">$500M 14d volume", "verified"),
]

HYPE_PRICE_USD = 58.69          # api.hyperliquid.xyz allMids, 2026-08-19
STAKE_HYPE = {"Tier 0 Wood": 10, "Tier 0 Bronze": 100, "Tier 0 Silver": 1_000,
              "Tier 0 Gold": 10_000, "Tier 0 Platinum": 100_000, "Tier 0 Diamond": 500_000}


def breakeven(round_trip_cost: float, horizon: str = "1d", phi: float = 0.5) -> float:
    """The hit rate a directional strategy must exceed. Rises with cost, falls with move size."""
    m = MEDIAN_ABS_MOVE[horizon]
    return 0.5 + round_trip_cost / (2.0 * phi * m)


def rows(horizon: str = "1d", phi: float = 0.5):
    out = []
    for venue, tier, maker, req, conf in TIERS:
        c = 2 * maker
        bar = breakeven(c, horizon, phi)
        stake = STAKE_HYPE.get(tier)
        out.append({
            "venue": venue, "tier": tier, "requirement": req, "confidence": conf,
            "maker_bps_per_side": maker / BPS,
            "round_trip_bps": c / BPS,
            "breakeven": bar,
            # The only comparison that matters: does what Genesis measured clear this bar?
            "dir2_clears": DIR2_ACCURACY_1D > bar if horizon == "1d" else None,
            "dir2_ci_low_clears": DIR2_CI_1D[0] > bar if horizon == "1d" else None,
            "stake_usd": None if stake is None else stake * HYPE_PRICE_USD,
        })
    return out
