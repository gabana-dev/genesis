"""
The trial ledger (market/ledger.py).

The properties that matter are the ones that make the count impossible to revise downward.
Everything else here is arithmetic against known answers.

Run: .venv/bin/python tests/test_ledger.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))

import ledger as L  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


_n = [0]


def new(tmp, name=None):
    """A fresh ledger per test. Sharing one file let counts leak between checks."""
    _n[0] += 1
    return L.Ledger(os.path.join(tmp, name or f"l{_n[0]}.jsonl"))


def declared(led, **kw):
    d = {"family": "F", "question": "q", "method": "m", "data": "d", "preregistered": True}
    d.update(kw)
    return led.declare(**d)


# ---- the anti-gaming properties ---------------------------------------------------------

@check
def abandoned_trials_stay_visible(tmp):
    """
    The whole point. Run twenty tests, report two, and the eighteen abandoned declarations
    are as permanent as the two reported. You cannot un-declare.
    """
    with new(tmp) as led:
        ids = [declared(led) for _ in range(20)]
        for t in ids[:2]:
            led.record(t, p_value=0.01, conclusion="reject")
        s = led.summary("F")
        assert s["declared"] == 20 and s["recorded"] == 2 and s["outstanding"] == 18, s
        assert len(led.outstanding("F")) == 18
    return "18 abandoned trials remain counted; the family is 20, not 2"


@check
def a_result_cannot_be_overwritten(tmp):
    with new(tmp) as led:
        t = declared(led)
        led.record(t, p_value=0.20, conclusion="no effect")
        try:
            led.record(t, p_value=0.01, conclusion="reject")
        except ValueError as e:
            assert "append-only" in str(e), e
            return "a recorded trial cannot be re-recorded with a better number"
    raise AssertionError("a result was silently overwritten")


@check
def undeclared_results_are_refused(tmp):
    with new(tmp) as led:
        try:
            led.record("never-declared", p_value=0.001)
        except ValueError as e:
            assert "never declared" in str(e), e
            return "a result with no prior declaration is refused"
    raise AssertionError("an undeclared result was accepted")


@check
def deleting_a_declaration_breaks_the_chain(tmp):
    """
    A trial counter that can be quietly edited is worth nothing. This is why the ledger is
    written to the hash-chained log rather than a JSON file.
    """
    path = os.path.join(tmp, "tamper.jsonl")
    with L.Ledger(path) as led:
        for _ in range(5):
            declared(led)
    assert L.Ledger(path).verify()["ok"], "clean ledger must verify"

    lines = open(path).read().splitlines()
    del lines[2]                                   # remove one declaration
    open(path, "w").write("\n".join(lines) + "\n")
    out = L.Ledger(path).verify()
    assert not out["ok"], out
    return "removing a declaration breaks the hash chain and fails verification"


@check
def truncating_the_ledger_is_detected(tmp):
    path = os.path.join(tmp, "trunc.jsonl")
    with L.Ledger(path) as led:
        for _ in range(6):
            declared(led)
    lines = open(path).read().splitlines()
    open(path, "w").write("\n".join(lines[:3]) + "\n")     # cut the tail
    out = L.Ledger(path).verify()
    assert not out["ok"], out
    return "cutting the tail is caught by the checkpoint, not the chain"


@check
def family_and_question_are_required(tmp):
    with new(tmp) as led:
        for bad in ({"family": ""}, {"question": ""}, {"method": ""}):
            try:
                declared(led, **bad)
            except ValueError:
                continue
            raise AssertionError(f"declaration accepted with {bad}")
    return "family, question and method cannot be omitted or left blank"


@check
def preregistered_and_exploratory_are_counted_apart(tmp):
    with new(tmp) as led:
        for _ in range(3):
            declared(led, preregistered=True)
        for _ in range(7):
            declared(led, preregistered=False)
        s = led.summary("F")
        assert s["preregistered"] == 3 and s["exploratory"] == 7, s
    return "an exploratory trial cannot hide inside a pre-registered count"


@check
def families_are_separate(tmp):
    with new(tmp) as led:
        for _ in range(4):
            declared(led, family="A")
        for _ in range(9):
            declared(led, family="B")
        assert led.count("A") == 4 and led.count("B") == 9 and led.count() == 13
        assert abs(led.summary("A")["bonferroni_alpha"] - 0.05 / 4) < 1e-12
    return "corrections apply within a family, not across the whole ledger"


@check
def context_is_not_a_trial(tmp):
    with new(tmp) as led:
        led.context("median absolute return by horizon")
        declared(led)
        assert led.count() == 1, led.count()
    return "a descriptive measurement is recorded but does not inflate the trial count"


# ---- multiple comparisons ----------------------------------------------------------------

@check
def bonferroni_bites_as_the_family_grows(tmp):
    with new(tmp) as led:
        ids = [declared(led) for _ in range(20)]
        for t in ids:
            led.record(t, p_value=0.03)
        s = led.summary("F")
        assert s["bonferroni_alpha"] == 0.05 / 20
        assert s["survives_bonferroni"] == [], "p=0.03 must not survive 20 trials"
    return "a p of 0.03 stops being interesting once 20 things were tried"


@check
def benjamini_hochberg_matches_a_worked_example():
    # Worked by hand: thresholds are alpha*i/m = 0.00625, 0.0125, 0.01875, 0.025, ...
    # Only the first two p-values fall below theirs, so BH selects 2 of 8 -- not 5. The
    # expected value in the first version of this test was simply wrong.
    ps = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205]
    out = L.benjamini_hochberg(ps, alpha=0.05)
    assert out == [0.001, 0.008], out
    assert L.benjamini_hochberg([0.9, 0.8], alpha=0.05) == []
    return "BH selects 2 of 8 against hand-computed thresholds, and none when none are small"


@check
def expected_max_sharpe_rises_with_trials():
    a = L.expected_max_sharpe(10)
    b = L.expected_max_sharpe(1000)
    assert 0 < a < b, (a, b)
    assert b > 3.0, b
    return f"the null bar rises from {a:.2f} at 10 trials to {b:.2f} at 1000"


@check
def deflated_sharpe_punishes_a_wide_search():
    """A Sharpe of 2 found after one look is convincing; after a thousand it is not."""
    honest = L.deflated_sharpe(2.0, n_trials=1, n_obs=1000)
    fished = L.deflated_sharpe(2.0, n_trials=1000, n_obs=1000)
    assert honest > 0.99, honest
    assert fished < 0.5, fished
    return f"the same Sharpe of 2.0 goes from {honest:.3f} to {fished:.3f} after 1000 trials"


@check
def norm_ppf_is_accurate():
    for p, want in ((0.975, 1.959964), (0.5, 0.0), (0.025, -1.959964), (1e-6, -4.753424)):
        got = L._norm_ppf(p)
        assert abs(got - want) < 1e-5, (p, got, want)
    return "the inverse normal is accurate in both tails"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-ledger-")
    failed = 0
    try:
        for fn in _checks:
            try:
                n = fn.__code__.co_argcount
                print(f"  ok  {fn.__name__}  --  {fn(tmp) if n else fn()}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL {fn.__name__}: {e}")
            except Exception as e:
                failed += 1
                print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"trial-ledger checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
