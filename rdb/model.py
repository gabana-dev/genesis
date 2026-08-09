"""
Step 12: the imported state-space model. Deliberately boring, and deliberately last.

IMPORT -- linear-Gaussian structural time series estimated by the Kalman filter:
  Kalman (1960); Harvey (1989), *Forecasting, Structural Time Series Models and the
  Kalman Filter*; Durbin & Koopman (2012), *Time Series Analysis by State Space Methods*.
  Implementation: statsmodels.tsa.statespace.structural.UnobservedComponents.

We do NOT implement Kalman filtering. We do not add models to improve the score. One
specification, chosen a priori from the structure of the data (half-hourly load has daily
and weekly cycles), with trigonometric seasonals because 336 seasonal dummies would be
absurd at this frequency.

Parameters are re-estimated on a fixed monthly schedule; between re-estimations the filter
recursively incorporates new observations and forecasts from the current state. That
recursive update is precisely the capability the milestone is meant to exercise.
"""

import numpy as np
import warnings

from config import HORIZON, STEPS_PER_WEEK

SPEC = dict(
    level="local level",
    freq_seasonal=[{"period": 48, "harmonics": 6}, {"period": 336, "harmonics": 3}],
)


def _build(endog):
    from statsmodels.tsa.statespace.structural import UnobservedComponents
    return UnobservedComponents(np.asarray(endog, dtype=float), **SPEC)


class StateSpaceForecaster:
    """
    mode: 'expanding' (all history to the origin) or 'rolling' (last `rolling_weeks`).
    The two differ ONLY in the training slice -- that difference is the adaptation test.
    """

    def __init__(self, mode="expanding", rolling_weeks=26, refit="monthly", fit_cap_weeks=104):
        self.mode = mode
        self.rolling_weeks = rolling_weeks
        self.refit = refit
        self.fit_cap_weeks = fit_cap_weeks      # cap on data used for PARAMETER estimation
        self._params = None
        self._params_month = None
        self.fits = 0

    def _slice(self, history):
        if self.mode == "rolling":
            return history.iloc[-self.rolling_weeks * STEPS_PER_WEEK:]
        return history

    def _maybe_refit(self, history):
        month = (history.index[-1].year, history.index[-1].month)
        if self._params is not None and self.refit == "monthly" and month == self._params_month:
            return
        train = self._slice(history)
        if self.fit_cap_weeks:                  # parameter estimation on a bounded window
            train = train.iloc[-self.fit_cap_weeks * STEPS_PER_WEEK:]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = _build(train).fit(disp=0, maxiter=50)
        self._params = res.params
        self._params_month = month
        self.fits += 1

    def __call__(self, history, future_index):
        self._maybe_refit(history)
        train = self._slice(history)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = _build(train).filter(self._params)
            fc = res.get_forecast(HORIZON)
        mean = np.asarray(fc.predicted_mean, dtype=float)
        se = np.asarray(fc.se_mean, dtype=float)
        return mean[:len(future_index)], se[:len(future_index)]
