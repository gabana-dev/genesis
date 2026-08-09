"""
Steps 9-11: rolling-origin evaluation, holdout protection, metrics and calibration.

This is the durable artifact of RDB-1. It is deliberately target-agnostic: pointing it at
AEMO RRP instead of TOTALDEMAND requires changing a column name, not the harness.

Evaluation protocol (frozen by contract):
  * origins step daily; each origin forecasts the next 48 half-hourly intervals (24h);
  * every forecast uses only observations at or before its origin;
  * expanding-window vs rolling-window training is the adaptation test;
  * the holdout period is unreachable unless the design-freeze marker exists.
"""

import numpy as np
import pandas as pd

from config import FREQ, HORIZON, STEPS_PER_DAY, STEPS_PER_WEEK


def origins(index, first_origin, last_origin, step_hours=24):
    """Daily forecast origins, each at the same clock time, inside the available index."""
    step = pd.Timedelta(hours=step_hours)
    out = []
    t = pd.Timestamp(first_origin)
    last = pd.Timestamp(last_origin)
    idx = pd.DatetimeIndex(index)
    while t <= last:
        if t in idx:
            pos = idx.get_loc(t)
            if pos + HORIZON < len(idx):
                out.append(t)
        t += step
    return out


def training_slice(series, origin, mode, rolling_weeks):
    """
    Data visible at the origin. Interval-ending stamps mean the observation labelled
    `origin` covers the period ENDING at the origin, so it is observed and included.
    """
    hist = series.loc[:origin]
    if mode == "expanding":
        return hist
    if mode == "rolling":
        return hist.iloc[-rolling_weeks * STEPS_PER_WEEK:]
    raise ValueError(mode)


def actuals(series, origin):
    idx = pd.DatetimeIndex(series.index)
    pos = idx.get_loc(origin)
    return series.iloc[pos + 1: pos + 1 + HORIZON]


# ---- metrics -------------------------------------------------------------------------

def mae(y, f):
    return float(np.mean(np.abs(np.asarray(y) - np.asarray(f))))


def rmse(y, f):
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(f)) ** 2)))


def skill(score, reference):
    """Positive means better than the reference; 0 means identical."""
    return float(1.0 - score / reference) if reference else float("nan")


def coverage(y, lower, upper):
    y = np.asarray(y)
    return float(np.mean((y >= np.asarray(lower)) & (y <= np.asarray(upper))))


def crps_gaussian(y, mu, sigma):
    """
    Closed-form CRPS for a Gaussian predictive distribution (Gneiting & Raftery 2007).
    A proper scoring rule -- it rewards calibration as well as sharpness, which is what
    anything downstream of a decision actually consumes.
    """
    from scipy.stats import norm
    y, mu, sigma = np.asarray(y, float), np.asarray(mu, float), np.asarray(sigma, float)
    sigma = np.maximum(sigma, 1e-9)
    z = (y - mu) / sigma
    return float(np.mean(sigma * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi))))


# ---- evaluation ----------------------------------------------------------------------

def evaluate(series, forecaster, origin_list, **kwargs):
    """
    Run a forecaster over origins and collect per-origin records.

    `forecaster(history, future_index, **kwargs)` returns either point forecasts, or
    (point, sigma) when it supplies predictive uncertainty.
    """
    rows = []
    for origin in origin_list:
        y = actuals(series, origin)
        hist = series.loc[:origin]
        out = forecaster(hist, y.index, **kwargs)
        sigma = None
        if isinstance(out, tuple):
            out, sigma = out
        rec = {
            "origin": origin,
            "mae": mae(y, out),
            "rmse": rmse(y, out),
            "n": len(y),
        }
        if sigma is not None:
            for level, z in ((50, 0.674), (80, 1.282), (95, 1.960)):
                rec[f"cov{level}"] = coverage(y, out - z * sigma, out + z * sigma)
            rec["crps"] = crps_gaussian(y, out, sigma)
        rows.append(rec)
    return pd.DataFrame(rows).set_index("origin")


def summarise(results, reference=None):
    """Headline metrics plus the per-year and per-season stability breakdowns."""
    out = {
        "origins": len(results),
        "mae": results["mae"].mean(),
        "rmse": results["rmse"].mean(),
    }
    if reference is not None:
        out["mae_skill_vs_ref"] = skill(results["mae"].mean(), reference["mae"].mean())
        out["rmse_skill_vs_ref"] = skill(results["rmse"].mean(), reference["rmse"].mean())
    for col in ("cov50", "cov80", "cov95", "crps"):
        if col in results:
            out[col] = results[col].mean()
    return out


def by_year(results):
    return results.groupby(results.index.year)[["mae", "rmse"]].mean()


def by_season(results):
    """Australian seasons; summer peaks are the operationally hard case."""
    season = results.index.month.map(
        {12: "summer", 1: "summer", 2: "summer", 3: "autumn", 4: "autumn", 5: "autumn",
         6: "winter", 7: "winter", 8: "winter", 9: "spring", 10: "spring", 11: "spring"}
    )
    return results.groupby(season)[["mae", "rmse"]].mean()
