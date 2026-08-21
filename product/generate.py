"""
Generate the Genesis v1 data surfaces.

Writes static JSON. No server, no database, no query layer -- a generated file on a CDN cannot
go down, costs nothing to serve, and needs no ops. Build a service only when someone asks a
question that cannot be precomputed.

    public/data/map.json        live clusters, size, distance, defensibility, COVERAGE
    public/data/scorecard.json  every claim Genesis has published and what happened to it
    public/data/meta.json       what is running, what is stale, what we cannot see

WHAT MAKES THIS DIFFERENT FROM EVERY OTHER LIQUIDATION MAP
    Three things, and all three are things a competitor would have to admit to in order to copy:

      COVERAGE      stated on the map itself. We see ~53% of open interest (F-0003) and say so.
                    No provider surveyed publishes a coverage figure for position data.
      DEFENSIBILITY the fraction of each cluster whose wallets have no free collateral left.
                    Requires `withdrawable`, which nobody sells and which is NOT derivable --
                    naive margin arithmetic misclassifies one wallet in five (F-0001).
      AGE           how stale the position map is against the live book. The map lags the book
                    by up to an hour (F-0008) and pretending otherwise fakes precision.

WHAT IT DOES NOT CLAIM
    Nothing here forecasts price. CASCADE-1 found forced flow does not move price more than a
    volatility-matched minute on Binance (F-0010), and says nothing about Hyperliquid either
    way. The map states what is positioned where and how much of it can defend. That is a fact
    about positions, not a prediction.
"""

import json
import os
import sys
import glob
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "findings"))

import liqmap as L  # noqa: E402
from build_index import front_matter  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
# The Astro build copies web/public/ into docs/, so the engine writes here and the site
# build publishes it. One pipeline: data first, then pages.
OUTDIR = os.path.join(ROOT, "web", "public", "data")

BUCKET_PCT = 0.005          # 0.5% buckets, as LIQ-2
RANGE_PCT = 0.10            # +/-10%
# A wallet with free collateral below this fraction of its maintenance requirement cannot
# meaningfully top up from inside the account. Declared here rather than tuned later.
THIN_RATIO = 0.05


def latest_snapshot():
    rows = None
    with open(L.LIQ2_SNAP_PATH) as f:
        for line in f:
            rows = line
    return json.loads(rows) if rows else None


def defensibility(positions):
    """
    Per position: can this wallet defend its liquidation price from inside the account?

    Reported two ways because they answer different questions and the gap between them is
    itself informative:
      zero  -- withdrawable is exactly 0. It cannot move at all without an external deposit.
      thin  -- withdrawable is under THIN_RATIO of maintenance margin. It can move a little.
    """
    out = []
    for p in positions:
        try:
            w = float(p.get("withdrawable") or 0.0)
            m = float(p.get("maint_margin") or 0.0)
        except (TypeError, ValueError):
            w, m = 0.0, 0.0
        ratio = (w / m) if m > 0 else None
        out.append({**p, "_w": w, "_ratio": ratio,
                    "_zero": w <= 0.0,
                    "_thin": (ratio is not None and ratio < THIN_RATIO) or w <= 0.0})
    return out


def build_map(snap):
    spot = snap["spot"]
    pos = defensibility(snap["positions"])

    buckets = {}
    for p in pos:
        rel = (p["liquidationPx"] - spot) / spot
        if abs(rel) > RANGE_PCT:
            continue
        b = int(rel / BUCKET_PCT)
        d = buckets.setdefault(b, {"notional": 0.0, "zero": 0.0, "thin": 0.0,
                                   "wallets": 0, "side": p["forced_side"]})
        d["notional"] += p["forced_notional"]
        d["wallets"] += 1
        if p["_zero"]:
            d["zero"] += p["forced_notional"]
        if p["_thin"]:
            d["thin"] += p["forced_notional"]

    clusters = []
    for b, d in sorted(buckets.items(), key=lambda kv: abs(kv[0])):
        if d["notional"] <= 0:
            continue
        clusters.append({
            "distance_pct": round(b * BUCKET_PCT * 100, 2),
            "price": round(spot * (1 + b * BUCKET_PCT), 2),
            "side": d["side"],
            "notional_usd": round(d["notional"], 2),
            "wallets": d["wallets"],
            "cannot_defend_pct": round(d["zero"] / d["notional"] * 100, 1),
            "thinly_defended_pct": round(d["thin"] / d["notional"] * 100, 1),
        })

    # The numerator and denominator MUST cover the same set. A first version summed `zero`
    # over every position while `total` covered only the +/-10% band, and reported 147.6%
    # "cannot defend" -- impossible, and caught only because the number exceeded 100.
    in_band = [p for p in pos if abs((p["liquidationPx"] - spot) / spot) <= RANGE_PCT]
    total = sum(c["notional_usd"] for c in clusters)
    zero = sum(p["forced_notional"] for p in in_band if p["_zero"])
    return clusters, total, zero, len(in_band), len(pos)


def build_scorecard():
    """
    Every claim Genesis has published, and what happened to it.

    Generated from findings/, never hand-written. REFUTED entries are included deliberately:
    a scorecard that keeps only its wins is a marketing page, and the refutations are the part
    a competitor cannot reproduce without publishing their own.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "findings", "F-*.md"))):
        # One parser, shared with findings/build_index.py. The local copy this replaced did not
        # strip the quotes around a quoted front-matter value, so every `observation` written in
        # quotes reached the published scorecard wearing literal \" marks.
        d = front_matter(p)
        if not d:
            continue
        out.append({k: d.get(k) for k in
                    ("id", "title", "status", "observation", "sample", "method",
                     "confidence", "first_recorded", "last_updated")})
    counts = {}
    for f in out:
        counts[f["status"]] = counts.get(f["status"], 0) + 1
    return out, counts


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    snap = latest_snapshot()
    if snap is None:
        raise SystemExit("no position snapshot yet")

    clusters, total, zero, n_in_band, n_pos = build_map(snap)
    age_s = (now.timestamp() * 1000 - snap["t"]) / 1000.0

    # THE DENOMINATOR. F-0014 measured the median published cluster at 0.44% of the book standing
    # in front of it, and named the reason every heatmap misleads: it scales clusters against each
    # other and never against the liquidity they would have to move. This site made that mistake
    # too. Fetched live rather than read from the archive, because generate.py runs on the laptop
    # and the hl2 recorder now runs on the server.
    book = L.standing_book({"sleep": L.BASE_SLEEP, "throttled": 0})

    map_doc = {
        "asset": "BTC", "venue": "hyperliquid",
        "generated_at": now.isoformat(timespec="seconds"),
        "map_taken_at": datetime.fromtimestamp(snap["t"] / 1000, timezone.utc)
                                .isoformat(timespec="seconds"),
        "map_age_seconds": round(age_s),
        "spot_at_map": snap["spot"],
        # Stated on the map itself. No surveyed provider publishes this for position data.
        # THIS SNAPSHOT'S OWN coverage, not the aspirational figure. A fast-tier scan covers
        # 300 wallets and sees far less than the 53.3% a full universe reaches (F-0003).
        # Publishing the better number would be exactly the dishonesty this surface exists to
        # avoid.
        "coverage": {
            "observed_fraction": round(snap["coverage"], 4),
            "tier": snap.get("tier"),
            "wallets_scanned": snap.get("scanned"),
            "method": "scanned position notional / exchange open interest",
            "note": "every figure below is a LOWER BOUND -- forced flow from wallets outside "
                    "this scan is invisible",
            "full_universe_estimate": 0.533,
            "reference": "F-0003",
        },
        # Only the +/-1% band is observable: 20 levels at nSigFigs=3 reach ~2.5%. Clusters beyond
        # that are compared against the book at spot, which is a PROXY and is labelled as one --
        # the book that will exist at a price 6% away is not something we can see today.
        "book": {
            "standing_notional_usd": round(book[0], 2) if book else None,
            "band_pct": 1.0,
            "mid": book[1] if book else None,
            "observable_reach_pct": round(book[2], 2) if book else None,
            "source": "hyperliquid l2Book, nSigFigs=3, fetched live",
            "note": "the denominator for every cluster below. Outside +/-1% it is a proxy, not "
                    "an observation -- the book at a distant price is not visible today",
            "reference": "F-0014",
        },
        "totals": {
            "wallets_with_positions": n_pos,
            "wallets_in_band": n_in_band,
            "forced_notional_usd": round(total, 2),
            "cannot_defend_usd": round(zero, 2),
            "cannot_defend_pct": round(zero / total * 100, 1) if total else None,
        },
        "clusters": clusters,
        "definitions": {
            "cannot_defend_pct": "share of cluster notional held by wallets with ZERO free "
                                 "collateral. They cannot move their liquidation price without "
                                 "depositing from outside. Requires `withdrawable`, which is not "
                                 "derivable from position and margin data (F-0001).",
            "thinly_defended_pct": f"free collateral below {THIN_RATIO:.0%} of maintenance margin",
        },
        "we_do_not_claim": [
            "that reaching a cluster causes a further price move -- tested on Binance and it "
            "did not beat a volatility-matched control (F-0010)",
            "anything about clusters we cannot see; coverage is stated above",
            "that a cluster is large. Against the book standing in front of it the median "
            "published cluster is 0.44% and the p90 is 5.1% (F-0014) -- which is why reaching "
            "one moves price about a tenth as much as the move it arrives on",
        ],
    }

    sc, counts = build_scorecard()
    scorecard_doc = {
        "generated_at": now.isoformat(timespec="seconds"),
        "note": "Every claim Genesis has published, including the ones that turned out wrong. "
                "REFUTED entries are never removed.",
        "counts": counts, "findings": sc,
    }

    meta_doc = {
        "generated_at": now.isoformat(timespec="seconds"),
        "what_we_cannot_see": [
            f"{(1-snap['coverage'])*100:.0f}% of open interest -- wallets absent from our "
            f"trade-derived universe",
            "cross-margin effects from positions in other assets",
            f"anything that changed in the last {round(age_s)}s; the map lags the book (F-0008)",
        ],
        "surfaces": ["map.json", "scorecard.json", "meta.json"],
    }

    for name, doc in (("map", map_doc), ("scorecard", scorecard_doc), ("meta", meta_doc)):
        with open(os.path.join(OUTDIR, f"{name}.json"), "w") as f:
            json.dump(doc, f, indent=1)

    print(f"map        {len(clusters)} clusters  ${total:,.0f} forced  "
          f"{map_doc['totals']['cannot_defend_pct']}% cannot defend  "
          f"coverage {snap['coverage']:.1%}  age {round(age_s)}s")
    print(f"scorecard  {len(sc)} findings  {counts}")
    print(f"written to {OUTDIR}")


if __name__ == "__main__":
    main()
