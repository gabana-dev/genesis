"""
The forced-flow map. Public data only, no account.

LIQ-1 (`collect`) is CLOSED -- its scan set, the 200 most active wallets, held 5.8% of exchange
open interest, because appearance count selects for market makers with flat books. It is kept
here so its single snapshot stays reproducible; nothing new runs through it.

LIQ-2 (`collect2`) is live. Contract: market/CONTRACT-liquidation-map-2.md, frozen 2026-08-19,
sha256 3ec70684b2aec79882191cb8393a22239a7c5c86821930c9cf60f6441639a800, before any LIQ-2
snapshot was taken. Superseded contract: market/CONTRACT-liquidation-map.md,
sha256 f5c54584e46c4e942e288852158602a99ec9a07182566222996bb41fb29d4bb3.

WHAT MAKES THIS DIFFERENT FROM EVERY OTHER GENESIS EXPERIMENT
    It reads OBLIGATION, not information. `liquidationPx` is the price at which the venue's own
    engine will close a position regardless of what anyone believes. It does not fire sooner for
    a faster participant, which is why this is the one line in the project where the 291 ms
    latency floor is irrelevant by construction.

NO SNOOPING RISK, STRUCTURALLY
    `clearinghouseState` is a snapshot with no historical version. It cannot be backfilled.
    Every observation this module collects post-dates the frozen contract, so there is no
    survivorship, no data reuse and no forking path available.

LIQ-2 RE-RANKS, AND THAT IS NOT THE THING LIQ-1 FORBADE
    LIQ-1 froze its scan set because a set drifting toward whatever is currently interesting is
    selection on the outcome. LIQ-2's deep scan re-ranks every 6 hours by position notional --
    the INPUT that determines how much forced flow a wallet contributes, mechanically, with no
    discretion. The population it ranks within is frozen; only the top-300 window moves.
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
# LIQ-2 two-tier scanning. LIQ-1's 200-most-active set covered 5.8% of exchange open interest
# because appearance count selects for market makers -- high turnover, flat books, distant
# liquidations. Position notional is the input that determines forced flow, so that is the
# ranking rule.
DEEP_EVERY_H = 6                    # full re-rank of the harvest set
FAST_N = 300                        # top N by position notional, scanned hourly
N_WALLETS = 200                     # LIQ-1 only; retained so its snapshot stays reproducible
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


def spot_price(budget, coin=None):
    mids = _post({"type": "allMids"}, budget)
    try:
        return float(mids[coin or COIN])
    except (TypeError, KeyError, ValueError):
        return None


def spot_prices(budget, coins):
    """Mid for several coins in one request, so a multi-asset scan does not make N of them."""
    mids = _post({"type": "allMids"}, budget) or {}
    out = {}
    for c in coins:
        try:
            out[c] = float(mids[c])
        except (TypeError, KeyError, ValueError):
            out[c] = None
    return out


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
            with_pos[coin] += 1
            positions[coin].append({
                "wallet": w, "szi": szi, "liquidationPx": lpx,
                "entryPx": p.get("entryPx"), "leverage": (p.get("leverage") or {}).get("value"),
                # short -> forced BUY, long -> forced SELL
                "forced_side": "buy" if szi < 0 else "sell",
                "forced_notional": abs(szi) * lpx,
                "account_value": (st.get("marginSummary") or {}).get("accountValue"),
                "maint_margin": st.get("crossMaintenanceMarginUsed"),
                # LIQ-2: free collateral -- the direct measure of capacity to move the
                # goalpost. clearinghouseState has NO history, so an hour collected without
                # this is an hour whose liquidation-price credibility is unrecoverable.
                "withdrawable": st.get("withdrawable"),
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


# ---------------------------------------------------------------------------------------
# LIQ-2: coverage, credibility weighting, and the two-tier scan
# ---------------------------------------------------------------------------------------

def exchange_open_interest(budget, coin=None):
    """Open interest in USD, from the venue. K2 makes coverage binding, not advisory."""
    return open_interests(budget, (coin or COIN,)).get(coin or COIN)


def open_interests(budget, coins):
    """Open interest for several coins in one request."""
    meta = _post({"type": "metaAndAssetCtxs"}, budget)
    out = {c: None for c in coins}
    try:
        names = [a["name"] for a in meta[0]["universe"]]
    except Exception:
        return out
    for c in coins:
        try:
            ctx = meta[1][names.index(c)]
            out[c] = float(ctx["openInterest"]) * float(ctx["markPx"])
        except Exception:
            pass
    return out


def credible_notional(p):
    """
    Forced notional discounted by the wallet's capacity to escape.

    A wallet with no free collateral cannot move its liquidation price from inside the account
    and counts at full weight; one holding ten times its maintenance requirement idle counts at
    roughly a tenth.

    THIS IS A DECLARED HYPOTHESIS ABOUT BEHAVIOUR, NOT A MEASUREMENT. LIQ-2 reports the raw map
    as primary and this alongside it, precisely so the weighting cannot quietly become the
    headline.
    """
    try:
        w = float(p.get("withdrawable") or 0.0)
        m = float(p.get("maint_margin") or 0.0)
    except (TypeError, ValueError):
        return p["forced_notional"]
    if m <= 0:
        return p["forced_notional"]
    return p["forced_notional"] / (1.0 + w / m)


def rank_by_notional(positions, n=FAST_N):
    """The deep scan's only job: re-rank by position notional. Mechanical, no discretion."""
    ranked = sorted(positions, key=lambda p: abs(p["szi"]) * p["liquidationPx"], reverse=True)
    seen, out = set(), []
    for p in ranked:
        if p["wallet"] in seen:
            continue
        seen.add(p["wallet"])
        out.append(p["wallet"])
        if len(out) >= n:
            break
    return out


HL1 = os.path.expanduser("~/genesis-evidence/hl1/btc-hl1.jsonl")
LIQ2_SNAP_PATH = f"{STATE_DIR}/snapshots-liq2.jsonl"

# ADDITIONAL ASSETS, RECORDED ALONGSIDE -- NEVER INSIDE -- THE LIQ-2 ARCHIVE.
#
# clearinghouseState returns every position a wallet holds, so these cost NO additional requests;
# the scanner was fetching and discarding them. But LIQ-2's contract is frozen and its coverage is
# defined against BTC open interest, so its archive keeps exactly the schema and the single asset
# it was frozen with. The extra assets go to their own files.
#
# Their coverage will be LOWER and that is not a defect to hide: the wallet universe was harvested
# from a BTC recording, so it is BTC-biased by construction. Coverage is stated per asset, as it
# is everywhere else here.
EXTRA_COINS = ("ETH", "SOL")


def snap_path(coin):
    return LIQ2_SNAP_PATH if coin == COIN else f"{STATE_DIR}/snapshots-{coin.lower()}.jsonl"
FASTSET_PATH = f"{STATE_DIR}/fastset.json"
UNIVERSE_PATH = f"{STATE_DIR}/universe.json"
CONTRACT_2 = "market/CONTRACT-liquidation-map-2.md"


def universe(recording=HL1, refresh=False):
    """
    Every distinct wallet in the hl1 recording -- the deep scan's population.

    Frozen on first call. The recording keeps growing, and a universe that grew with it would
    make coverage across snapshots incomparable: the denominator would be the exchange but the
    numerator would be a widening net.
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    if os.path.exists(UNIVERSE_PATH) and not refresh:
        return json.load(open(UNIVERSE_PATH))["wallets"]
    from hl_harvest import wallets_from_recording
    wallets = wallets_from_recording(recording)
    json.dump({"wallets": wallets, "fixed_at": datetime.now(timezone.utc).isoformat(),
               "source": recording, "n": len(wallets)}, open(UNIVERSE_PATH, "w"))
    return wallets


def scan(wallets, budget):
    """BTC positions across a wallet list. The tiers differ only in which list they are given.

    Kept as a thin wrapper over scan_multi so there is ONE implementation of the per-position
    logic. LIQ-2's contract is frozen and its coverage is measured against BTC open interest, so
    the BTC output of this function must not change; delegating guarantees it cannot drift from
    the multi-asset path.
    """
    out, scanned, with_pos = scan_multi(wallets, budget, (COIN,))
    return out.get(COIN, []), scanned, with_pos[COIN]


def scan_multi(wallets, budget, coins):
    """Positions in `coins` across a wallet list, in ONE pass.

    clearinghouseState returns every position a wallet holds, so scanning additional assets costs
    no additional requests -- the previous version fetched them and threw them away. Returns
    ({coin: [positions]}, wallets_scanned, {coin: wallets_with_a_position}).
    """
    coins = tuple(coins)
    positions = {c: [] for c in coins}
    with_pos = {c: 0 for c in coins}
    scanned = 0
    for w in wallets:
        st = _post({"type": "clearinghouseState", "user": w}, budget)
        scanned += 1
        if not st:
            continue
        for ap in st.get("assetPositions") or []:
            p = ap.get("position") or {}
            coin = p.get("coin")
            if coin not in positions:
                continue
            try:
                szi = float(p.get("szi") or 0.0)
                lpx = p.get("liquidationPx")
                if szi == 0.0 or lpx in (None, ""):
                    continue
                lpx = float(lpx)
            except (TypeError, ValueError):
                continue
            with_pos[coin] += 1
            positions[coin].append({
                "wallet": w, "szi": szi, "liquidationPx": lpx,
                "entryPx": p.get("entryPx"), "leverage": (p.get("leverage") or {}).get("value"),
                "forced_side": "buy" if szi < 0 else "sell",
                "forced_notional": abs(szi) * lpx,
                "account_value": (st.get("marginSummary") or {}).get("accountValue"),
                "maint_margin": st.get("crossMaintenanceMarginUsed"),
                "withdrawable": st.get("withdrawable"),
            })
    return positions, scanned, with_pos


def bucketise2(snap):
    """
    LIQ-2 map: raw buckets, credibility-weighted buckets, and measured coverage.

    Raw is primary. The weighted map is computed in the same pass so the two can never come from
    different snapshots, and it is stored under its own keys so nothing can read one as the other.
    """
    spot, oi = snap["spot"], snap["oi_usd"]
    buys, sells, wbuys, wsells = {}, {}, {}, {}
    held = 0.0
    for p in snap["positions"]:
        held += p["forced_notional"]
        rel = (p["liquidationPx"] - spot) / spot
        if abs(rel) > RANGE_PCT:
            continue
        b = int(rel / BUCKET_PCT)
        raw, wgt = (buys, wbuys) if p["forced_side"] == "buy" else (sells, wsells)
        raw[b] = raw.get(b, 0.0) + p["forced_notional"]
        wgt[b] = wgt.get(b, 0.0) + credible_notional(p)

    def nearest_dense(d, sign):
        cands = [abs(k) * BUCKET_PCT for k, v in d.items()
                 if v >= DENSE_USD and (k > 0 if sign > 0 else k < 0)]
        return min(cands) if cands else None

    within = lambda d, pct: sum(v for k, v in d.items() if abs(k) * BUCKET_PCT <= pct)  # noqa: E731
    fb, fs = within(buys, IMBALANCE_PCT), within(sells, IMBALANCE_PCT)
    tot = fb + fs
    wb, ws = within(wbuys, IMBALANCE_PCT), within(wsells, IMBALANCE_PCT)
    wtot = wb + ws
    return {
        "contract": CONTRACT_2, "tier": snap["tier"],
        "t": snap["t"], "spot": spot,
        "scanned": snap["scanned"], "with_position": snap["with_position"],
        "buckets_buy": buys, "buckets_sell": sells,
        "buckets_buy_credible": wbuys, "buckets_sell_credible": wsells,
        "forced_buy_10pct": within(buys, RANGE_PCT),
        "forced_sell_10pct": within(sells, RANGE_PCT),
        "forced_buy_5pct": fb, "forced_sell_5pct": fs,
        "credible_buy_5pct": wb, "credible_sell_5pct": ws,
        "imbalance": ((fb - fs) / tot) if tot > 0 else None,
        "imbalance_credible": ((wb - ws) / wtot) if wtot > 0 else None,
        "nearest_dense_above": nearest_dense(buys, +1),
        "nearest_dense_below": nearest_dense(sells, -1),
        "largest_bucket_share_buy": (max(buys.values()) / sum(buys.values())) if buys else None,
        "largest_bucket_share_sell": (max(sells.values()) / sum(sells.values())) if sells else None,
        # Section 3: coverage is a first-class output on every snapshot, not a check
        # somebody might remember to run. LIQ-1 died of exactly that omission.
        "oi_usd": oi,
        "scanned_notional": held,
        "coverage": (held / oi) if oi else None,
        "throttled": snap["throttled"],
    }


def collect2(tier, recording=HL1):
    """
    One LIQ-2 snapshot. `tier` is "deep" (whole universe, re-ranks the fast set) or "fast"
    (top FAST_N by position notional from the last deep scan).
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    budget = {"sleep": BASE_SLEEP, "throttled": 0}

    if tier == "deep":
        wallets = universe(recording)
    else:
        if not os.path.exists(FASTSET_PATH):
            return {"error": "no fast set yet; a deep scan must run first"}
        wallets = json.load(open(FASTSET_PATH))["wallets"]

    coins = (COIN,) + EXTRA_COINS
    spots = spot_prices(budget, coins)
    ois = open_interests(budget, coins)
    if spots.get(COIN) is None:
        return {"error": "no spot price"}

    all_pos, scanned, with_pos = scan_multi(wallets, budget, coins)
    t_ms = int(time.time() * 1000)

    rows = {}
    for coin in coins:
        if spots.get(coin) is None:
            continue
        snap = {"t": t_ms, "spot": spots[coin], "oi_usd": ois.get(coin), "tier": tier,
                "scanned": scanned, "with_position": with_pos[coin],
                "positions": all_pos[coin], "throttled": budget["throttled"]}
        r = bucketise2(snap)
        r["positions"] = all_pos[coin]
        # The extra assets carry their own asset field. BTC's schema is untouched: the LIQ-2
        # archive must stay exactly what the frozen contract describes.
        if coin != COIN:
            r["asset"] = coin
        with open(snap_path(coin), "a") as f:
            f.write(json.dumps(r) + "\n")
        rows[coin] = r

    row = rows[COIN]
    positions = all_pos[COIN]

    # The fast set is ranked on BTC notional ONLY, exactly as the contract froze it. Ranking on a
    # blend across assets would silently change the LIQ-2 population.
    if tier == "deep":
        json.dump({"wallets": rank_by_notional(positions), "ranked_at": row["t"],
                   "rule": "top %d by |szi| * liquidationPx" % FAST_N},
                  open(FASTSET_PATH, "w"))

    return {k: row[k] for k in
            ("tier", "t", "spot", "scanned", "with_position", "coverage",
             "forced_buy_5pct", "forced_sell_5pct", "credible_buy_5pct", "credible_sell_5pct",
             "imbalance", "nearest_dense_above", "nearest_dense_below", "throttled")}


if __name__ == "__main__":
    print(json.dumps(collect2(sys.argv[1] if len(sys.argv) > 1 else "fast")))


# ---------------------------------------------------------------------------------------
# FIRST MULTI-ASSET SCAN, 2026-08-21 -- two results, recorded before anything is built on them.
#
# 1. ETH AND SOL ARE TOO SPARSE TO PUBLISH, and coverage hides it.
#
#    coverage    positions   in-band notional   clusters
#    BTC  30.5%     260           $48.2M          29
#    ETH  35.8%     104            $0.4M           4
#    SOL  99.8%      67            $0.1M           1
#
#    ETH coverage LOOKS better than BTC. But the wallets we hold barely have ETH or SOL positions
#    within +/-10% of spot, so the map is nearly empty. A per-asset page built on four clusters
#    worth $0.4M would be a thin page dressed as an analytical answer, which product/PLAN.md
#    explicitly forbids. Keep collecting -- it costs no requests -- publish nothing yet.
#
#    SOL's 99.8% should be read with suspicion, not pride. Scanned notional is |szi| * liqPx while
#    open interest is size * markPx, so the ratio compares two different bases and inflates when
#    liquidation prices sit far from mark. That is inherited from the frozen contract, not
#    introduced here, but it is visible now and should not be quoted as "we see all of SOL".
#
# 2. IT DID NOT RESCUE CALIBRATION, which was half the reason for doing it.
#
#    The hope was that other assets would give cannot_defend_pct the variance BTC lacks. The
#    opposite: ETH is 4/4 at 100% and SOL 1/1, stdev 0.0 for both, against BTC's 36.3. Adding
#    assets made the metric look MORE pinned, not less. The contrast calibration needs is not
#    here, and it has to be found in another variable or another framing.
# ---------------------------------------------------------------------------------------
