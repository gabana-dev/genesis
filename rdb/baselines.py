"""
Step 8: baselines. Established, deliberately simple, and fitted only on data available
at the forecast origin.

  persistence     -- value at the same clock time on the previous day
  seasonal_naive  -- value at the same clock time on the same weekday last week.
                     This is the SERIOUS baseline. On electricity load it is strong, and
                     beating it is a modest bar rather than an achievement.
  calendar_ols    -- OLS on time-of-day x weekday dummies plus a linear trend

Reference: Hyndman & Athanasopoulos, *Forecasting: Principles and Practice*, on naive and
seasonal-naive benchmarks.

Every forecast for horizon k uses only observations at or before the origin. The lag
arithmetic is checked in tests rather than trusted.
"""

import numpy as np

from config import HORIZON, STEPS_PER_DAY, STEPS_PER_WEEK


def persistence(history, horizon=HORIZON):
    """y_hat[T+k] = y[T+k-48]; for k<=48 every index needed is at or before the origin."""
    assert horizon <= STEPS_PER_DAY, "persistence would need unobserved values"
    return np.asarray(history[-STEPS_PER_DAY:][:horizon], dtype=float)


def seasonal_naive(history, horizon=HORIZON):
    """y_hat[T+k] = y[T+k-336]; same time-of-day, same weekday, previous week."""
    assert horizon <= STEPS_PER_WEEK
    window = np.asarray(history[-STEPS_PER_WEEK:], dtype=float)
    return window[:horizon]


def _design(index):
    """Time-of-day dummies x weekday dummies, plus a linear trend. Causal by construction."""
    tod = (index.hour * 2 + index.minute // 30).to_numpy()
    dow = index.dayofweek.to_numpy()
    n = len(index)
    X = np.zeros((n, STEPS_PER_DAY + 7 + 2))
    X[np.arange(n), tod] = 1.0
    X[np.arange(n), STEPS_PER_DAY + dow] = 1.0
    X[:, -2] = np.arange(n) / max(n, 1)
    X[:, -1] = 1.0
    return X


def calendar_ols(train_series, future_index):
    """Fit on the training window only; predict on future calendar features."""
    X = _design(train_series.index)
    y = train_series.to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    Xf = _design(future_index)
    # continue the trend past the end of training
    n = len(train_series)
    Xf[:, -2] = (np.arange(len(future_index)) + n) / max(n, 1)
    return Xf @ beta


BASELINES = ("persistence", "seasonal_naive", "calendar_ols")
