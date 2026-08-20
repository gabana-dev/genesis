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
