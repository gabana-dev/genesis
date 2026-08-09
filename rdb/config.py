"""
RDB-1 frozen contract constants.

Every value here is fixed by the reviewed milestone contract. Changing one changes the
experiment, so they live in one place and are read (never redefined) everywhere else.

Data source: AEMO NEM public price & demand.
  Licence: AEMO Copyright Permissions -- "AEMO confirms its general permission for anyone
  to use AEMO Material for any purpose, but only with accurate and appropriate attribution
  of the relevant AEMO Material and AEMO as its author."
  Required attribution: "Source: AEMO".
"""

from pathlib import Path

REGION = "NSW1"
TARGET = "TOTALDEMAND"

URL = "https://aemo.com.au/aemo/data/nem/priceanddemand/PRICE_AND_DEMAND_{ym}_{region}.csv"

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "rdb_data"
RAW_DEV = DATA / "raw_dev"
RAW_HOLDOUT = DATA / "raw_holdout"
MANIFEST = DATA / "manifest.json"

# Periods (contract). Holdout is not downloaded and not readable until the design is frozen.
DEV_START, DEV_END = "2015-01", "2022-12"
HOLDOUT_START, HOLDOUT_END = "2023-01", "2026-06"

# The source changed native resolution at the 5-minute settlement go-live.
# Verified from row counts: 2021-09 = 1441 rows (30-min), 2021-10 = 8929 rows (5-min).
NATIVE_30MIN_THROUGH = "2021-09"

FREQ = "30min"
STEPS_PER_DAY = 48
STEPS_PER_WEEK = 336
HORIZON = 48                    # 24 hours ahead

# Timestamps are interval-ENDING: the row labelled 00:30 covers 00:00-00:30.
# Treating them as interval-starting would leak 30 minutes of future into every forecast.
INTERVAL_ENDING = True

EXPECTED_COLUMNS = ["REGION", "SETTLEMENTDATE", "TOTALDEMAND", "RRP", "PERIODTYPE"]

ATTRIBUTION = "Source: AEMO. AEMO makes no representation as to the accuracy or completeness of this data."


class HoldoutLocked(Exception):
    """Raised when code attempts to reach the holdout before the design is frozen."""


# Technical holdout protection: flipped only by the explicit freeze step, never by
# development or model-selection code. See rdb/README.md.
FREEZE_MARKER = DATA / "DESIGN_FROZEN"


def holdout_unlocked() -> bool:
    return FREEZE_MARKER.exists()


def require_holdout_unlocked() -> None:
    if not holdout_unlocked():
        raise HoldoutLocked(
            "The 2023-01..2026-06 holdout is locked. It becomes readable only after the "
            "design is frozen and the freeze marker is written. Development and "
            "model-selection runs must never touch it."
        )
