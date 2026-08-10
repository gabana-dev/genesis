"""
MEASURE-1 measurements A-J, in contract order.

Q1 (is there structure) is computed and reported before Q2 (does it survive costs), because
the contract forbids letting the cost answer colour the structure answer.

Aggregation is SEGMENT-AWARE throughout: the 1-minute series contains 22 venue halts, and
aggregating across one would manufacture a "1-hour return" spanning six real hours and label
it an ordinary observation. Segment-aware aggregation costs 11 of 2,766 daily blocks (0.4%).
"""

import json
import sys

import numpy as np

import data
import stats

FEE_TIERS = {                       # round-trip fee fractions, FEES ONLY (contract section 3)
    "spot_taker": 0.0020,
    "futures_taker": 0.0010,
    "futures_maker": 0.0004,
}
CAPTURES = (1.0, 0.5, 0.25)


def segment_returns(segs, k):
    """Log returns over k-minute blocks, computed within contiguous segments only."""
    out = []
    for s in segs:
        if len(s) < 2 * k:
            continue
        agg = data.aggregate(s, k)
        out.append(data.log_returns(data.close(agg)))
    return np.concatenate(out) if out else np.array([])


def year_of(rows_ms):
    """Vectorised. A Python-level loop here is called per segment per year and dominates."""
    return (np.asarray(rows_ms, dtype="int64").astype("datetime64[ms]")
            .astype("datetime64[Y]").astype("int64") + 1970)


def _seg_year(s):
    return int(year_of(data.open_time(s)[:1])[0])


# ---- A: return magnitude ---------------------------------------------------------------

def measure_A(segs):
    out = {}
    for name, k in data.HORIZONS:
        r = segment_returns(segs, k)
        if len(r) < 30:
            continue
        a = np.abs(r)
        med = float(np.median(a))
        lo, hi = stats.block_bootstrap_ci(a, np.median, n_boot=200)
        out[name] = {"n": int(len(r)), "median_abs": med, "ci": [lo, hi],
                     "q25": float(np.percentile(a, 25)), "q75": float(np.percentile(a, 75)),
                     "std": float(np.std(r))}
    return out


# ---- F: variance ratio (Q1) -------------------------------------------------------------

def measure_F(segs):
    """
    Lo-MacKinlay VR. Base interval is stated explicitly for every entry: VR(q) compares
    q-period variance to q times the base-period variance, so 'the horizon' is base*q.
    """
    out = {}
    plans = [(1, [5, 15, 60], "1m"), (60, [4, 24, 72], "1h")]
    for base_k, qs, base_name in plans:
        r = segment_returns(segs, base_k)
        for q in qs:
            vr, z, p = stats.variance_ratio(r, q)
            horizon = f"{base_k * q}m"
            out[f"{base_name}x{q}"] = {"base": base_name, "q": q, "horizon_minutes": base_k * q,
                                       "n": int(len(r)), "vr": vr, "z2": z, "p": p,
                                       "rejects_random_walk": bool(p == p and p < 0.05)}
    return out


def measure_F_by_year(segs, rows):
    """Stability across years. An answer that is not stable across years is not an answer."""
    out = {}
    years = sorted({_seg_year(s) for s in segs})
    for y in years:
        sub = [s for s in segs if len(s) > 1440 and _seg_year(s) == y]
        if not sub:
            continue
        r = segment_returns(sub, 60)
        if len(r) < 500:
            continue
        vr, z, p = stats.variance_ratio(r, 24)          # 1h base, q=24 -> daily
        out[str(y)] = {"n": int(len(r)), "vr": vr, "z2": z, "p": p}
    return out


# ---- G: signature plot (Q1) -------------------------------------------------------------

def measure_G(segs):
    """
    Realized volatility as a function of sampling frequency. RV inflated at fine sampling is
    microstructure noise, not volatility; where the plot flattens is the finest interval at
    which a measurement means anything.
    """
    out = {}
    for k in (1, 2, 5, 10, 15, 30, 60, 120):
        r = segment_returns(segs, k)
        if len(r) < 100:
            continue
        per_day = np.sqrt(np.mean(r ** 2) * (1440 / k))
        out[f"{k}m"] = {"n": int(len(r)), "rv_daily": float(per_day)}
    return out


# ---- H: Roll effective spread (Q1) ------------------------------------------------------

def measure_H(segs, rows):
    """
    Roll (1984) on 1-minute closes, pooled and per year, plus the raw lag-1 autocorrelation
    it is meant to explain.
    """
    r1 = segment_returns(segs, 1)
    ac1 = stats.autocorr(r1, 1)
    longest = max(segs, key=len)
    roll = stats.roll_spread(data.close(longest))
    per_year = {}
    for y in sorted({_seg_year(s) for s in segs}):
        sub = [s for s in segs if len(s) > 1440 and _seg_year(s) == y]
        if not sub:
            continue
        s = max(sub, key=len)
        rr = stats.roll_spread(data.close(s))
        per_year[str(y)] = {"autocorr_1m": stats.autocorr(data.log_returns(data.close(s)), 1),
                            "roll_spread_frac": rr["spread_frac"],
                            "model_applies": rr["model_applies"], "cov": rr["cov"]}
    return {"autocorr_1m_pooled": ac1, "roll_longest_segment": roll, "by_year": per_year}


# ---- I, J: liquidity and seasonality ----------------------------------------------------

def measure_IJ(rows):
    hourly = data.aggregate(rows, 60)
    r = data.log_returns(data.close(hourly))
    qv = data.quote_volume(hourly)[1:]
    ts = data.open_time(hourly)[1:]
    hod = ((ts // 3_600_000) % 24).astype(int)
    dow = (((ts // 86_400_000) + 4) % 7).astype(int)          # 1970-01-01 was a Thursday

    by_hour = {}
    for h in range(24):
        m = hod == h
        by_hour[h] = {"n": int(m.sum()),
                      "median_abs_return": float(np.median(np.abs(r[m]))),
                      "median_quote_volume": float(np.median(qv[m])),
                      "amihud": stats.amihud(r[m], qv[m])}
    by_dow = {}
    for d in range(7):
        m = dow == d
        by_dow[d] = {"n": int(m.sum()),
                     "median_abs_return": float(np.median(np.abs(r[m]))),
                     "median_quote_volume": float(np.median(qv[m]))}
    return {"by_hour_utc": by_hour, "by_weekday": by_dow,
            "amihud_pooled": stats.amihud(r, qv)}


# ---- B: break-even hit rate (Q2) --------------------------------------------------------

def measure_B(A, spread_impact):
    """
    p* = 1/2 + c / (2*phi*m), with c = fees + spread + impact.

    `spread_impact` is the measured non-fee cost at a chosen notional (section 4C/4D). The
    maker column is an UPPER BOUND on maker attractiveness: adverse selection is a Q3 term and
    is not included anywhere here.
    """
    out = {}
    for horizon, a in A.items():
        m = a["median_abs"]
        row = {}
        for tier, fee in FEE_TIERS.items():
            c = fee + spread_impact
            row[tier] = {"cost_total": c, "cost_fees": fee, "cost_spread_impact": spread_impact,
                         "p_star": {str(phi): stats.breakeven_hit_rate(c, m, phi)
                                    for phi in CAPTURES}}
        out[horizon] = {"median_abs_move": m, "tiers": row}
    return out


def main(out_path, book_path=None):
    rows, facts = data.load(log=None)
    segs = data.contiguous_segments(rows, facts)
    report = {"data_facts": {k: v for k, v in facts.items() if k != "halt_index"},
              "n_segments": len(segs)}

    report["A_return_magnitude"] = A = measure_A(segs)
    report["F_variance_ratio"] = measure_F(segs)
    report["F_variance_ratio_by_year"] = measure_F_by_year(segs, rows)
    report["G_signature_plot"] = measure_G(segs)
    report["H_roll_spread"] = measure_H(segs, rows)
    report["IJ_liquidity_seasonality"] = measure_IJ(rows)

    if book_path:
        report["CD_spread_and_impact"] = cd = measure_CD(book_path)
        si = cd["round_trip"]["10000"]["median"]
    else:
        si = 0.0
    report["B_breakeven"] = measure_B(A, si)

    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=float)
    return report


def measure_CD(path, market="BTCUSDT", notionals=(1000, 10000, 50000, 100000, 500000)):
    import book as bk
    spreads, rt, depth = [], {n: [] for n in notionals}, []
    n = 0
    for _, b, a in bk.walk(path, market, every_ms=1000):
        spreads.append(bk.spread(b, a)["frac"])
        depth.append(sum(float(p) * float(q) for p, q in b.items()))
        n += 1
        if n % 5:
            continue
        for k in notionals:
            v = bk.round_trip_impact(b, a, k)
            rt[k].append(v if v is not None else np.nan)
    s = np.array(spreads)
    out = {"n_samples": n, "source": path,
           "spread": {"median_frac": float(np.median(s)), "p95_frac": float(np.percentile(s, 95))},
           "recorded_depth_usd_median": float(np.median(depth)), "round_trip": {}}
    for k, v in rt.items():
        v = np.array(v)
        ok = np.isfinite(v)
        out["round_trip"][str(k)] = {
            "median": float(np.median(v[ok])) if ok.any() else None,
            "p95": float(np.percentile(v[ok], 95)) if ok.any() else None,
            "depth_exhausted": int((~ok).sum()), "n": int(len(v))}
    return out


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
