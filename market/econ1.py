"""
ECON-1 forward collector and evaluator.

Contract: market/CONTRACT-economics.md, frozen 2026-08-19, Amendment 1 at sha256
e65a68460ba89a99d0c771393d4b4fc14ae8419f465f7e4ac4313af3f9a4e29c.

WHAT THIS IS
    A daily job. It extends the metrics archive, re-fits the FROZEN DIR-2 specification on the
    trailing 730 days at each decision point, records the prediction, and — once a day has
    passed — the realised return and the net P&L after the full cost stack.

    It evaluates NOTHING until K1 is satisfied. `evaluate()` refuses below 270 completed
    trades, and the refusal is the whole point: a forward test that can be peeked at whenever
    it looks good is a backtest with extra steps.

WHY BACKFILL IS NOT LOOK-AHEAD
    The collector runs after the fact and computes predictions for decision points already in
    the past. That is legitimate here and would not be in general. Every feature at time t is
    built from a trailing window ENDING at t, and the model is fitted on the 730 days BEFORE t.
    Nothing at t uses information from after t. The contract's requirement is that the
    evaluation points did not exist when it was frozen -- 2026-08-20 onward -- not that the
    process runs in real time.

    The check that keeps this honest is in the tests: mutating the future must not change any
    past prediction by a single bit.

WHAT IS FROZEN AND MAY NOT BE TOUCHED
    The five features, the model form (OLS on the forward return, sign of the fit), the
    training window, the horizon, the four benchmarks, and the cost stack. `VENUE` is the one
    run-time choice the contract permits, and it is recorded in every report.
"""

import json
import os
import sys
import time
import urllib.request
import zipfile
import io
import csv
from datetime import date, datetime, timedelta, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import feemap as FM  # noqa: E402
import stats as ST  # noqa: E402

CONTRACT = "market/CONTRACT-economics.md"
CONTRACT_SHA256 = "e65a68460ba89a99d0c771393d4b4fc14ae8419f465f7e4ac4313af3f9a4e29c"

HOME = os.path.expanduser("~/genesis-evidence")
METRICS_DIR = f"{HOME}/metrics"
STATE_DIR = f"{HOME}/econ1"
OBS_PATH = f"{STATE_DIR}/observations.jsonl"

# Contract section 3.
START_MS = int(datetime(2026, 8, 20, tzinfo=timezone.utc).timestamp() * 1000)
INTERVAL_MS = 8 * 3600 * 1000
DAY = 3                                   # decision points per day
HORIZON = 1 * DAY                         # 1 day primary
TRAIN = 730 * DAY
Z_WINDOW = 30 * DAY
FEATURES = ["taker_z", "oi_z", "doi_z", "toptrader_z", "crowd_z"]

# Contract section 6, K1.
MIN_TRADES = 270

# Cost stack. Adverse selection is the MEASURED 1-day value from as-horizon.json, not an
# assumption -- see research/adverse-selection-horizon.md.
BPS = 1e-4
AS_PER_FILL = 0.1301 * BPS
VENUE = "Hyperliquid perp / Tier 0 base"          # recorded in every report
VENUE_MAKER = 0.000150
VENUE_SPREAD_CAPTURE = 0.1554 * BPS               # measured, 2026-08-19

M_URL = ("https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/"
         "BTCUSDT-metrics-{d}.zip")
K_URL = ("https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=8h"
         "&startTime={start}&limit=1000")


def round_trip_cost() -> float:
    """fees(2 fills) - spread captured + adverse selection(2 fills). Contract section 4.1."""
    return 2 * VENUE_MAKER - VENUE_SPREAD_CAPTURE + 2 * AS_PER_FILL


# ---------------------------------------------------------------------------------------
# Data refresh
# ---------------------------------------------------------------------------------------

def _get(url, timeout=90, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "genesis/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def refresh_metrics(through: date = None) -> dict:
    """Download any daily metrics files we do not already hold. Idempotent."""
    os.makedirs(METRICS_DIR, exist_ok=True)
    through = through or (datetime.now(timezone.utc).date() - timedelta(days=1))
    d = date(2026, 8, 1)
    got, missing = 0, 0
    while d <= through:
        p = f"{METRICS_DIR}/BTCUSDT-metrics-{d}.zip"
        if not (os.path.exists(p) and os.path.getsize(p) > 0):
            try:
                with open(p, "wb") as f:
                    f.write(_get(M_URL.format(d=d)))
                got += 1
            except Exception:
                if os.path.exists(p):
                    os.remove(p)
                missing += 1
        d += timedelta(days=1)
    return {"downloaded": got, "unavailable": missing, "through": str(through)}


def load_metrics() -> dict:
    """
    Every metrics row we hold, keyed by 5-minute timestamp. Empty fields are NaN and are never
    interpolated -- the same rule CARRY-1 applies to a missing price leg.
    """
    import glob
    fields = ["sum_open_interest", "sum_open_interest_value",
              "count_toptrader_long_short_ratio", "sum_toptrader_long_short_ratio",
              "count_long_short_ratio", "sum_taker_long_short_vol_ratio"]
    rows = []
    for f in sorted(glob.glob(f"{METRICS_DIR}/*.zip")):
        try:
            with zipfile.ZipFile(f) as z:
                txt = z.read(z.namelist()[0]).decode()
        except Exception:
            continue
        for r in csv.DictReader(io.StringIO(txt)):
            v = []
            for k in fields:
                s = (r.get(k) or "").strip().strip('"')
                v.append(float(s) if s else np.nan)
            ts = datetime.fromisoformat(r["create_time"]).replace(tzinfo=timezone.utc)
            rows.append((int(ts.timestamp() * 1000), *v))
    rows.sort(key=lambda x: x[0])
    return {"ts": np.array([r[0] for r in rows], dtype=float),
            "arr": np.array([r[1:] for r in rows], dtype=float)}


def load_klines(start_ms: int) -> dict:
    """8-hourly perp closes, keyed on the boundary the candle CLOSES on."""
    out, t = {}, start_ms
    while True:
        batch = json.loads(_get(K_URL.format(start=int(t))))
        if not batch:
            break
        for k in batch:
            out[int(k[6]) + 1] = float(k[4])
        if len(batch) < 1000:
            break
        t = batch[-1][0] + 1
    return out


# ---------------------------------------------------------------------------------------
# Features -- identical to DIR-2, and frozen
# ---------------------------------------------------------------------------------------

def _trailing_z(x, window):
    """z against a trailing window ENDING at the point. Never full-sample."""
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(n):
        w = x[max(0, i - window + 1):i + 1]
        w = w[np.isfinite(w)]
        if len(w) < window // 2:
            continue
        sd = w.std()
        if sd > 0:
            out[i] = (x[i] - w.mean()) / sd
    return out


def build_grid(metrics: dict, closes: dict) -> dict:
    """One row per 8h boundary carrying only what was observable at it."""
    if len(metrics["ts"]) == 0:
        return {"t": np.array([])}
    lo = int(metrics["ts"][0] // INTERVAL_MS + 1) * INTERVAL_MS
    hi = int(metrics["ts"][-1] // INTERVAL_MS) * INTERVAL_MS
    bounds = np.arange(lo, hi + 1, INTERVAL_MS, dtype=float)

    # Last metrics row at or BEFORE the boundary. One row forward would be a look-ahead.
    idx = np.searchsorted(metrics["ts"], bounds, side="right") - 1
    ok = idx >= 0
    idx = np.clip(idx, 0, len(metrics["ts"]) - 1)
    stale = (bounds - metrics["ts"][idx]) > INTERVAL_MS
    bad = (~ok) | stale

    def take(col):
        v = metrics["arr"][idx, col].astype(float)
        v[bad] = np.nan
        return v

    oi = take(0)
    doi = np.full(len(oi), np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        # D-D2: a handful of rows report zero open interest, which is a venue artefact and not
        # a market state. Excluded here rather than left for a downstream isfinite() to catch.
        prev, cur = oi[:-DAY], oi[DAY:]
        good = (prev > 0) & (cur > 0)
        r = np.full(len(cur), np.nan)
        r[good] = np.log(cur[good] / prev[good])
        doi[DAY:] = r

    cols = {
        "t": bounds,
        "close": np.array([closes.get(int(b), np.nan) for b in bounds]),
        "taker_z": _trailing_z(take(5), Z_WINDOW),
        "oi_z": _trailing_z(oi, Z_WINDOW),
        "doi_z": _trailing_z(doi, Z_WINDOW),
        "toptrader_z": _trailing_z(take(3), Z_WINDOW),
        "crowd_z": _trailing_z(take(4), Z_WINDOW),
    }
    return cols


def label(close, h):
    y = np.full(len(close), np.nan)
    y[:-h] = np.log(close[h:] / close[:-h])
    return y


def predict_at(cols, i, h=HORIZON):
    """
    The frozen specification, evaluated at index i using only data strictly before it.

    Training labels reach `h` forward, so the training set stops at i-h: a sample whose label
    extends past the decision point would be using the future to predict it.
    """
    X = np.column_stack([cols[f] for f in FEATURES])
    y = label(cols["close"], h)
    lo = max(0, i - TRAIN)
    tr = np.arange(lo, i - h)
    tr = tr[np.isfinite(X[tr]).all(axis=1) & np.isfinite(y[tr])]
    if len(tr) < len(FEATURES) + 10 or not np.isfinite(X[i]).all():
        return None
    A = np.column_stack([np.ones(len(tr)), X[tr]])
    beta, *_ = np.linalg.lstsq(A, y[tr], rcond=None)
    return float(np.concatenate([[1.0], X[i]]) @ beta)


# ---------------------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------------------

def collect(refresh=True) -> dict:
    """Append every decision point at or after START_MS whose outcome is now known."""
    os.makedirs(STATE_DIR, exist_ok=True)
    info = refresh_metrics() if refresh else {"downloaded": 0, "unavailable": 0}
    metrics = load_metrics()
    closes = load_klines(START_MS - TRAIN * INTERVAL_MS)
    cols = build_grid(metrics, closes)
    y = label(cols["close"], HORIZON)

    have = set()
    if os.path.exists(OBS_PATH):
        for line in open(OBS_PATH):
            have.add(json.loads(line)["t"])

    added = 0
    with open(OBS_PATH, "a") as f:
        for i, t in enumerate(cols["t"]):
            if t < START_MS or t in have or not np.isfinite(y[i]):
                continue
            p = predict_at(cols, i)
            if p is None:
                continue
            row = {"t": float(t), "fit": p, "side": int(np.sign(p)),
                   "forward_return": float(y[i]), "close": float(cols["close"][i]),
                   "features": {k: float(cols[k][i]) for k in FEATURES},
                   "recorded_at": datetime.now(timezone.utc).isoformat()}
            f.write(json.dumps(row) + "\n")
            added += 1
    return {"appended": added, "total": len(have) + added, **info}


def observations() -> list:
    if not os.path.exists(OBS_PATH):
        return []
    return [json.loads(l) for l in open(OBS_PATH)]


# ---------------------------------------------------------------------------------------
# Evaluation -- gated by K1
# ---------------------------------------------------------------------------------------

def evaluate(n_boot=2000, n_perm=10000, seed=20260820) -> dict:
    """
    The four declared benchmarks, the controls, and the declared decomposition.

    K1: refuses below MIN_TRADES. The refusal is not a formality. A forward test that can be
    read whenever it looks encouraging is a backtest with extra steps, and the discipline is
    the only thing separating ECON-1 from the exploratory numbers it exists to replace.
    """
    obs = observations()
    n = len(obs)
    base = {"contract": CONTRACT, "contract_sha256": CONTRACT_SHA256, "venue": VENUE,
            "round_trip_cost_bps": round_trip_cost() / BPS,
            "adverse_selection_per_fill_bps": AS_PER_FILL / BPS,
            "n_trades": n, "min_trades": MIN_TRADES}
    if n < MIN_TRADES:
        base.update({"readable": False,
                     "reason": f"K1: {n} of {MIN_TRADES} completed trades. No result may be "
                               f"quoted, including a partial one."})
        return base

    side = np.array([o["side"] for o in obs], dtype=float)
    ret = np.array([o["forward_return"] for o in obs])
    cost = round_trip_cost()
    net = side * ret - cost
    exposure = float(side.mean())
    rng = np.random.default_rng(seed)

    # B2 -- buy and hold, one entry and exit over the whole period.
    bh = float(ret.mean() - cost / n)
    # B4 -- a constant position at the strategy's own net exposure, same cost treatment.
    b4 = float(exposure * ret.mean() - cost / n)
    # B3 -- permute the signs. Preserves the long/short counts exactly, destroys the timing.
    perm = np.array([(rng.permutation(side) * ret).mean() - cost for _ in range(n_perm)])

    out = dict(base)
    out.update({
        "readable": True,
        "net_mean_bps": float(net.mean()) / BPS,
        "net_median_bps": float(np.median(net)) / BPS,
        "net_sd_bps": float(net.std()) / BPS,
        "per_trade_sharpe": float(net.mean() / net.std()) if net.std() > 0 else None,
        "worst_bps": float(net.min()) / BPS,
        "deciles_bps": [float(q) / BPS for q in np.quantile(net, np.arange(0.1, 1.0, 0.1))],
        "B1_positive": bool(net.mean() > 0),
        "B2_buy_and_hold_bps": bh / BPS,
        "B2_cleared": bool(net.mean() > bh),
        "B3_perm_p95_bps": float(np.quantile(perm, 0.95)) / BPS,
        "B3_cleared": bool(net.mean() > np.quantile(perm, 0.95)),
        "B4_exposure_matched_bps": b4 / BPS,
        "B4_cleared": bool(net.mean() > b4),
        "net_exposure": exposure,
        "long_fraction": float((side > 0).mean()),
        "directionally_biased": bool(not 0.40 <= (side > 0).mean() <= 0.60),
        "de_drifted_bps": float((side * (ret - ret.mean())).mean()) / BPS,
    })
    out["all_benchmarks_cleared"] = bool(out["B1_positive"] and out["B2_cleared"]
                                         and out["B3_cleared"] and out["B4_cleared"])
    try:
        lo, hi = ST.block_bootstrap_ci(net, lambda a: float(np.mean(a)),
                                       n_boot=n_boot, block=HORIZON, alpha=0.05)
        out["net_mean_ci_bps"] = [lo / BPS, hi / BPS]
    except Exception as e:
        out["net_mean_ci_bps"] = None
        out["ci_error"] = f"{type(e).__name__}: {e}"

    # Section 4.5 / F6 -- does the magnitude asymmetry persist forward?
    hit = np.sign(side) == np.sign(ret)
    if hit.any() and (~hit).any():
        w, l = np.abs(ret[hit]).mean(), np.abs(ret[~hit]).mean()
        out["F6_magnitude"] = {"mean_abs_right_bps": w / BPS, "mean_abs_wrong_bps": l / BPS,
                               "ratio": float(w / l), "holds": bool(w / l > 1.05)}

    # Section 4.4 -- declared forward decomposition. DESCRIPTION ONLY. No cell may be selected
    # on and no benchmark may be evaluated within a cell.
    def by_quintile(key, label_):
        q = np.quantile(key, [0.2, 0.4, 0.6, 0.8])
        b = np.digitize(key, q)
        return {f"{label_}_q{i+1}": {"n": int((b == i).sum()),
                                     "net_bps": float(net[b == i].mean()) / BPS}
                for i in range(5) if (b == i).any()}

    out["decomposition"] = {
        **by_quintile(np.abs(ret), "magnitude"),
        **by_quintile(np.abs(np.diff(np.concatenate([[ret[0]], ret]))), "volatility"),
        "long": {"n": int((side > 0).sum()),
                 "net_bps": float(net[side > 0].mean()) / BPS} if (side > 0).any() else None,
        "short": {"n": int((side < 0).sum()),
                  "net_bps": float(net[side < 0].mean()) / BPS} if (side < 0).any() else None,
        "note": "description only; no cell may be selected on (contract section 4.4)",
    }

    # Declared reporting dimension, not a search dimension (contract section 4.3).
    dow = np.array([datetime.fromtimestamp(o["t"] / 1000, timezone.utc).weekday() for o in obs])
    out["by_day_of_week_bps"] = {int(d): float(net[dow == d].mean()) / BPS
                                 for d in range(7) if (dow == d).any()}
    return out
