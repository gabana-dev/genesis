"""
LIQ-1: the forced-flow map. Public data only, no account.

Contract: market/CONTRACT-liquidation-map.md, frozen 2026-08-19 before any snapshot was taken.

WHAT MAKES THIS DIFFERENT FROM EVERY OTHER GENESIS EXPERIMENT
    It reads OBLIGATION, not information. `liquidationPx` is the price at which the venue's own
    engine will close a position regardless of what anyone believes. It does not fire sooner for
    a faster participant, which is why this is the one line in the project where the 291 ms
    latency floor is irrelevant by construction.

NO SNOOPING RISK, STRUCTURALLY
    `clearinghouseState` is a snapshot with no historical version. It cannot be backfilled.
    Every observation this module collects post-dates the frozen contract, so there is no
    survivorship, no data reuse and no forking path available.

THE SCAN SET IS FIXED AT FIRST SCAN AND NEVER RE-SELECTED
    Re-ranking mid-experiment would let the set drift toward whatever is currently interesting,
    which is selection on the outcome by another name.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

INFO = "https://api.hyperliquid.xyz/info"
STATE_DIR = os.path.expanduser("~/genesis-evidence/liqmap")
SNAP_PATH = f"{STATE_DIR}/snapshots.jsonl"
SCANSET_PATH = f"{STATE_DIR}/scanset.json"

CONTRACT = "market/CONTRACT-liquidation-map.md"

# Section 3 and 4. Every value copied from the contract.
N_WALLETS = 200
COIN = "BTC"
BUCKET_PCT = 0.005                  # 0.5% buckets
RANGE_PCT = 0.10                    # +/- 10%
IMBALANCE_PCT = 0.05                # the secondary uses +/- 5%
DENSE_USD = 1_000_000               # "nearest dense bucket" threshold
BASE_SLEEP = 0.35
MAX_BACKOFF = 60.0


def _post(body, budget):
    req = urllib.request.Request(INFO, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    for _ in range(8):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.loads(r.read())
            budget["sleep"] = max(BASE_SLEEP, budget["sleep"] * 0.95)
            time.sleep(budget["sleep"])
            return out
        except urllib.error.HTTPError as e:
            if e.code == 429:
                budget["sleep"] = min(MAX_BACKOFF, max(1.0, budget["sleep"] * 2.0))
                budget["throttled"] += 1
                time.sleep(budget["sleep"])
                continue
            return None
        except Exception:
            time.sleep(2.0)
    return None


def build_scanset(recording, n=N_WALLETS):
    """
    The 200 most active wallets, fixed at first scan and reused thereafter.

    Persisted deliberately: a scan set recomputed each run would drift with activity, and a
    drifting set is selection on the outcome.
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    if os.path.exists(SCANSET_PATH):
        return json.load(open(SCANSET_PATH))["wallets"]
    seen = Counter()
    for line in open(recording):
        e = json.loads(line)
        if e.get("event_class") != "OBSERVATION":
            continue
        raw = e.get("body", {}).get("world", {}).get("raw", {})
        if raw.get("channel") != "trades":
            continue
        for t in raw.get("data") or []:
            for u in (t.get("users") or []):
                seen[u] += 1
    wallets = [w for w, _ in seen.most_common(n)]
    json.dump({"wallets": wallets, "fixed_at": datetime.now(timezone.utc).isoformat(),
               "source": recording, "n": len(wallets)}, open(SCANSET_PATH, "w"), indent=1)
    return wallets


def spot_price(budget):
    mids = _post({"type": "allMids"}, budget)
    try:
        return float(mids[COIN])
    except (TypeError, KeyError, ValueError):
        return None


def snapshot(recording, budget=None):
    """
    One hourly snapshot: every scanned wallet's BTC position and liquidation price, bucketed.

    A SHORT liquidates by BUYING and a LONG by SELLING -- the forced direction is the opposite
    of the position's sign, and getting that backwards would invert the entire map while leaving
    every number plausible.
    """
    budget = budget or {"sleep": BASE_SLEEP, "throttled": 0}
    wallets = build_scanset(recording)
    spot = spot_price(budget)
    if spot is None:
        return None

    positions, scanned, with_pos = [], 0, 0
    for w in wallets:
        st = _post({"type": "clearinghouseState", "user": w}, budget)
        scanned += 1
        if not st:
            continue
        for ap in st.get("assetPositions") or []:
            p = ap.get("position") or {}
            if p.get("coin") != COIN:
                continue
            try:
                szi = float(p.get("szi") or 0.0)
                lpx = p.get("liquidationPx")
                if szi == 0.0 or lpx in (None, ""):
                    continue
                lpx = float(lpx)
            except (TypeError, ValueError):
                continue
            with_pos += 1
            positions.append({
                "wallet": w, "szi": szi, "liquidationPx": lpx,
                "entryPx": p.get("entryPx"), "leverage": (p.get("leverage") or {}).get("value"),
                # short -> forced BUY, long -> forced SELL
                "forced_side": "buy" if szi < 0 else "sell",
                "forced_notional": abs(szi) * lpx,
                "account_value": (st.get("marginSummary") or {}).get("accountValue"),
                "maint_margin": st.get("crossMaintenanceMarginUsed"),
            })

    return {"t": int(time.time() * 1000), "spot": spot,
            "scanned": scanned, "with_position": with_pos,
            "positions": positions, "throttled": budget["throttled"]}


def bucketise(snap):
    """Forced notional by 0.5% bucket out to +/-10%, plus the declared summary quantities."""
    spot = snap["spot"]
    buys, sells = {}, {}
    for p in snap["positions"]:
        rel = (p["liquidationPx"] - spot) / spot
        if abs(rel) > RANGE_PCT:
            continue
        b = int(rel / BUCKET_PCT)
        (buys if p["forced_side"] == "buy" else sells)[b] = \
            (buys if p["forced_side"] == "buy" else sells).get(b, 0.0) + p["forced_notional"]

    def nearest_dense(d, sign):
        cands = [abs(k) * BUCKET_PCT for k, v in d.items()
                 if v >= DENSE_USD and (k > 0 if sign > 0 else k < 0)]
        return min(cands) if cands else None

    within = lambda d, pct: sum(v for k, v in d.items() if abs(k) * BUCKET_PCT <= pct)  # noqa: E731
    fb, fs = within(buys, IMBALANCE_PCT), within(sells, IMBALANCE_PCT)
    tot = fb + fs
    return {
        "t": snap["t"], "spot": spot,
        "scanned": snap["scanned"], "with_position": snap["with_position"],
        "buckets_buy": buys, "buckets_sell": sells,
        "forced_buy_10pct": within(buys, RANGE_PCT),
        "forced_sell_10pct": within(sells, RANGE_PCT),
        "forced_buy_5pct": fb, "forced_sell_5pct": fs,
        "imbalance": ((fb - fs) / tot) if tot > 0 else None,
        "nearest_dense_above": nearest_dense(buys, +1),
        "nearest_dense_below": nearest_dense(sells, -1),
        "largest_bucket_share_buy": (max(buys.values()) / sum(buys.values())) if buys else None,
        "largest_bucket_share_sell": (max(sells.values()) / sum(sells.values())) if sells else None,
        "note": ("scan set is 200 wallets, so this is a LOWER BOUND on cluster density; "
                 "forced flow from unscanned wallets is invisible (contract section 3)"),
    }


def collect(recording=os.path.expanduser("~/genesis-evidence/hl1/btc-hl1.jsonl")):
    """One snapshot, appended. Intended to run hourly from cron."""
    os.makedirs(STATE_DIR, exist_ok=True)
    snap = snapshot(recording)
    if snap is None:
        return {"error": "no spot price"}
    row = bucketise(snap)
    # Raw positions are kept alongside the summary: the map is derived, and a derived number
    # whose inputs were discarded cannot be rechecked.
    row["positions"] = snap["positions"]
    with open(SNAP_PATH, "a") as f:
        f.write(json.dumps(row) + "\n")
    return {k: row[k] for k in
            ("t", "spot", "scanned", "with_position", "forced_buy_5pct", "forced_sell_5pct",
             "imbalance", "nearest_dense_above", "nearest_dense_below")}
