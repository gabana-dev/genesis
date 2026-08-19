"""
COVERAGE TEST — are the wallets LIQ-2 cannot see dormant, or merely trading other assets?

Declared in research/on-chain-enumeration-scope.md §7 BEFORE running. This module fixes the
sampling rule, the sample size and the decision thresholds in code so that the interpretation
cannot be chosen after the numbers arrive.

THE QUESTION
    LIQ-2 reached 20.24% of exchange open interest and its universe is exhausted: the top 300
    of 5,395 wallets hold 97.8% of scan-set notional, so scanning more of the same kind gains
    nothing. The missing ~80% is therefore held by wallets absent from our universe entirely.

    Our universe came from a BTC-only trade recording. So the missing wallets are one of:

      ACTIVE ELSEWHERE  they trade, but in assets we never recorded. Reachable -- widening the
                        recording to all assets would find them, and coverage has a path up.
      DORMANT           they hold without trading. Unreachable -- on-chain enumeration of deep
                        history is ~210 years, so nothing we can build finds them.

WHY L1 BLOCKS ARE THE RIGHT INSTRUMENT HERE
    Block transactions carry every actor regardless of asset, so a block sample is exactly the
    all-asset population our BTC-only recording could not see. It is still a sample of RECENT
    activity and cannot speak for genuinely dormant wallets -- which is the point: if even the
    all-asset active population fails to add notional, the remainder is dormant by elimination.

Run: .venv/bin/python market/coverage_test.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import liqmap as L  # noqa: E402

RPC = "https://rpc.hyperliquid.xyz/explorer"
OUT = os.path.expanduser("~/genesis-evidence/liqmap/coverage-test.json")

# ---------------------------------------------------------------------------------------
# DECLARED BEFORE THE RUN. Nothing below may be tuned after seeing a result.
# ---------------------------------------------------------------------------------------
TIP = 530_000_000          # measured 2026-08-19
BLOCK_STRIDE = 1_000       # every 1000th block back from the tip -- mechanical, no discretion
N_BLOCKS = 40              # ~8 min at the measured 0.08 blocks/s
MAX_NOVEL = 400            # cap on clearinghouseState calls, ~11 min at 1.585 s/wallet

# Decision rule, fixed here. `rate` is the fraction of scanned wallets holding a BTC position;
# `mean` is mean forced notional per holding wallet. Both are compared against the LIQ-2 deep
# scan's own figures, so the comparison is against our existing universe rather than a guess.
ACTIVE_RATE_FRAC = 0.50    # novel rate >= 50% of baseline AND
ACTIVE_MEAN_FRAC = 0.50    # novel mean >= 50% of baseline  -> ACTIVE ELSEWHERE
DORMANT_RATE_FRAC = 0.25   # novel rate < 25% of baseline   -> DORMANT
DORMANT_MEAN_FRAC = 0.10   # or novel mean < 10% of baseline -> DORMANT
# anything else -> INCONCLUSIVE, reported as such and not resolved by choosing a side.


def _post(body, tries=8):
    req = urllib.request.Request(RPC, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    back = 5.0
    for _ in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(back)
                back = min(60.0, back * 2)
                continue
            return None
        except Exception:
            time.sleep(3)
    return None


def sample_addresses():
    """Distinct `user` addresses from N_BLOCKS sampled every BLOCK_STRIDE back from the tip."""
    users, ok = set(), 0
    for i in range(N_BLOCKS):
        out = _post({"type": "blockDetails", "height": TIP - i * BLOCK_STRIDE})
        bd = out.get("blockDetails") if isinstance(out, dict) else None
        if not isinstance(bd, dict):
            continue
        ok += 1
        for t in bd.get("txs") or []:
            u = t.get("user")
            if u:
                users.add(u.lower())
        time.sleep(1.0)
    return users, ok


def baseline():
    """The LIQ-2 deep scan's own hold rate and mean notional -- what we already reach."""
    path = L.LIQ2_SNAP_PATH
    deep = None
    for line in open(path):
        row = json.loads(line)
        if row.get("tier") == "deep":
            deep = row
    if deep is None:
        raise RuntimeError("no deep scan to baseline against")
    pos = deep["positions"]
    return {"scanned": deep["scanned"], "holding": len(pos),
            "rate": len(pos) / deep["scanned"],
            "mean_notional": sum(p["forced_notional"] for p in pos) / max(len(pos), 1),
            "total_notional": sum(p["forced_notional"] for p in pos),
            "coverage": deep["coverage"], "oi_usd": deep["oi_usd"]}


def verdict(b, novel_rate, novel_mean):
    if (novel_rate >= ACTIVE_RATE_FRAC * b["rate"]
            and novel_mean >= ACTIVE_MEAN_FRAC * b["mean_notional"]):
        return "ACTIVE ELSEWHERE"
    if (novel_rate < DORMANT_RATE_FRAC * b["rate"]
            or novel_mean < DORMANT_MEAN_FRAC * b["mean_notional"]):
        return "DORMANT"
    return "INCONCLUSIVE"


def main():
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    b = baseline()
    universe = {w.lower() for w in L.universe()}

    print(f"baseline (LIQ-2 deep): {b['holding']}/{b['scanned']} hold BTC "
          f"({b['rate']:.1%}), mean ${b['mean_notional']:,.0f}, coverage {b['coverage']:.2%}")
    print(f"sampling {N_BLOCKS} blocks every {BLOCK_STRIDE} back from {TIP:,} ...")

    sampled, blocks_ok = sample_addresses()
    novel = sorted(sampled - universe)
    print(f"  {blocks_ok} blocks read, {len(sampled)} distinct addresses, "
          f"{len(novel)} NOT in our {len(universe)}-wallet universe")

    scan_list = novel[:MAX_NOVEL]
    budget = {"sleep": L.BASE_SLEEP, "throttled": 0}
    positions, scanned, holding = L.scan(scan_list, budget)

    novel_rate = holding / scanned if scanned else 0.0
    novel_total = sum(p["forced_notional"] for p in positions)
    novel_mean = novel_total / holding if holding else 0.0
    v = verdict(b, novel_rate, novel_mean)

    result = {
        "started": started, "finished": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "declared_in": "research/on-chain-enumeration-scope.md §7",
        "rule": {"stride": BLOCK_STRIDE, "n_blocks": N_BLOCKS, "max_novel": MAX_NOVEL,
                 "active_rate_frac": ACTIVE_RATE_FRAC, "active_mean_frac": ACTIVE_MEAN_FRAC,
                 "dormant_rate_frac": DORMANT_RATE_FRAC, "dormant_mean_frac": DORMANT_MEAN_FRAC},
        "baseline": b,
        "blocks_read": blocks_ok, "addresses_sampled": len(sampled),
        "novel_addresses": len(novel), "novel_scanned": scanned,
        "novel_holding": holding, "novel_rate": novel_rate,
        "novel_total_notional": novel_total, "novel_mean_notional": novel_mean,
        "rate_vs_baseline": novel_rate / b["rate"] if b["rate"] else None,
        "mean_vs_baseline": novel_mean / b["mean_notional"] if b["mean_notional"] else None,
        "throttled": budget["throttled"],
        "verdict": v,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(result, open(OUT, "w"), indent=1)

    print(f"\n  novel scanned {scanned}, holding {holding} ({novel_rate:.1%})")
    print(f"  novel mean notional ${novel_mean:,.0f}   total ${novel_total:,.0f}")
    print(f"  rate vs baseline {result['rate_vs_baseline']:.2f}x   "
          f"mean vs baseline {result['mean_vs_baseline']:.2f}x")
    print(f"\n  VERDICT: {v}")
    return result


if __name__ == "__main__":
    main()
