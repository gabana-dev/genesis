"""
How many INDEPENDENT bets does the crypto perp cross-section actually contain?

WHY THIS QUESTION, AND WHY NOW
    MEASURE-1 §8 established a hard boundary: settling the daily horizon by time series on
    BTCUSDT alone would need 68 years of history from a seven-year-old instrument. Not a
    backlog -- a limit of the same kind as the 291 ms latency floor. The corrected finding
    names the escape: evidence "of a different kind -- conditional, cross-sectional or
    event-based".

    The cross-sectional route is the one with an arithmetic precondition, and it is cheap to
    check. Power grows with sqrt(n), and a cross-section multiplies n by the number of
    instruments ONLY to the extent those instruments are independent. Grinold's fundamental
    law states it directly: IR ~ IC * sqrt(BR), where BR counts independent bets, not tickers.

    Crypto is widely observed to trade as a single risk asset. If that is true here, thirty
    perps may carry the statistical weight of two or three, and the cross-sectional escape is
    narrower than it looks. Better to learn that from arithmetic, before committing.

WHAT THIS IS NOT
    Not a trial. No hypothesis is tested and nothing is accepted or rejected -- this is a
    descriptive measurement of the environment, recorded as CONTEXT under the ledger's own
    definition. Nothing here is part of EXEC-1, which is frozen.

    It selects no instrument, proposes no strategy, and says nothing about whether any signal
    exists. It measures how much room there would be if one did.

TWO MEASURES, BECAUSE THE SIMPLE ONE FLATTERS
    1. Average pairwise correlation, and the textbook effective breadth
           BR_eff = k / (1 + (k-1) * rho_bar)
       Simple, standard, and assumes every pair shares the same correlation -- which is false
       whenever a few instruments move together more tightly than the rest.

    2. The participation ratio of the correlation eigenvalue spectrum
           N_eff = (sum lambda_i)^2 / sum(lambda_i^2)
       The effective dimensionality of the system, making no equicorrelation assumption. This
       is the honest number when the correlation structure is uneven.

    Reported together. Where they disagree, the second one is the one to believe, and the
    disagreement itself says the cross-section is not uniform.

DATA
    Binance USD-M perpetual futures monthly kline archives -- the same bulk mirror data.py
    uses for spot, under the futures path. 4h bars, because 4h is where MEASURE-1 located the
    affordability floor and a correlation measured at 1m would answer a different question.
"""

from __future__ import annotations

import io
import os
import urllib.error
import urllib.request
import zipfile
from datetime import date

import numpy as np

import data as D

# The futures (USD-M perpetual) mirror of the archive data.py reads for spot. Perps, not spot,
# because perps are what would actually be traded and what the question was asked about.
FUTURES_BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
CACHE = os.path.expanduser("~/genesis-evidence/market-data/futures")

# 4h, because MEASURE-1 put the affordability floor at 4h. Correlation is horizon-dependent:
# instruments that look distinct minute to minute routinely move as one over hours, and the
# minute-scale number would answer a question nobody asked.
INTERVAL = "4h"


def month(symbol: str, y: int, m: int, interval: str = INTERVAL):
    """One month of perp klines, cached. None when the month was never published."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{symbol}-{interval}-{y}-{m:02d}.npy")
    if os.path.exists(path):
        return np.load(path)

    url = f"{FUTURES_BASE}/{symbol}/{interval}/{symbol}-{interval}-{y}-{m:02d}.zip"
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            blob = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        rows = D._parse(z.read(z.namelist()[0]))
    np.save(path, rows)
    return rows


def series(symbol: str, start: date, end: date, interval: str = INTERVAL):
    """Closes and open times for one symbol over the window, or None if never published."""
    chunks = [c for c in (month(symbol, y, m, interval) for y, m in D._months(start, end))
              if c is not None and len(c)]
    if not chunks:
        return None
    rows = np.vstack(chunks)
    rows = rows[np.argsort(rows[:, 0])]
    # A duplicated bar at a month boundary would enter the return series twice and bias its
    # autocorrelation. Keep the first occurrence of each open_time.
    _, keep = np.unique(rows[:, 0], return_index=True)
    return rows[np.sort(keep)]


def aligned_returns(symbols, start: date, end: date, interval: str = INTERVAL):
    """
    Log returns on the intersection of timestamps present for EVERY symbol.

    Intersection, not union-with-fill. Forward-filling a missing bar inserts a zero return,
    which drags every correlation involving that symbol toward zero and would make the
    cross-section look more independent than it is -- flattering the exact quantity being
    measured. Symbols with no data are dropped and named.
    """
    got, missing = {}, []
    for s in symbols:
        rows = series(s, start, end, interval)
        if rows is None or len(rows) < 50:
            missing.append(s)
            continue
        got[s] = rows

    if len(got) < 2:
        return [], np.empty((0, 0)), missing

    common = None
    for rows in got.values():
        ts = set(rows[:, 0].astype(np.int64))
        common = ts if common is None else (common & ts)
    common = np.array(sorted(common), dtype=np.int64)
    if len(common) < 50:
        return [], np.empty((0, 0)), missing

    names, cols = [], []
    for s, rows in sorted(got.items()):
        idx = {int(t): i for i, t in enumerate(rows[:, 0].astype(np.int64))}
        closes = np.array([rows[idx[t], 4] for t in common], dtype=np.float64)
        if np.any(closes <= 0):
            missing.append(s)
            continue
        names.append(s)
        cols.append(np.diff(np.log(closes)))

    return names, np.column_stack(cols) if cols else np.empty((0, 0)), missing


def effective_breadth(corr: np.ndarray) -> dict:
    """
    Two readings of the same matrix. See the module docstring for why both.

    The eigenvalue participation ratio is the one to trust when they disagree: the
    equicorrelation formula assumes a structure that a real cross-section rarely has.
    """
    k = corr.shape[0]
    off = corr[~np.eye(k, dtype=bool)]
    rho_bar = float(off.mean())

    # Guard the pathological case rather than emitting a negative or exploded breadth: with
    # rho_bar <= -1/(k-1) the equicorrelation matrix is not positive semi-definite and the
    # formula has no meaning.
    denom = 1.0 + (k - 1) * rho_bar
    br_equi = float(k / denom) if denom > 1e-9 else float("inf")

    lam = np.linalg.eigvalsh(corr)
    lam = np.clip(lam, 0.0, None)
    n_eff = float((lam.sum() ** 2) / (lam ** 2).sum())

    return {
        "k_instruments": k,
        "rho_mean": rho_bar,
        "rho_median": float(np.median(off)),
        "rho_min": float(off.min()),
        "rho_max": float(off.max()),
        "breadth_equicorrelation": br_equi,
        "breadth_participation_ratio": n_eff,
        "pc1_variance_share": float(lam.max() / lam.sum()),
        "pc1_plus_pc2_share": float(np.sort(lam)[-2:].sum() / lam.sum()),
    }


def measure(symbols, start: date, end: date, interval: str = INTERVAL) -> dict:
    names, rets, missing = aligned_returns(symbols, start, end, interval)
    if rets.size == 0 or len(names) < 2:
        return {"error": "not enough aligned data", "missing": missing}

    corr = np.corrcoef(rets, rowvar=False)
    out = effective_breadth(corr)
    out.update({
        "symbols": names,
        "unavailable": missing,
        "interval": interval,
        "n_bars": int(rets.shape[0]),
        "window": f"{start.isoformat()}..{end.isoformat()}",
        "source": FUTURES_BASE,
    })
    return out, corr, names
