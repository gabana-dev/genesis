"""
RDB-1 harness checks. These target ingestion and series-construction defects, which are
the failure modes most likely to silently invalidate every downstream result.

Specifically covered, per the milestone instruction:
  * the September/October 2021 native-resolution boundary;
  * the interval-ending convention, verified from raw data rather than assumed;
  * no duplicated, missing, shifted, or cross-boundary-mixed intervals;
  * holdout inaccessibility before the design is frozen.

Run: .venv/bin/python tests/test_rdb_series.py
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rdb"))

import config
import series
from ingest import months


def test_month_enumeration():
    assert months("2015-01", "2015-03") == ["201501", "201502", "201503"]
    assert len(months("2015-01", "2022-12")) == 96
    assert len(months("2023-01", "2026-06")) == 42


def test_native_resolution_boundary():
    assert series.native_resolution("202108") == "30min"
    assert series.native_resolution("202109") == "30min"   # last native 30-min month
    assert series.native_resolution("202110") == "5min"    # 5-minute settlement go-live
    assert series.native_resolution("202111") == "5min"


def test_september_october_2021_boundary_is_seamless():
    """The riskiest join in the dataset: 30-min September meets 5-min October."""
    sep = series._read_month(config.RAW_DEV / "202109_NSW1.csv")
    oct_ = series._read_month(config.RAW_DEV / "202110_NSW1.csv")
    series.verify_interval_ending(sep, "202109")
    series.verify_interval_ending(oct_, "202110")

    sep_c = series.to_canonical_30min(sep, "202109")
    oct_c = series.to_canonical_30min(oct_, "202110")

    # September's last canonical stamp is midnight 1 Oct; October's first is 00:30 the same
    # day. Adjacent, not overlapping -- no duplicate and no gap across the boundary.
    assert sep_c.index[-1] == pd.Timestamp("2021-10-01 00:00:00")
    assert oct_c.index[0] == pd.Timestamp("2021-10-01 00:30:00")
    assert oct_c.index[0] - sep_c.index[-1] == pd.Timedelta(minutes=30)
    assert sep_c.index.intersection(oct_c.index).empty


def test_five_minute_aggregation_uses_exactly_six_intervals():
    oct_ = series._read_month(config.RAW_DEV / "202110_NSW1.csv")
    counts = oct_.resample("30min", closed="right", label="right").count()
    assert (counts == 6).all(), "a 30-min period did not receive exactly six 5-min intervals"
    agg = series.to_canonical_30min(oct_, "202110")
    assert len(agg) == 31 * 48
    # the aggregate is the mean of its six constituents, at the interval-ending label
    first_six = oct_.loc["2021-10-01 00:05":"2021-10-01 00:30"]
    assert len(first_six) == 6
    assert abs(agg.loc["2021-10-01 00:30"] - first_six.mean()) < 1e-9


def test_interval_ending_verified_not_assumed():
    """A month starting at 00:00 would indicate interval-STARTING and must be rejected."""
    s = series._read_month(config.RAW_DEV / "201501_NSW1.csv")
    assert s.index[0] == pd.Timestamp("2015-01-01 00:30:00")
    assert s.index[-1] == pd.Timestamp("2015-02-01 00:00:00")
    shifted = s.copy()
    shifted.index = shifted.index - pd.Timedelta(minutes=30)
    try:
        series.verify_interval_ending(shifted, "201501")
    except ValueError:
        return
    raise AssertionError("interval-ending validation failed to reject a shifted index")


def test_no_dst_gaps_in_market_time():
    """NEM market time does not observe DST: April and October have exactly 48 intervals/day."""
    for ym, days in (("202004", 30), ("202010", 31)):
        s = series._read_month(config.RAW_DEV / f"{ym}_NSW1.csv")
        c = series.to_canonical_30min(s, ym)
        assert len(c) == days * 48, f"{ym}: {len(c)} intervals, expected {days * 48}"


def test_canonical_series_is_complete_and_regular():
    s = series.build("dev")
    assert s.index.freq is None or str(s.index.freq) == "<30 * Minutes>"
    assert not s.index.has_duplicates
    full = pd.date_range(s.index[0], s.index[-1], freq="30min")
    assert len(full) == len(s), "gaps in the canonical series"
    assert s.isna().sum() == 0
    assert s.index[0] == pd.Timestamp("2015-01-01 00:30:00")
    assert s.index[-1] == pd.Timestamp("2023-01-01 00:00:00")


def test_holdout_is_locked():
    assert not config.holdout_unlocked(), "holdout must be locked during development"
    for call in (lambda: series.build("holdout"),):
        try:
            call()
        except config.HoldoutLocked:
            continue
        raise AssertionError("holdout was reachable while locked")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"PASS -- {len(fns)} harness checks")
