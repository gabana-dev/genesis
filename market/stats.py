"""
Statistical machinery for MEASURE-1. All methods are established and cited.

Nothing here is a Genesis invention. The moving-block bootstrap exists because financial
returns are serially dependent and heteroskedastic, so an IID bootstrap would understate every
interval reported (CONTRACT-measurement.md section 8).

References
    Lo, A. & MacKinlay, A.C. (1988). Stock market prices do not follow random walks.
        Review of Financial Studies 1(1), 41-66.
    Roll, R. (1984). A simple implicit measure of the effective bid-ask spread.
        Journal of Finance 39(4), 1127-1139.
    Andersen, T., Bollerslev, T., Diebold, F. & Labys, P. (2000). Great realizations.
        Risk 13, 105-108.  [realized-volatility signature plot]
    Amihud, Y. (2002). Illiquidity and stock returns. Journal of Financial Markets 5(1), 31-56.
    Politis, D. & Romano, J. (1994). The stationary bootstrap. JASA 89(428), 1303-1313.
"""

import numpy as np


def block_bootstrap_ci(x, stat, n_boot=2000, block=None, alpha=0.05, seed=20260810):
    """
    Moving-block bootstrap interval (Kunsch 1989; Politis & Romano 1994).

    Block length defaults to n^(1/3), the standard rule for a dependent series. The block is
    what preserves serial dependence; drawing individual observations would treat returns as
    IID and produce intervals that are too narrow.
    """
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n < 8:
        return (float("nan"), float("nan"))
    L = block or max(2, int(round(n ** (1 / 3))))
    n_blocks = int(np.ceil(n / L))
    rng = np.random.default_rng(seed)
    off = np.arange(L)
    # One resample at a time. Building all n_boot index rows at once would allocate an
    # (n_boot x n) matrix -- 16GB for 500 x 4M -- which is why this is a loop, not a broadcast.
    vals = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        starts = rng.integers(0, n - L + 1, size=n_blocks)
        idx = (starts[:, None] + off[None, :]).ravel()[:n]
        vals[i] = stat(x[idx])
    lo, hi = np.nanpercentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def variance_ratio(r, q):
    """
    Lo-MacKinlay variance ratio at aggregation q, with the heteroskedasticity-robust
    statistic z2. VR = Var(q-period return) / (q * Var(1-period return)).

    VR = 1  -> the series is a random walk at this horizon (no linear predictability)
    VR > 1  -> positive autocorrelation, trending
    VR < 1  -> negative autocorrelation, mean-reverting -- OR bid-ask bounce, which is why
               the Roll estimate below must be checked before any such result is believed.

    Returns (vr, z2, p_two_sided). z2 is robust to heteroskedasticity, which returns
    unambiguously have; the homoskedastic z1 would reject far too often here.
    """
    r = np.asarray(r, dtype=np.float64)
    n = len(r)
    if n < 4 * q:
        return float("nan"), float("nan"), float("nan")
    mu = r.mean()
    va = np.sum((r - mu) ** 2) / (n - 1)

    # overlapping q-period returns
    c = np.cumsum(np.insert(r, 0, 0.0))
    rq = c[q:] - c[:-q]
    m = q * (n - q + 1) * (1 - q / n)
    vb = np.sum((rq - q * mu) ** 2) / m
    vr = vb / va

    d = (r - mu) ** 2
    theta = 0.0
    for j in range(1, q):
        # delta_j = sum[(r_t-mu)^2 (r_{t-j}-mu)^2] / [sum (r_t-mu)^2]^2.
        # The 1/n scaling is already implicit -- numerator ~ n, denominator ~ n^2 -- so an
        # explicit factor of n here makes theta n times too large and z smaller by sqrt(n).
        # That bug let a series with VR = 0.38 (theoretical 0.31) go unrejected at p = 0.86.
        num = np.sum(d[j:] * d[:-j])
        den = np.sum(d) ** 2
        delta = num / den
        theta += ((2 * (q - j) / q) ** 2) * delta
    z2 = (vr - 1) / np.sqrt(theta) if theta > 0 else float("nan")
    from math import erfc, sqrt
    p = erfc(abs(z2) / sqrt(2)) if np.isfinite(z2) else float("nan")
    return float(vr), float(z2), float(p)


def roll_spread(prices):
    """
    Roll (1984) effective spread: s = 2*sqrt(-cov(dp_t, dp_{t-1})).

    Valid only when the serial covariance is negative -- which is the bid-ask bounce Roll's
    model describes. A POSITIVE covariance means the model does not apply, and is itself
    informative: it says the price changes trend rather than bounce. Reported as NaN with the
    covariance exposed, never silently clipped to zero.
    """
    p = np.asarray(prices, dtype=np.float64)
    dp = np.diff(p)
    cov = float(np.cov(dp[1:], dp[:-1])[0, 1])
    s = 2.0 * np.sqrt(-cov) if cov < 0 else float("nan")
    mid = float(np.median(p))
    return {"cov": cov, "spread_abs": s, "spread_frac": s / mid if s == s else float("nan"),
            "model_applies": cov < 0}


def autocorr(r, lag=1):
    r = np.asarray(r, dtype=np.float64)
    if len(r) < lag + 8:
        return float("nan")
    a, b = r[lag:], r[:-lag]
    return float(np.corrcoef(a, b)[0, 1])


def realized_vol(r):
    """Realized volatility of a return series: sqrt(sum of squared returns)."""
    return float(np.sqrt(np.sum(np.asarray(r, dtype=np.float64) ** 2)))


def amihud(returns, dollar_volume):
    """
    Amihud (2002) illiquidity: mean of |return| / dollar volume. Higher means the price moves
    more per dollar traded. Scaled by 1e6 for readability (impact per $1M).
    """
    r = np.abs(np.asarray(returns, dtype=np.float64))
    v = np.asarray(dollar_volume, dtype=np.float64)
    ok = v > 0
    return float(np.mean(r[ok] / v[ok]) * 1e6)


def breakeven_hit_rate(cost, move, capture):
    """
    CONTRACT-measurement.md section 2:  p* = 1/2 + c / (2 * phi * m)

    cost, move: fractions (0.001 = 0.1%). capture: phi in (0, 1].
    Returns p* in [0.5, 1], or NaN when the horizon cannot break even at any accuracy
    (p* > 1 means even perfect prediction loses money after costs).
    """
    if move <= 0 or capture <= 0:
        return float("nan")
    p = 0.5 + cost / (2.0 * capture * move)
    return float(p) if p <= 1.0 else float("nan")
