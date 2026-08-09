"""
Step 4-6 of the harness: resolution-transition handling, interval-ending validation,
canonical 30-minute series construction.

The 2021 resolution change is treated as an explicit, tested data boundary rather than
something hidden inside preprocessing:

  * through 2021-09 the source is ALREADY 30-minute -- used as-is, never resampled;
  * from 2021-10 the source is 5-minute -- exactly six intervals aggregated per 30 minutes;
  * the result is exactly one canonical observation per 30-minute interval, with no
    duplicated, missing, shifted, or cross-boundary-mixed intervals.

Timestamps are interval-ENDING and this is VERIFIED from the raw data (see
verify_interval_ending), not assumed.
"""

import pandas as pd

from config import (FREQ, NATIVE_30MIN_THROUGH, RAW_DEV, RAW_HOLDOUT, REGION, TARGET,
                    require_holdout_unlocked)


def _read_month(path):
    df = pd.read_csv(path, usecols=["SETTLEMENTDATE", TARGET], parse_dates=["SETTLEMENTDATE"])
    return df.set_index("SETTLEMENTDATE")[TARGET].sort_index()


def native_resolution(ym):
    """'30min' or '5min' for a YYYYMM string, per the contract's declared boundary."""
    return "30min" if ym[:4] + "-" + ym[4:6] <= NATIVE_30MIN_THROUGH else "5min"


def verify_interval_ending(s, ym):
    """
    Interval-ending means the first observation of a month is one interval AFTER midnight
    and the last is exactly midnight of the following month. Under interval-starting the
    first observation would be 00:00. Verified per month rather than assumed once.
    """
    first, last = s.index[0], s.index[-1]
    step = pd.Timedelta(minutes=30 if native_resolution(ym) == "30min" else 5)
    month_start = pd.Timestamp(f"{ym[:4]}-{ym[4:6]}-01")
    next_month = month_start + pd.offsets.MonthBegin(1)
    if first != month_start + step:
        raise ValueError(f"{ym}: first stamp {first} != {month_start + step} (interval-ending broken)")
    if last != next_month:
        raise ValueError(f"{ym}: last stamp {last} != {next_month} (interval-ending broken)")
    expected = int((next_month - month_start) / step)
    if len(s) != expected:
        raise ValueError(f"{ym}: {len(s)} rows, expected {expected} (gaps or duplicates)")
    return True


def to_canonical_30min(s, ym):
    """
    Native 30-minute months pass through untouched. Native 5-minute months aggregate
    exactly six intervals per 30-minute period, preserving the interval-ending label
    (closed='right', label='right'), so 00:05..00:30 becomes the interval ending 00:30.
    """
    if native_resolution(ym) == "30min":
        return s
    agg = s.resample(FREQ, closed="right", label="right").mean()
    counts = s.resample(FREQ, closed="right", label="right").count()
    if not (counts == 6).all():
        bad = counts[counts != 6]
        raise ValueError(f"{ym}: {len(bad)} periods did not aggregate exactly 6 intervals")
    return agg


def build(period="dev"):
    """Assemble the canonical 30-minute series for a period, validating every month."""
    if period == "dev":
        raw_dir = RAW_DEV
    else:
        require_holdout_unlocked()
        raw_dir = RAW_HOLDOUT

    parts = []
    for path in sorted(raw_dir.glob(f"*_{REGION}.csv")):
        ym = path.name.split("_")[0]
        s = _read_month(path)
        verify_interval_ending(s, ym)
        parts.append(to_canonical_30min(s, ym))

    out = pd.concat(parts).sort_index()
    if out.index.has_duplicates:
        dupes = out.index[out.index.duplicated()]
        raise ValueError(f"duplicate canonical stamps: {dupes[:5].tolist()}")
    full = pd.date_range(out.index[0], out.index[-1], freq=FREQ)
    if len(full) != len(out):
        missing = full.difference(out.index)
        raise ValueError(f"{len(missing)} missing 30-min intervals, first: {missing[:5].tolist()}")
    out.name = TARGET
    return out


if __name__ == "__main__":
    s = build("dev")
    print(f"canonical 30-min series: {len(s)} obs  {s.index[0]} -> {s.index[-1]}")
    print(f"NaNs: {s.isna().sum()}   min {s.min():.1f}  mean {s.mean():.1f}  max {s.max():.1f}")
