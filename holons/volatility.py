"""
The volatility sensing holon: HAR-RV, walk-forward, reporting its own measured error.

PROPOSAL -- not adopted. Descriptive; tests no hypothesis.

WHY THIS ONE FIRST
    Of everything Genesis has measured, volatility predictability is the finding that did not
    decay. The exploration recorded OOS R-squared of +0.5563 pooled against -0.0037 for
    next-day RETURN on identical features -- and log volatility still autocorrelates at +0.19
    six months out. So this is the one sensing holon whose quantity is known to carry signal.

    It is also the honest place to start because its weakness is known too. The pooled
    +0.5563 is inflated: pooling across years admits between-year variance in the average
    volatility LEVEL into the denominator, and distinguishing a calm year from a violent one
    is a much easier task than predicting tomorrow. Per year the figure is 0.26 to 0.39. This
    holon reports the per-period number, never the pooled one.

A NOTE ON PROVENANCE
    The exploration that produced those figures committed its writeup but not its code, so
    the numbers are not reproducible from the repository. The HAR here is therefore written
    fresh against `market/data.py` rather than wrapping anything, and until it reproduces the
    committed figures it declares itself FITTED, not MEASURED. Promotion to MEASURED is the
    researcher's call and requires the reproduction to be recorded.

THE MODEL
    Corsi (2009). Predict tomorrow's log realized volatility from yesterday's, the trailing
    week's mean, and the trailing month's mean:

        log RV_{t+1} = b0 + b_d log RV_t + b_w mean(log RV_{t-4..t}) + b_m mean(log RV_{t-21..t})

    Three terms, deliberately simple, hard to overfit. That is the point of using it.

WHERE ITS UNCERTAINTY COMES FROM
    Not from the regression's textbook standard error, which assumes the model is right. From
    the holon's OWN walk-forward residuals: the standard deviation of its last `error_window`
    out-of-sample misses. When the model degrades, the error bar widens on its own, and the
    integrator down-weights it without anyone intervening.
"""

import os
import sys
from collections import deque

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))
sys.path.insert(0, os.path.dirname(__file__))

import data as gdata  # noqa: E402

from holon import Basis, Claim, Holon  # noqa: E402

DAY_S = 86_400.0
WEEK, MONTH = 5, 22
MIN_TRAIN = 250          # a year of daily observations before it will speak at all
ERROR_WINDOW = 60        # how many recent OOS misses define its own uncertainty


def realized_vol_daily(minute_rows):
    """
    Daily realized volatility from minute bars: sqrt of the sum of squared minute log returns
    within each UTC day. Days with fewer than 60% of their minutes are dropped rather than
    scaled up -- a partial day's RV is a different quantity, and inflating it would
    manufacture a volatility spike out of a data gap.
    """
    import datetime as dt

    closes = gdata.close(minute_rows)
    opens = gdata.open_time(minute_rows)
    days, cur, prev_close, cur_day = {}, [], None, None

    for t, c in zip(opens, closes):
        d = dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).date()
        if d != cur_day:
            if cur_day is not None:
                days[cur_day] = cur
            cur, cur_day = [], d
        if prev_close is not None and prev_close > 0 and c > 0:
            cur.append(np.log(c / prev_close))
        prev_close = c
    if cur_day is not None:
        days[cur_day] = cur

    out = []
    for d in sorted(days):
        r = np.asarray(days[d], dtype=float)
        if len(r) < 0.6 * 1440:
            continue
        out.append((d, float(np.sqrt((r ** 2).sum()))))
    return out


def har_features(log_rv, i):
    """Features for predicting day i+1, using only information available at the close of day i."""
    return np.array([
        1.0,
        log_rv[i],
        log_rv[i - WEEK + 1:i + 1].mean(),
        log_rv[i - MONTH + 1:i + 1].mean(),
    ])


class VolatilityHolon(Holon):
    """
    Emits a claim about tomorrow's log realized volatility, or None.

    Returns None when it has too little history to fit, when the underlying record is not
    vouched for, or when its own recent errors have grown past `max_sigma` -- a holon whose
    error bar has blown out should stop talking rather than emit a wide claim the integrator
    has to discount.
    """

    quantity = "log_rv_next"
    basis = Basis.FITTED

    def __init__(self, name="volatility", error_window=ERROR_WINDOW, max_sigma=2.0):
        super().__init__(name)
        self.error_window = error_window
        self.max_sigma = max_sigma
        self._errors = deque(maxlen=error_window)
        self._beta = None

    def fit_predict(self, log_rv, i):
        """
        Fit on everything strictly before day i, predict day i+1. Never refits on the future:
        the design matrix stops at i, and the target is shifted one day forward.
        """
        rows = [har_features(log_rv, j) for j in range(MONTH - 1, i)]
        target = [log_rv[j + 1] for j in range(MONTH - 1, i)]
        if len(rows) < MIN_TRAIN:
            return None
        X, y = np.array(rows), np.array(target)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        self._beta = beta
        return float(har_features(log_rv, i) @ beta)

    def assess(self, view):
        """
        `view` carries the daily log RV series, the index of "today", and the completeness
        label for the record underneath it.
        """
        log_rv, i, complete = view["log_rv"], view["i"], view["completeness"]
        if not complete:
            return None

        pred = self.fit_predict(log_rv, i)
        if pred is None:
            return None

        if len(self._errors) < 20:
            return None                     # no self-measured error yet; it declines to speak

        sigma = float(np.std(self._errors, ddof=1))
        if not np.isfinite(sigma) or sigma <= 0 or sigma > self.max_sigma:
            return None

        return Claim(
            holon=self.name,
            quantity=self.quantity,
            horizon_s=DAY_S,
            estimate=pred,
            uncertainty=sigma,
            basis=self.basis,
            completeness=True,
            at=view["at"],
            notes=f"HAR(d,w,m); sigma from {len(self._errors)} walk-forward residuals",
        )

    def score(self, actual, predicted):
        """Feed back yesterday's outcome. This is what makes the uncertainty self-measured."""
        self._errors.append(actual - predicted)


def walk_forward(log_rv, holon, start=None):
    """
    Run the holon across the series, scoring as it goes. Returns per-day records.

    The scoring order matters and is the reason this is a function rather than a loop in a
    test: the holon must predict day i+1 using only its errors up to day i, then be told the
    outcome. Reversing those two lines leaks the future into the error bar.
    """
    n = len(log_rv)
    start = start or (MONTH - 1 + MIN_TRAIN)
    out = []
    for i in range(start, n - 1):
        claim = holon.assess({"log_rv": log_rv, "i": i, "completeness": True, "at": float(i)})
        pred = holon.fit_predict(log_rv, i)
        if pred is not None:
            out.append({"i": i, "claim": claim, "pred": pred, "actual": log_rv[i + 1]})
            holon.score(log_rv[i + 1], pred)
    return out


def oos_r2(records):
    """Out-of-sample R-squared against the mean of the realised values."""
    a = np.array([r["actual"] for r in records])
    p = np.array([r["pred"] for r in records])
    return float(1.0 - ((a - p) ** 2).sum() / ((a - a.mean()) ** 2).sum())
