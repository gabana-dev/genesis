"""
The cross-sectional volatility holon: predict BTC's volatility from everything except BTC.

Classification: IMPORT + BUILD — engineering. Not research. No novelty claimed.

WHY THIS ONE SECOND
    The integrator's whole justification is that it can tell whether two holons are actually
    independent. With one holon it is a passthrough and proves nothing. With two holons drawn
    from the SAME data it measured rho = 0.969 and refused — which it did, on two volatility
    holons, and which is the failure that produced its breadth gate.

    So the second holon must predict the SAME quantity from DIFFERENT information, or the test
    is rigged. This one does:

        volatility.py    BTC's own 1-minute realized volatility history
        cross_section    the daily realized volatility of ~30 OTHER perps, from 4h bars

    Disjoint inputs, identical target, identical model form. If crypto volatility carries
    cross-sectional information that BTC's own history does not, effective breadth clears the
    gate and the combination is worth making. If it does not, the integrator refuses — and that
    is a real answer, obtained cheaply, which is the point of building the gate first.

WHY BTC IS EXCLUDED FROM ITS OWN PREDICTOR
    Including it would import the other holon's information and guarantee correlation. The
    exclusion costs accuracy and buys a clean independence test, deliberately.

WHY THE SAME MODEL FORM
    Corsi's HAR shape — today, the trailing week, the trailing month — is used here too, over
    the cross-sectional mean rather than over BTC's own history. Holding the functional form
    fixed means any measured independence comes from the DATA, not from one holon having a
    richer model than the other.

A NOTE ON THE ESTIMATOR
    Daily realized volatility here is built from 4h bars — six observations a day — while
    volatility.py builds its target from 1-minute bars. That makes this a coarser estimate of
    the same object, and the coarseness is part of what makes the information different. The
    TARGET both holons predict is the same 1-minute-derived series, so they stay comparable.
"""

import datetime as dt
import os
import sys
from collections import deque
from datetime import date

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))
sys.path.insert(0, os.path.dirname(__file__))

import breadth  # noqa: E402
import data as D  # noqa: E402

from holon import Basis, Claim, Holon  # noqa: E402

DAY_S = 86_400.0
WEEK, MONTH = 5, 22
MIN_TRAIN = 250
ERROR_WINDOW = 60
MIN_BARS_PER_DAY = 4        # of six; a day missing a third of its bars is dropped, not scaled
MIN_SYMBOLS = 5             # below this, "the cross-section" is not one


def daily_log_rv(rows) -> dict:
    """
    Daily realized volatility from 4h bars, keyed by UTC date, as a natural log.

    Days with fewer than MIN_BARS_PER_DAY are dropped rather than scaled up. Inflating a
    partial day manufactures a volatility spike out of a data gap — the same rule
    volatility.py applies to minute bars, for the same reason.
    """
    closes = D.close(rows)
    opens = D.open_time(rows)
    by_day, prev = {}, None
    for t, c in zip(opens, closes):
        d = dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).date()
        if prev is not None and prev > 0 and c > 0:
            by_day.setdefault(d, []).append(np.log(c / prev))
        prev = c

    out = {}
    for d, r in by_day.items():
        if len(r) < MIN_BARS_PER_DAY:
            continue
        rv = float(np.sqrt(np.sum(np.square(np.asarray(r)))))
        if rv > 0:
            out[d] = float(np.log(rv))
    return out


def cross_section_series(symbols, start: date, end: date, exclude="BTCUSDT"):
    """
    The daily cross-sectional MEAN of log realized volatility, over every symbol but `exclude`.

    Returns (dates, values, used_symbols, dropped_symbols).

    A day is kept only when at least MIN_SYMBOLS instruments reported it. Averaging over two
    survivors and calling it a cross-section would let a single instrument's outage move the
    feature, which is the cross-sectional equivalent of scaling up a partial day.
    """
    per_symbol, dropped = {}, []
    for s in symbols:
        if s == exclude:
            continue
        rows = breadth.series(s, start, end)
        if rows is None or len(rows) < 50:
            dropped.append(s)
            continue
        rv = daily_log_rv(rows)
        if len(rv) < 50:
            dropped.append(s)
            continue
        per_symbol[s] = rv

    if len(per_symbol) < MIN_SYMBOLS:
        return [], np.empty(0), sorted(per_symbol), dropped

    all_days = sorted({d for rv in per_symbol.values() for d in rv})
    dates, values = [], []
    for d in all_days:
        vals = [rv[d] for rv in per_symbol.values() if d in rv]
        if len(vals) < MIN_SYMBOLS:
            continue
        dates.append(d)
        values.append(float(np.mean(vals)))
    return dates, np.asarray(values), sorted(per_symbol), dropped


def har_features(x, i):
    """HAR shape over the cross-section, using only information available at the close of i."""
    return np.array([
        1.0,
        x[i],
        x[i - WEEK + 1:i + 1].mean(),
        x[i - MONTH + 1:i + 1].mean(),
    ])


class CrossSectionVolatilityHolon(Holon):
    """
    Predicts BTC's next-day log realized volatility from the rest of the market.

    Returns None when it has too little history to fit, when the record is not vouched for,
    when it has not yet measured its own error, or when that error has grown past `max_sigma`.
    """

    quantity = "log_rv_next"
    basis = Basis.FITTED

    def __init__(self, name="cross_section_vol", error_window=ERROR_WINDOW, max_sigma=2.0):
        super().__init__(name)
        self.error_window = error_window
        self.max_sigma = max_sigma
        self._errors = deque(maxlen=error_window)
        self._beta = None

    def fit_predict(self, xs, ys, i):
        """
        Fit on everything strictly before day i, predict day i+1.

        `xs` is the cross-sectional feature series; `ys` is BTC's own log RV — the TARGET only,
        never a feature. Mixing it in would import the other holon's information and destroy
        the independence this holon exists to test.
        """
        rows = [har_features(xs, j) for j in range(MONTH - 1, i)]
        target = [ys[j + 1] for j in range(MONTH - 1, i)]
        if len(rows) < MIN_TRAIN:
            return None
        beta, *_ = np.linalg.lstsq(np.array(rows), np.array(target), rcond=None)
        self._beta = beta
        return float(har_features(xs, i) @ beta)

    def assess(self, view):
        if not view["completeness"]:
            return None
        pred = self.fit_predict(view["xs"], view["ys"], view["i"])
        if pred is None:
            return None
        if len(self._errors) < 20:
            return None

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
            notes=(f"HAR over the cross-sectional mean of {view.get('n_symbols', '?')} perps, "
                   f"BTC excluded; sigma from {len(self._errors)} walk-forward residuals"),
        )

    def score(self, actual, predicted):
        self._errors.append(actual - predicted)


def align(cs_dates, cs_values, btc_dates, btc_values):
    """
    Restrict both series to the days present in BOTH, in order.

    Intersection, never fill. A forward-filled cross-sectional value would repeat yesterday's
    market state as though it were observed today, which is exactly the kind of invented
    observation the recorder refuses to make.
    """
    btc = dict(zip(btc_dates, btc_values))
    days = [d for d in cs_dates if d in btc]
    xs = np.array([v for d, v in zip(cs_dates, cs_values) if d in btc], dtype=float)
    ys = np.array([btc[d] for d in days], dtype=float)
    return days, xs, ys
