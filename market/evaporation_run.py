"""
Evaporation across the full cached history, at several bands and horizons.

STREAMING, NOT LOADING. The first version called E.load() over every cached day, which builds
{t: {pct: notional}} for all of them -- roughly 45 million dict entries across three years, several
gigabytes, on a laptop that is simultaneously recording q5. It would have thrashed or died.

The horizon is at most 15 minutes, so only a bounded lookahead is ever needed. This walks day by
day with a rolling buffer, holds one day plus the horizon at a time, and applies the
non-overlapping stride DURING accumulation rather than after -- so neither the snapshots nor the
intermediate rows are ever fully materialised.

Reports `distinct_days` on every bucket. Volatility clusters, so a bucket with 200 observations
drawn from three days is three observations wearing a costume, and the count alone hides that.
That failure has now appeared three times in this project.

Run:  .venv/bin/python market/evaporation_run.py [symbol]
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import bookdepth as B  # noqa: E402
import evaporation as E  # noqa: E402

OUT = os.path.expanduser("~/genesis-evidence/bookdepth/evaporation.json")

# Declared before the run. Bands are the venue's own published levels; horizons bracket the
# timescale a liquidation cascade resolves on.
BANDS = {"0.2-1%": (0.2, 1.0), "2-5%": (2.0, 5.0)}
HORIZONS = (1, 5, 15)
MAX_H_MS = max(HORIZONS) * 60000


def cached_days(sym):
    d = os.path.join(B.CACHE, sym)
    return sorted(f.split("-bookDepth-")[1].replace(".zip", "") for f in os.listdir(d))


def day_snapshots(sym, d):
    """One day as {t_ms: {pct: notional}}, or None if not cached."""
    p = B._cache_path(sym, d)
    if not os.path.exists(p):
        return None
    cur = defaultdict(dict)
    for t, pct, _depth, notional in B.read_day(p):
        cur[t][pct] = notional
    return cur


def day_closes(sym, d):
    p = B.fetch_klines(sym, d, "1m")
    if not p:
        return None
    return {t: c for t, _o, _h, _l, c in B.read_klines(p)}


def collect(sym, days):
    """
    Stream every day once, emitting rows per (band, horizon) with the stride already applied.

    Buffers only the previous day's tail, which is all a 15-minute lookahead can need.
    """
    rows = {(b, h): [] for b in BANDS for h in HORIZONS}
    last_emit = {(b, h): None for b in BANDS for h in HORIZONS}
    snaps_prev, closes_prev = {}, {}
    missing_depth, missing_px = [], []
    seen_snapshots = 0

    for i, d in enumerate(days):
        sd = day_snapshots(sym, d)
        if sd is None:
            missing_depth.append(d)
            snaps_prev, closes_prev = {}, {}
            continue
        cd = day_closes(sym, d)
        if cd is None:
            missing_px.append(d)
            snaps_prev, closes_prev = {}, {}
            continue

        # previous day's tail + this day: enough for any lookahead that crosses midnight
        snaps = {**snaps_prev, **sd}
        closes = {**closes_prev, **cd}
        seen_snapshots += len(sd)

        for t in sorted(sd):
            for bname, band in BANDS.items():
                d0 = E.band_notional(snaps[t], *band)
                if d0 <= 0:
                    continue
                m0 = (t // 60000) * 60000
                c0 = closes.get(m0)
                if not c0 or c0 <= 0:
                    continue
                for h in HORIZONS:
                    key = (bname, h)
                    step = h * 60000
                    le = last_emit[key]
                    if le is not None and t - le < step:
                        continue                    # stride applied during accumulation
                    s2 = snaps.get(t + step)
                    c1 = closes.get(m0 + step)
                    if s2 is None or not c1:
                        continue
                    d1 = E.band_notional(s2, *band)
                    if d1 <= 0:
                        continue
                    rows[key].append((d1 / d0, abs(c1 - c0) / c0 * 100.0, t))
                    last_emit[key] = t

        cutoff = max(sd) - MAX_H_MS
        snaps_prev = {t: v for t, v in sd.items() if t >= cutoff}
        closes_prev = {t: v for t, v in cd.items() if t >= cutoff - 60000}

        if (i + 1) % 120 == 0:
            n = len(rows[("0.2-1%", 5)])
            print(f"  {d}  {i+1}/{len(days)} days   rows(0.2-1%,5m)={n:,}", flush=True)

    return rows, {"missing_depth": missing_depth, "missing_px": missing_px,
                  "snapshots": seen_snapshots}


def buckets(rows, quantiles=(0.5, 0.9, 0.99, 0.999)):
    if len(rows) < 50:
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


def run(sym="BTCUSDT"):
    days = cached_days(sym)
    print(f"{sym}: {len(days)} cached days, {days[0]} -> {days[-1]}", flush=True)
    t0 = time.time()
    rows, meta = collect(sym, days)
    print(f"  streamed {meta['snapshots']:,} snapshots in {time.time()-t0:.0f}s", flush=True)

    result = {"symbol": sym,
              "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "days": len(days), "first_day": days[0], "last_day": days[-1],
              "snapshots": meta["snapshots"],
              "missing_depth_days": len(meta["missing_depth"]),
              "missing_price_days": len(meta["missing_px"]),
              "bands": {b: {} for b in BANDS}}

    for (bname, h), r in rows.items():
        bk = buckets(r)
        result["bands"][bname][f"{h}m"] = {"non_overlapping": len(r), "buckets": bk}
        print(f"\n  band {bname}  horizon {h}m   independent rows {len(r):,}", flush=True)
        for x in bk:
            print(f"    move {x['move_lo_pct']:6.3f}–{x['move_hi_pct']:6.3f}%  "
                  f"n={x['n']:>6,}  days={x['distinct_days']:>4}  "
                  f"median {x['median_rel_depth']:.4f}  p25 {x['p25']:.4f}", flush=True)

    json.dump(result, open(OUT, "w"), indent=1)
    print(f"\nwritten to {OUT}   ({time.time()-t0:.0f}s total)")
    return result


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT")
