"""
Checks for the orientation layer (DR0005).

WHY THESE, AND NOT "IT PRINTS A REPORT"
    Run against a healthy repository, `status.py` prints a tidy page and proves nothing --
    it would print the same page with every detector removed. So each check below CONSTRUCTS
    the failure the layer exists to surface and asserts that it is surfaced:

      - a committed checkpoint that no live log corresponds to (the real defect: 3,673 events
        recorded against an actual 580,658, unnoticed for a week)
      - an outstanding trial whose declared question differs from what a summary would say
        (the real defect: E3 computed at the wrong horizon and offset)
      - an unreadable or absent input (the real defect: health.py exiting 0 having read
        nothing -- silence must never read as health)

    And one check that the layer obeys DR0005: it writes nothing.

Run: .venv/bin/python tests/test_status.py
"""

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import status as S  # noqa: E402

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def write_log(dirpath, name, last_hash, events=10):
    os.makedirs(dirpath, exist_ok=True)
    logp = os.path.join(dirpath, name)
    with open(logp, "w") as f:
        f.write('{"event": 1}\n')
    json.dump({"event_count": events, "last_index": events - 1, "last_hash": last_hash,
               "updated_at": "2026-08-18T00:00:00+00:00"},
              open(logp + ".checkpoint", "w"))
    return logp


@check
def a_committed_checkpoint_with_no_live_log_is_flagged(tmp):
    """THE REAL DEFECT. A checkpoint describing a log that no longer matches must not read ok."""
    ev = os.path.join(tmp, "evidence")
    write_log(os.path.join(ev, "q3"), "live.jsonl", last_hash="aaaa")

    root = os.path.join(tmp, "repo", "market", "evidence")
    os.makedirs(root, exist_ok=True)
    json.dump({"event_count": 3673, "last_hash": "STALE_HASH",
               "updated_at": "2026-08-10T14:59:33+00:00"},
              open(os.path.join(root, "q3-recording.checkpoint"), "w"))

    old_ev, old_root = S.EVIDENCE, S.ROOT
    S.EVIDENCE, S.ROOT = ev, os.path.join(tmp, "repo")
    try:
        out = S.evidence_status()
    finally:
        S.EVIDENCE, S.ROOT = old_ev, old_root

    states = {c["file"]: c["state"] for c in out["committed"]}
    bad = [f for f, st in states.items() if st != "current"]
    assert bad, f"a checkpoint with no matching live log was reported as fine: {states}"
    assert "NO LIVE LOG" in states[bad[0]], states
    return f"stale committed checkpoint flagged: {states[bad[0]]}"


@check
def a_matching_checkpoint_is_reported_current(tmp):
    """The other half: a real match must NOT be flagged, or the detector is just noise."""
    ev = os.path.join(tmp, "evidence")
    write_log(os.path.join(ev, "q3"), "live.jsonl", last_hash="MATCHING")

    root = os.path.join(tmp, "repo", "market", "evidence")
    os.makedirs(root, exist_ok=True)
    json.dump({"event_count": 10, "last_hash": "MATCHING",
               "updated_at": "2026-08-18T00:00:00+00:00"},
              open(os.path.join(root, "ok.checkpoint"), "w"))

    old_ev, old_root = S.EVIDENCE, S.ROOT
    S.EVIDENCE, S.ROOT = ev, os.path.join(tmp, "repo")
    try:
        out = S.evidence_status()
    finally:
        S.EVIDENCE, S.ROOT = old_ev, old_root

    states = [c["state"] for c in out["committed"]]
    assert states == ["current"], states
    return "a checkpoint matching a live log reads current"


@check
def a_missing_evidence_directory_says_so(tmp):
    """Silence must never read as health."""
    old = S.EVIDENCE
    S.EVIDENCE = os.path.join(tmp, "definitely-absent")
    try:
        out = S.evidence_status()
    finally:
        S.EVIDENCE = old
    assert "error" in out, out
    assert S.UNKNOWN in out["error"], out["error"]
    return "an absent evidence directory reports 'could not determine', not an empty list"


@check
def an_unreadable_checkpoint_is_named_not_skipped(tmp):
    ev = os.path.join(tmp, "evidence", "x")
    os.makedirs(ev, exist_ok=True)
    logp = os.path.join(ev, "a.jsonl")
    open(logp, "w").write("{}\n")
    open(logp + ".checkpoint", "w").write("{{{ not json")

    old = S.EVIDENCE
    S.EVIDENCE = os.path.join(tmp, "evidence")
    try:
        out = S.evidence_status()
    finally:
        S.EVIDENCE = old
    rec = out["live"][0]
    assert S.UNKNOWN in str(rec.get("checkpoint")), rec
    return "an unreadable checkpoint is reported as unreadable, not silently dropped"


@check
def outstanding_trials_print_their_declared_question(tmp):
    """
    THE E3 DEFECT. A summary saying "E3" is what caused the wrong horizon to be used; the
    declared question is what corrects it. The question must reach the rendered output.
    """
    s = {
        "generated_at": "2026-08-18T00:00:00+00:00",
        "ledger": {"verify": {"ok": True}, "declared": 27, "recorded": 26,
                   "outstanding": [{"trial_id": "3488b1e1", "family": "EXEC-1/E3",
                                    "question": "Does more than 100% of the maker advantage "
                                                "survive adverse selection at the touch at 60s?"}]},
        "contracts": [], "evidence": {"live": [], "committed": []},
        "recorder": {"running": False}, "repo": {"last_commit": "x", "uncommitted": []},
        "records": {"experiments": [], "decisions": []},
    }
    text = S.render(s)
    assert "OUTSTANDING 3488b1e1" in text, text
    assert "at the touch at 60s" in text, "the declared question did not reach the output"
    return "an outstanding trial prints its full declared question, not just its name"


@check
def a_broken_ledger_chain_is_not_reported_as_verified(tmp):
    s = {
        "generated_at": "t", "ledger": {"verify": {"ok": False, "problems": [{"kind": "hash"}]},
                                        "declared": 1, "recorded": 1, "outstanding": []},
        "contracts": [], "evidence": {"live": [], "committed": []},
        "recorder": {"running": False}, "repo": {"last_commit": "x", "uncommitted": []},
        "records": {"experiments": [], "decisions": []},
    }
    text = S.render(s)
    assert "FAILED" in text, text
    assert "verified" not in text.split("chain")[1].split("\n")[0], text
    return "a failed chain renders as FAILED, never as verified"


@check
def the_layer_writes_nothing(tmp):
    """DR0005: it reports, it does not decide. Nothing it touches may change."""
    ev = os.path.join(tmp, "evidence", "q3")
    logp = write_log(ev, "l.jsonl", last_hash="h")
    before = {p: os.stat(p).st_mtime_ns for p in
              (logp, logp + ".checkpoint")}
    listing_before = sorted(os.listdir(ev))

    old = S.EVIDENCE
    S.EVIDENCE = os.path.join(tmp, "evidence")
    try:
        S.gather()
    finally:
        S.EVIDENCE = old

    after = {p: os.stat(p).st_mtime_ns for p in before}
    assert before == after, "status.py modified a file it read"
    assert sorted(os.listdir(ev)) == listing_before, "status.py created a file"
    return "gather() mutates nothing and creates nothing"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-status-")
    failed = 0
    try:
        for fn in _checks:
            d = os.path.join(tmp, fn.__name__)
            os.makedirs(d, exist_ok=True)
            try:
                print(f"  ok  {fn.__name__}  --  {fn(d)}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL {fn.__name__}: {e}")
            except Exception as e:
                failed += 1
                print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"orientation-layer checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
