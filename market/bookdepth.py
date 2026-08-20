"""
Binance historical order-book depth — the free input for cascade modelling.

WHAT THIS IS
    `data.binance.vision/data/futures/um/daily/bookDepth/` publishes, per symbol per day:

        timestamp, percentage, depth, notional

    Twelve levels per snapshot -- +/-0.2%, 1%, 2%, 3%, 4%, 5% from mid -- every 30 seconds.
    Roughly 0.55 MB zipped per symbol-day, so three years of one symbol is about 600 MB.
    Verified available from 2023; 2022 returns 404.

WHY IT MATTERS
    Every liquidation heatmap on the market assumes the order book stands still while a cascade
    runs. It does not: liquidity is withdrawn precisely when price moves fast, which is why
    cascades cascade. This dataset measures that directly, over years, for free.

    It is also the input to the only number nobody publishes -- if forced flow of size S hits,
    how far does price travel before the book absorbs it.

DEPENDENCIES: stdlib only, deliberately.
    The collector on the production server must never need a wheel to build, so nothing in the
    Genesis data path may require one. numpy is used for analysis, never for fetching.
"""

import io
import os
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date, timedelta

BASE = ("https://data.binance.vision/data/futures/um/daily/bookDepth/"
        "{sym}/{sym}-bookDepth-{d}.zip")
CACHE = os.path.expanduser("~/genesis-evidence/bookdepth")

# The twelve levels the venue publishes. Fixed by the source, not chosen by us.
LEVELS = (-5.0, -4.0, -3.0, -2.0, -1.0, -0.2, 0.2, 1.0, 2.0, 3.0, 4.0, 5.0)


def _cache_path(sym, d):
    return os.path.join(CACHE, sym, f"{sym}-bookDepth-{d}.zip")


def fetch_day(sym, d, retries=3):
    """
    One symbol-day, cached. Returns the local path, or None when the venue has no file.

    A 404 is a fact about the archive, not a failure: coverage genuinely starts in 2023 and
    individual days are occasionally missing. Those are recorded by the caller rather than
    retried forever.
    """
    p = _cache_path(sym, d)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return p
    os.makedirs(os.path.dirname(p), exist_ok=True)
    url = BASE.format(sym=sym, d=d)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                raw = r.read()
            tmp = p + ".part"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, p)          # never leave a half-written zip in the cache
            return p
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 ** attempt)
        except Exception:
            time.sleep(2 ** attempt)
    return None


def read_day(path):
    """
    Rows from one cached zip as (timestamp_ms, percentage, depth, notional).

    Timestamps are 'YYYY-MM-DD HH:MM:SS' UTC in the source. They are converted to epoch
    MILLISECONDS here and never handled as strings downstream -- the seconds/milliseconds
    boundary has already cost this project one crash, and an ASOF join against the wrong unit
    fails silently rather than loudly.
    """
    import calendar
    out = []
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        for i, line in enumerate(z.read(name).decode().splitlines()):
            if i == 0 and line.startswith("timestamp"):
                continue
            try:
                ts, pct, depth, notional = line.split(",")
                t = calendar.timegm(time.strptime(ts, "%Y-%m-%d %H:%M:%S")) * 1000
                out.append((t, float(pct), float(depth), float(notional)))
            except (ValueError, IndexError):
                continue
    return out


def pull(sym, start, end, progress_every=30):
    """
    Cache every day in [start, end]. Idempotent and resumable: existing files are not refetched,
    so an interrupted pull continues rather than restarting.
    """
    d, got, missing, bytes_ = start, 0, [], 0
    t0 = time.time()
    while d <= end:
        ds = d.isoformat()
        p = fetch_day(sym, ds)
        if p:
            got += 1
            bytes_ += os.path.getsize(p)
        else:
            missing.append(ds)
        if got and got % progress_every == 0:
            el = time.time() - t0
            print(f"  {ds}  {got} days  {bytes_/1e6:.0f} MB  "
                  f"{got/max(el,1):.1f} days/s  {len(missing)} missing", flush=True)
        d += timedelta(days=1)
    return {"symbol": sym, "days": got, "missing": missing,
            "bytes": bytes_, "elapsed_s": round(time.time() - t0)}


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    start = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date(2023, 1, 1)
    end = date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else date.today() - timedelta(days=1)
    print(f"pulling {sym} bookDepth {start} -> {end}")
    r = pull(sym, start, end)
    print(f"\n{r['days']} days, {r['bytes']/1e6:.0f} MB, {len(r['missing'])} missing, "
          f"{r['elapsed_s']}s")
    if r["missing"]:
        print(f"missing days (first 10): {r['missing'][:10]}")


# ---------------------------------------------------------------------------------------
# Prices. bookDepth publishes notional at percentage offsets and NEVER the price itself, so
# any move calculation has to come from klines joined on time.
# ---------------------------------------------------------------------------------------

KLINE_BASE = ("https://data.binance.vision/data/futures/um/daily/klines/"
              "{sym}/{iv}/{sym}-{iv}-{d}.zip")
KLINE_CACHE = os.path.expanduser("~/genesis-evidence/market-data/futures-daily")


def fetch_klines(sym, d, interval="1m", retries=3):
    """
    One symbol-day of klines, cached.

    DAILY, not monthly: the monthly archive is only published after a month closes, so the
    current month is always absent from it. breadth.month() returns None for August for exactly
    that reason, which is correct behaviour and the wrong tool here.
    """
    p = os.path.join(KLINE_CACHE, sym, interval, f"{sym}-{interval}-{d}.zip")
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return p
    os.makedirs(os.path.dirname(p), exist_ok=True)
    url = KLINE_BASE.format(sym=sym, iv=interval, d=d)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                raw = r.read()
            tmp = p + ".part"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, p)
            return p
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 ** attempt)
        except Exception:
            time.sleep(2 ** attempt)
    return None


def read_klines(path):
    """(open_time_ms, open, high, low, close) per bar. Times are already epoch ms in the source."""
    out = []
    with zipfile.ZipFile(path) as z:
        for i, line in enumerate(z.read(z.namelist()[0]).decode().splitlines()):
            f = line.split(",")
            if i == 0 and not f[0].lstrip("-").isdigit():
                continue
            try:
                out.append((int(f[0]), float(f[1]), float(f[2]), float(f[3]), float(f[4])))
            except (ValueError, IndexError):
                continue
    return out
