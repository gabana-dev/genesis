"""
DIR-2: the declared grid from CONTRACT-direction-2.md, and nothing else.

Frozen 2026-08-19 at sha256 df746b42458e5fdd7eec8471c21fc18758e522a8fede7203458b42f5f93ca99a,
before any predictive figure was computed.

WHAT DIFFERS FROM DIR-1, AND WHAT DELIBERATELY DOES NOT
    Everything except the features and the gate is carried over unchanged -- same 8h decision
    grid, same purged walk-forward, same embargo, same OLS-sign model, same imported bar. The
    two results have to be comparable, and a second difference would make any gap between them
    unattributable.

THE GATE IS APPLIED TO THE TEST SET ONLY
    Training uses every point. Gating training too would shrink it below usefulness AND change
    the question from "does this state select predictable moments" to "does a model fitted only
    on rare states generalise". Those are different hypotheses and only the first is declared.

THE BAR DOES NOT MOVE
    52.8% at 1 day, 51.5% at 3 days, imported from MEASURE-1. Trading less often does not lower
    a per-trade break-even: the cost of a round trip is identical whether you make ten or ten
    thousand. Restated here because it is the most natural thing to get wrong about a
    conditional strategy.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import dir1 as D1  # noqa: E402
import stats as ST  # noqa: E402

CONTRACT = "market/CONTRACT-direction-2.md"
CONTRACT_SHA256 = "df746b42458e5fdd7eec8471c21fc18758e522a8fede7203458b42f5f93ca99a"

METRICS = os.path.expanduser("~/genesis-evidence/metrics/metrics-consolidated.npy")
METRICS_SHA256 = "30b98a961a461adc9478cd62b7ee75ba60e8d9ee69c3592fe75d9d281af06db0"

# Column order in the consolidated array.
M_TS, M_OI, M_OIV, M_CT_LS, M_ST_LS, M_C_LS, M_TAKER = range(7)

Z_WINDOW = D1.Z_WINDOW              # 30 days in decision points, as DIR-1
GATE_Z = 2.0                        # section 4, fixed once, applied uniformly
MIN_TEST_PREDICTIONS = 200          # K1
DAY = D1.DAY

FEATURES = ["taker_z", "oi_z", "doi_z", "toptrader_z", "crowd_z"]

GATES = {
    "G1_flow_extreme":      lambda c: np.abs(c["taker_z"]) > GATE_Z,
    "G2_leverage_build":    lambda c: c["doi_z"] > GATE_Z,
    "G3_toptrader_extreme": lambda c: np.abs(c["toptrader_z"]) > GATE_Z,
    "G4_crowd_extreme":     lambda c: np.abs(c["crowd_z"]) > GATE_Z,
    "G5_no_gate":           lambda c: np.ones(len(c["t"]), dtype=bool),
}


def load_metrics():
    a = np.load(METRICS)
    return a[np.argsort(a[:, M_TS])]


def assemble():
    """
    DIR-1's decision grid, plus the metrics fields carried forward to each 8h boundary.

    `searchsorted(side="right") - 1` takes the last metrics row at or BEFORE the boundary.
    Taking the row after it would be a one-observation look-ahead, invisible in the output and
    worth roughly nothing in accuracy terms -- which is exactly why it has to be excluded by
    construction rather than by care.
    """
    cols = D1.build_rows()
    m = load_metrics()
    mt = m[:, M_TS] * 1000.0                       # metrics timestamps are seconds

    idx = np.searchsorted(mt, cols["t"], side="right") - 1
    valid = idx >= 0
    idx = np.clip(idx, 0, len(m) - 1)

    # Staleness guard: a metrics row more than one interval old is not evidence about now.
    stale = (cols["t"] - mt[idx]) > (8 * 3600 * 1000)
    bad = (~valid) | stale

    def take(col):
        v = m[idx, col].astype(float)
        v[bad] = np.nan
        return v

    oi = take(M_OI)
    cols["open_interest"] = oi
    cols["taker"] = take(M_TAKER)
    cols["toptrader"] = take(M_ST_LS)
    cols["crowd"] = take(M_C_LS)

    # 24h change in open interest, in log terms. Trailing only.
    doi = np.full(len(oi), np.nan)
    doi[DAY:] = np.log(oi[DAY:] / oi[:-DAY])
    cols["doi"] = doi

    cols["taker_z"] = D1._trailing_z(cols["taker"], Z_WINDOW)
    cols["oi_z"] = D1._trailing_z(oi, Z_WINDOW)
    cols["doi_z"] = D1._trailing_z(doi, Z_WINDOW)
    cols["toptrader_z"] = D1._trailing_z(cols["toptrader"], Z_WINDOW)
    cols["crowd_z"] = D1._trailing_z(cols["crowd"], Z_WINDOW)
    return cols


def walk_forward_gated(cols, feature_names, h, gate_mask):
    """
    DIR-1's protocol with the gate applied to the test indices only.

    Training is ungated by design (see module docstring). Purge and embargo are unchanged, so
    a gated result and DIR-1's ungated one differ in the gate and in nothing else.
    """
    X = np.column_stack([cols[f] for f in feature_names])
    y = D1.label(cols["close"], h)
    ok = np.isfinite(X).all(axis=1) & np.isfinite(y)

    n = len(y)
    preds, truth, per_window = [], [], []
    start = 0
    while start + D1.TRAIN + h + D1.TEST <= n:
        tr_end = start + D1.TRAIN
        tr = np.arange(start, tr_end - h)
        te = np.arange(tr_end + h, min(tr_end + h + D1.TEST, n))
        tr = tr[ok[tr]]
        te = te[ok[te] & gate_mask[te]]                    # <- the gate, test side only
        if len(tr) > len(feature_names) + 10 and len(te) >= 1:
            p = D1.ols_sign(X[tr], y[tr], X[te])
            per_window.append({"train_end_t": float(cols["t"][tr_end]),
                               "n_test": int(len(te)),
                               "accuracy": float(np.mean(np.sign(p) == np.sign(y[te])))})
            preds.append(p)
            truth.append(y[te])
        start += D1.ROLL

    if not preds:
        return None, None, []
    return np.concatenate(preds), np.concatenate(truth), per_window


def _year_concentration(cols, mask, pool_idx):
    """K6: is a gate's passing set concentrated in one calendar year?"""
    import datetime as dt
    ts = cols["t"][pool_idx][mask[pool_idx]]
    if len(ts) == 0:
        return None, None
    years = [dt.datetime.fromtimestamp(t / 1000.0, dt.UTC).year for t in ts]
    top = max(set(years), key=years.count)
    return top, years.count(top) / len(years)


def cell(cols, gate_name, gate_fn, hname, h, n_boot=2000):
    mask = gate_fn(cols)
    mask = np.where(np.isfinite(mask.astype(float)), mask, False).astype(bool)
    pred, truth, windows = walk_forward_gated(cols, FEATURES, h, mask)

    out = {"gate": gate_name, "horizon": hname,
           "gate_pass_rate": float(mask.mean())}
    if pred is None or len(pred) < MIN_TEST_PREDICTIONS:
        out.update({"sufficient": False, "n_predictions": 0 if pred is None else int(len(pred)),
                    "excluded_reason": f"fewer than {MIN_TEST_PREDICTIONS} predictions"})
        return out

    hits = (np.sign(pred) == np.sign(truth)).astype(float)
    acc = float(hits.mean())
    accs = [w["accuracy"] for w in windows]
    bar = D1.BAR[(hname, 0.5)]
    yr, conc = _year_concentration(cols, mask, np.arange(len(cols["t"])))
    out.update({
        "sufficient": True,
        "n_predictions": int(len(pred)), "n_windows": len(windows),
        "accuracy": acc,
        "bar_phi_0.50": bar, "bar_phi_0.25": D1.BAR[(hname, 0.25)],
        "clears_phi_0.50": acc > bar,
        "per_window_sd": float(np.std(accs)),
        "edge_over_coinflip": acc - 0.5,
        "regime_sd_exceeds_edge": float(np.std(accs)) > abs(acc - 0.5),   # K4
        "dominant_year": yr, "dominant_year_share": conc,
        "regime_bound": bool(conc is not None and conc > 0.60),           # K6
        "per_window_accuracy": accs,
    })
    try:
        lo, hi = ST.block_bootstrap_ci(hits, lambda a: float(np.mean(a)),
                                       n_boot=n_boot, block=h, alpha=0.05)
        out["accuracy_ci"] = [float(lo), float(hi)]
        out["ci_excludes_bar"] = bool(lo > bar)
    except Exception as e:
        out["accuracy_ci"] = None
        out["ci_error"] = f"{type(e).__name__}: {e}"
    return out


def null_p95_best(n_trials, n_obs, n_sims=20000, seed=20260819):
    """
    K3 as CORRECTED. DIR-1 compared the best cell against the MEAN of the null maximum, which
    is a coin flip and rejected only half of pure noise (defect D-D1). The p95 is the test.
    """
    rng = np.random.default_rng(seed)
    best = rng.binomial(n_obs, 0.5, size=(n_sims, n_trials)).max(axis=1) / n_obs
    return {"mean_best": float(best.mean()), "p95_best": float(np.quantile(best, 0.95)),
            "n_trials": n_trials, "n_obs": n_obs}


def run(n_boot=2000):
    cols = assemble()
    report = {
        "contract": CONTRACT, "contract_sha256": CONTRACT_SHA256,
        "metrics_sha256": METRICS_SHA256,
        "decision_points": int(len(cols["t"])),
        "features": FEATURES,
        "grid": {"gates": list(GATES), "horizons": list(D1.HORIZONS),
                 "declared_trials": len(GATES) * len(D1.HORIZONS)},
        "cells": {},
    }
    for hname, h in D1.HORIZONS.items():
        for gname, gfn in GATES.items():
            report["cells"][f"{gname}|{hname}"] = cell(cols, gname, gfn, hname, h, n_boot)

    good = [c for c in report["cells"].values() if c.get("sufficient")]
    if good:
        n_obs = int(np.median([c["n_predictions"] for c in good]))
        null = null_p95_best(len(good), n_obs)
        best = max(good, key=lambda c: c["accuracy"])
        report["zero_skill"] = null
        report["best_cell"] = {
            "gate": best["gate"], "horizon": best["horizon"], "accuracy": best["accuracy"],
            "null_p95": null["p95_best"],
            "exceeds_null_p95": best["accuracy"] > null["p95_best"],   # K3, corrected
        }
    return report
