"""
Collector-watch checks, against synthetic evidence trees with hand-set timestamps.

The monitor is the only thing standing between a silent cron failure and losing ECON-1's
90-day forward test. Two bugs were already made building it, and both are pinned here:

  1. The first _last_append read the tail 64 KB and parsed the last JSON line. LIQ-2 rows carry
     2,342 positions and run ~500 KB, so the parse failed and a healthy collector reported
     STALLED. A monitor that cries wolf gets ignored.
  2. The first watch script embedded Python in shell, the Python had a quoting error, and the
     script exited 0 logging "all collectors ok". A monitor that reports health BECAUSE it is
     broken is worse than none.

Run: .venv/bin/python tests/test_collectors.py
"""

import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import status as S  # noqa: E402
import collector_watch as W  # noqa: E402

_checks = []
H = 3600.0


def check(fn):
    _checks.append(fn)
    return fn


def tree(log_age_h=0.0, data_age_h=0.0, data_bytes=10, make_log=True, make_data=True):
    """An evidence dir whose log and data files have precisely controlled ages."""
    d = tempfile.mkdtemp()
    now = time.time()
    logp, datap = os.path.join(d, "collect.log"), os.path.join(d, "obs.jsonl")
    if make_log:
        open(logp, "w").write("run\n")
        os.utime(logp, (now - log_age_h * H, now - log_age_h * H))
    if make_data:
        open(datap, "wb").write(b"x" * data_bytes)
        os.utime(datap, (now - data_age_h * H, now - data_age_h * H))
    return logp, datap


def run_one(**spec):
    """Evaluate a single synthetic collector through the real collectors_status()."""
    saved = S.COLLECTORS
    try:
        S.COLLECTORS = [spec]
        return S.collectors_status()[0]
    finally:
        S.COLLECTORS = saved


def base(logp, datap, cadence_h=24, **extra):
    return {"name": "t", "why": "test", "cadence_h": cadence_h,
            "log": logp, "data": datap, **extra}


@check
def fresh_collector_is_ok():
    logp, datap = tree(0.5, 0.5)
    r = run_one(**base(logp, datap))
    assert r["verdict"] == "OK", r
    return "recent run and recent append"


@check
def a_job_that_stopped_running_is_stalled():
    logp, datap = tree(log_age_h=100, data_age_h=100)
    r = run_one(**base(logp, datap))
    assert r["ran"] == "STALLED" and r["verdict"] == "STALLED", r
    return "no run in 100h at a 24h cadence"


@check
def the_target_failure_fires_running_but_not_appending():
    # THE failure this monitor exists for: cron fires daily, data never grows.
    logp, datap = tree(log_age_h=0.1, data_age_h=200)
    r = run_one(**base(logp, datap))
    assert r["ran"] == "OK", r
    assert r["advanced"] == "STALLED", r
    assert r["verdict"] == "STALLED", r
    return "ran OK, advanced STALLED — the November failure"


@check
def one_missed_run_is_tolerated_two_are_not():
    ok = run_one(**base(*tree(30, 30)))          # 1.25x cadence
    bad = run_one(**base(*tree(60, 60)))         # 2.5x cadence
    assert ok["verdict"] == "OK", ok
    assert bad["verdict"] == "STALLED", bad
    return "grace is 2x cadence"


@check
def empty_data_before_the_due_date_is_not_an_alarm():
    logp, datap = tree(0.1, 0.1, data_bytes=0)
    r = run_one(**base(logp, datap, advance_from="2099-01-01"))
    assert r["advanced"] == "not yet due", r
    assert r["verdict"] == "OK", r
    return "ECON-1 before 2026-08-21"


@check
def empty_data_after_the_due_date_is_an_alarm():
    logp, datap = tree(0.1, 0.1, data_bytes=0)
    r = run_one(**base(logp, datap, advance_from="2000-01-01"))
    assert r["advanced"] == "STALLED", r
    return "due and still empty"


@check
def a_finished_collector_stops_alarming():
    # q5 closes ~25 Aug. Without this it reports STALLED forever and trains the reader
    # to ignore the monitor.
    logp, datap = tree(500, 500)
    r = run_one(**base(logp, datap, advance_until="2000-01-01"))
    assert r["verdict"] == "complete", r
    return "past its end date, no alarm"


@check
def a_job_that_never_ran_is_not_silently_ok():
    logp, datap = tree(make_log=False)
    r = run_one(**base(logp, datap))
    assert r["ran"] == S.UNKNOWN, r
    assert r["verdict"] != "OK", r
    return "missing log never passes"


@check
def huge_records_do_not_produce_a_false_alarm():
    # Bug 1: LIQ-2 rows are ~500 KB, larger than any tail window.
    logp, datap = tree(0.2, 0.2, data_bytes=2_000_000)
    r = run_one(**base(logp, datap))
    assert r["verdict"] == "OK", r
    return "500 KB rows still read as healthy"


def _isolated_log(fn):
    """
    Run a watch check against a throwaway log.

    W.main() APPENDS, and pointing it at the real log wrote fake STALLED lines into the
    operational record -- which during a genuine incident would read as history. A test must
    never write to the thing it is testing the integrity of.
    """
    saved = W.LOG
    try:
        W.LOG = os.path.join(tempfile.mkdtemp(), "watch.log")
        return fn()
    finally:
        W.LOG = saved


@check
def watch_reports_failure_rather_than_passing():
    # Bug 2: the watch must never exit 0 when it could not perform the check.
    saved = W.problems
    try:
        def boom():
            raise RuntimeError("simulated source change")
        W.problems = boom
        assert _isolated_log(W.main) == 1, "a watch that cannot check must not report healthy"
    finally:
        W.problems = saved
    return "unable to check == alarm"


@check
def watch_exit_codes_match_state():
    saved = W.problems
    try:
        W.problems = lambda: []
        assert _isolated_log(W.main) == 0
        W.problems = lambda: ["econ1: STALLED (ran OK, advanced STALLED)"]
        assert _isolated_log(W.main) == 1
    finally:
        W.problems = saved
    return "0 healthy, 1 alarm"


@check
def tests_never_write_to_the_operational_log():
    before = os.path.getsize(W.LOG) if os.path.exists(W.LOG) else 0
    saved = W.problems
    try:
        W.problems = lambda: ["synthetic: STALLED"]
        _isolated_log(W.main)
    finally:
        W.problems = saved
    after = os.path.getsize(W.LOG) if os.path.exists(W.LOG) else 0
    assert after == before, "a test wrote to the real collector-watch log"
    return "operational log untouched by tests"


@check
def real_collectors_are_all_declared_sanely():
    for c in S.COLLECTORS:
        for k in ("name", "cadence_h", "log", "data", "why"):
            assert k in c, f"{c.get('name')} missing {k}"
        assert c["cadence_h"] > 0
    names = [c["name"] for c in S.COLLECTORS]
    assert len(names) == len(set(names)), names
    return f"{len(S.COLLECTORS)} declared: {', '.join(names)}"


@check
def status_json_carries_collectors():
    s = S.gather()
    assert "collectors" in s and s["collectors"], "collector_watch parses this key"
    assert json.dumps(s)
    return "gather() exposes collectors and stays serialisable"


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
          f"collector-watch checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
