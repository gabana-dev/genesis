"""
COND-1: the declared grid from CONTRACT-conditioners.md, and nothing else.

Contract frozen 2026-08-18 at sha256
b8a295dd7769e36c46a47a62aff28656727d3d859da06d402e34a3446d912e7f.

WRITTEN BEFORE THE DATA LANDS, DELIBERATELY
    q5 closes ~2026-08-25. Writing this afterwards would mean writing it under time pressure
    against a sample that exists once, with every arbitrary choice made while a result is
    visible. `exec1.py` was written the same way for the same reason, and its docstring puts
    it better than this one can: a grid built after seeing the data is not a grid.

    It also means the arithmetic can be checked against synthetic series with known answers
    before real prices are ever involved -- the only place a silent error shows itself.

WHAT COND-1 ACTUALLY MEASURES, RESTATED
    Markout at 60 s is the adverse-selection term. The horizon study since measured adverse
    selection at 0.1301 bps at ONE DAY against 1.1871 at 60 s, so for a daily strategy this
    conditions roughly 8% of the cost stack. COND-1 is still worth running -- it is frozen,
    the recording is paid for, and markout matters for any shorter-horizon work -- but it is
    NOT the cost lever, and no result here should be reported as if it were.

NOTHING HERE MAY BE TUNED AFTER SEEING A RESULT.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import ledger as L  # noqa: E402
import stats as ST  # noqa: E402

CONTRACT = "market/CONTRACT-conditioners.md"
CONTRACT_SHA256 = "b8a295dd7769e36c46a47a62aff28656727d3d859da06d402e34a3446d912e7f"

BPS = 1e-4

# Section 4. Every value copied from the contract; none chosen here.
BASIS_BUCKETS_BPS = [(0.0, 0.5), (0.5, 1.5), (1.5, 3.0), (3.0, float("inf"))]
BASIS_SIGNS = ("positive", "negative")
B_LOOKBACKS_MS = (1_000, 5_000)
B_THRESHOLDS = (0.25, 0.50)
C_DEPLETION = (0.50, 0.80)
C_BURST_MS = (200, 1_000)
C_QUIET_MS = 500                       # single value, fixed
D_SWEEP_BUCKETS_BTC = [(0.0, 0.1), (0.1, 1.0), (1.0, 5.0), (5.0, float("inf"))]
D_MAX_GAP_MS = (1, 50)

PRIMARY_HORIZON_MS = 60_000            # section 2
POOL = "certain"
MIN_FILLS = 200                        # K1
ALPHA = 0.05
DECLARED_TRIALS = 29                   # 24 conditioned + 5 reference
BONFERRONI = ALPHA / DECLARED_TRIALS

# K4
MAX_INCOMPLETE_FRACTION = 0.25
# K3
C_PRECISION_ABANDON = 0.30
# K5 -- section 7's unverified assumption
MAX_CLOCK_DISAGREEMENT_MS = 50


def cells():
    """
    The 29 declared cells, enumerated so the family cannot silently grow.

    Returned as (conditioner, key, params). `reference` cells carry params=None and are the
    unconditioned baseline plus each conditioner pooled across its own buckets.
    """
    out = [("reference", "unconditioned", None)]
    for sign in BASIS_SIGNS:
        for lo, hi in BASIS_BUCKETS_BPS:
            out.append(("A", f"basis_{sign}_{lo:g}-{hi:g}bps", {"sign": sign, "lo": lo, "hi": hi}))
    for lb in B_LOOKBACKS_MS:
        for th in B_THRESHOLDS:
            out.append(("B", f"cancel_{lb}ms_{th:g}", {"lookback_ms": lb, "threshold": th}))
    for dep in C_DEPLETION:
        for burst in C_BURST_MS:
            out.append(("C", f"cascade_{dep:g}_{burst}ms",
                        {"depletion": dep, "burst_ms": burst, "quiet_ms": C_QUIET_MS}))
    for lo, hi in D_SWEEP_BUCKETS_BTC:
        for gap in D_MAX_GAP_MS:
            out.append(("D", f"sweep_{lo:g}-{hi:g}btc_{gap}ms",
                        {"lo": lo, "hi": hi, "max_gap_ms": gap}))
    for c in ("A", "B", "C", "D"):
        out.append(("reference", f"pooled_{c}", None))
    return out


def check_family():
    """The count is fixed by the contract. If this fails, the grid drifted."""
    n = len(cells())
    if n != DECLARED_TRIALS:
        raise AssertionError(f"family drifted: {n} cells against {DECLARED_TRIALS} declared")
    return n


# ---------------------------------------------------------------------------------------
# Conditioner primitives. Each takes observations and returns a per-fill mask.
# ---------------------------------------------------------------------------------------

def basis_bps(perp_mid: float, spot_mid: float) -> float:
    """(perp - spot)/spot in bps. Section 5, conditioner A."""
    return ((perp_mid - spot_mid) / spot_mid) / BPS


def a_mask(basis_series, sign, lo, hi):
    b = np.asarray(basis_series, dtype=float)
    side = (b > 0) if sign == "positive" else (b < 0)
    mag = np.abs(b)
    return side & (mag >= lo) & (mag < hi)


def cancellation_ratio(removed_size, traded_size, visible_depth):
    """
    Conditioner B. Size that LEFT a price level without a matching trade, over visible
    same-side depth.

    Binance's diff-depth stream cannot tell a cancel from a fill on its own -- a level going to
    zero is ambiguous. With trades on the same clock it becomes decidable, and that is the
    whole reason q5 records both. `traded_size` is subtracted rather than assumed zero.
    """
    removed = np.asarray(removed_size, dtype=float)
    traded = np.asarray(traded_size, dtype=float)
    depth = np.asarray(visible_depth, dtype=float)
    cancelled = np.maximum(removed - traded, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(depth > 0, cancelled / depth, np.nan)
    return r


def b_mask(ratio, threshold):
    r = np.asarray(ratio, dtype=float)
    return np.isfinite(r) & (r > threshold)


def cascade_fires(taker_volume, visible_depth, depletion):
    """
    Conditioner C's detector: one-sided taker volume consuming more than `depletion` of
    same-side visible depth inside the burst window.
    """
    v = np.asarray(taker_volume, dtype=float)
    d = np.asarray(visible_depth, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.where(d > 0, v / d, np.nan)
    return np.isfinite(frac) & (frac > depletion)


def precision_against_key(fired, key_present):
    """
    C's DECLARED primary. Of the windows where the detector fired, the fraction in which the
    venue published at least one liquidation.

    Precision only, and the contract says why: `!forceOrder@arr` publishes only the largest
    liquidation per symbol per 1000 ms, so ABSENCE IS NOT EVIDENCE OF ABSENCE. The negative
    cell of a 2x2 is unreliable, recall is a lower bound, and a Fisher exact over the full
    table would be biased by an amount Genesis cannot quantify.
    """
    f = np.asarray(fired, dtype=bool)
    k = np.asarray(key_present, dtype=bool)
    if f.sum() == 0:
        return None
    return float((f & k).sum() / f.sum())


def reconstruct_sweeps(trade_ids, sides, times_ms, sizes, max_gap_ms):
    """
    Conditioner D. Consecutive trade ids, same aggressor side, within `max_gap_ms` -- one
    taker order sweeping the book.

    Aggressor side is READ from Binance's `m` flag, never inferred. This is not aggTrade:
    aggTrade merges same-price fills from one taker order, so a sweep across four levels
    appears as four records. Reconstruction from individual trades recovers the parent.
    """
    ids = np.asarray(trade_ids, dtype=np.int64)
    t = np.asarray(times_ms, dtype=float)
    sz = np.asarray(sizes, dtype=float)
    sd = np.asarray(sides)
    sweeps, start = [], 0
    for i in range(1, len(ids) + 1):
        broken = (i == len(ids)) or (ids[i] != ids[i - 1] + 1) \
            or (sd[i] != sd[i - 1]) or (t[i] - t[i - 1] > max_gap_ms)
        if broken:
            sweeps.append({"first": int(ids[start]), "last": int(ids[i - 1]),
                           "side": sd[start], "size": float(sz[start:i].sum()),
                           "t0": float(t[start]), "t1": float(t[i - 1])})
            start = i
    return sweeps


def d_mask(sweep_sizes, lo, hi):
    s = np.asarray(sweep_sizes, dtype=float)
    return (s >= lo) & (s < hi)


# ---------------------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------------------

def cell_report(markouts, name, conditioner):
    """One cell. K1 governs sufficiency; a thin cell is reported, never merged."""
    m = np.asarray([x for x in markouts if np.isfinite(x)], dtype=float)
    out = {"cell": name, "conditioner": conditioner, "n_fills": int(m.size)}
    if m.size < MIN_FILLS:
        out.update({"sufficient": False,
                    "excluded_reason": f"K1: {m.size} fills against {MIN_FILLS} required"})
        return out
    out.update({"sufficient": True,
                "median_markout_bps": float(np.median(m)) / BPS,
                "mean_markout_bps": float(m.mean()) / BPS})
    try:
        lo, hi = ST.block_bootstrap_ci(m, lambda a: float(np.median(a)),
                                       n_boot=2000, block=64, alpha=ALPHA)
        out["median_ci_bps"] = [lo / BPS, hi / BPS]
    except Exception as e:
        out["median_ci_bps"] = None
        out["ci_error"] = f"{type(e).__name__}: {e}"
    return out


def correct(p_values):
    """Section 2: BH at q=0.05, with Bonferroni reported alongside. Neither chosen after."""
    keep, crit = L.benjamini_hochberg(p_values, alpha=ALPHA)
    return {"benjamini_hochberg_survivors": keep, "bh_critical": crit,
            "bonferroni_alpha": BONFERRONI, "declared_trials": DECLARED_TRIALS}


def k4_window(incomplete_fraction):
    """
    K4. Above 25% incomplete, the analysis window is restricted to complete intervals AND the
    restriction is reported on every result -- never applied silently.
    """
    restricted = incomplete_fraction > MAX_INCOMPLETE_FRACTION
    return {"incomplete_fraction": incomplete_fraction,
            "restricted_to_complete_intervals": bool(restricted),
            "must_be_reported_on_every_result": bool(restricted)}


def k5_clock(spot_ts_ms, perp_ts_ms):
    """
    K5. Conditioner A compares two books by venue timestamp, on an assumption Genesis has
    never verified. If the engines disagree by more than 50 ms, A is VOID -- B, C and D are
    unaffected.
    """
    d = float(np.median(np.abs(np.asarray(spot_ts_ms, dtype=float)
                               - np.asarray(perp_ts_ms, dtype=float))))
    return {"median_abs_disagreement_ms": d,
            "A_void": bool(d > MAX_CLOCK_DISAGREEMENT_MS),
            "threshold_ms": MAX_CLOCK_DISAGREEMENT_MS}
