"""
Evaporation across the full cached history, at several bands and horizons.

Reports `distinct_days` on every bucket. Volatility clusters, so a bucket with 200 observations
drawn from three days is three observations wearing a costume, and the count alone would hide
that. This is the same failure the power audit found in GEN-1 and that turned up twice more
while building this module.

Run:  .venv/bin/python market/evaporation_run.py [symbol]
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import bookdepth as B  # noqa: E402
import evaporation as E  # noqa: E402

OUT = os.path.expanduser("~/genesis-evidence/bookdepth/evaporation.json")

# Declared before the run. Bands are the venue's own published levels; horizons bracket the
# timescale a liquidation cascade resolves on.
BANDS = {"0.2-1%": (0.2, 1.0), "2-5%": (2.0, 5.0)}
HORIZONS = (1, 5, 15)


def cached_days(sym):
    d = os.path.join(B.CACHE, sym)
    return sorted(f.split("-bookDepth-")[1].replace(".zip", "") for f in os.listdir(d))


def load_prices(sym, days):
    closes, missing = {}, []
    for d in days:
        p = B.fetch_klines(sym, d, "1m")
        if not p:
            missing.append(d)
            continue
        for t, _o, _h, _l, c in B.read_klines(p):
            closes[t] = c
    return closes, missing


def run(sym="BTCUSDT"):
    days = cached_days(sym)
    print(f"{sym}: {len(days)} cached days, {days[0]} -> {days[-1]}", flush=True)

    t0 = time.time()
    snaps, missing_depth = E.load(sym, days)
    print(f"  depth snapshots: {len(snaps):,}  ({time.time()-t0:.0f}s)", flush=True)
    closes, missing_px = load_prices(sym, days)
    print(f"  price bars: {len(closes):,}  missing price days: {len(missing_px)}", flush=True)

    result = {"symbol": sym, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "days": len(days), "first_day": days[0], "last_day": days[-1],
              "snapshots": len(snaps), "missing_depth_days": len(missing_depth),
              "missing_price_days": len(missing_px), "bands": {}}

    for bname, band in BANDS.items():
        result["bands"][bname] = {}
        for h in HORIZONS:
            h_ms = h * 60000
            rows = []
            for t, s in snaps.items():
                s2 = snaps.get(t + h_ms)
                if s2 is None:
                    continue
                d0 = E.band_notional(s, *band)
                d1 = E.band_notional(s2, *band)
                if d0 <= 0 or d1 <= 0:
                    continue
                m0 = (t // 60000) * 60000
                c0, c1 = closes.get(m0), closes.get(m0 + h_ms)
                if not c0 or not c1 or c0 <= 0:
                    continue
                rows.append((d1 / d0, abs(c1 - c0) / c0 * 100.0, t))

            nov = E.non_overlapping(rows, h)
            buckets = E.evaporation_by_bucket(nov)
            result["bands"][bname][f"{h}m"] = {
                "raw": len(rows), "non_overlapping": len(nov), "buckets": buckets}

            print(f"\n  band {bname}  horizon {h}m   "
                  f"raw {len(rows):,} -> independent {len(nov):,}", flush=True)
            for r in buckets:
                print(f"    move {r['move_lo_pct']:6.3f}–{r['move_hi_pct']:6.3f}%  "
                      f"n={r['n']:>6,}  days={r['distinct_days']:>4}  "
                      f"median {r['median_rel_depth']:.4f}  p25 {r['p25']:.4f}", flush=True)

    json.dump(result, open(OUT, "w"), indent=1)
    print(f"\nwritten to {OUT}   ({time.time()-t0:.0f}s total)")
    return result


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT")
