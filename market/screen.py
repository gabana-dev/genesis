"""
SCREEN-1 — which market-state variables carry information the trailing tape does not already have?

WHY THIS FILE EXISTS. Five product hypotheses have now died, and four of them died the same death:
the quantity looked informative and turned out to be volatility wearing a costume (F-0010), or a
constant (F-0012), or arithmetic that did not hold (F-0015). Designing a sixth feature and then
testing it is the slow way to find the seventh failure.

So this inverts the order. Instead of choosing a variable and testing it, it screens EVERY
candidate we can compute against the two failure modes that killed the others:

    DOES IT VARY?          A predictor with no spread separates nothing. This is CAL-1's P1,
                           which killed `cannot_defend_pct` before the experiment ran.
    IS IT JUST THE TAPE?   Condition on trailing realised range. A variable that stops separating
                           once you know what the market has already been doing is not adding
                           information. This is the control CASCADE-1 lost to.

THE OUTCOME VARIABLE IS NOT PRICE DIRECTION. F-0005 measured that direction at this horizon needs
4,900 independent observations -- 13.4 years -- so any screen against direction is unpowered
before it starts. The outcome here is FORWARD TRADING CONDITIONS: the realised range over the
next 24 hours. That is the only outcome family this project has ever beaten a control on
(IMPACT-1), and it is the honest form of the question a leveraged trader actually asks --
"is this a bad place to be carrying leverage" rather than "which way is it going".

NOTHING HERE IS A FINDING. It is a screen: it decides what is worth pre-registering, and its only
authority is to eliminate. A variable that survives gets a contract with kill conditions before
any claim is published.

DATA, all free and already on disk:
    metrics   5-minute open interest and positioning ratios, BTCUSDT, from 2020-09  (701,594 rows)
    klines    1-minute OHLCV, from 2019
    funding   8-hourly funding rate, from 2020-01 (7,212 prints)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

EVIDENCE = os.path.expanduser("~/genesis-evidence")
METRICS = f"{EVIDENCE}/metrics/metrics-consolidated.npy"
KLINES = f"{EVIDENCE}/market-data"
FUNDING = f"{EVIDENCE}/market-data/BTCUSDT-funding.npy"

M_TS, M_OI, M_OIV, M_CT_LS, M_ST_LS, M_C_LS, M_TAKER = range(7)

HOUR = 3600_000
TRAIL_H = 24            # what the market has already been doing
FWD_H = 24              # the outcome horizon
# Trailing-range bands, in bps. The control: within a band the market has been equally volatile,
# so anything the candidate still separates is information the tape did not already carry.
TRAIL_BANDS = [0, 120, 220, 380, 700, 1e9]


def hourly_klines():
    """{hour_ms: (open, high, low, close)} across every cached month."""
    out = {}
    for fn in sorted(os.listdir(KLINES)):
        if not fn.startswith("BTCUSDT-1m-") or not fn.endswith(".npy"):
            continue
        a = np.load(f"{KLINES}/{fn}")
        t = (a[:, 0] // HOUR * HOUR).astype(np.int64)
        for h in np.unique(t):
            m = a[t == h]
            out[int(h)] = (m[0, 1], m[:, 2].max(), m[:, 3].min(), m[-1, 4])
    return out


def build():
    """One row per hour: trailing range, forward range, and every candidate variable."""
    kl = hourly_klines()
    hours = np.array(sorted(kl), dtype=np.int64)
    o = np.array([kl[int(h)][0] for h in hours])
    hi = np.array([kl[int(h)][1] for h in hours])
    lo = np.array([kl[int(h)][2] for h in hours])
    cl = np.array([kl[int(h)][3] for h in hours])

    def rolling_range(n, forward):
        """Realised range in bps over n hours, backward or forward, as a fraction of the anchor."""
        out = np.full(len(hours), np.nan)
        for i in range(len(hours)):
            a, b = (i + 1, i + 1 + n) if forward else (max(0, i - n + 1), i + 1)
            if b > len(hours) or a >= b:
                continue
            base = cl[i] if forward else o[a]
            if base <= 0:
                continue
            out[i] = (hi[a:b].max() - lo[a:b].min()) / base * 1e4
        return out

    trail = rolling_range(TRAIL_H, forward=False)
    fwd = rolling_range(FWD_H, forward=True)

    m = np.load(METRICS)
    m = m[np.argsort(m[:, M_TS])]
    mt = (m[:, M_TS] * 1000).astype(np.int64)
    # Last metrics row at or BEFORE each hour. Taking the row after would be a look-ahead that is
    # invisible in the output -- the same trap dir2.py documents.
    idx = np.searchsorted(mt, hours, side="right") - 1
    ok = idx >= 0
    idx = np.clip(idx, 0, len(m) - 1)

    oi = np.where(ok, m[idx, M_OIV], np.nan)          # open interest in USD
    ct_ls = np.where(ok, m[idx, M_CT_LS], np.nan)     # top traders, by account count
    st_ls = np.where(ok, m[idx, M_ST_LS], np.nan)     # top traders, by position size
    c_ls = np.where(ok, m[idx, M_C_LS], np.nan)       # all accounts
    taker = np.where(ok, m[idx, M_TAKER], np.nan)     # taker buy/sell volume ratio

    def pct_change(x, n):
        out = np.full(len(x), np.nan)
        out[n:] = np.where(x[:-n] > 0, (x[n:] - x[:-n]) / x[:-n] * 100, np.nan)
        return out

    def zscore(x, n=24 * 30):
        """Level against its own recent history — a raw OI figure means nothing without it."""
        out = np.full(len(x), np.nan)
        for i in range(n, len(x)):
            w = x[i - n:i]
            w = w[~np.isnan(w)]
            if len(w) < n // 2 or w.std() == 0:
                continue
            out[i] = (x[i] - w.mean()) / w.std()
        return out

    # Funding prints 8-hourly; the last print AT OR BEFORE the hour, same no-look-ahead rule.
    fund = np.full(len(hours), np.nan)
    if os.path.exists(FUNDING):
        f = np.load(FUNDING)
        fi = np.searchsorted(f[:, 0].astype(np.int64), hours, side="right") - 1
        fund = np.where(fi >= 0, f[np.clip(fi, 0, len(f) - 1), 1], np.nan)

    cands = {
        "OI level (z, 30d)": zscore(oi),
        "OI change 24h %": pct_change(oi, 24),
        "OI change 1h %": pct_change(oi, 1),
        # The user's own hypothesis: leverage carried per unit of realised movement.
        "OI / trailing range": np.where(trail > 0, oi / trail, np.nan),
        "top traders L/S (size)": st_ls,
        "top traders L/S (count)": ct_ls,
        "all accounts L/S": c_ls,
        "taker buy/sell ratio": taker,
        "funding rate": fund,
        "funding rate (z, 30d)": zscore(fund),
    }
    return hours, trail, fwd, cands


def screen(trail, fwd, cands):
    print(f"\noutcome: realised range over the NEXT {FWD_H}h, in bps")
    print(f"control: realised range over the PREVIOUS {TRAIL_H}h\n")
    print(f"{'candidate':<26}{'n':>8}{'spread p10-p90':>22}{'R2 vs trail':>13}"
          f"{'lift within bands':>20}")
    print("-" * 89)

    rows = []
    for name, x in cands.items():
        good = ~np.isnan(x) & ~np.isnan(trail) & ~np.isnan(fwd)
        n = int(good.sum())
        if n < 5000:
            print(f"{name:<26}{n:>8}   too few observations")
            continue
        xv, tv, fv = x[good], trail[good], fwd[good]
        p10, p90 = np.percentile(xv, [10, 90])

        # How much of the candidate is already explained by what the market has been doing.
        r = np.corrcoef(xv, tv)[0, 1]
        r2 = r * r

        # THE TEST. Inside each trailing-volatility band, split the candidate at its own median
        # and compare median forward range. A candidate that adds nothing gives lift ~1.0.
        lifts, weights = [], []
        for a, b in zip(TRAIL_BANDS, TRAIL_BANDS[1:]):
            band = (tv >= a) & (tv < b)
            if band.sum() < 500:
                continue
            xb, fb = xv[band], fv[band]
            med = np.median(xb)
            hi_, lo_ = fb[xb >= med], fb[xb < med]
            if len(hi_) < 200 or len(lo_) < 200:
                continue
            lifts.append(np.median(hi_) / np.median(lo_))
            weights.append(band.sum())
        if not lifts:
            print(f"{name:<26}{n:>8}   no usable band")
            continue
        lift = float(np.average(lifts, weights=weights))
        spread = f"{p10:.2f} – {p90:.2f}"
        print(f"{name:<26}{n:>8}{spread:>22}{r2:>13.3f}{lift:>20.3f}")
        rows.append((name, n, p10, p90, r2, lift, lifts))
    return rows


if __name__ == "__main__":
    hours, trail, fwd, cands = build()
    print(f"SCREEN-1 — {len(hours):,} hours of BTCUSDT")
    rows = screen(trail, fwd, cands)
    print("\nlift = median forward range of the upper half of the candidate, divided by the lower")
    print("half, INSIDE a trailing-volatility band, averaged across bands by weight.")
    print("1.00 means the candidate adds nothing the trailing tape did not already say.")
    print("\nSCREEN ONLY. Nothing here may be published as a claim.")
