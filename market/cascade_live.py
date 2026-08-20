"""
First end-to-end cascade run: real Hyperliquid book, real positions, tested model.

WHAT THIS JOINS
    hl2      Hyperliquid l2Book at nSigFigs=3, reaching ~2.7% either side of mid
    liqmap   LIQ-2 position snapshots -- per-wallet size and exact liquidation price
    cascade  the fixed-point sweep, 11 checks passing

WHAT IT IS NOT
    Not a forecast. Not a product number. It answers one narrow question -- given the book we
    can see and the positions we can see, how far would forced flow travel -- and every
    limitation below is load-bearing rather than boilerplate:

      * COVERAGE. LIQ-2 sees roughly half of open interest (F-0003), and the fast tier less. A
        cluster ladder built from it is a LOWER BOUND on forced size, so the cascade computed
        here is a lower bound too.
      * EVAPORATION IS NOT APPLIED YET. The measurement is still running; until it lands this
        uses evaporation=1.0, which is the static book every commercial heatmap assumes and
        which F-0002 says is wrong. The number is therefore OPTIMISTIC BY CONSTRUCTION.
      * BOOK REACH. 20 levels at nSigFigs=3 span ~2.7%. Beyond that the book cannot speak, and
        the model reports exhaustion instead of extrapolating.
      * F-0006 does not apply here -- this book IS Hyperliquid's. The Binance-transfer
        assumption only bites once evaporation is applied.
"""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import cascade as C  # noqa: E402

HL2 = os.path.expanduser("~/genesis-evidence/hl2/btc-l2book.jsonl")
LIQ2 = os.path.expanduser("~/genesis-evidence/liqmap/snapshots-liq2.jsonl")


def latest_book(path=HL2):
    """Most recent l2Book snapshot as ({bid_px: sz}, {ask_px: sz}, mid, t)."""
    # Filter on event class AND channel. A bare substring match on "l2Book" also catches the
    # SUBSCRIPTION_ACK, whose body has no `world` at all -- the same mistake as matching "WORLD"
    # against q5, where the class is actually OBSERVATION.
    last = None
    for line in open(path):
        if '"l2Book"' not in line:
            continue
        e = json.loads(line)
        if e.get("event_class") != "OBSERVATION":
            continue
        # The dialect prefixes the venue channel: it is "hl_l2Book", not "l2Book". Matched on
        # the suffix rather than an exact string, because guessing the exact name has now been
        # wrong three times in this area (WORLD vs OBSERVATION, the ACK, and the prefix).
        ch = e.get("body", {}).get("world", {}).get("channel") or ""
        if not ch.endswith("l2Book"):
            continue
        last = e
    if last is None:
        return None
    e = last
    raw = e["body"]["world"]["raw"]
    bids, asks = raw["data"]["levels"]
    b = {float(l["px"]): float(l["sz"]) for l in bids}
    a = {float(l["px"]): float(l["sz"]) for l in asks}
    mid = (max(b) + min(a)) / 2
    # ALWAYS epoch milliseconds, never a string. The observation carries `received_at` as ISO;
    # the position snapshots carry `t` as epoch ms. Comparing them raw is a TypeError today and
    # would be a silent misalignment the moment one side changed type -- which is the whole
    # reason bookdepth.py converts at the parse boundary.
    obs = e["body"].get("observation", {})
    t = obs.get("t")
    if t is None:
        iso = obs.get("received_at") or e["body"].get("received_at")
        t = int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000) if iso else None
    return b, a, mid, t


def cluster_ladder(path=LIQ2, side="sell"):
    """
    Forced flow as [(trigger_price, notional)] from the most recent snapshot.

    A LONG liquidates by SELLING, so longs form the ladder BELOW spot. Getting this backwards
    inverts the entire map while leaving every number plausible, which is why it is asserted
    here rather than inferred at the call site.
    """
    rows = [json.loads(l) for l in open(path)]
    snap = rows[-1]
    want = "sell" if side == "sell" else "buy"
    out = [(p["liquidationPx"], p["forced_notional"])
           for p in snap["positions"] if p["forced_side"] == want]
    out.sort(key=lambda x: -x[0] if want == "sell" else x[0])
    return out, snap["spot"], snap["coverage"], snap["t"]


def run(trigger_notional=None):
    bk = latest_book()
    if bk is None:
        return {"error": "no hl2 book yet"}
    bids, _asks, mid, t_book = bk
    ladder, spot, coverage, t_map = cluster_ladder(side="sell")

    # The trigger: forced selling from positions whose liquidation price is at or above the
    # current book mid -- i.e. already underwater relative to where the book is now.
    if trigger_notional is None:
        trigger_notional = sum(n for p, n in ladder if p >= mid)
        if trigger_notional <= 0:
            nearest = max((p for p, _ in ladder if p < mid), default=None)
            trigger_notional = sum(n for p, n in ladder if nearest and p == nearest)

    res = C.bracket(bids, "bids", trigger_notional, ladder, mid,
                    evaporation_optimistic=1.0,
                    evaporation_pessimistic=1.0)   # NOT YET MEASURED -- see module docstring

    book_notional = sum(p * q for p, q in bids.items())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "book_mid": mid, "book_bid_notional": book_notional,
        "book_reach_pct": (mid - min(bids)) / mid * 100,
        "map_spot": spot, "map_coverage": coverage,
        "clock_gap_s": (abs(t_book - t_map) / 1000.0
                        if t_book is not None and t_map is not None else None),
        "clusters_below_mid": sum(1 for p, _ in ladder if p < mid),
        "forced_notional_total": sum(n for _, n in ladder),
        "trigger_notional": trigger_notional,
        "result": res,
        "caveats": ["coverage ~half of open interest; forced size is a LOWER BOUND",
                    "evaporation not applied; static book, OPTIMISTIC by construction",
                    "book reaches ~2.7%; beyond that the model reports exhaustion"],
    }


if __name__ == "__main__":
    r = run()
    print(json.dumps(r, indent=1, default=str))
