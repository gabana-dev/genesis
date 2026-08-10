"""
The canonical completeness rule (recorder/completeness.py).

Governing question, and the only one the rule answers:

    "Can Genesis legitimately claim that this specific reconstructed book contains every
     venue-published change up to time T?"

These checks cover the rule as decided by the researcher on 2026-08-10, including the six
conditions on which `replay` and `health` previously disagreed. One of those six was the
confirmed defect D-C; the other five were latent and had never fired.

NOT covered here, deliberately: reconstruction accuracy. BAV-1 run 2 measured high fidelity
(M3 ~= 0.98, M4/M6 exactly zero) while the completeness label was wrong for every controlled
probe. The two claims are independent and are tested separately.

Run: .venv/bin/python tests/test_completeness.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import completeness as C  # noqa: E402
import dialects  # noqa: E402
import health  # noqa: E402
import replay  # noqa: E402
from log import EventLog  # noqa: E402
from stream import Ingestor  # noqa: E402

SYM = "BTCUSDT"
_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def anchor(uid=1):
    return {"lastUpdateId": uid, "bids": [["100.0", "1.0"]], "asks": [["101.0", "2.0"]]}


def upd(U, u, qty="3.0"):
    return {"e": "depthUpdate", "E": 1, "s": SYM, "U": U, "u": u,
            "b": [["100.0", qty]], "a": []}


def anchored(log):
    """A live, anchored, complete book."""
    i = Ingestor(log, dialect=dialects.BINANCE)
    i.connection_opened("c1", "wss://x")
    i.observe(anchor(1), request={"symbol": SYM, "role": "anchor"})
    return i


# ---- D-C: the confirmed defect from BAV-1 run 2 -----------------------------------------

@check
def connection_closed_invalidates(tmp):
    """
    D-C. Run 2 reported `complete` through 14 deliberate disconnections it had announced
    itself. The reason is not that closure proves loss -- it is that Genesis was not
    observing, so it cannot claim every published change was captured.
    """
    path = os.path.join(tmp, "dc.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.observe(upd(2, 2))
        assert replay.order_book_at(path, SYM)["complete"] is True, "precondition"
        i.connection_closed("deliberate interruption")
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is False, b
    assert "not observing" in (b["reason"] or ""), b["reason"]
    return "a closed connection invalidates completeness -- the run-2 failure"


@check
def probe_during_disconnection_is_incomplete(tmp):
    """The exact BAV-1 controlled-interruption shape: probe fired inside the dwell."""
    path = os.path.join(tmp, "dwell.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.observe(upd(2, 2))
        i.log.append("RECORDER", "RECONNECT_FORCED", {"deliberate": True})
        i.connection_closed("controlled interruption")
        i.observe({"lastUpdateId": 99, "bids": [["100.0", "9.0"]], "asks": [["101.0", "9.0"]]},
                  request={"symbol": SYM, "probe_id": "BAV-001"})
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is False, b
    return "a probe inside a controlled dwell now reads incomplete"


@check
def reconnect_and_valid_anchor_restores(tmp):
    path = os.path.join(tmp, "restore.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.connection_closed("interruption")
        i.connection_opened("c2", "wss://x")
        assert replay.order_book_at(path, SYM)["complete"] is False, "still incomplete"
        i.observe(anchor(500), request={"symbol": SYM, "role": "anchor"})
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is True and b["reason"] is None, b
    return "only a valid anchor restores completeness after an interruption"


# ---- the five latent divergences --------------------------------------------------------

@check
def malformed_message_invalidates(tmp):
    path = os.path.join(tmp, "mal.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.observe("not-a-json-object")
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is False and "malformed" in (b["reason"] or ""), b
    return "an unparseable payload invalidates: we cannot even read what it claimed"


@check
def error_invalidates_fail_safe(tmp):
    path = os.path.join(tmp, "err.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.error("rest_snapshot_failed", "HTTPError 503")
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is False and "rest_snapshot_failed" in (b["reason"] or ""), b
    assert C.ERROR_KIND_EXEMPTIONS == frozenset(), "the exemption list must stay empty"
    return "any observation-path error invalidates; exemption list empty by decision"


@check
def unknown_error_kind_still_invalidates(tmp):
    path = os.path.join(tmp, "err2.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.error("SomeFutureExceptionName", "unseen")
    assert replay.order_book_at(path, SYM)["complete"] is False
    return "an unrecognised error kind fails safe rather than preserving the claim"


@check
def recorder_stopped_invalidates(tmp):
    path = os.path.join(tmp, "stop.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.stopped("run complete")
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is False and "ceased" in (b["reason"] or ""), b
    return "observation ceasing invalidates completeness"


@check
def subscription_scope_is_per_market(tmp):
    # Real ordering: connect, subscribe, anchor. A reconnect re-subscribes the same market.
    path = os.path.join(tmp, "sub.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log, dialect=dialects.BINANCE)
        i.connection_opened("c1", "wss://x")
        i.subscription_changed(["depth"], [SYM])
        i.observe(anchor(1), request={"symbol": SYM, "role": "anchor"})
        i.connection_opened("c2", "wss://x")
        i.subscription_changed(["depth"], [SYM])          # same market, already known
        i.observe(anchor(2), request={"symbol": SYM, "role": "anchor"})
    assert replay.order_book_at(path, SYM)["complete"] is True, "re-subscribing must not break"

    path2 = os.path.join(tmp, "sub2.jsonl")
    with EventLog(path2) as log:
        i = anchored(log)
        i.subscription_changed(["depth"], ["ETHUSDT"])    # a different, new market
    b = replay.order_book_at(path2, SYM)
    assert b["complete"] is True, f"adding another market must not invalidate {SYM}: {b}"
    return "a newly added market does not invalidate an already-observed one"


@check
def anchor_invalid_does_not_restore(tmp):
    path = os.path.join(tmp, "ai.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log, dialect=dialects.BINANCE)
        i.connection_opened("c1", "wss://x")
        i.observe({"lastUpdateId": 5, "bids": [], "asks": []},
                  request={"symbol": SYM, "role": "anchor"})
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is False and "INVALID" in (b["reason"] or ""), b
    return "an empty anchor establishes nothing and does not restore"


# ---- conditions that must NOT invalidate ------------------------------------------------

@check
def benign_events_do_not_invalidate(tmp):
    path = os.path.join(tmp, "benign.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.observe(upd(2, 2), received_at="2026-08-10T00:00:00+00:00")   # clock anomaly
        i.log.append("RECORDER", "RECONNECT_FORCED", {"deliberate": True})
        i.log.append("RECORDER", "PROBE_FAILED", {"probe_id": "BAV-002", "error": "timeout"})
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is True, f"timestamp anomaly / forced-notice / probe failure: {b}"
    return "TIMESTAMP_ANOMALY, RECONNECT_FORCED and PROBE_FAILED leave completeness intact"


@check
def identical_duplicate_does_not_invalidate(tmp):
    path = os.path.join(tmp, "dup.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.observe(upd(2, 2))
        i.observe(upd(2, 2))
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is True, b
    return "a byte-identical repeat loses nothing"


# ---- the consolidation property ---------------------------------------------------------

@check
def replay_and_health_agree(tmp):
    """
    The structural point of the consolidation. Previously `replay` invalidated on 5
    conditions and `health` on 6+, overlapping on 4, and neither was a subset of the other.
    """
    path = os.path.join(tmp, "agree.jsonl")
    with EventLog(path) as log:
        i = anchored(log)
        i.observe(upd(2, 2))
        i.connection_closed("interruption")      # replay used to ignore this
        i.connection_opened("c2", "wss://x")
        i.observe(anchor(500), request={"symbol": SYM, "role": "anchor"})
        i.observe(upd(501, 501))
        i.error("transport", "boom")             # replay used to ignore this too
    rep = health.report(path)
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is False, b
    reasons = " ".join(iv["reason"] for iv in rep["incomplete_intervals"])
    assert "not observing" in reasons, reasons
    assert any("error" in iv["reason"] for iv in rep["incomplete_intervals"]), reasons
    open_ended = [iv for iv in rep["incomplete_intervals"] if iv["open_ended"]]
    assert open_ended, "the trailing error must leave an open-ended interval"
    return "replay and health now derive completeness from the same rule"


@check
def account_field_is_renamed(tmp):
    """Execution resolution is a different claim and no longer shares the word."""
    path = os.path.join(tmp, "acct.jsonl")
    with EventLog(path) as log:
        Ingestor(log).execution(kind="fill", market_ticker=SYM, raw={},
                                received_at="2026-08-10T00:00:00+00:00",
                                client_order_id="x", count="1", price_dollars="1")
    s = replay.account_state_at(path)
    assert "all_executions_resolved" in s and "complete" not in s, list(s)
    assert s["all_executions_resolved"] is False
    return "account state reports all_executions_resolved, never 'complete'"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-completeness-")
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
          f"canonical completeness checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
