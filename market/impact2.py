"""
IMPACT-1 pre-condition P1 — the cost of ONE sweep, not of one minute.

WHY THIS FILE EXISTS. `market/impact.py` measured, over 635,682 minutes, that the ratio of a
minute's volume to the standing book separates price excursion, and that the separation survives
conditioning on the previous minute's range. That is the control CASCADE-1 lost to, so the
relationship is real at minute resolution.

It is still not the customer's question. A minute whose volume equalled 20% of the book is not
one order eating 20% of the book -- it is hundreds of orders against a book that replenished
between them. `market/CONTRACT-impact.md` P1 therefore forbids quoting any figure in bps or
dollars until impact is estimated at BURST level: a contiguous run of same-side aggressive trades,
priced against the mid where the run began.

Same venue as the depth, deliberately: futures/um, BTCUSDT. bookDepth and aggTrades describe the
same book, so no cross-venue assumption is smuggled in here. (The Hyperliquid transfer is a
separate open question -- F-0006.)

DISK. A day of aggTrades is ~46 MB zipped and ~250 MB open. It is streamed from the zip, reduced
to bursts, and the zip is deleted. Nothing accumulates; only the burst summaries are kept.
"""
import csv
import io
import json
import os
import sys
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
import bookdepth as BD
from impact import BAND, depth_series, klines_by_minute, DEPTH_DIR, EVIDENCE

AGG = ("https://data.binance.vision/data/futures/um/daily/aggTrades/"
       "{sym}/{sym}-aggTrades-{d}.zip")
SCRATCH = os.path.expanduser("~/genesis-evidence/impact-agg")

# A sweep is one intent. 200ms is generous for a taker order working through levels and tight
# enough that two unrelated orders a second apart are not merged into a fictional whale.
GAP_MS = 200

# Only bursts big enough that the cost question is worth asking. Below this the answer is
# "you pay the spread" and no model is needed.
MIN_NOTIONAL = 50_000

RATIO_BINS = [0.0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 1e9]
PRIOR = [0, 5, 10, 20, 40, 1e9]


def bursts(day):
    """Stream one day of aggTrades, yielding (start_ms, side, notional, vwap_bps, disp_bps).

    vwap_bps  what the taker actually paid against the price where the sweep began -- the cost.
    disp_bps  how far the sweep moved the print -- the displacement other people see.

    Both are signed so that positive is adverse to the taker. They differ, and the difference is
    the point: displacement is what a heatmap would show you, cost is what leaves your account.
    """
    url = AGG.format(sym="BTCUSDT", d=day)
    path = f"{SCRATCH}/{day}.zip"
    os.makedirs(SCRATCH, exist_ok=True)
    if not os.path.exists(path):
        try:
            urllib.request.urlretrieve(url, path)
        except Exception:
            if os.path.exists(path):
                os.remove(path)
            return
    try:
        with zipfile.ZipFile(path) as z:
            name = z.namelist()[0]
            with z.open(name) as fh:
                cur = None
                for row in csv.reader(io.TextIOWrapper(fh, "utf-8")):
                    if not row or not row[0].lstrip("-").isdigit():
                        continue          # header row, present on newer days only
                    price = float(row[1])
                    qty = float(row[2])
                    ts = int(row[5])
                    # is_buyer_maker true => the AGGRESSOR was the seller.
                    side = -1 if row[6].lower() in ("true", "1") else 1
                    if cur and (side != cur["side"] or ts - cur["last"] > GAP_MS):
                        out = _close(cur)
                        if out:
                            yield out
                        cur = None
                    if cur is None:
                        cur = {"side": side, "start": ts, "last": ts, "p0": price,
                               "pn": price, "notional": 0.0, "qty": 0.0}
                    cur["last"] = ts
                    cur["pn"] = price
                    cur["notional"] += price * qty
                    cur["qty"] += qty
                if cur:
                    out = _close(cur)
                    if out:
                        yield out
    finally:
        if os.path.exists(path):
            os.remove(path)


def _close(b):
    if b["notional"] < MIN_NOTIONAL or b["qty"] <= 0 or b["p0"] <= 0:
        return None
    vwap = b["notional"] / b["qty"]
    return (b["start"], b["side"], b["notional"],
            (vwap - b["p0"]) / b["p0"] * 1e4 * b["side"],
            (b["pn"] - b["p0"]) / b["p0"] * 1e4 * b["side"])


def run(days, verbose=True):
    cells = defaultdict(list)          # (prior band, ratio band) -> vwap_bps
    disp = defaultdict(list)
    kl_cache = {}
    total = 0

    for i, day in enumerate(days):
        ym = day[:7]
        if ym not in kl_cache:
            kl_cache = {ym: klines_by_minute(ym)}
        kl = kl_cache[ym]
        dpath = f"{DEPTH_DIR}/BTCUSDT-bookDepth-{day}.zip"
        if not kl or not os.path.exists(dpath):
            continue
        try:
            depth = depth_series(dpath)
        except Exception:
            continue

        n = 0
        for start, _side, notional, vwap_bps, disp_bps in bursts(day):
            minute = start - (start % 60000)
            standing = depth.get(minute)
            prev = kl.get(minute - 60000)
            if not standing or prev is None:
                continue
            po, ph, pl = prev[0], prev[1], prev[2]
            if po <= 0:
                continue
            prior_bps = (ph - pl) / po * 1e4
            ratio = notional / standing
            pb = next(b for b, nb in zip(PRIOR, PRIOR[1:]) if b <= prior_bps < nb)
            for lo, hi in zip(RATIO_BINS, RATIO_BINS[1:]):
                if lo <= ratio < hi:
                    cells[(pb, lo)].append(vwap_bps)
                    disp[(pb, lo)].append(disp_bps)
                    break
            n += 1
        total += n
        if verbose:
            print(f"  {day}: {n:,} bursts joined ({i+1}/{len(days)})", flush=True)
    return cells, disp, total


def table(cells, label, min_n=300):
    import statistics
    ratios = sorted({r for _, r in cells})
    print(f"\n{label}")
    print("rows flat => the minute-level result was aggregation artefact (K1 fires)\n")
    print("prior range".ljust(16) + "".join(f"{r:g}+".rjust(13) for r in ratios))
    for pb, nb in zip(PRIOR, PRIOR[1:]):
        line = (f"{pb:g}-{nb:g} bps" if nb < 1e8 else f"{pb:g}+ bps").ljust(16)
        shown = False
        for r in ratios:
            v = cells.get((pb, r), [])
            if len(v) >= min_n:
                line += f"{statistics.median(v):.1f} ({len(v)//1000}k)".rjust(13)
                shown = True
            else:
                line += "-".rjust(13)
        if shown:
            print(line)


def sample_days(every, start="2023-01-01", end="2026-08-19"):
    """Every Nth day across the whole archive, so regimes are not sampled from one bull run."""
    d0 = date.fromisoformat(start)
    d1 = date.fromisoformat(end)
    out, d = [], d0
    while d <= d1:
        out.append(d.isoformat())
        d += timedelta(days=every)
    return out


if __name__ == "__main__":
    every = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    days = sample_days(every)
    print(f"IMPACT-1 P1 — burst-level impact, {len(days)} days sampled every {every}")
    cells, disp, total = run(days)
    print(f"\n{total:,} bursts >= ${MIN_NOTIONAL:,} joined to standing depth")
    table(cells, "COST PAID — median vwap slippage (bps) by prior minute's range x burst/depth")
    table(disp, "DISPLACEMENT — median print movement (bps), same cells")
    out = f"{EVIDENCE}/impact-burst.json"
    json.dump({"days": len(days), "every": every, "gap_ms": GAP_MS,
               "min_notional": MIN_NOTIONAL, "band_pct": BAND, "bursts": total,
               "cost": {f"{p}|{r}": v for (p, r), v in cells.items()},
               }, open(out, "w"))
    print(f"\nwritten to {out}")
    print("\nP1 EVIDENCE. Nothing here may be quoted to a user until CONTRACT-impact.md is frozen.")
