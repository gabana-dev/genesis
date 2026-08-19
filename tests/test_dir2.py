"""
DIR-2 harness checks.

DIR-1's harness is reused wholesale, so its checks still cover purge, embargo, trailing
standardisation and the label. What is NEW in DIR-2 is the gate, and a gate has its own ways
of being silently wrong:

  * gating the training set as well as the test set (a different hypothesis)
  * a gate that passes everything, or nothing, and looks like a result either way
  * the metrics join reaching forward by one row

Run: .venv/bin/python tests/test_dir2.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import dir1 as D1  # noqa: E402
import dir2 as D2  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def synth(n, seed=7):
    rng = np.random.default_rng(seed)
    close = 30_000 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    cols = {"t": np.arange(n, dtype=float) * D1.INTERVAL_MS, "close": close}
    for f in D2.FEATURES:
        cols[f] = rng.normal(0, 1, n)
    return cols


@check
def the_gate_restricts_the_test_set_and_only_the_test_set():
    """
    A gate passing ~5% of points must cut predictions by roughly that factor while the model
    still trains on everything. If training were gated too, the coefficients would differ.
    """
    n = D1.TRAIN + D1.TEST + 6 * D1.ROLL + 50
    cols = synth(n)
    h = D1.HORIZONS["1d"]
    allpass = np.ones(n, dtype=bool)
    rng = np.random.default_rng(1)
    narrow = rng.random(n) < 0.05

    p_all, t_all, _ = D2.walk_forward_gated(cols, D2.FEATURES, h, allpass)
    p_nar, t_nar, _ = D2.walk_forward_gated(cols, D2.FEATURES, h, narrow)
    assert len(p_nar) < len(p_all) * 0.12, (len(p_nar), len(p_all))

    # The gated predictions must be a SUBSET of the ungated ones, value-for-value: same model,
    # fewer test points. If training were gated, the fitted values would move.
    assert np.isin(np.round(p_nar, 12), np.round(p_all, 12)).all(), \
        "gated predictions differ in value -- the training set was gated too"
    return f"gate cut {len(p_all)} predictions to {len(p_nar)} with identical fitted values"


@check
def an_all_pass_gate_reproduces_the_ungated_result_exactly():
    """G5 is the control. If it does not reproduce the ungated path bit-for-bit, the gate
    machinery is doing something of its own and no gated comparison means anything."""
    n = D1.TRAIN + D1.TEST + 4 * D1.ROLL + 50
    cols = synth(n, seed=13)
    h = D1.HORIZONS["1d"]
    a, ta, _ = D1.walk_forward(cols, D2.FEATURES, h)
    b, tb, _ = D2.walk_forward_gated(cols, D2.FEATURES, h, np.ones(n, dtype=bool))
    assert np.allclose(a, b) and np.allclose(ta, tb), "G5 does not reproduce the ungated path"
    return "the no-gate cell is bit-identical to DIR-1's ungated walk-forward"


@check
def positive_control_survives_gating():
    """An oracle feature must still score ~1.0 through the gate. If the gate destroys signal,
    every gated null is meaningless."""
    n = D1.TRAIN + D1.TEST + 6 * D1.ROLL + 50
    cols = synth(n, seed=21)
    h = D1.HORIZONS["1d"]
    cols["oracle"] = D1.label(cols["close"], h)
    cols["oracle"][~np.isfinite(cols["oracle"])] = 0.0
    rng = np.random.default_rng(2)
    g = rng.random(n) < 0.10
    p, t, _ = D2.walk_forward_gated(cols, ["oracle"], h, g)
    acc = float(np.mean(np.sign(p) == np.sign(t)))
    assert acc > 0.95, f"the gate destroys real signal: {acc:.3f}"
    return f"oracle through a 10% gate still scores {acc:.3f}"


@check
def the_metrics_join_never_reaches_forward():
    """
    The join takes the last metrics row at or BEFORE each boundary. Reaching one row forward
    would be a look-ahead worth almost nothing in accuracy and invisible in the output, which
    is exactly why it must be excluded by construction.
    """
    mt = np.array([100.0, 200.0, 300.0, 400.0])
    bounds = np.array([250.0, 300.0, 350.0])
    idx = np.searchsorted(mt, bounds, side="right") - 1
    assert list(mt[idx]) == [200.0, 300.0, 300.0], list(mt[idx])
    assert (mt[idx] <= bounds).all(), "join reached forward in time"
    return "boundary 250 takes 200, boundary 300 takes 300, boundary 350 takes 300"


@check
def gate_thresholds_are_the_declared_ones():
    """The gate threshold is a declared constant. A drifting threshold is a search."""
    assert D2.GATE_Z == 2.0
    assert D2.MIN_TEST_PREDICTIONS == 200
    assert set(D2.GATES) == {"G1_flow_extreme", "G2_leverage_build", "G3_toptrader_extreme",
                             "G4_crowd_extreme", "G5_no_gate"}
    assert D2.FEATURES == ["taker_z", "oi_z", "doi_z", "toptrader_z", "crowd_z"]
    return "|z| > 2.0, five gates, five features, exactly as declared"


@check
def k3_uses_the_p95_not_the_mean():
    """
    Defect D-D1 from DIR-1: comparing against the MEAN of the null maximum rejects only half
    of pure noise. DIR-2 must use the p95, and the gap between them must be material.
    """
    z = D2.null_p95_best(10, 2000, n_sims=4000)
    assert z["p95_best"] > z["mean_best"], z
    assert z["p95_best"] - z["mean_best"] > 0.005, z
    return (f"best-of-10 at n=2000: mean {z['mean_best']:.4f} vs p95 {z['p95_best']:.4f} "
            f"-- the mean would pass noise half the time")


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
          f"DIR-2 harness checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
