"""
Market data acquisition for MEASURE-1.

Public Binance data only. No credentials, no authenticated endpoints, read-only.
Source: https://data.binance.vision/ monthly kline archives (the bulk mirror of the public
REST klines endpoint; identical content, far fewer requests).

TIMESTAMP SEMANTICS -- verified, not assumed, per CONTRACT-measurement.md section 7.
Column 0 is interval-OPENING time and column 6 is interval-CLOSING time, with
close = open + interval - 1ms. `verify_timestamp_semantics()` re-checks this against the raw
bytes on every ingest. Treating opening as closing would leak a full interval of future into
every return -- the RDB-1 section 2 error class.

Data lives outside the repository (~/genesis-evidence/market-data/) because it is large and
re-downloadable. What the project's claims rest on is committed; bulk inputs are not.
"""

import io
import os
import urllib.error
import urllib.request
import zipfile
from datetime import date

import numpy as np

BASE = "https://data.binance.vision/data/spot/monthly/klines"
CACHE = os.path.expanduser("~/genesis-evidence/market-data")

# Binance kline columns. Only the ones MEASURE-1 uses are retained.
_OPEN_TIME, _OPEN, _HIGH, _LOW, _CLOSE, _VOL, _CLOSE_TIME, _QUOTE_VOL, _TRADES = range(9)

FIELDS = ("open_time", "open", "high", "low", "close", "volume", "quote_volume", "trades")
MINUTE_MS = 60_000


def _months(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def verify_timestamp_semantics(rows, interval_ms=MINUTE_MS):
    """
    Contract section 7. Confirms the interval-OPENING reading against the raw bytes.

    TWO DATA FACTS, both found by this check on the first ingest and neither assumed:

    1. HALT-TRUNCATED BARS. Binance publishes a short final kline at the instant trading
       stops, followed by a gap until it resumes. 2019-06-07 21:13 spans 13,524 ms with zero
       volume and zero trades, then 61 bars are missing. A genuine property of the venue.

    2. `close_time` IS NOT RELIABLE in the bulk archives. 2021-12-24 04:59 spans 54,362 ms
       with 1,124 trades and is followed immediately by an on-schedule 05:00 bar opening at
       the previous close. No halt occurred; the field is simply wrong. An earlier version of
       this function tested opening-semantics via `close_time` and rejected the file.

    The alignment is established by BOUNDARY ALIGNMENT, which depends on neither quirk:
        (a) every `open_time` is an exact multiple of the interval, and
        (b) `close_time == open_time + interval - 1` for the overwhelming majority of bars.
    Together these say the two columns bracket exactly one interval starting at `open_time`,
    which is what "interval-opening" means. If the timestamps were interval-CLOSING, (b)
    would have to read `open_time - interval + 1`.

    A THIRD test was tried and DISCARDED as invalid: `open[i] == close[i-1]`. It fails for
    51.8% of adjacent bars, because the first trade of a minute is not generally at the last
    trade price of the previous minute. That is ordinary microstructure -- a real price jump
    at the boundary -- and not evidence of misalignment. Recorded because it is a fact about
    minute-to-minute price changes that bears on the Roll estimate in section 4H.
    """
    ot, ct = rows[:, _OPEN_TIME], rows[:, _CLOSE_TIME]
    span = (ct - ot).astype(np.int64)
    steps = np.diff(ot).astype(np.int64)
    if not np.all(steps > 0):
        raise ValueError("open_time is not strictly increasing")

    misaligned = int(np.sum(ot.astype(np.int64) % interval_ms != 0))
    if misaligned:
        raise ValueError(f"{misaligned} open_time values are not on an interval boundary")

    short = np.flatnonzero(span != interval_ms - 1)
    if len(short) / len(rows) > 0.01:
        raise ValueError(
            f"close_time != open_time + interval - 1 for {len(short) / len(rows):.2%} of bars "
            f"-- too many to treat as venue quirks; the reading may be wrong")

    halt_like = [int(i) for i in short if i < len(steps) and steps[i] != interval_ms]
    return {
        "interval_ms": int(interval_ms),
        "monotonic": True,
        "all_open_times_on_interval_boundary": True,
        "short_close_time_bars": int(len(short)),
        "of_which_precede_a_halt": len(halt_like),
    }


def _parse(csv_bytes):
    text = csv_bytes.decode()
    lines = text.splitlines()
    if lines and not lines[0][:1].isdigit():      # 2025+ archives carry a header row
        lines = lines[1:]
    out = np.empty((len(lines), 9), dtype=np.float64)
    for i, line in enumerate(lines):
        f = line.split(",")
        out[i] = (float(f[0]), float(f[1]), float(f[2]), float(f[3]), float(f[4]),
                  float(f[5]), float(f[6]), float(f[7]), float(f[8]))

    # UNIT CHANGE. Binance switched the bulk archives from millisecond to MICROSECOND
    # timestamps during 2025; both units appear across the history. Detected by magnitude --
    # ms since epoch is ~1.7e12 for the 2020s, us is ~1.7e15 -- and normalised to ms so the
    # series is homogeneous. Silently concatenating the two would place every 2025+ bar
    # ~50,000 years in the future.
    if out[0, _OPEN_TIME] > 1e14:
        # floor, not plain division: a microsecond close_time of ...59999999 becomes
        # ...59999.999, and the fractional millisecond is not real precision.
        out[:, [_OPEN_TIME, _CLOSE_TIME]] = np.floor(out[:, [_OPEN_TIME, _CLOSE_TIME]] / 1000.0)
    return out


def month(symbol, y, m, interval="1m"):
    """One month of klines as an (n, 9) float64 array. Cached; downloaded once."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{symbol}-{interval}-{y}-{m:02d}.npy")
    if os.path.exists(path):
        return np.load(path)

    name = f"{symbol}-{interval}-{y}-{m:02d}.zip"
    url = f"{BASE}/{symbol}/{interval}/{name}"
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            blob = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None                            # month not published (yet, or ever)
        raise
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        rows = _parse(z.read(z.namelist()[0]))
    verify_timestamp_semantics(rows)
    np.save(path, rows)
    return rows


def load(symbol="BTCUSDT", start=date(2019, 1, 1), end=None, interval="1m", log=print):
    """
    The full 1-minute series, concatenated and integrity-checked.

    Returns (rows, facts). `facts` records what was verified rather than assumed: timestamp
    semantics, coverage, and every gap found. Gaps are REPORTED, never interpolated -- an
    invented bar is an invented observation.
    """
    end = end or date.today()
    parts, missing = [], []
    for y, m in _months(start, end):
        r = month(symbol, y, m, interval)
        if r is None:
            missing.append(f"{y}-{m:02d}")
            continue
        parts.append(r)
        if log and len(parts) % 12 == 0:
            log(f"  {symbol} {interval}: {y}-{m:02d}  ({sum(len(p) for p in parts):,} bars)")
    if not parts:
        raise RuntimeError(f"no data for {symbol} {start}..{end}")

    rows = np.concatenate(parts)
    ts = rows[:, _OPEN_TIME]
    step = MINUTE_MS if interval == "1m" else int(np.median(np.diff(ts)))
    d = np.diff(ts).astype(np.int64)
    gap_at = np.flatnonzero(d != step)
    gap_bars = (d[gap_at] // step - 1) if len(gap_at) else np.array([], dtype=np.int64)
    facts = {
        "symbol": symbol,
        "interval": interval,
        "timestamps": verify_timestamp_semantics(rows, step),
        "n_bars": int(len(rows)),
        "first": int(ts[0]),
        "last": int(ts[-1]),
        "months_missing": missing,
        "n_halts": int(len(gap_at)),
        "missing_bars": int(gap_bars.sum()) if len(gap_at) else 0,
        "largest_halt_minutes": int(gap_bars.max()) if len(gap_at) else 0,
        "duplicate_timestamps": int(np.sum(d == 0)),
        "halt_index": gap_at.astype(np.int64).tolist(),
    }
    facts["missing_fraction"] = facts["missing_bars"] / (facts["n_bars"] + facts["missing_bars"])
    return rows, facts


def contiguous_segments(rows, facts):
    """
    Split the series at every halt, so that aggregation never merges two bars that are not
    actually adjacent in time.

    Aggregating across a halt would manufacture a "1-hour return" spanning six real hours and
    label it as an ordinary observation -- an invented observation, which is the one thing the
    project does not do. Segments are returned; how they are used is the caller's decision.
    """
    cuts = [0] + [i + 1 for i in facts["halt_index"]] + [len(rows)]
    return [rows[a:b] for a, b in zip(cuts, cuts[1:]) if b > a]


def close(rows):
    return rows[:, _CLOSE]


def quote_volume(rows):
    return rows[:, _QUOTE_VOL]


def high_low(rows):
    return rows[:, _HIGH], rows[:, _LOW]


def open_time(rows):
    return rows[:, _OPEN_TIME]


def aggregate(rows, k):
    """
    Aggregate k consecutive 1-minute bars. Aggregation is by POSITION, and the caller must
    have established that the series is gap-free (or accept that a gap merges two
    non-adjacent bars). `load` reports gaps precisely so this choice is visible.
    """
    n = (len(rows) // k) * k
    r = rows[:n].reshape(-1, k, rows.shape[1])
    out = np.empty((r.shape[0], rows.shape[1]), dtype=np.float64)
    out[:, _OPEN_TIME] = r[:, 0, _OPEN_TIME]
    out[:, _OPEN] = r[:, 0, _OPEN]
    out[:, _HIGH] = r[:, :, _HIGH].max(axis=1)
    out[:, _LOW] = r[:, :, _LOW].min(axis=1)
    out[:, _CLOSE] = r[:, -1, _CLOSE]
    out[:, _VOL] = r[:, :, _VOL].sum(axis=1)
    out[:, _CLOSE_TIME] = r[:, -1, _CLOSE_TIME]
    out[:, _QUOTE_VOL] = r[:, :, _QUOTE_VOL].sum(axis=1)
    out[:, _TRADES] = r[:, :, _TRADES].sum(axis=1)
    return out


def log_returns(prices):
    return np.diff(np.log(prices))


HORIZONS = (("1m", 1), ("5m", 5), ("15m", 15), ("1h", 60),
            ("4h", 240), ("1d", 1440), ("3d", 4320))
