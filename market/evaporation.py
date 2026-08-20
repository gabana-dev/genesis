"""
Does the order book stand still while price moves? Measured, not assumed.

THE QUESTION
    Every liquidation heatmap implicitly models a cascade against a STATIC book: $40M of forced
    selling meets whatever depth is showing, and price moves by however much that absorbs.

    Market makers do not stand still. Liquidity is withdrawn precisely when price moves fast,
    which is why cascades cascade rather than fizzle. If depth at +/-1% halves during a 1% move,
    every published cascade estimate is optimistic by construction.

    Nobody publishes this. It is measurable on three years of free data.

WHAT IS MEASURED
    For each 30-second bookDepth snapshot: depth notional within a band, and the price move over
    the following window. Then depth is compared across move-size buckets -- quiet periods
    against violent ones -- for the SAME symbol and the SAME hour-of-day, because liquidity has
    a strong diurnal cycle and comparing 03:00 to 14:00 would measure the clock, not the stress.

WHAT IT CANNOT SHOW
    Direction of causation. Depth falling during fast moves is consistent with makers pulling
    quotes AND with quotes being consumed. Both produce a thinner book and both make a cascade
    travel further, which is what a cascade model needs -- but "makers withdraw" is a story, not
    a finding, and this module does not test it.

DEPENDENCIES: stdlib + numpy. No new packages.
"""

import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import bookdepth as B  # noqa: E402

CACHE = B.CACHE


def load(sym, days):
    """
    Snapshots as {t_ms: {pct: notional}}, for the given ISO dates. Days absent from the cache
    are skipped and counted; a missing day is a gap in the archive, not an error.
    """
    snaps, missing = {}, []
    for d in days:
        p = B._cache_path(sym, d)
        if not os.path.exists(p):
            missing.append(d)
            continue
        cur = defaultdict(dict)
        for t, pct, _depth, notional in B.read_day(p):
            cur[t][pct] = notional
        snaps.update(cur)
    return snaps, missing


def mid_proxy(snap):
    """
    A mid-price proxy is NOT available in bookDepth -- it publishes notional at percentage
    offsets, never the price itself. Price must come from klines and be joined on time.

    Returning None here rather than inventing a number, because a silently wrong mid would
    corrupt every move calculation downstream.
    """
    return None


def band_notional(snap, lo=0.2, hi=1.0):
    """
    Notional resting within a band on both sides.

    Uses the published levels only. The venue reports notional AT each offset, so summing 0.2
    and 1.0 is the liquidity out to 1% -- not an integral, and not interpolated. Stated because
    treating these as cumulative when they are per-level, or vice versa, silently rescales
    every result.
    """
    tot = 0.0
    for pct in (lo, hi):
        tot += snap.get(pct, 0.0) + snap.get(-pct, 0.0)
    return tot


def by_hour_baseline(snaps, band=(0.2, 1.0)):
    """Median band notional per hour-of-day -- the diurnal cycle that must be divided out."""
    buckets = defaultdict(list)
    for t, s in snaps.items():
        n = band_notional(s, *band)
        if n > 0:
            buckets[(t // 3600000) % 24].append(n)
    return {h: float(np.median(v)) for h, v in buckets.items() if v}


def relative_depth(snaps, band=(0.2, 1.0)):
    """
    Depth at each snapshot as a multiple of its hour-of-day median.

    1.0 means a typical book for that time of day; 0.5 means half the usual liquidity. This is
    the quantity to compare across move sizes, because raw notional would mostly measure the
    clock.
    """
    base = by_hour_baseline(snaps, band)
    out = {}
    for t, s in snaps.items():
        b = base.get((t // 3600000) % 24)
        n = band_notional(s, *band)
        if b and b > 0 and n > 0:
            out[t] = n / b
    return out


def summarise(rel):
    if not rel:
        return {}
    v = np.array(sorted(rel.values()))
    return {"n": len(v), "median": float(np.median(v)),
            "p05": float(v[int(0.05 * len(v))]), "p95": float(v[int(0.95 * len(v))])}


# ---------------------------------------------------------------------------------------
# The measurement
# ---------------------------------------------------------------------------------------

def aligned(sym, days, band=(0.2, 1.0), horizon_min=5):
    """
    Join each depth snapshot to the price move over the FOLLOWING `horizon_min` minutes.

    Forward, never backward. A backward-looking join would measure depth after the move and
    answer a different question -- and it is the version that would accidentally look
    predictive, because the book is visibly thin once a move has already happened.

    Returns (rel_depth, abs_move_pct) pairs, where rel_depth is normalised by hour-of-day
    median so the diurnal liquidity cycle is divided out rather than measured.
    """
    snaps, missing_depth = load(sym, days)
    rel = relative_depth(snaps, band)

    closes = {}
    missing_px = []
    for d in days:
        p = B.fetch_klines(sym, d, "1m")
        if not p:
            missing_px.append(d)
            continue
        for t, _o, _h, _l, c in B.read_klines(p):
            closes[t] = c
    if not closes or not rel:
        return [], {"missing_depth": missing_depth, "missing_px": missing_px}

    minute = lambda ms: (ms // 60000) * 60000  # noqa: E731
    out = []
    for t, r in rel.items():
        m0 = minute(t)
        c0 = closes.get(m0)
        c1 = closes.get(m0 + horizon_min * 60000)
        if c0 and c1 and c0 > 0:
            out.append((r, abs(c1 - c0) / c0 * 100.0))
    return out, {"missing_depth": missing_depth, "missing_px": missing_px,
                 "snapshots": len(rel), "matched": len(out)}


def evaporation(pairs, quantiles=(0.5, 0.9, 0.99, 0.999)):
    """
    Median relative depth, bucketed by how violent the following window was.

    Buckets are quantiles of the move distribution, not fixed thresholds, so the comparison is
    self-calibrating across symbols and regimes rather than depending on a number chosen after
    seeing the data.
    """
    if not pairs:
        return []
    rels = np.array([p[0] for p in pairs])
    moves = np.array([p[1] for p in pairs])
    cuts = [0.0] + [float(np.quantile(moves, q)) for q in quantiles] + [float(moves.max()) + 1]
    rows = []
    for lo, hi in zip(cuts, cuts[1:]):
        m = (moves >= lo) & (moves < hi)
        if m.sum() < 20:
            continue
        rows.append({"move_lo_pct": lo, "move_hi_pct": hi, "n": int(m.sum()),
                     "median_rel_depth": float(np.median(rels[m])),
                     "p25": float(np.quantile(rels[m], 0.25))})
    return rows


def during(sym, days, band=(0.2, 1.0), horizon_min=5):
    """
    EVAPORATION proper: depth AFTER the window divided by depth BEFORE it, bucketed by how big
    the move was.

    `aligned` answers a different question -- depth now against the move next, i.e. whether a
    thin book PRECEDES violence. Both matter and they are not the same:

        aligned  : thin book -> big move        (predictive, and possibly just permissive)
        during   : big move  -> book gets thinner  (the cascade AMPLIFIER)

    Only the second one changes a cascade estimate, because it says the liquidity a heatmap
    counted on is not there by the time the forced flow arrives.

    Ratio of raw notional, not of the hour-normalised value: before and after are minutes apart,
    so the diurnal cycle is common to both and divides out on its own.
    """
    snaps, missing_depth = load(sym, days)
    closes, missing_px = {}, []
    for d in days:
        p = B.fetch_klines(sym, d, "1m")
        if not p:
            missing_px.append(d)
            continue
        for t, _o, _h, _l, c in B.read_klines(p):
            closes[t] = c
    if not snaps or not closes:
        return [], {"missing_depth": missing_depth, "missing_px": missing_px}

    h_ms = horizon_min * 60000
    out = []
    for t, s in snaps.items():
        s2 = snaps.get(t + h_ms)
        if s2 is None:
            continue
        d0, d1 = band_notional(s, *band), band_notional(s2, *band)
        if d0 <= 0 or d1 <= 0:
            continue
        m0 = (t // 60000) * 60000
        c0, c1 = closes.get(m0), closes.get(m0 + h_ms)
        if not c0 or not c1 or c0 <= 0:
            continue
        out.append((d1 / d0, abs(c1 - c0) / c0 * 100.0))
    return out, {"missing_depth": missing_depth, "missing_px": missing_px, "pairs": len(out)}


def report(rows, label):
    print(f"\n{label}")
    for r in rows:
        print(f"  move {r['move_lo_pct']:6.3f}–{r['move_hi_pct']:6.3f}%  n={r['n']:>7,}  "
              f"median {r['median_rel_depth']:.3f}   p25 {r['p25']:.3f}")


def non_overlapping(rows, horizon_min=5):
    """
    Reduce to non-overlapping observations by striding at the horizon length.

    Snapshots are 30 s apart and the window is `horizon_min`, so consecutive rows share most of
    their window. Counting them as independent inflates n roughly tenfold -- the error the power
    audit found in GEN-1 and that I repeated in CASCADE-1's first draft.

    A gap-based episode collapse is the WRONG tool here and was tried first: bookDepth is a
    continuous series with no gaps, so a 30-minute gap rule reduced 24,043 rows to 7. Discrete
    events have episodes; a continuous series has a sampling stride.

    Volatility clusters, so even horizon-spaced rows inside one storm are not fully independent.
    `distinct_days` is therefore reported per bucket as the honest lower bound on breadth.
    """
    if not rows:
        return []
    rows = sorted(rows, key=lambda x: x[2])
    step = horizon_min * 60000
    out, last = [], None
    for r in rows:
        if last is None or r[2] - last >= step:
            out.append(r)
            last = r[2]
    return out


def evaporation_by_bucket(rows, quantiles=(0.5, 0.9, 0.99, 0.999)):
    """As `evaporation`, plus the number of distinct UTC days behind each bucket."""
    import numpy as np
    if not rows:
        return []
    ratio = np.array([r[0] for r in rows])
    move = np.array([r[1] for r in rows])
    day = np.array([r[2] // 86400000 for r in rows])
    cuts = [0.0] + [float(np.quantile(move, q)) for q in quantiles] + [float(move.max()) + 1]
    out = []
    for lo, hi in zip(cuts, cuts[1:]):
        m = (move >= lo) & (move < hi)
        if m.sum() < 10:
            continue
        out.append({"move_lo_pct": lo, "move_hi_pct": hi, "n": int(m.sum()),
                    "distinct_days": int(len(set(day[m].tolist()))),
                    "median_rel_depth": float(np.median(ratio[m])),
                    "p25": float(np.quantile(ratio[m], 0.25))})
    return out
