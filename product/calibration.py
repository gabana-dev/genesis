"""
The calibration record: what Isobath said, and what happened next.

WHY THIS IS THE FIRST THING WE BUILD (product/PLAN.md). Everything else here can be copied in a
fortnight -- the map, the check, the copy, the design. What cannot be copied is a public record of
our own calls against subsequent outcomes, because it only accrues with TIME. Every day not
recording is a day of moat not built.

THIS FILE RECORDS. IT DOES NOT CONCLUDE.

That separation is deliberate and it is the whole discipline. Recording needs no pre-registration
because it makes no claim. The moment we say "clusters we called vulnerable resolved N% of the
time", that is a finding, and it needs a frozen contract with kill conditions like every other
finding in this project. Building the analysis into the recorder would let the analysis quietly
follow the data.

So: two append-only files, no judgement in either.

    calls.jsonl      every cluster we published, at the moment we published it
    outcomes.jsonl   what the same bucket looked like H hours later

THE CONFOUNDS, WRITTEN DOWN NOW rather than discovered later by someone defending a number:

  1. THE SCAN SET MOVES. The fast tier is the top 300 wallets by position notional, re-ranked by
     every deep scan. A bucket's notional can fall because positions closed, or because the
     wallets holding them dropped out of the top 300. These are not the same event and the raw
     data cannot tell them apart. Both scan tiers and both wallet sets are recorded so the
     analysis can condition on it.

  2. COVERAGE MOVES. Observed fraction is not constant between snapshots, so a notional change is
     partly a change in how much we could see. Coverage is recorded on both sides.

  3. SURVIVORSHIP. A wallet that is fully liquidated vanishes from the scan entirely. Its
     disappearance looks identical to it having closed voluntarily.

  4. PRICE PATH IS SAMPLED, NOT CONTINUOUS. Snapshots are hourly at best, so "did spot reach the
     cluster" is answered from an hourly series and will miss intra-hour touches. Recorded as a
     lower bound, and named as one.
"""
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone

# The clusters recorded here MUST be the clusters the site publishes, so they come from the
# generator itself rather than being rebuilt. A second implementation of bucketing would drift,
# and a calibration record of numbers we never showed anyone is worthless.
_spec = importlib.util.spec_from_file_location(
    "genmap", os.path.join(os.path.dirname(__file__), "generate.py"))
_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gen)

EVIDENCE = os.path.expanduser("~/genesis-evidence/liqmap")
SNAP = f"{EVIDENCE}/snapshots-liq2.jsonl"
OUT = os.path.expanduser("~/genesis-evidence/calibration")
CALLS = f"{OUT}/calls.jsonl"
OUTCOMES = f"{OUT}/outcomes.jsonl"

# Horizons at which a call is resolved. Chosen to bracket the cadence we can actually observe:
# shorter than 6h and the hourly scan barely moves, longer than 72h and the scan set has been
# re-ranked several times over.
HORIZONS_H = (6, 24, 72)

# A cluster is only worth recording if it is close enough to be reachable and big enough to
# matter. Both thresholds are recorded in every row so a later analysis can widen them without
# re-deriving what was captured.
MAX_DISTANCE_PCT = 10.0
MIN_NOTIONAL_USD = 250_000.0


def _read_snapshots():
    """Every snapshot, oldest first. Each carries its own buckets, spot and coverage."""
    rows = []
    with open(SNAP) as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return sorted(rows, key=lambda r: r["t"])


def call_id(t, distance_pct):
    """Stable id for a (snapshot, bucket). Deterministic so re-running never double-records."""
    return hashlib.sha256(f"{t}:{distance_pct:.2f}".encode()).hexdigest()[:16]


def clusters_of(snap):
    """Exactly the clusters the site publishes for this snapshot."""
    try:
        clusters, _total, _zero, _in_band, _n = _gen.build_map(snap)
        return clusters
    except (KeyError, ZeroDivisionError, TypeError):
        return []


def _existing(path, key):
    seen = set()
    if not os.path.exists(path):
        return seen
    with open(path) as f:
        for line in f:
            try:
                seen.add(json.loads(line)[key])
            except (json.JSONDecodeError, KeyError):
                continue
    return seen


def record_calls():
    """Append every cluster from every snapshot not already recorded. Idempotent."""
    os.makedirs(OUT, exist_ok=True)
    seen = _existing(CALLS, "id")
    snaps = _read_snapshots()
    written = 0

    with open(CALLS, "a") as f:
        for snap in snaps:
            spot = snap.get("spot")
            if not spot:
                continue
            cov = snap.get("coverage")
            for c in clusters_of(snap):
                if abs(c["distance_pct"]) > MAX_DISTANCE_PCT or c["notional_usd"] < MIN_NOTIONAL_USD:
                    continue
                cid = call_id(snap["t"], c["distance_pct"])
                if cid in seen:
                    continue
                f.write(json.dumps({
                    "id": cid,
                    "t": snap["t"],
                    "asset": "BTC",
                    "venue": "hyperliquid",
                    "side": c["side"],
                    "price": c["price"],
                    "spot": spot,
                    "distance_pct": c["distance_pct"],
                    "notional_usd": c["notional_usd"],
                    "wallets": c["wallets"],
                    # THE CLAIM BEING CALIBRATED, recorded verbatim as published.
                    "cannot_defend_pct": c["cannot_defend_pct"],
                    "thinly_defended_pct": c["thinly_defended_pct"],
                    # Confounds, captured at call time so they can be conditioned on later.
                    "tier": snap.get("tier"),
                    "scanned": snap.get("scanned"),
                    "coverage": cov,
                    "thresholds": {"max_distance_pct": MAX_DISTANCE_PCT,
                                   "min_notional_usd": MIN_NOTIONAL_USD},
                }) + "\n")
                seen.add(cid)
                written += 1
    return written


def _nearest(snaps, target_t, tolerance_h=2):
    """The snapshot closest to a target time, or None if nothing is within tolerance.

    None rather than the nearest-whatever: resolving a 24h horizon against a snapshot 9 hours
    adrift is not a 24h outcome, and silently pretending otherwise is how a calibration record
    stops meaning anything.
    """
    best, best_gap = None, tolerance_h * 3600 * 1000
    for s in snaps:
        gap = abs(s["t"] - target_t)
        if gap <= best_gap:
            best, best_gap = s, gap
    return best


def resolve():
    """For every call old enough, record what the same bucket looked like H hours later."""
    os.makedirs(OUT, exist_ok=True)
    snaps = _read_snapshots()
    if not snaps:
        return 0
    latest = snaps[-1]["t"]
    done = _existing(OUTCOMES, "key")
    written = 0

    calls = []
    if os.path.exists(CALLS):
        with open(CALLS) as f:
            for line in f:
                try:
                    calls.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    with open(OUTCOMES, "a") as f:
        for c in calls:
            for h in HORIZONS_H:
                key = f"{c['id']}:{h}"
                if key in done:
                    continue
                target = c["t"] + h * 3600 * 1000
                if target > latest:
                    continue                      # not yet resolvable; try again next run
                later = _nearest(snaps, target)
                if later is None:
                    continue                      # gap in the archive; leave it unresolved

                # MATCH ON PRICE, NEVER ON DISTANCE.
                #
                # The first version matched the later bucket by distance_pct, and the sanity
                # check showed a cluster going from $343k to $85.7M in six hours. Nothing moved:
                # distance is measured from a spot that had itself moved, so "the 0.0% bucket"
                # six hours later holds a completely different set of positions. Price is the
                # invariant -- the wallets liquidating at $77,000 are the same wallets later.
                #
                # Half a bucket width, computed from the spot at CALL time, so the tolerance is
                # the same size as the bucket the claim was made about.
                tol = c["spot"] * _gen.BUCKET_PCT / 2
                after, after_cd, matched = 0.0, None, None
                for lc in clusters_of(later):
                    if abs(lc["price"] - c["price"]) <= tol:
                        if matched is None or abs(lc["price"] - c["price"]) < abs(matched - c["price"]):
                            after, after_cd, matched = lc["notional_usd"], lc["cannot_defend_pct"], lc["price"]

                # Did the hourly series ever show spot at or past the cluster? A LOWER BOUND:
                # hourly sampling cannot see an intra-hour touch.
                window = [s for s in snaps if c["t"] <= s["t"] <= later["t"] and s.get("spot")]
                reached = any(
                    (s["spot"] >= c["price"]) if c["side"] == "buy" else (s["spot"] <= c["price"])
                    for s in window
                )

                f.write(json.dumps({
                    "key": key,
                    "id": c["id"],
                    "horizon_h": h,
                    "resolved_at": later["t"],
                    "actual_gap_h": round(abs(later["t"] - target) / 3600000, 3),
                    "notional_before": c["notional_usd"],
                    "notional_after": round(after, 2),
                    "cannot_defend_pct_after": after_cd,
                    "matched_price": matched,
                    "match_tolerance_usd": round(tol, 2),
                    "spot_after": later.get("spot"),
                    "spot_reached_cluster": reached,
                    "reached_is_lower_bound": True,
                    "samples_in_window": len(window),
                    # The confounds again, on the far side.
                    "tier_after": later.get("tier"),
                    "coverage_after": later.get("coverage"),
                }) + "\n")
                done.add(key)
                written += 1
    return written


def status():
    calls = sum(1 for _ in open(CALLS)) if os.path.exists(CALLS) else 0
    outs = sum(1 for _ in open(OUTCOMES)) if os.path.exists(OUTCOMES) else 0
    return {"calls": calls, "outcomes": outs,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


if __name__ == "__main__":
    n_calls = record_calls()
    n_out = resolve()
    s = status()
    print(f"recorded {n_calls} new call(s), resolved {n_out} outcome(s)")
    print(f"total: {s['calls']} calls, {s['outcomes']} outcomes")
    if "--why" in sys.argv:
        print("\nThis file records. It does not conclude. Any claim drawn from it needs a frozen\n"
              "contract with kill conditions, like every other finding in this project.")


# ---------------------------------------------------------------------------------------
# FIRST OBSERVATION FROM THE RECORD, 2026-08-21 -- not a finding, a warning about one.
#
# 71% of recorded clusters sit at EXACTLY 100% cannot-defend. Median 100.0, and only 56 of 433
# fall below 90%. The headline metric is very nearly a constant.
#
# A predictor with almost no variance cannot discriminate, so "clusters we called vulnerable
# resolved more often" may be unanswerable as currently defined -- not because the effect is
# absent, but because there is no contrast to measure it against. If nearly every cluster is
# 100%, saying so distinguishes nothing.
#
# This is exactly the class of problem that killed GEN-1 (a test that could not resolve anything
# below 54.67% and measured 52.10%), and it is better to know now, on day one of recording, than
# after six months of accumulating a column that turns out to be flat.
#
# It does NOT mean stop recording. `thinly_defended_pct`, notional, distance and wallet count all
# vary, and the contrast may live in one of those. It means the contract, when written, must
# state which variable carries the contrast and must show that variable has enough spread to
# detect the effect it claims -- before any outcome is computed.
# ---------------------------------------------------------------------------------------
