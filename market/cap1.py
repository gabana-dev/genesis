"""
CAP-1: the declared grid from CONTRACT-capacity.md, and nothing else.

This module chooses nothing. Every parameter below is copied from the contract, which was
frozen 2026-08-18 before any capacity result had been computed. It reuses `exec1.build_orders`
and `fills.simulate` rather than reimplementing them, so the $10,000 anchor cell is resolved by
exactly the code that produced EXEC-1's published figures. A reimplementation would make K1 a
test of two codebases agreeing rather than of the re-simulation being correct.

ONE PASS, ALL SIZES
    `fills.simulate` resolves each order independently against the recorded book, so all four
    sizes are built into a single order set and resolved in one traversal of the 3.4 GB log.
    Four separate passes would read the same bytes four times and, more importantly, would
    resolve identical decision times against separately-parsed book states -- introducing a
    difference between size cells that came from the reader rather than from the market.

DEFECT D-C1, RECORDED NOT REPAIRED
    CONTRACT-capacity.md section 4 states "TTL | 60,000 ms (as EXEC-1)". EXEC-1's TTL is
    300,000 ms. The line is internally contradictory: the number and the parenthetical
    disagree, and only one of them can be honoured.

    Resolved in favour of the parenthetical, i.e. TTL = 300,000 ms, on these grounds:

      1. The contract's governing sentence is "Identical to EXEC-1's in every respect EXCEPT
         size, so the size slope is the only thing that varies and any difference is
         attributable." A 60,000 ms TTL would vary a second parameter and destroy exactly the
         attribution the grid was built to preserve.
      2. K1 requires the $10,000 cell to reproduce EXEC-1 within 0.05 bps. Under a different
         TTL it could not, so the declared kill condition would fire on the transcription
         error rather than on anything about the re-simulation.

    This is recorded in research/cap-1-contract-defect.md and reported with every result. It
    is a deviation from the literal text of a frozen contract, and it is not hidden.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import exec1 as X  # noqa: E402
import fills as F  # noqa: E402

CONTRACT = "market/CONTRACT-capacity.md"
CONTRACT_SHA256 = "a239531e27d44f451da8f823b24e7e20725d5971d9ac6c4d12927947a99d88e0"

# CONTRACT-capacity.md section 4.
SIZES_USD = (1_000.0, 10_000.0, 100_000.0, 1_000_000.0)
ANCHOR_SIZE_USD = 10_000.0
LATENCY_MS = 291.0                 # the measured floor, EXEC-1's primary arm
PRIMARY_HORIZON_MS = 60_000
POOL = "certain"

# D-C1: EXEC-1's value, not the contradictory literal in the contract. See module docstring.
TTL_MS = X.TTL_MS                  # 300_000.0
TTL_DEVIATION = {
    "defect": "D-C1",
    "contract_says": "60,000 ms (as EXEC-1)",
    "exec1_actual": X.TTL_MS,
    "used": X.TTL_MS,
    "why": ("the contract's own governing sentence requires identity with EXEC-1 except for "
            "size; honouring the literal 60,000 would vary a second parameter and cause K1 to "
            "fire on a transcription error"),
    "recorded_in": "research/cap-1-contract-defect.md",
}

# K2: a cell below this many certain fills reports insufficient data and is EXCLUDED from
# correction rather than merged with a neighbour.
MIN_CERTAIN_FILLS = 200

# K1: the anchor must reproduce EXEC-1's net saving to within this, in bps.
ANCHOR_TOLERANCE_BPS = 0.05
EXEC1_NET_SAVING_BPS_60S = 1.8129   # 3.000 - 1.1871, EXEC-1's 60 s certain-pool figure

BPS = 1e-4


def build_orders(start_ms, end_ms):
    """
    The full declared order set: every EXEC-1 cell, at every declared size.

    order_id is prefixed with the size so a resolved order can be traced back to its grid
    position without a side table, exactly as EXEC-1 does for cell and time.
    """
    orders = []
    for size in SIZES_USD:
        for o in X.build_orders(start_ms, end_ms, ttl_ms=TTL_MS, size_usd=size):
            o.order_id = f"{int(size)}|{o.order_id}"
            orders.append(o)
    return orders


def size_of(order):
    return float(order.order_id.split("|", 1)[0])


def group_by_size(orders):
    out = {s: [] for s in SIZES_USD}
    for o in orders:
        out.setdefault(size_of(o), []).append(o)
    return out


def group_by_size_and_offset(orders):
    """The 12 declared trials: 4 sizes x 3 offsets, both sides pooled at each offset."""
    out = {}
    for o in orders:
        out.setdefault((size_of(o), o.offset_ticks), []).append(o)
    return out


def net_saving_bps(orders, horizon_ms=PRIMARY_HORIZON_MS, pool=POOL):
    """
    CAP-1's primary endpoint: maker advantage minus adverse selection, per side, in bps.

    Returns None when the pool is empty. `fraction_of_advantage_lost` is EXEC-1's own
    statistic, so the anchor is compared against EXEC-1 through the same arithmetic rather
    than through a parallel implementation of it.
    """
    lost = X.advantage_lost(orders, horizon_ms=horizon_ms, pool=pool)
    if lost is None:
        return None
    return (F.MAKER_ADVANTAGE * (1.0 - lost)) / BPS


def cell_report(orders, horizon_ms=PRIMARY_HORIZON_MS):
    """One grid cell. Secondary metrics are reported but may not replace the primary."""
    certain = [o for o in orders if o.outcome == "certain"]
    optimistic = [o for o in orders if o.outcome == "optimistic_only"]
    n = len(orders)
    enough = len(certain) >= MIN_CERTAIN_FILLS
    return {
        "n_orders": n,
        "n_reached": sum(1 for o in orders if o.reached),
        "reach_rate": (sum(1 for o in orders if o.reached) / n) if n else None,
        "n_certain": len(certain),
        "n_optimistic_extra": len(optimistic),
        "fill_rate_lower_bound": len(certain) / n if n else None,
        "fill_rate_upper_bound": (len(certain) + len(optimistic)) / n if n else None,
        # C5 is stated in terms of this width.
        "ambiguity_width": len(optimistic) / n if n else None,
        "net_saving_bps": net_saving_bps(orders, horizon_ms) if enough else None,
        "sufficient": enough,                       # K2
        "excluded_reason": None if enough else
                           f"fewer than {MIN_CERTAIN_FILLS} certain fills",
    }


def report(orders, horizon_ms=PRIMARY_HORIZON_MS):
    by_size = group_by_size(orders)
    by_cell = group_by_size_and_offset(orders)

    out = {
        "contract": CONTRACT, "contract_sha256": CONTRACT_SHA256,
        "grid": {"sizes_usd": list(SIZES_USD), "offsets": list(X.OFFSET_TICKS),
                 "sides": list(X.SIDES), "latency_ms": LATENCY_MS, "ttl_ms": TTL_MS,
                 "declared_trials": len(SIZES_USD) * len(X.OFFSET_TICKS)},
        "ttl_deviation": TTL_DEVIATION,
        "primary": {"endpoint": "net execution saving per side, bps",
                    "horizon_ms": horizon_ms, "pool": POOL},
        "by_size": {str(int(s)): cell_report(by_size[s], horizon_ms) for s in SIZES_USD},
        "by_size_and_offset": {f"{int(s)}|{off}": cell_report(v, horizon_ms)
                               for (s, off), v in sorted(by_cell.items())},
    }

    # K1 -- the anchor. Checked here rather than by the caller, so no result can be read
    # without the check having been made.
    anchor = out["by_size"][str(int(ANCHOR_SIZE_USD))]["net_saving_bps"]
    out["k1_anchor"] = {
        "expected_bps": EXEC1_NET_SAVING_BPS_60S,
        "observed_bps": anchor,
        "tolerance_bps": ANCHOR_TOLERANCE_BPS,
        "passes": (anchor is not None
                   and abs(anchor - EXEC1_NET_SAVING_BPS_60S) <= ANCHOR_TOLERANCE_BPS),
        "consequence_if_failed": ("K1: the whole run is VOID and reported as a defect in the "
                                  "re-simulation; no other cell may be interpreted"),
    }
    return out


def run(path, market, start_ms, end_ms, *, every_ms=X.BOOK_SAMPLE_MS,
        markout_ms=X.MARKOUT_MS):
    orders = build_orders(start_ms, end_ms)
    F.simulate(path, market, orders, latency_ms=LATENCY_MS,
               markout_ms=markout_ms, every_ms=every_ms)
    return orders, report(orders)
