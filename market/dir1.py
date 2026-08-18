"""
DIR-1: the declared grid from CONTRACT-direction.md, and nothing else.

Frozen 2026-08-18 at sha256 0e319d3630e1c3d852e4968a723b5cace869f01c7003a435250dadbe77b26f78,
before any predictive figure was computed. This module chooses nothing.

LEAKAGE IS THE ONLY FAILURE THAT MATTERS HERE
    K5 voids the entire run if any feature uses information unavailable at its decision
    timestamp. Three separate places where that could happen, and how each is closed:

      1. FEATURES. Every feature is built from bars strictly at or before the decision
         boundary. `_trailing` slices [i-n : i], never [i-n : i+1].

      2. STANDARDISATION. z-scores use a trailing window ending at the decision timestamp, not
         a full-sample mean and standard deviation. A full-sample z-score is the most common
         leak in this literature and it is invisible in the output -- accuracy simply comes
         out too high.

      3. PURGE AND EMBARGO. A training sample at time s carries a label reaching s+H. If
         s+H lands past the train/test boundary, that label overlaps the test period and the
         sample is PURGED. Separately, the first H of each test window is EMBARGOED, so a test
         label cannot overlap the training window either. Both directions, because the overlap
         is symmetric.

MODEL CLASS
    OLS on the forward return, prediction taken as the sign of the fitted value. Linear by
    contract section 3, which cites Pindza (2026): LightGBM -10.94% out-of-sample R2 against
    linear OLS +1.23% on 3.4M observations under purged validation.
"""

import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import stats as ST  # noqa: E402

CONTRACT = "market/CONTRACT-direction.md"
CONTRACT_SHA256 = "0e319d3630e1c3d852e4968a723b5cace869f01c7003a435250dadbe77b26f78"

BARS = os.path.expanduser("~/genesis-evidence/market-data/*.npy")
CARRY = os.path.expanduser("~/genesis-evidence/carry1")

INTERVAL_MS = 8 * 3600 * 1000
DAY = 3                                   # decision points per day
HORIZONS = {"1d": 1 * DAY, "3d": 3 * DAY}

# Section 1. Measured by MEASURE-1, not chosen here.
BAR = {("1d", 0.5): 0.5280868101002973, ("3d", 0.5): 0.5151417834228978,
       ("1d", 0.25): 0.5561736202005947, ("3d", 0.25): 0.5302835668457958}

# Section 6.2, in decision points.
TRAIN = 730 * DAY
TEST = 90 * DAY
ROLL = 90 * DAY
MIN_TEST_PREDICTIONS = 30                 # K1
Z_WINDOW = 30 * DAY                       # trailing standardisation window

FEATURE_SETS = {
    "F1_funding": ["funding", "funding_z"],
    "F2_basis": ["basis", "basis_z"],
    "F3_har_rv": ["rv_1d", "rv_5d", "rv_22d"],
    "F4_momentum": ["ret_1d", "ret_7d", "ret_30d"],
    "F5_trade_size": ["trade_size_z"],
    "F6_combined": ["funding", "funding_z", "basis", "basis_z",
                    "rv_1d", "rv_5d", "rv_22d",
                    "ret_1d", "ret_7d", "ret_30d", "trade_size_z"],
}


# ---------------------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------------------

def _snap(t):
    return int(round(t / INTERVAL_MS) * INTERVAL_MS)


def load_bars():
    """All minute bars, concatenated and sorted. Columns: t,O,H,L,C,V,close_t,quoteV,n."""
    files = sorted(glob.glob(BARS))
    a = np.concatenate([np.load(f) for f in files], axis=0)
    return a[np.argsort(a[:, 0])]


def build_rows():
    """
    One row per 8h decision boundary, carrying only what was observable at it.

    Minute bars are aggregated to the boundary; funding and basis come from the CARRY-1
    archive on the same boundaries. Rows missing any input are dropped and counted -- never
    interpolated, for the same reason CARRY-1 drops them.
    """
    bars = load_bars()
    t = bars[:, 0]
    close = bars[:, 4]
    vol = bars[:, 5]
    ntr = bars[:, 8]

    # Boundary index: for each 8h boundary, the position of the last minute bar at or before it.
    lo, hi = _snap(t[0]) + INTERVAL_MS, _snap(t[-1])
    bounds = np.arange(lo, hi + 1, INTERVAL_MS)
    idx = np.searchsorted(t, bounds, side="right")          # bars[:idx] are strictly before
    keep = idx > 0
    bounds, idx = bounds[keep], idx[keep]

    # Minute log returns, for realised volatility.
    lr = np.zeros_like(close)
    lr[1:] = np.log(close[1:] / close[:-1])

    csum_v = np.concatenate([[0.0], np.cumsum(vol)])
    csum_n = np.concatenate([[0.0], np.cumsum(ntr)])
    csum_r2 = np.concatenate([[0.0], np.cumsum(lr ** 2)])

    MIN_PER_8H = 480

    def rv(n_points):
        """Realised volatility over the trailing n_points 8h intervals, ending at the boundary."""
        m = n_points * MIN_PER_8H
        start = np.maximum(idx - m, 0)
        return np.sqrt(np.maximum(csum_r2[idx] - csum_r2[start], 0.0))

    def trailing_ret(n_points):
        m = n_points * MIN_PER_8H
        start = np.maximum(idx - m, 0)
        return np.log(close[idx - 1] / close[start])

    def mean_trade_size(n_points):
        m = n_points * MIN_PER_8H
        start = np.maximum(idx - m, 0)
        v = csum_v[idx] - csum_v[start]
        n = csum_n[idx] - csum_n[start]
        return np.where(n > 0, v / np.maximum(n, 1), np.nan)

    funding = {_snap(int(f["fundingTime"])): float(f["fundingRate"])
               for f in json.load(open(f"{CARRY}/funding.json"))}
    perp = {int(k[6] + 1): float(k[4]) for k in json.load(open(f"{CARRY}/perp_klines.json"))}
    spot = {int(k[6] + 1): float(k[4]) for k in json.load(open(f"{CARRY}/spot_klines.json"))}

    fr = np.array([funding.get(int(b), np.nan) for b in bounds])
    bs = np.array([(perp[int(b)] - spot[int(b)]) / spot[int(b)]
                   if int(b) in perp and int(b) in spot else np.nan for b in bounds])

    cols = {
        "t": bounds.astype(float),
        "close": close[idx - 1],
        "funding": fr,
        "basis": bs,
        "rv_1d": rv(DAY), "rv_5d": rv(5 * DAY), "rv_22d": rv(22 * DAY),
        "ret_1d": trailing_ret(DAY), "ret_7d": trailing_ret(7 * DAY),
        "ret_30d": trailing_ret(30 * DAY),
        "trade_size": mean_trade_size(DAY),
    }
    return cols


def _trailing_z(x, window):
    """
    z-score against a trailing window ENDING AT the current point, inclusive.

    A full-sample z-score would leak the future into every feature and is the classic silent
    leak in this literature -- it does not error, it just makes the accuracy too high.
    """
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(n):
        s = max(0, i - window + 1)
        w = x[s:i + 1]
        w = w[np.isfinite(w)]
        if len(w) < window // 2:
            continue
        sd = w.std()
        if sd > 0:
            out[i] = (x[i] - w.mean()) / sd
    return out


def assemble():
    c = build_rows()
    c["funding_z"] = _trailing_z(c["funding"], Z_WINDOW)
    c["basis_z"] = _trailing_z(c["basis"], Z_WINDOW)
    c["trade_size_z"] = _trailing_z(c["trade_size"], Z_WINDOW)
    return c


# ---------------------------------------------------------------------------------------
# Walk-forward
# ---------------------------------------------------------------------------------------

def label(close, h):
    """Forward log return over h decision points. NaN where the future is not in the sample."""
    y = np.full(len(close), np.nan)
    y[:-h] = np.log(close[h:] / close[:-h])
    return y


def ols_sign(Xtr, ytr, Xte):
    """OLS on the forward return; the prediction is the sign of the fitted value."""
    A = np.column_stack([np.ones(len(Xtr)), Xtr])
    beta, *_ = np.linalg.lstsq(A, ytr, rcond=None)
    B = np.column_stack([np.ones(len(Xte)), Xte])
    return B @ beta


def walk_forward(cols, feature_names, h):
    """
    Purged walk-forward with an embargo of one full horizon, both directions.

    Returns (pooled predictions, pooled truth, per-window accuracies).
    """
    X = np.column_stack([cols[f] for f in feature_names])
    y = label(cols["close"], h)
    ok = np.isfinite(X).all(axis=1) & np.isfinite(y)

    n = len(y)
    preds, truth, per_window = [], [], []
    start = 0
    while start + TRAIN + h + TEST <= n:
        tr_end = start + TRAIN
        # PURGE: a training label reaching past tr_end overlaps the test period.
        tr = np.arange(start, tr_end - h)
        # EMBARGO: the first h of the test window would overlap the training labels.
        te = np.arange(tr_end + h, min(tr_end + h + TEST, n))
        tr = tr[ok[tr]]
        te = te[ok[te]]
        if len(tr) > len(feature_names) + 10 and len(te) >= MIN_TEST_PREDICTIONS:
            p = ols_sign(X[tr], y[tr], X[te])
            acc = float(np.mean(np.sign(p) == np.sign(y[te])))
            per_window.append({"train_end_t": float(cols["t"][tr_end]),
                               "n_test": len(te), "accuracy": acc})
            preds.append(p)
            truth.append(y[te])
        start += ROLL

    if not preds:
        return None, None, []
    return np.concatenate(preds), np.concatenate(truth), per_window


def _accuracy(pred_truth):
    p, t = pred_truth
    return float(np.mean(np.sign(p) == np.sign(t)))


def cell(cols, name, feature_names, hname, h, n_boot=2000):
    pred, truth, windows = walk_forward(cols, feature_names, h)
    out = {"feature_set": name, "horizon": hname, "n_features": len(feature_names)}
    if pred is None or len(pred) == 0:
        out.update({"sufficient": False, "excluded_reason": "no usable windows"})
        return out

    hits = (np.sign(pred) == np.sign(truth)).astype(float)
    acc = float(hits.mean())
    accs = [w["accuracy"] for w in windows]
    out.update({
        "sufficient": True,
        "n_predictions": int(len(pred)),
        "n_windows": len(windows),
        "accuracy": acc,
        "bar_phi_0.50": BAR[(hname, 0.5)],
        "bar_phi_0.25": BAR[(hname, 0.25)],
        "clears_phi_0.50": acc > BAR[(hname, 0.5)],
        "clears_phi_0.25": acc > BAR[(hname, 0.25)],
        "per_window_accuracy": accs,
        "per_window_sd": float(np.std(accs)),
        "edge_over_coinflip": acc - 0.5,
        # D5 / K4: is the regime-to-regime spread larger than the effect itself?
        "regime_sd_exceeds_edge": float(np.std(accs)) > abs(acc - 0.5),
        "windows": windows,
    })
    try:
        lo, hi = ST.block_bootstrap_ci(hits, lambda a: float(np.mean(a)),
                                       n_boot=n_boot, block=h, alpha=0.05)
        out["accuracy_ci"] = [float(lo), float(hi)]
        out["ci_excludes_bar"] = bool(lo > BAR[(hname, 0.5)])
    except Exception as e:
        out["accuracy_ci"] = None
        out["ci_error"] = f"{type(e).__name__}: {e}"
    return out


def expected_best_under_zero_skill(n_trials, n_obs, n_sims=20000, seed=20260818):
    """
    Section 5. The headline will be "the best cell", so the best of 12 coin-flips at this
    sample size is computed and reported beside it. K3: a winner not exceeding this is noise.
    """
    rng = np.random.default_rng(seed)
    best = rng.binomial(n_obs, 0.5, size=(n_sims, n_trials)).max(axis=1) / n_obs
    return {"expected_best_accuracy": float(best.mean()),
            "p95_best_accuracy": float(np.quantile(best, 0.95)),
            "n_trials": n_trials, "n_obs": n_obs}


def run(n_boot=2000):
    cols = assemble()
    report = {
        "contract": CONTRACT, "contract_sha256": CONTRACT_SHA256,
        "decision_points": int(len(cols["t"])),
        "first_t": float(cols["t"][0]), "last_t": float(cols["t"][-1]),
        "grid": {"feature_sets": list(FEATURE_SETS), "horizons": list(HORIZONS),
                 "declared_trials": len(FEATURE_SETS) * len(HORIZONS)},
        "protocol": {"train": TRAIN, "test": TEST, "roll": ROLL,
                     "embargo": "one full horizon, both directions",
                     "model": "OLS on forward return; prediction is the sign of the fit"},
        "cells": {},
    }
    for hname, h in HORIZONS.items():
        for name, feats in FEATURE_SETS.items():
            report["cells"][f"{name}|{hname}"] = cell(cols, name, feats, hname, h, n_boot)

    good = [c for c in report["cells"].values() if c.get("sufficient")]
    if good:
        n_obs = int(np.median([c["n_predictions"] for c in good]))
        report["zero_skill"] = expected_best_under_zero_skill(len(good), n_obs)
        best = max(good, key=lambda c: c["accuracy"])
        report["best_cell"] = {
            "feature_set": best["feature_set"], "horizon": best["horizon"],
            "accuracy": best["accuracy"],
            "expected_best_under_zero_skill": report["zero_skill"]["expected_best_accuracy"],
            # K3
            "exceeds_zero_skill_expectation":
                best["accuracy"] > report["zero_skill"]["expected_best_accuracy"],
        }
    return report
