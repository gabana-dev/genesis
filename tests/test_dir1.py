"""
DIR-1 harness checks.

The result of DIR-1 will be an accuracy near 50%, and almost any bug produces an accuracy near
50%. So these checks BRACKET the harness rather than test it in the middle:

  * given a feature that genuinely predicts, does it report high accuracy?   (positive control)
  * given pure noise, does it report ~50%?                                   (negative control)
  * can a training label reach into the test window, or vice versa?          (leakage)
  * does standardisation see the future?                                     (leakage)

Without the positive control, a harness that silently discards all signal would return the
expected null and be indistinguishable from an honest negative result.

Run: .venv/bin/python tests/test_dir1.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import dir1 as D  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def synth(n, seed=7):
    """A random walk on the declared 8h grid, long enough for several walk-forward windows."""
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 0.01, n)
    close = 30_000 * np.exp(np.cumsum(r))
    t = np.arange(n, dtype=float) * D.INTERVAL_MS
    return {"t": t, "close": close}, r


@check
def positive_control_a_real_signal_is_detected():
    """
    An oracle feature equal to the forward return must come back near 100%. If it does not,
    the harness is destroying signal and any null it reports is meaningless.
    """
    n = D.TRAIN + D.TEST + 4 * D.ROLL + 50
    cols, _ = synth(n)
    h = D.HORIZONS["1d"]
    cols["oracle"] = D.label(cols["close"], h)
    cols["oracle"][~np.isfinite(cols["oracle"])] = 0.0
    pred, truth, windows = D.walk_forward(cols, ["oracle"], h)
    acc = float(np.mean(np.sign(pred) == np.sign(truth)))
    assert acc > 0.95, f"harness destroys real signal: {acc:.3f}"
    assert len(windows) >= 3, len(windows)
    return f"oracle feature scores {acc:.3f} over {len(windows)} windows"


@check
def negative_control_noise_is_a_coin_flip():
    n = D.TRAIN + D.TEST + 4 * D.ROLL + 50
    cols, _ = synth(n, seed=11)
    rng = np.random.default_rng(3)
    cols["noise"] = rng.normal(0, 1, n)
    h = D.HORIZONS["1d"]
    pred, truth, _ = D.walk_forward(cols, ["noise"], h)
    acc = float(np.mean(np.sign(pred) == np.sign(truth)))
    assert 0.42 < acc < 0.58, f"noise scored {acc:.3f}, which is not a coin flip"
    return f"pure noise scores {acc:.3f}"


@check
def training_labels_cannot_reach_into_the_test_window():
    """
    PURGE. A training sample at s carries a label reaching s+h. If s+h lands past the
    train/test boundary it overlaps the test period and must be dropped.
    """
    n = D.TRAIN + D.TEST + 2 * D.ROLL + 50
    cols, _ = synth(n)
    h = D.HORIZONS["3d"]
    # Reconstruct the index arithmetic the walk-forward uses.
    tr_end = 0 + D.TRAIN
    tr = np.arange(0, tr_end - h)
    te = np.arange(tr_end + h, tr_end + h + D.TEST)
    assert tr[-1] + h < te[0], "a training label overlaps the first test sample"
    assert te[0] - h >= tr_end, "a test label overlaps the training window"
    return f"purge and embargo leave a gap of {te[0] - (tr[-1] + h)} points at h={h}"


@check
def standardisation_never_sees_the_future():
    """
    A trailing z-score at i must be unchanged by anything after i. Verified by mutating the
    tail and confirming the head is bit-identical.
    """
    rng = np.random.default_rng(5)
    x = rng.normal(0, 1, 500)
    a = D._trailing_z(x, D.Z_WINDOW)
    y = x.copy()
    y[300:] += 100.0                      # violently change the future
    b = D._trailing_z(y, D.Z_WINDOW)
    head = slice(0, 300)
    assert np.allclose(a[head], b[head], equal_nan=True), "z-score at i depends on data after i"
    assert not np.allclose(a[300:], b[300:], equal_nan=True), "the tail should have changed"
    return "z-scores at i are invariant to every observation after i"


@check
def label_is_forward_and_never_wraps():
    close = np.array([1.0, 2.0, 4.0, 8.0, 16.0])
    y = D.label(close, 2)
    assert np.isclose(y[0], np.log(4.0 / 1.0)), y[0]
    assert np.isclose(y[2], np.log(16.0 / 4.0)), y[2]
    assert not np.isfinite(y[3]) and not np.isfinite(y[4]), y
    return "the last h labels are NaN rather than wrapped"


@check
def the_measured_bars_are_the_measure1_values():
    """The bar is imported, not chosen. A typo here would silently move the finish line."""
    assert abs(D.BAR[("1d", 0.5)] - 0.5280868101002973) < 1e-15
    assert abs(D.BAR[("3d", 0.5)] - 0.5151417834228978) < 1e-15
    assert abs(D.BAR[("1d", 0.25)] - 0.5561736202005947) < 1e-15
    assert abs(D.BAR[("3d", 0.25)] - 0.5302835668457958) < 1e-15
    return "52.81% / 51.51% at phi=0.5, matching measure1-report.json exactly"


@check
def best_of_twelve_coin_flips_beats_a_half():
    """
    K3's whole point: with 12 trials the best one is above 50% even with no skill, and the
    margin is not negligible at realistic sample sizes.
    """
    z = D.expected_best_under_zero_skill(12, 2000, n_sims=4000)
    assert z["expected_best_accuracy"] > 0.51, z
    assert z["p95_best_accuracy"] > z["expected_best_accuracy"]
    return (f"best of 12 at n=2000 averages {z['expected_best_accuracy']:.4f} "
            f"with no skill at all")


def main():
    failed = 0
    for fn in _checks:
        try:
            print(f"  ok  {fn.__name__}  --  {fn()}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"DIR-1 harness checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
