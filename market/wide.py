"""
WIDE-1 — a second, wider wallet population, deliberately separate from the frozen LIQ-2 archive.

WHY SEPARATE, AND WHY THIS MATTERS MORE THAN IT SOUNDS. LIQ-2's universe is frozen at 5,395
wallets by contract, so that coverage is comparable across every snapshot ever taken: a universe
that grew with the recording would widen the numerator while the denominator stayed the exchange,
and every published coverage figure would silently drift upward for no reason. That freeze is
correct and it is not being touched. This file writes to its own archive and never opens LIQ-2's.

WHY IT EXISTS NOW. The recording has since discovered **51,765** distinct wallets, of which 46,370
appeared after the freeze. F-0016 measured that nine public market-state variables carry no
information about forward trading conditions beyond the trailing tape -- and noted the half that
measurement could not reach: the quantities that are actually ours (per-wallet collateral,
concentration, exposure against the book) could not be screened because the archive is days old
where the test needed years. Widening the population now is what makes that screen possible later.

WHY A SAMPLE RATHER THAN ALL 51,765. A full pass costs about five hours of continuous requests,
which would contend with the LIQ-2 scans for the same rate budget and risk damaging the archive
that is already working. A UNIFORM RANDOM SAMPLE, frozen once with its seed recorded, is both
cheaper and better for the longitudinal question: the same wallets are followed through time, so
a change in the aggregate is a change in behaviour rather than a change in who was looked at.
That is precisely the confound F-0011 caught in the fast tier and F-0013 could not escape.

WHAT THIS IS NOT. It does not improve the coverage figure the site publishes. That figure belongs
to LIQ-2 and stays LIQ-2's. This is a research archive, and anything derived from it must say so.
"""
import json
import os
import random
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import liqmap as L

STATE_DIR = L.STATE_DIR
WIDESET_PATH = f"{STATE_DIR}/wideset.json"
WIDE_SNAP_PATH = f"{STATE_DIR}/snapshots-wide.jsonl"

N_SAMPLE = 8000
SEED = 20260822          # recorded so the draw is reproducible and cannot be quietly re-rolled


def build_wideset(recording=L.HL1, n=N_SAMPLE, seed=SEED, refresh=False):
    """Freeze a uniform random sample of every wallet the recording has seen.

    Frozen on first call for the same reason LIQ-2's universe is: a sample that is re-drawn each
    run measures a different population each run, and no change over time means anything.
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    if os.path.exists(WIDESET_PATH) and not refresh:
        return json.load(open(WIDESET_PATH))["wallets"]
    from hl_harvest import wallets_from_recording
    allw = wallets_from_recording(recording)
    rng = random.Random(seed)
    # Sorted before sampling: wallets_from_recording orders by trade frequency, so sampling the
    # raw order with a seeded rng would still be reproducible but would depend on the recording's
    # length. Sorting makes the draw a function of the wallet set alone.
    pool = sorted(set(allw))
    wallets = rng.sample(pool, min(n, len(pool)))
    json.dump({"wallets": wallets, "n": len(wallets), "drawn_from": len(pool),
               "seed": seed, "source": recording,
               "fixed_at": datetime.now(timezone.utc).isoformat()},
              open(WIDESET_PATH, "w"))
    return wallets


def collect(verbose=True):
    wallets = build_wideset()
    budget = {"sleep": L.BASE_SLEEP, "throttled": 0}
    spot = L.spot_price(budget)
    oi = L.exchange_open_interest(budget)
    if spot is None:
        return {"error": "no spot price"}

    positions, scanned, with_pos = L.scan(wallets, budget)
    snap = {"t": int(time.time() * 1000), "spot": spot, "oi_usd": oi, "tier": "wide",
            "scanned": scanned, "with_position": with_pos, "positions": positions,
            "throttled": budget["throttled"]}
    row = L.bucketise2(snap)
    row["positions"] = positions
    row["tier"] = "wide"
    # Stated on the row itself, not left to whoever reads the file later. A wide-tier coverage
    # figure next to a LIQ-2 one invites exactly the comparison that is not valid.
    row["population"] = {"kind": "uniform random sample", "n": len(wallets),
                         "drawn_from": json.load(open(WIDESET_PATH))["drawn_from"],
                         "seed": SEED,
                         "note": "research archive; NOT the population behind the published map"}
    with open(WIDE_SNAP_PATH, "a") as f:
        f.write(json.dumps(row) + "\n")

    out = {k: row.get(k) for k in ("t", "spot", "scanned", "with_position", "coverage")}
    out["forced_sell_10pct"] = row.get("forced_sell_10pct")
    if verbose:
        print(json.dumps(out))
    return out


if __name__ == "__main__":
    collect()
