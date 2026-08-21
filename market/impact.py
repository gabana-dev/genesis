"""
IMPACT-1 (feasibility) — given the depth that was actually there, how far did price move?

WHY THIS AND NOT ANOTHER SIGNAL. Every idea this project has killed was a PREDICTION about the
market: will the cluster be reached (F-0010, refuted), does vulnerability rank anything (F-0012,
refuted), do survivors differ from casualties (F-0013, unmeasurable). This is a different kind of
object -- **the cost of the trader's own action**. It is verifiable the moment they trade, and it
is the one category CONTRACT/business-plan §7 permits us to sell.

    "Closing $2.1M right now costs roughly X basis points."

And it is better than a naive estimate for a reason we already measured: every execution model
assumes the book stays put. F-0002 measured that it does not -- near-book depth falls to 0.846
during large moves and 0.657 in the worst quarter. The cost that matters is the cost under
stress, which is exactly where a static book lies.

THIS IS A FEASIBILITY MEASUREMENT, NOT A FINDING. It runs before any contract, to establish
whether the relationship exists and is stable enough to be worth pre-registering. Nothing here
may be published as a claim.

INPUTS, both free and already on disk:
  bookDepth   notional at +/-0.2/1/2/3/4/5% of mid, every 30s, 1,324 days from 2023
  1m klines   open/high/low/close/volume/quote_volume/trades, 91 months from 2019
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import bookdepth as BD

EVIDENCE = os.path.expanduser("~/genesis-evidence")
DEPTH_DIR = f"{EVIDENCE}/bookdepth/BTCUSDT"
KLINES = f"{EVIDENCE}/market-data"

# The band the cost question actually lives in. A position being closed in a hurry eats the near
# book; the 5% shelf is irrelevant to a market order that finishes in seconds.
BAND = 1.0

# Buckets of "how much of the visible book did the minute's volume represent". Wide, because the
# distribution is heavily skewed and the interesting region is the tail.
RATIO_BINS = [0.0, 0.05, 0.1, 0.2, 0.35, 0.6, 1.0, 2.0, 5.0, 1e9]


def depth_series(path):
    """{minute_ms: notional within ±BAND%} for one day, taking the last snapshot in each minute.

    Last rather than first: the question is what depth was standing when the volume arrived, and
    a snapshot 55 seconds stale is a worse answer than one 5 seconds stale.
    """
    per_minute = {}
    for ts, pct, _depth, notional in BD.read_day(path):
        if abs(pct) > BAND:
            continue
        minute = ts - (ts % 60000)
        slot = per_minute.setdefault(minute, {"ts": 0, "notional": 0.0})
        if ts >= slot["ts"]:
            if ts > slot["ts"]:
                slot["ts"], slot["notional"] = ts, 0.0
            slot["notional"] += notional
    return {m: v["notional"] for m, v in per_minute.items() if v["notional"] > 0}


def klines_by_minute(year_month):
    """{minute_ms: (open, high, low, close, quote_volume, trades)} from the cached npy."""
    import numpy as np
    path = f"{KLINES}/BTCUSDT-1m-{year_month}.npy"
    if not os.path.exists(path):
        return {}
    a = np.load(path)
    # 9 columns: open_time, o, h, l, c, volume, close_time, quote_volume, trades
    return {int(r[0]): (r[1], r[2], r[3], r[4], r[7], r[8]) for r in a}


def run_controlled(days, verbose=True):
    """THE TEST THAT MATTERS.

    High volume and a wide range occur in the same minutes because volatility causes both. A
    relationship between the two proves nothing on its own -- that is precisely how CASCADE-1
    died, beating a permutation null and losing to a volatility-matched control.

    So: condition on the PREVIOUS minute's range, which is volatility already in progress and
    cannot be caused by this minute's volume. Within each prior-volatility band, does the
    volume/depth ratio still separate the outcomes? If it does not, this is the same illusion.
    """
    files = sorted(os.listdir(DEPTH_DIR))[:days]
    # (prior-range band, ratio band) -> moves
    cells = defaultdict(list)
    PRIOR = [0, 5, 10, 20, 40, 1e9]
    kl_cache = {}

    for i, fn in enumerate(files):
        ym = fn.split("-bookDepth-")[1][:7]
        if ym not in kl_cache:
            kl_cache = {ym: klines_by_minute(ym)}
        kl = kl_cache[ym]
        if not kl:
            continue
        try:
            depth = depth_series(f"{DEPTH_DIR}/{fn}")
        except Exception:
            continue

        for minute, notional in depth.items():
            bar, prev = kl.get(minute), kl.get(minute - 60000)
            if bar is None or prev is None:
                continue
            o, h, l, c, qv, _t = bar
            po, ph, pl, _pc, _pqv, _pt = prev
            if o <= 0 or po <= 0 or notional <= 0 or qv <= 0:
                continue
            prior_bps = (ph - pl) / po * 10000
            ratio = qv / notional
            move_bps = (h - l) / o * 10000
            pb = next(b for b, nb in zip(PRIOR, PRIOR[1:]) if b <= prior_bps < nb)
            for lo, hi in zip(RATIO_BINS, RATIO_BINS[1:]):
                if lo <= ratio < hi:
                    cells[(pb, lo)].append(move_bps)
                    break

        if verbose and (i + 1) % 90 == 0:
            print(f"  {i+1}/{len(files)} days", flush=True)
    return cells, PRIOR


def summarise_controlled(cells, PRIOR):
    import statistics
    ratios = sorted({r for _, r in cells})
    print(f"\nMedian move (bps), by PRIOR minute's range and volume/depth ratio")
    print("If the ratio adds nothing beyond volatility already in progress, rows are flat.\n")
    head = "prior range".ljust(16) + "".join(f"{r:g}+".rjust(11) for r in ratios)
    print(head)
    for pb, nb in zip(PRIOR, PRIOR[1:]):
        line = (f"{pb:g}-{nb:g} bps" if nb < 1e8 else f"{pb:g}+ bps").ljust(16)
        any_cell = False
        for r in ratios:
            v = cells.get((pb, r), [])
            line += (f"{statistics.median(v):.0f} ({len(v)//1000}k)".rjust(11)
                     if len(v) >= 300 else "-".rjust(11))
            any_cell |= len(v) >= 300
        if any_cell:
            print(line)


def run(days, verbose=True):
    """Join depth to the following minute's volume and price move."""
    files = sorted(os.listdir(DEPTH_DIR))[:days]
    buckets = defaultdict(list)
    kl_cache = {}
    joined = skipped = 0

    for i, fn in enumerate(files):
        ym = fn.split("-bookDepth-")[1][:7]
        if ym not in kl_cache:
            kl_cache = {ym: klines_by_minute(ym)}     # one month resident at a time
        kl = kl_cache[ym]
        if not kl:
            continue
        try:
            depth = depth_series(f"{DEPTH_DIR}/{fn}")
        except Exception:
            continue

        for minute, notional in depth.items():
            bar = kl.get(minute)
            if bar is None:
                skipped += 1
                continue
            o, h, l, c, qv, _trades = bar
            if o <= 0 or notional <= 0 or qv <= 0:
                continue
            # RATIO: quote volume traded, against the notional standing within +/-1%.
            ratio = qv / notional
            # MOVE: the full excursion, not close-open. A market order pays the excursion; a
            # minute that round-trips still cost the trader who crossed it.
            move_bps = (h - l) / o * 10000
            for lo, hi in zip(RATIO_BINS, RATIO_BINS[1:]):
                if lo <= ratio < hi:
                    buckets[(lo, hi)].append(move_bps)
                    break
            joined += 1

        if verbose and (i + 1) % 60 == 0:
            print(f"  {i+1}/{len(files)} days, {joined:,} minutes joined", flush=True)

    return buckets, joined, skipped


def summarise(buckets, joined, skipped):
    import statistics
    print(f"\n{joined:,} minutes joined, {skipped:,} unmatched\n")
    print(f"{'volume / depth(±1%)':<22}{'n':>10}{'median bps':>13}{'p75':>9}{'p95':>9}")
    rows = []
    for (lo, hi), moves in sorted(buckets.items()):
        if len(moves) < 200:
            continue
        moves.sort()
        med = statistics.median(moves)
        p75 = moves[int(len(moves) * 0.75)]
        p95 = moves[int(len(moves) * 0.95)]
        label = f"{lo:g} – {hi:g}" if hi < 1e8 else f"{lo:g}+"
        print(f"{label:<22}{len(moves):>10,}{med:>13.1f}{p75:>9.1f}{p95:>9.1f}")
        rows.append({"lo": lo, "hi": hi, "n": len(moves), "median_bps": med,
                     "p75_bps": p75, "p95_bps": p95})
    return rows


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    print(f"IMPACT-1 feasibility — {days} days of bookDepth joined to 1m klines")
    b, j, s = run(days)
    rows = summarise(b, j, s)
    out = f"{EVIDENCE}/impact-feasibility.json"
    json.dump({"band_pct": BAND, "days": days, "joined": j, "buckets": rows},
              open(out, "w"), indent=1)
    print(f"\nwritten to {out}")
    print("\nFEASIBILITY ONLY. Nothing here may be published as a claim.")
