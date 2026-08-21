"""
CASCADE-1 runner. Contract: market/CONTRACT-cascade.md, frozen 2026-08-20,
sha256 7dee22eed9cdaecb833687f93a56add383e7856bf059d2475841a55089e9bb46.

THE QUESTION
    After a large forced liquidation, does price continue in the direction the forced flow
    pushed it, over the following minutes, by more than the cost of acting?

    Every liquidation product shows WHERE clusters sit. None publishes whether reaching one does
    anything. This is the empirical version of that question, on 48,104 liquidation events across
    757 symbols already recorded in q5.

EVERY PARAMETER BELOW IS COPIED FROM THE FROZEN CONTRACT.
    Nothing here chooses a threshold, a horizon, or a benchmark. If a value here disagrees with
    the contract, the contract wins and the run is void.

EPISODES, NOT EVENTS (contract §5, K1)
    90% of large liquidations fall within 60 s of another. They are cascade episodes, not
    independent draws, and counting events as observations inflates n roughly threefold. The
    contract's first draft made exactly that error and the power section caught it.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import bookdepth as B  # noqa: E402

Q5 = os.path.expanduser("~/genesis-evidence/q5/btcusdt-q5.jsonl")
OUT = os.path.expanduser("~/genesis-evidence/cascade1/result.json")

# --- contract §4, §5, §6 ---------------------------------------------------------------
STRATA = {"primary_250k": 250_000, "secondary_1m": 1_000_000, "secondary_50k": 50_000}
PRIMARY = "primary_250k"
HORIZONS_MIN = (1, 5, 15)
EPISODE_GAP_MS = 60_000
K1_MIN_EPISODES = 170
PERMUTATIONS = 10_000
SEED = 20260820


def load_events(path=Q5):
    """(t_ms, symbol, side, notional) for every forceOrder in the recording."""
    out = []
    with open(path) as f:
        for line in f:
            if '"forceOrder"' not in line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("body", {}).get("world", {}).get("channel") != "forceOrder":
                continue
            o = (e["body"]["world"].get("raw") or {}).get("o") or {}
            try:
                t = int(o["T"])
                px = float(o.get("ap") or o["p"])
                out.append((t, o["s"], o["S"], px * float(o["q"])))
            except (KeyError, TypeError, ValueError):
                continue
    return out


def episodes(events, threshold, gap_ms=EPISODE_GAP_MS):
    """
    Collapse to independent episodes: same symbol, same side, separated by >= gap.

    Each episode is represented by its LARGEST event, and carries the episode's total notional.
    """
    by = defaultdict(list)
    for t, sym, side, n in events:
        if n >= threshold:
            by[(sym, side)].append((t, n))
    out = []
    for (sym, side), rows in by.items():
        rows.sort()
        cur = [rows[0]]
        for r in rows[1:]:
            if r[0] - cur[-1][0] > gap_ms:
                out.append((max(cur, key=lambda x: x[1])[0], sym, side,
                            sum(x[1] for x in cur)))
                cur = [r]
            else:
                cur.append(r)
        out.append((max(cur, key=lambda x: x[1])[0], sym, side, sum(x[1] for x in cur)))
    return sorted(out)


def klines_for(symbols, days, interval="1m"):
    """{symbol: {minute_ms: close}} from the free daily archive."""
    out = {}
    for sym in symbols:
        closes = {}
        for d in days:
            p = B.fetch_klines(sym, d, interval)
            if not p:
                continue
            for t, _o, _h, _l, c in B.read_klines(p):
                closes[t] = c
        if closes:
            out[sym] = closes
    return out


def forward_return(closes, t_ms, horizon_min, side):
    """
    Signed return in the FORCED direction over the horizon, in bps.

    A forced SELL pushes price down, so continuation is a further fall: the sign is flipped so
    that positive always means "continued in the direction the flow pushed".
    """
    m0 = (t_ms // 60000) * 60000
    c0 = closes.get(m0)
    c1 = closes.get(m0 + horizon_min * 60000)
    if not c0 or not c1 or c0 <= 0:
        return None
    r = (c1 - c0) / c0 * 10_000.0
    return -r if side == "SELL" else r


def matched_control(closes, t_ms, horizon_min, side, rng, tries=40):
    """
    Tier 2: a random minute in the SAME symbol within the SAME hour.

    The load-bearing benchmark. Liquidations happen when markets are already moving, so an
    unmatched comparison measures volatility clustering and calls it causation.
    """
    hour = (t_ms // 3600000) * 3600000
    for _ in range(tries):
        m = hour + rng.integers(0, 60) * 60000
        if abs(m - t_ms) < 120000:      # not the event's own neighbourhood
            continue
        r = forward_return(closes, m, horizon_min, side)
        if r is not None:
            return r
    return None


def run():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    events = load_events()
    days = sorted({datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat()
                   for t, _, _, _ in events})
    print(f"events {len(events):,}  days {days[0]}..{days[-1]}", flush=True)

    result = {"contract": "market/CONTRACT-cascade.md",
              "sha256": "7dee22eed9cdaecb833687f93a56add383e7856bf059d2475841a55089e9bb46",
              "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "events": len(events), "days": days, "strata": {}}

    for name, thr in STRATA.items():
        eps = episodes(events, thr)
        syms = sorted({s for _, s, _, _ in eps})
        print(f"\n{name} (>=${thr:,}): {len(eps)} episodes, {len(syms)} symbols", flush=True)
        closes = klines_for(syms, days)
        stratum = {"threshold": thr, "episodes": len(eps), "symbols": len(syms), "horizons": {}}

        for h in HORIZONS_MIN:
            obs, ctrl = [], []
            for t, sym, side, _n in eps:
                c = closes.get(sym)
                if not c:
                    continue
                r = forward_return(c, t, h, side)
                if r is None:
                    continue
                obs.append(r)
                m = matched_control(c, t, h, side, rng)
                if m is not None:
                    ctrl.append(m)
            if len(obs) < 10:
                stratum["horizons"][f"{h}m"] = {"n": len(obs), "note": "too few to report"}
                continue

            o = np.array(obs)
            perm = np.array([np.mean(o * rng.choice([-1, 1], size=len(o)))
                             for _ in range(PERMUTATIONS)])
            stratum["horizons"][f"{h}m"] = {
                "n": len(o), "mean_bps": float(o.mean()), "median_bps": float(np.median(o)),
                "hit_rate": float((o > 0).mean()),
                "tier0_perm_p95_bps": float(np.quantile(perm, 0.95)),
                "tier0_clears": bool(o.mean() > np.quantile(perm, 0.95)),
                "tier2_control_n": len(ctrl),
                "tier2_control_mean_bps": float(np.mean(ctrl)) if ctrl else None,
                "tier2_clears": bool(o.mean() > np.mean(ctrl)) if ctrl else None,
            }
            r = stratum["horizons"][f"{h}m"]
            print(f"  {h:>2}m  n={r['n']:>4}  mean {r['mean_bps']:>8.2f} bps  "
                  f"hit {r['hit_rate']:.3f}  perm p95 {r['tier0_perm_p95_bps']:.2f}  "
                  f"ctrl {r['tier2_control_mean_bps'] or 0:.2f}  "
                  f"T0 {'Y' if r['tier0_clears'] else 'n'} "
                  f"T2 {'Y' if r['tier2_clears'] else 'n'}", flush=True)
        result["strata"][name] = stratum

    p = result["strata"].get(PRIMARY, {})
    result["K1_met"] = p.get("episodes", 0) >= K1_MIN_EPISODES
    result["K1_required"] = K1_MIN_EPISODES
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(result, open(OUT, "w"), indent=1)
    print(f"\nK1 ({K1_MIN_EPISODES} episodes in {PRIMARY}): "
          f"{'MET' if result['K1_met'] else 'NOT MET -- unevaluable'}")
    print(f"written to {OUT}  ({time.time()-t0:.0f}s)")
    return result


if __name__ == "__main__":
    run()
