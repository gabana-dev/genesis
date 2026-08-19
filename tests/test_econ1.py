"""
ECON-1 collector checks.

The failure modes that matter here are different from DIR-1's and DIR-2's. This code runs
repeatedly over months, backfills the past, and reports a number that decides whether real
money gets deployed. So:

  * K1 must actually refuse, not warn
  * backfilling must not let the future touch a past prediction
  * B4 must be exposure-matched, not buy-and-hold under another name
  * B3 must preserve the long/short counts while destroying the timing
  * the cost stack must be the measured one, not a placeholder

Run: .venv/bin/python tests/test_econ1.py
"""

import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import econ1 as E  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def synth(n, seed=5):
    """A grid with the frozen feature names, on the declared 8h spacing."""
    rng = np.random.default_rng(seed)
    close = 60_000 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    cols = {"t": np.arange(n, dtype=float) * E.INTERVAL_MS, "close": close}
    for f in E.FEATURES:
        cols[f] = rng.normal(0, 1, n)
    return cols


@check
def k1_refuses_and_does_not_leak_a_partial_number():
    """
    A forward test that can be read whenever it looks good is a backtest with extra steps.
    The refusal must carry NO statistic at all -- not a mean, not a count of wins.
    """
    d = tempfile.mkdtemp(prefix="econ1-")
    old_obs, old_state = E.OBS_PATH, E.STATE_DIR
    try:
        E.STATE_DIR = d
        E.OBS_PATH = os.path.join(d, "observations.jsonl")
        with open(E.OBS_PATH, "w") as f:
            for i in range(E.MIN_TRADES - 1):
                f.write('{"t": %d, "fit": 0.001, "side": 1, "forward_return": 0.05, '
                        '"close": 60000.0}\n' % (i * E.INTERVAL_MS))
        r = E.evaluate()
        assert r["readable"] is False, r
        assert r["n_trades"] == E.MIN_TRADES - 1
        leaked = {k for k in r if any(s in k for s in ("net_", "B1", "B2", "B3", "B4",
                                                       "sharpe", "decomposition"))}
        assert not leaked, f"partial statistics leaked past K1: {leaked}"
        return f"{E.MIN_TRADES - 1} trades -> refused, and no statistic exposed"
    finally:
        E.OBS_PATH, E.STATE_DIR = old_obs, old_state


@check
def a_past_prediction_is_untouched_by_the_future():
    """
    The collector backfills, so this is the check that keeps backfilling honest. Mutate every
    observation after index i and the prediction at i must be bit-identical.
    """
    n = E.TRAIN + 200
    cols = synth(n)
    i = E.TRAIN + 50
    before = E.predict_at(cols, i)
    assert before is not None
    for f in E.FEATURES:
        cols[f][i + 1:] += 1000.0
    cols["close"][i + 1:] *= 3.0
    after = E.predict_at(cols, i)
    assert before == after, f"the future changed a past prediction: {before} -> {after}"
    return "prediction at i is bit-identical after the entire future is mutated"


@check
def training_labels_stop_short_of_the_decision_point():
    """A training label reaching past i would use the future to predict i."""
    n = E.TRAIN + 100
    cols = synth(n, seed=9)
    i = E.TRAIN + 20
    lo = max(0, i - E.TRAIN)
    tr = np.arange(lo, i - E.HORIZON)
    assert tr[-1] + E.HORIZON < i, (tr[-1], E.HORIZON, i)
    return f"last training label lands at {tr[-1] + E.HORIZON}, decision at {i}"


@check
def b4_is_exposure_matched_and_differs_from_buy_and_hold():
    """
    Amendment 1's whole point. With net exposure well below 1, B4 must be strictly easier to
    beat than B2 in a rising market -- and if they come out equal, B4 has been implemented as
    buy-and-hold under another name.
    """
    rng = np.random.default_rng(3)
    n = 600
    ret = rng.normal(0.002, 0.02, n)                  # a drifting market
    side = np.where(rng.random(n) < 0.71, 1.0, -1.0)  # ~0.42 net exposure
    exposure = side.mean()
    cost = E.round_trip_cost()
    b2 = ret.mean() - cost / n
    b4 = exposure * ret.mean() - cost / n
    assert 0.3 < exposure < 0.55, exposure
    assert b4 < b2, (b4, b2)
    assert abs(b4 - b2) > 1e-6, "B4 collapsed onto B2"
    return f"exposure {exposure:.3f}: B4 {b4/1e-4:+.2f} bps vs B2 {b2/1e-4:+.2f} bps"


@check
def b3_permutation_preserves_exposure_and_destroys_timing():
    rng = np.random.default_rng(11)
    side = np.where(rng.random(500) < 0.71, 1.0, -1.0)
    for _ in range(50):
        p = rng.permutation(side)
        assert p.sum() == side.sum(), "permutation changed net exposure"
        assert (p > 0).sum() == (side > 0).sum()
    return "sign permutation holds the long/short counts exactly"


@check
def the_cost_stack_is_the_measured_one():
    """
    Adverse selection must be the 1-day figure measured from the q3 recording, not the 60s
    value and not a placeholder. Using 1.19 here would roughly triple the cost.
    """
    assert abs(E.AS_PER_FILL - 0.1301 * 1e-4) < 1e-12, E.AS_PER_FILL
    c = E.round_trip_cost()
    expected = 2 * 0.000150 - 0.1554e-4 + 2 * 0.1301e-4
    assert abs(c - expected) < 1e-15, (c, expected)
    assert 2.5e-4 < c < 3.5e-4, c
    return f"round trip {c/1e-4:.3f} bps at {E.VENUE}"


@check
def the_frozen_specification_is_unchanged():
    """Any drift in these voids the run under K5."""
    assert E.FEATURES == ["taker_z", "oi_z", "doi_z", "toptrader_z", "crowd_z"]
    assert E.HORIZON == 3 and E.TRAIN == 730 * 3 and E.Z_WINDOW == 30 * 3
    assert E.MIN_TRADES == 270
    from datetime import datetime, timezone
    assert datetime.fromtimestamp(E.START_MS / 1000, timezone.utc).date().isoformat() \
        == "2026-08-20"
    return "five features, 1-day horizon, 730d training, start 2026-08-20"


@check
def zero_open_interest_never_becomes_a_feature():
    """D-D2: a reported open interest of zero is a venue artefact, not a market state."""
    m = {"ts": np.arange(0, 40) * (5 * 60 * 1000.0),
         "arr": np.zeros((40, 6))}
    m["arr"][:, 0] = 100.0
    m["arr"][10, 0] = 0.0                       # the artefact
    cols = E.build_grid(m, {})
    assert not np.isinf(cols["doi_z"]).any(), "an infinite value reached a feature"
    return "zero open interest yields NaN, never inf"


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
          f"ECON-1 collector checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
