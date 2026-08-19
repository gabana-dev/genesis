"""
Disk-guard checks. This is the only module in Genesis that terminates a running experiment,
so its thresholds and its targeting are pinned here.

Nothing in this file may signal a real process. `stop` is stubbed in every check that reaches
it, and a dedicated check asserts SIGKILL is never sent -- SIGKILL would truncate the log and
break the checkpoint, which is the exact corruption the guard exists to prevent.

The log-isolation check is here for the same reason it is in test_collectors.py: an earlier
test wrote fake STALLED lines into an operational log, where during a real incident they would
have read as history.

Run: .venv/bin/python tests/test_disk_guard.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_guard as G  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def run(free, pids, dry=False):
    """Drive main() with a synthetic disk state and no capacity to touch a real process."""
    saved = (G.free_gb, G.find_target, G.stop, G.notify, G.LOG)
    calls = {"stopped": None, "notified": []}
    try:
        G.LOG = os.path.join(tempfile.mkdtemp(), "guard.log")
        G.free_gb = lambda: free
        G.find_target = lambda: list(pids)
        G.stop = lambda p, dry_run=False: calls.__setitem__("stopped", list(p)) or "stubbed"
        G.notify = lambda t, m: calls["notified"].append((t, m))
        code = G.main(["--dry-run"] if dry else [])
        return code, calls
    finally:
        G.free_gb, G.find_target, G.stop, G.notify, G.LOG = saved


@check
def plenty_of_space_is_quiet():
    code, c = run(free=50.0, pids=[123])
    assert code == 0, code
    assert c["stopped"] is None and not c["notified"], c
    return "no action, no noise"


@check
def low_disk_warns_but_does_not_stop():
    code, c = run(free=2.5, pids=[123])          # below WARN_GB(3), above STOP_GB(1)
    assert code == 1, code
    assert c["stopped"] is None, "warned and killed -- must only warn"
    assert c["notified"], "low disk must be loud"
    return "warns at 3 GB, kills nothing"


@check
def critical_disk_stops_the_target():
    code, c = run(free=0.8, pids=[123])
    assert code == 1, code
    assert c["stopped"] == [123], c
    return "stops at 1 GB"


@check
def threshold_boundaries_are_inclusive():
    _, warn = run(free=G.WARN_GB, pids=[1])
    _, stop = run(free=G.STOP_GB, pids=[1])
    assert warn["stopped"] is None and warn["notified"], "at exactly WARN_GB: warn only"
    assert stop["stopped"] == [1], "at exactly STOP_GB: stop"
    return f"warn <= {G.WARN_GB} GB, stop <= {G.STOP_GB} GB"


@check
def critical_disk_with_nothing_running_does_not_crash():
    code, c = run(free=0.5, pids=[])
    assert code == 1, code
    assert c["stopped"] is None, c
    return "already stopped, still reports"


@check
def sigkill_is_never_sent():
    # Check what is SENT, not what is mentioned. The first version of this grepped the whole
    # file for the word and tripped on the docstring explaining why SIGKILL is never used --
    # a test failing on its own subject's documentation.
    src = open(os.path.join(os.path.dirname(__file__), "..", "disk_guard.py")).read()
    for forbidden in ("signal.SIGKILL", "SIGKILL)", "kill -9", ", 9)"):
        assert forbidden not in src, f"guard must never send SIGKILL ({forbidden!r})"
    assert "signal.SIGTERM" in src, "guard must send SIGTERM"
    return "SIGTERM only, no escalation path exists"


@check
def targeting_is_narrow_and_excludes_itself():
    assert G.TARGET_MATCH == "recorder/run.py spot-perp", G.TARGET_MATCH
    src = open(os.path.join(os.path.dirname(__file__), "..", "disk_guard.py")).read()
    assert 'disk_guard" not in cmd' in src, "guard must not match itself"
    return f"matches only {G.TARGET_MATCH!r}"


@check
def a_guard_that_cannot_check_is_loud():
    saved = (G.free_gb, G.LOG, G.notify)
    noted = []
    try:
        G.LOG = os.path.join(tempfile.mkdtemp(), "guard.log")
        G.notify = lambda t, m: noted.append(t)
        def boom():
            raise OSError("volume disappeared")
        G.free_gb = boom
        assert G.main([]) == 1, "failure to check must not report healthy"
        assert noted, "failure must notify"
    finally:
        G.free_gb, G.LOG, G.notify = saved
    return "unable to check == alarm"


@check
def tests_never_write_to_the_operational_log():
    before = os.path.getsize(G.LOG) if os.path.exists(G.LOG) else 0
    run(free=0.5, pids=[999])
    after = os.path.getsize(G.LOG) if os.path.exists(G.LOG) else 0
    assert after == before, "a test wrote to the real disk-guard log"
    return "operational log untouched"


@check
def the_real_volume_is_readable():
    gb = G.free_gb()
    assert gb > 0, gb
    return f"{gb:.2f} GB free on {G.VOLUME}"


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
          f"disk-guard checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
