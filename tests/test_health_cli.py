"""
Regression checks for the `health.py` command-line entry point.

WHY THESE EXIST
    `EVIDENCE.md` documented `python recorder/health.py <log>` as the way to verify an
    archived log while `health.py` had no `__main__` block. Run exactly as documented it
    imported cleanly, printed nothing, and exited **0** -- a documented integrity check that
    returned success without reading a single event. Found 2026-08-17 against the EXEC-1 log,
    where it "verified" 3.4 GB in 0.3 seconds.

    Every check below asserts on the EXIT STATUS, not on the output, because the exit status
    is the part a caller acts on and the part that was wrong. A check that only asserted
    "prints a report" would have passed against the original defect for the no-argument case,
    which is exactly the case that was broken.

Fixtures are SYNTHETIC and built through EventLog itself, so no real evidence is read and
none can be written.

Run: .venv/bin/python tests/test_health_cli.py
"""

import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import events as E  # noqa: E402
from log import EventLog  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
PYTHON = os.path.join(ROOT, ".venv", "bin", "python")
HEALTH = os.path.join(ROOT, "recorder", "health.py")

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def run(*args):
    """Returns (returncode, stdout, stderr). Never raises on non-zero -- that is the subject."""
    p = subprocess.run([PYTHON, HEALTH, *args], capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout, p.stderr


def a_small_log(tmp, name="ok.jsonl"):
    path = os.path.join(tmp, name)
    log = EventLog(path)
    log.append(E.RECORDER, "RECORDER_STARTED", {"note": "synthetic fixture"})
    for i in range(5):
        log.append(E.WORLD, "depthUpdate",
                   {"world": {"market_ticker": "TESTUSDT"}, "i": i})
    return path


@check
def no_arguments_is_a_usage_error_not_a_pass(tmp):
    """THE ORIGINAL DEFECT. Bare invocation used to print nothing and exit 0."""
    rc, out, err = run()
    assert rc == 2, f"bare invocation returned {rc}, expected 2"
    assert "usage" in err.lower(), f"no usage message on stderr: {err!r}"
    assert rc != 0, "a command that checked nothing reported success"
    return "bare invocation exits 2 with a usage message"


@check
def a_missing_log_cannot_report_success(tmp):
    rc, out, err = run(os.path.join(tmp, "does-not-exist.jsonl"))
    assert rc == 2, f"missing log returned {rc}, expected 2"
    assert "no such log" in err, err
    return "a missing log exits 2"


@check
def an_unreadable_log_cannot_report_success(tmp):
    path = os.path.join(tmp, "garbage.jsonl")
    with open(path, "w") as f:
        f.write("this is not an event log\n{{{\n")
    rc, out, err = run(path)
    assert rc == 2, f"unreadable log returned {rc}, expected 2 (got stdout={out[:120]!r})"
    return "an unparseable log exits 2 rather than claiming a verdict"


@check
def an_intact_log_verifies_and_exits_zero(tmp):
    rc, out, err = run(a_small_log(tmp))
    assert rc == 0, f"intact log returned {rc}, expected 0. stderr={err[:200]!r}"
    assert "integrity verified   True" in out, out[:400]
    assert "total events         6" in out, out[:400]
    return "an intact log exits 0 and reports integrity verified"


@check
def a_broken_chain_exits_one_and_says_so(tmp):
    """
    The check that matters most: a corrupted log must be DISTINGUISHABLE from an intact one
    by exit status alone. Exit 1, not 0 (silently wrong) and not 2 (could not check).
    """
    path = a_small_log(tmp, "broken.jsonl")
    with open(path) as f:
        lines = f.readlines()
    lines[2] = lines[2].replace('"i": 1', '"i": 999')
    with open(path, "w") as f:
        f.writelines(lines)

    rc, out, err = run(path)
    assert rc == 1, f"broken chain returned {rc}, expected 1. stdout={out[:300]!r}"
    assert "integrity verified   False" in out, out[:400]
    return "a tampered log exits 1, separate from both pass (0) and could-not-check (2)"


@check
def the_three_outcomes_have_three_distinct_codes(tmp):
    """
    Collapsing 'verified false' into 'could not check' would rebuild a smaller version of the
    original defect: a caller could no longer tell a failed verification from an absent one.
    """
    ok = a_small_log(tmp, "distinct_ok.jsonl")
    bad = a_small_log(tmp, "distinct_bad.jsonl")
    with open(bad) as f:
        lines = f.readlines()
    lines[1] = lines[1].replace('"i": 0', '"i": 777')
    with open(bad, "w") as f:
        f.writelines(lines)

    codes = {
        "verified": run(ok)[0],
        "not_verified": run(bad)[0],
        "cannot_check": run(os.path.join(tmp, "absent.jsonl"))[0],
    }
    assert len(set(codes.values())) == 3, f"exit codes collapsed: {codes}"
    assert codes == {"verified": 0, "not_verified": 1, "cannot_check": 2}, codes
    return f"three outcomes, three codes: {codes}"


@check
def json_output_is_machine_readable(tmp):
    import json
    rc, out, err = run(a_small_log(tmp, "json.jsonl"), "--json")
    assert rc == 0, f"returned {rc}; stderr={err[:200]!r}"
    rep = json.loads(out)
    assert rep["integrity_verified"] is True, rep.get("integrity_verified")
    assert rep["total_events"] == 6, rep["total_events"]
    return "--json emits a parseable report and still exits 0"


def main():
    tmp = tempfile.mkdtemp(prefix="health-cli-")
    failed = 0
    try:
        for fn in _checks:
            try:
                print(f"  ok  {fn.__name__}  --  {fn(tmp)}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL {fn.__name__}: {e}")
            except Exception as e:
                failed += 1
                print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"health CLI checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
