"""
GEN-1: the DIR-2 specification, unchanged, run against five assets it has never seen.

Contract: market/CONTRACT-generalisation.md, frozen 2026-08-19 at sha256
ee3f7e08535c02eba5aa24d2174c9a4f3b02f4806d7ab3f64c2dcd6a76fb72a9, before any non-BTC metrics
file had been read.

WHAT IS AND IS NOT ALLOWED TO VARY
    Features, model form, training window, horizons, embargo and purge are copied from DIR-2
    and are identical across all five assets. K5 voids the run if any of them is changed per
    asset. What DOES vary, necessarily, is the BAR: each asset is judged against its own
    break-even, computed from its own measured median move, because a fixed cost against a
    larger move is a lower bar. Using BTC's bar everywhere would be the mistake this contract
    exists to correct.

WHY IT IS EXPECTED TO FAIL
    Pindza (2026) found no cross-asset transfer in crypto microstructure models, and Genesis's
    own cross-section holon measured effective breadth 1.03 across 25 instruments. GEN-1 is run
    anyway because a declared expectation is not a measurement, and because the asymmetry
    favours running it: failure on all five makes ECON-1's November read close to decided in
    advance, and that is worth knowing in August.
"""

import csv
import glob
import io
import json
import os
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import dir1 as D1  # noqa: E402
import dir2 as D2  # noqa: E402
import econ1 as E1  # noqa: E402
import stats as ST  # noqa: E402

CONTRACT = "market/CONTRACT-generalisation.md"
CONTRACT_SHA256 = "ee3f7e08535c02eba5aa24d2174c9a4f3b02f4806d7ab3f64c2dcd6a76fb72a9"

SYMBOLS = ("ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
METRICS_ROOT = os.path.expanduser("~/genesis-evidence/metrics-multi")
BPS = 1e-4
PHI = 0.5
MIN_PREDICTIONS = 500                      # K1
COVERAGE_DEGRADED = 0.50                   # section 8
DECLARED_TRIALS = len(SYMBOLS) * len(D1.HORIZONS)

# Shared cost stack, section 8: both terms were measured on BTC, so per-asset bars are
# approximate and an asset clearing narrowly has not clearly cleared anything.
COST_NETTED = 0.348 * BPS

FIELDS = ["sum_open_interest", "sum_open_interest_value",
          "count_toptrader_long_short_ratio", "sum_toptrader_long_short_ratio",
          "count_long_short_ratio", "sum_taker_long_short_vol_ratio"]


def load_metrics(symbol):
    """
    Every metrics row held for a symbol. Empty fields are NaN and never interpolated.

    TIMESTAMPS ARE IN MILLISECONDS, matching `econ1.build_grid`, which is the grid builder used
    below. This is the boundary the 2026-08-19 assessment flagged as a latent trap: `dir2`
    represents the same quantity in SECONDS and multiplies by 1000, `econ1` uses milliseconds
    directly, and nothing marked the seam. A first draft of this module returned seconds and
    handed them to a millisecond consumer. The trap was named in the morning and sprung the
    same hour, which is the argument for marking it here rather than remembering it.
    """
    rows, files, unreadable = [], 0, 0
    for f in sorted(glob.glob(f"{METRICS_ROOT}/{symbol}/*.zip")):
        files += 1
        try:
            with zipfile.ZipFile(f) as z:
                txt = z.read(z.namelist()[0]).decode()
        except Exception:
            unreadable += 1
            continue
        for r in csv.DictReader(io.StringIO(txt)):
            v = []
            for k in FIELDS:
                s = (r.get(k) or "").strip().strip('"')
                v.append(float(s) if s else np.nan)
            ts = datetime.fromisoformat(r["create_time"]).replace(tzinfo=timezone.utc)
            rows.append((ts.timestamp() * 1000.0, *v))   # MILLISECONDS -- see docstring
    rows.sort(key=lambda x: x[0])
    if not rows:
        return None
    a = np.array(rows, dtype=float)
    return {"ts": a[:, 0], "arr": a[:, 1:], "files": files, "unreadable": unreadable}


def load_klines(symbol):
    """8-hourly closes, keyed on the boundary the candle closes on."""
    url = ("https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=8h"
           "&startTime={t}&limit=1000")
    out, t = {}, int(datetime(2020, 8, 1, tzinfo=timezone.utc).timestamp() * 1000)
    while True:
        for attempt in range(4):
            try:
                raw = urllib.request.urlopen(url.format(s=symbol, t=t), timeout=90).read()
                batch = json.loads(raw)
                break
            except Exception:
                if attempt == 3:
                    return out
                time.sleep(2 * (attempt + 1))
        if not batch:
            break
        for k in batch:
            out[int(k[6]) + 1] = float(k[4])
        if len(batch) < 1000:
            break
        t = batch[-1][0] + 1
        time.sleep(0.2)
    return out


def median_abs_move(closes, h):
    """The asset's own median absolute move over the horizon -- the bar's denominator."""
    ks = sorted(closes)
    c = np.array([closes[k] for k in ks], dtype=float)
    if len(c) <= h:
        return None
    r = np.abs(np.log(c[h:] / c[:-h]))
    r = r[np.isfinite(r)]
    return float(np.median(r)) if r.size else None


def bar_for(move, cost=COST_NETTED, phi=PHI):
    return 0.5 + cost / (2 * phi * move)


def assemble(symbol):
    """DIR-2's grid construction, for an arbitrary symbol."""
    m = load_metrics(symbol)
    if m is None:
        return None, None
    closes = load_klines(symbol)
    if not closes:
        return None, None
    # build_grid already computes every declared feature, including the trailing z-scores.
    # An earlier draft recomputed taker_z here; it was dead code and is removed rather than
    # left to look load-bearing.
    cols = E1.build_grid({"ts": m["ts"], "arr": m["arr"]}, closes)
    return cols, {"metrics_files": m["files"], "unreadable": m["unreadable"],
                  "metrics_rows": int(len(m["ts"])), "klines": len(closes),
                  "closes": closes}


def cell(cols, symbol, hname, h, closes, n_boot=2000):
    mask = np.ones(len(cols["t"]), dtype=bool)
    pred, truth, windows = D2.walk_forward_gated(cols, D2.FEATURES, h, mask)
    out = {"symbol": symbol, "horizon": hname}
    if pred is None or len(pred) < MIN_PREDICTIONS:
        out.update({"sufficient": False,
                    "n_predictions": 0 if pred is None else int(len(pred)),
                    "excluded_reason": f"K1: fewer than {MIN_PREDICTIONS} predictions"})
        return out

    move = median_abs_move(closes, h)
    bar = bar_for(move) if move else None
    hits = (np.sign(pred) == np.sign(truth)).astype(float)
    acc = float(hits.mean())
    accs = [w["accuracy"] for w in windows]
    side = np.sign(pred)
    out.update({
        "sufficient": True,
        "n_predictions": int(len(pred)), "n_windows": len(windows),
        "accuracy": acc,
        "median_abs_move_bps": (move / BPS) if move else None,
        "own_bar": bar,
        "clears_own_bar": bool(bar is not None and acc > bar),
        "long_fraction": float((side > 0).mean()),
        "net_exposure": float(side.mean()),
        "per_window_sd": float(np.std(accs)),
        "regime_sd_exceeds_edge": float(np.std(accs)) > abs(acc - 0.5),      # K4
        "per_window_accuracy": accs,
    })
    try:
        lo, hi = ST.block_bootstrap_ci(hits, lambda a: float(np.mean(a)),
                                       n_boot=n_boot, block=h, alpha=0.05)
        out["accuracy_ci"] = [float(lo), float(hi)]
        out["ci_excludes_bar"] = bool(bar is not None and lo > bar)
    except Exception as e:
        out["accuracy_ci"] = None
        out["ci_error"] = f"{type(e).__name__}: {e}"
    return out


def null_p95_best(n_trials, n_obs, n_sims=20000, seed=20260819):
    """K3, in DIR-2's corrected form: the p95 of the null maximum, never its mean."""
    rng = np.random.default_rng(seed)
    best = rng.binomial(n_obs, 0.5, size=(n_sims, n_trials)).max(axis=1) / n_obs
    return {"mean_best": float(best.mean()), "p95_best": float(np.quantile(best, 0.95)),
            "n_trials": n_trials, "n_obs": n_obs}


def run(n_boot=2000):
    report = {"contract": CONTRACT, "contract_sha256": CONTRACT_SHA256,
              "symbols": list(SYMBOLS), "features": D2.FEATURES,
              "cost_stack_bps": COST_NETTED / BPS,
              "declared_trials": DECLARED_TRIALS, "cells": {}, "data": {}}

    for sym in SYMBOLS:
        cols, meta = assemble(sym)
        if cols is None:
            report["data"][sym] = {"error": "no metrics or klines"}
            continue
        closes = meta.pop("closes")
        finite = {f: float(np.isfinite(cols[f]).mean()) for f in D2.FEATURES}
        meta["feature_coverage"] = finite
        meta["degraded"] = bool(min(finite.values()) < COVERAGE_DEGRADED)
        report["data"][sym] = meta
        for hname, h in D1.HORIZONS.items():
            report["cells"][f"{sym}|{hname}"] = cell(cols, sym, hname, h, closes, n_boot)

    good = [c for c in report["cells"].values() if c.get("sufficient")]
    if good:
        n_obs = int(np.median([c["n_predictions"] for c in good]))
        null = null_p95_best(len(good), n_obs)
        best = max(good, key=lambda c: c["accuracy"])
        report["zero_skill"] = null
        report["best_cell"] = {
            "symbol": best["symbol"], "horizon": best["horizon"],
            "accuracy": best["accuracy"], "null_p95": null["p95_best"],
            "exceeds_null_p95": best["accuracy"] > null["p95_best"],
        }
        report["K2_none_clear"] = not any(c["clears_own_bar"] for c in good)
    return report
