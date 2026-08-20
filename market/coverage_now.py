"""
What fraction of Hyperliquid BTC open interest can we actually see today?

LIQ-2 answered 20.24%, from a universe frozen on FOUR HOURS of recording -- the defect in
research/DEFECT-universe-was-four-hours-not-21-days.md. The recording now knows 31,349 wallets
against the 5,395 that figure came from, so the number is stale and the real one is unmeasured.

THIS IS A MEASUREMENT FOR A BUSINESS DECISION, NOT A CONTRACT EXPERIMENT.
    LIQ-2 is dead: K2 fired, its verdict stands, its secondary is never computed. Nothing here
    may be used to revive it. What is being priced is whether an archive of this data is worth
    building, which turns entirely on how much of the exchange it would cover.

WHY STRATIFIED RATHER THAN A FULL SCAN
    31,349 wallets at the measured 1.585 s/wallet is 13.8 hours, which would starve the hourly
    collection for most of a day. Instead:

      stratum A  the 5,395 wallets already scanned -- notional taken from the most recent deep
                 scan, no rescan needed
      stratum B  a RANDOM sample of the 25,954 wallets discovered since, scanned now

    Total notional is estimated as A + (mean per new wallet x 25,954). Random sampling makes
    that unbiased. Notional is heavy-tailed, so the interval is bootstrapped rather than
    assumed normal, and it will be wide -- which is itself the honest answer.

    The sample must be RANDOM, not activity-ordered. Ordering by activity is what produced the
    5.8% coverage of LIQ-1, because appearance count is anti-correlated with position size.
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import liqmap as L  # noqa: E402

SEED = 20260820          # fixed so the sample is reproducible
SAMPLE = 1200            # ~32 min at 1.585 s/wallet
OUT = os.path.expanduser("~/genesis-evidence/liqmap/coverage-now.json")


def known_stratum():
    """Notional held by the old 5,395, from the most recent deep scan."""
    deep = None
    for line in open(L.LIQ2_SNAP_PATH):
        row = json.loads(line)
        if row.get("tier") == "deep":
            deep = row
    if deep is None:
        raise RuntimeError("no deep scan to read stratum A from")
    return {"wallets": deep["scanned"],
            "holding": len(deep["positions"]),
            "notional": sum(p["forced_notional"] for p in deep["positions"]),
            "oi_usd": deep["oi_usd"],
            "at": deep["t"]}


def bootstrap_ci(values, n_total, draws=2000):
    """Percentile interval on the ESTIMATED TOTAL for a stratum, resampling wallets."""
    rng = random.Random(SEED)
    n = len(values)
    out = []
    for _ in range(draws):
        s = sum(values[rng.randrange(n)] for _ in range(n))
        out.append(s / n * n_total)
    out.sort()
    return out[int(0.025 * draws)], out[int(0.975 * draws)]


def main():
    uni = json.load(open("/tmp/claude-501/-Users-gabana/b84fd402-f17a-4af6-80bd-3127411f57c3"
                         "/scratchpad/universe_now.json"))
    new = uni["new"]
    a = known_stratum()

    rng = random.Random(SEED)
    sample = rng.sample(new, min(SAMPLE, len(new)))

    print(f"stratum A: {a['wallets']:,} wallets, {a['holding']:,} holding, "
          f"${a['notional']:,.0f}")
    print(f"stratum B: sampling {len(sample):,} of {len(new):,} new wallets "
          f"(~{len(sample)*1.585/60:.0f} min)\n")

    budget = {"sleep": L.BASE_SLEEP, "throttled": 0}
    positions, scanned, holding = L.scan(sample, budget)

    per = {w: 0.0 for w in sample}
    for p in positions:
        per[p["wallet"]] += p["forced_notional"]
    vals = list(per.values())

    b_mean = sum(vals) / len(vals)
    b_total = b_mean * len(new)
    lo, hi = bootstrap_ci(vals, len(new))

    oi = L.exchange_open_interest(budget) or a["oi_usd"]
    total = a["notional"] + b_total

    res = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": "business sizing; LIQ-2 stays dead and is not revived by this",
        "seed": SEED,
        "universe_now": len(uni["current"]), "old_universe": a["wallets"],
        "new_wallets": len(new), "sampled": scanned, "sample_holding": holding,
        "sample_hold_rate": holding / max(scanned, 1),
        "stratum_a_notional": a["notional"],
        "stratum_b_mean_per_wallet": b_mean,
        "stratum_b_estimated_total": b_total,
        "stratum_b_ci": [lo, hi],
        "oi_usd": oi,
        "coverage_point": total / oi,
        "coverage_ci": [(a["notional"] + lo) / oi, (a["notional"] + hi) / oi],
        "liq2_coverage_for_comparison": 0.2024,
        "throttled": budget["throttled"],
    }
    json.dump(res, open(OUT, "w"), indent=1)

    print(f"sample: {holding}/{scanned} hold BTC ({res['sample_hold_rate']:.1%}), "
          f"mean ${b_mean:,.0f}/wallet")
    print(f"stratum B estimated total: ${b_total:,.0f}  95% CI [${lo:,.0f}, ${hi:,.0f}]")
    print(f"\nexchange OI      ${oi:,.0f}")
    print(f"estimated visible ${total:,.0f}")
    print(f"\nCOVERAGE {res['coverage_point']:.1%}   "
          f"95% CI [{res['coverage_ci'][0]:.1%}, {res['coverage_ci'][1]:.1%}]")
    print(f"LIQ-2 reported   20.24%")
    return res


if __name__ == "__main__":
    main()
