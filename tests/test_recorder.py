"""
Recorder checks.

The messages here are SYNTHETIC, hand-built to the documented Kalshi payload shapes. They are
test fixtures and nothing else: no synthetic message generator exists inside the `recorder`
package, so fabricated data cannot reach a real log by accident. Nothing in this file has been
compared against a live venue feed.

Run: .venv/bin/python tests/test_recorder.py
"""

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import events as E  # noqa: E402
import health  # noqa: E402
import replay  # noqa: E402
from log import EventLog, read, verify  # noqa: E402
from stream import Ingestor  # noqa: E402

TICKER = "KXBTC15M-26AUG091400"

_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def snapshot(seq, ts_ms, yes=None, no=None):
    return {"type": "orderbook_snapshot", "sid": 1, "seq": seq,
            "msg": {"market_ticker": TICKER, "market_id": "m1", "ts_ms": ts_ms,
                    "yes_dollars_fp": yes or [["0.43", 100], ["0.42", 250]],
                    "no_dollars_fp": no or [["0.56", 80]]}}


def delta(seq, ts_ms, side, price, d, client_order_id=None):
    msg = {"market_ticker": TICKER, "market_id": "m1", "ts_ms": ts_ms,
           "side": side, "price_dollars": price, "delta_fp": d}
    if client_order_id:
        msg["client_order_id"] = client_order_id
    return {"type": "orderbook_delta", "sid": 1, "seq": seq, "msg": msg}


@check
def test_append_only_and_hash_chain(tmp):
    path = os.path.join(tmp, "a.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log, connection_id="c1")
        ing.started({"markets": [TICKER]})
        ing.observe(snapshot(1, 1000))
        ing.observe(delta(2, 1100, "yes", "0.43", -10))
        ing.stopped("done")
    ok, problems = verify(path)
    assert ok and not problems, problems
    evs = list(read(path))
    assert [e["event_index"] for e in evs] == list(range(len(evs)))
    assert evs[0]["prev_hash"] == E.GENESIS_HASH
    return f"{len(evs)} events, chain verified"


@check
def test_tamper_is_detected(tmp):
    path = os.path.join(tmp, "b.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log)
        ing.observe(snapshot(1, 1000))
        ing.observe(delta(2, 1100, "yes", "0.43", -10))
        ing.observe(delta(3, 1200, "yes", "0.43", -5))
    lines = open(path).read().splitlines()
    ev = json.loads(lines[1])
    ev["body"]["world"]["raw"]["msg"]["delta_fp"] = -99999
    lines[1] = json.dumps(ev, ensure_ascii=False)
    open(path, "w").write("\n".join(lines) + "\n")
    ok, problems = verify(path)
    assert not ok and problems[0]["kind"] == "hash_mismatch", problems
    assert problems[0]["index"] == 1
    return f"alteration detected at index {problems[0]['index']}"


@check
def test_deletion_is_detected(tmp):
    path = os.path.join(tmp, "c.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log)
        for i in range(1, 5):
            ing.observe(delta(i, 1000 + i, "yes", "0.43", -1))
    lines = open(path).read().splitlines()
    del lines[2]
    open(path, "w").write("\n".join(lines) + "\n")
    ok, problems = verify(path)
    assert not ok, "removing an event must break the chain"
    return f"deletion detected: {problems[0]['kind']} at {problems[0]['index']}"


@check
def test_sequence_gap_is_recorded_not_repaired(tmp):
    path = os.path.join(tmp, "d.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log)
        ing.observe(snapshot(1, 1000))
        ing.observe(delta(2, 1100, "yes", "0.43", -10))
        ing.observe(delta(7, 1600, "yes", "0.43", -5))   # 3..6 missing
    gaps = [e for e in read(path) if e["event_type"] == "SEQUENCE_GAP"]
    assert len(gaps) == 1, gaps
    b = gaps[0]["body"]
    assert (b["missing_from"], b["missing_to"]) == (3, 6), b
    deltas = [e for e in read(path)
              if e["event_class"] == E.WORLD and e["event_type"] == "orderbook_delta"]
    assert len(deltas) == 2, "missing deltas must not be synthesised"
    return f"gap {b['missing_from']}..{b['missing_to']} recorded; no deltas fabricated"


@check
def test_book_replay_is_deterministic_and_marks_incompleteness(tmp):
    path = os.path.join(tmp, "e.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log)
        ing.observe(snapshot(1, 1000))
        ing.observe(delta(2, 1100, "yes", "0.43", -40))
        ing.observe(delta(3, 1200, "yes", "0.41", 60))

    a = replay.order_book_at(path, TICKER)
    b = replay.order_book_at(path, TICKER)
    assert a == b, "replay must be deterministic"
    assert a["complete"] is True, a
    assert a["book"]["yes"] == {"0.43": 60, "0.42": 250, "0.41": 60}, a["book"]
    assert a["book"]["no"] == {"0.56": 80}

    # a mid-log timestamp reproduces the earlier state, not the latest one
    evs = [e for e in read(path) if e["event_class"] == E.WORLD]
    at = evs[1]["body"]["observation"]["received_at"]
    mid = replay.order_book_at(path, TICKER, at=at)
    assert mid["book"]["yes"]["0.43"] == 60 and "0.41" not in mid["book"]["yes"], mid["book"]

    with EventLog(path) as log:
        Ingestor(log).observe(delta(9, 1900, "yes", "0.42", -50))  # gap 4..8
    after = replay.order_book_at(path, TICKER)
    assert after["complete"] is False and "sequence gap" in after["reason"], after
    return "deterministic; point-in-time correct; incompleteness inherited across the gap"


@check
def test_both_clocks_preserved(tmp):
    path = os.path.join(tmp, "f.jsonl")
    with EventLog(path) as log:
        Ingestor(log, connection_id="conn-9").observe(delta(1, 1786282117728, "yes", "0.43", 5))
    ev = [e for e in read(path) if e["event_class"] == E.WORLD][0]
    assert ev["body"]["world"]["venue_ts_ms"] == 1786282117728
    assert ev["body"]["observation"]["received_at"].endswith("+00:00")
    assert ev["body"]["world"]["raw"]["msg"]["ts_ms"] == 1786282117728
    assert ev["body"]["observation"]["connection_id"] == "conn-9"
    return "venue ts_ms, Genesis received_at and recorded_at all distinct and preserved"


@check
def test_account_replay_from_events_only(tmp):
    path = os.path.join(tmp, "g.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log)
        d = ing.decision(boundary_at=E.now(), model_id="none", model_version="0",
                         input_event_ids=[], decision={"note": "fixture"})
        ing.intent(client_order_id="o1", market_ticker=TICKER, side="yes", action="buy",
                   count=20, price_dollars="0.43", order_type="limit",
                   decision_event_id=d["event_id"])
        ing.execution(kind="ack", market_ticker=TICKER, raw={}, received_at=E.now(),
                      client_order_id="o1", order_id="v1")
        ing.execution(kind="partial_fill", market_ticker=TICKER, raw={}, received_at=E.now(),
                      client_order_id="o1", order_id="v1", side="yes", action="buy",
                      count=7, price_dollars="0.43", fee_dollars="0.02")

    s = replay.account_state_at(path)
    assert s["positions"] == {f"{TICKER}|yes": 7}, s["positions"]
    assert s["cash_dollars"] == "-3.03", s["cash_dollars"]        # 7*0.43 + 0.02
    assert s["fees_dollars"] == "0.02"
    assert s["open_orders"]["o1"]["filled"] == 7
    assert s["reserved_collateral_dollars"] == "5.59"             # 13 unfilled * 0.43
    assert len(s["fills"]) == 1

    with EventLog(path) as log:
        Ingestor(log).execution(kind="settlement", market_ticker=TICKER, raw={},
                                received_at=E.now(), side="yes", count=7,
                                price_dollars="1.00", fee_dollars="0.00")
    s2 = replay.account_state_at(path)
    assert s2["cash_dollars"] == "3.97", s2["cash_dollars"]       # -3.03 + 7.00
    assert s2["complete"] is True, s2["reasons"]
    assert s2["settlements"][0]["observed"] is True
    assert s2["settlements"][0]["independently_verified"] is False
    return "position, cash, fees, reserved collateral and settlement replayed from log alone"


@check
def test_no_fill_is_ever_inferred(tmp):
    path = os.path.join(tmp, "h.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log)
        ing.observe(snapshot(1, 1000))
        ing.intent(client_order_id="o9", market_ticker=TICKER, side="yes", action="buy",
                   count=5, price_dollars="0.43", order_type="limit")
    s = replay.account_state_at(path)
    assert s["positions"] == {}, "an intent must never create a position"
    assert s["cash_dollars"] == "0"
    assert "o9" in s["open_orders"]
    return "intent without execution yields no position and no cash movement"


@check
def test_restart_does_not_look_continuous(tmp):
    path = os.path.join(tmp, "i.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log)
        ing.started({"run": 1})
        ing.observe(delta(1, 1000, "yes", "0.43", 5))
    with EventLog(path) as log:                       # separate process would behave the same
        ing = Ingestor(log)
        ing.started({"run": 2})
        ing.observe(delta(2, 1100, "yes", "0.43", 5))
    runs = {e["recorder_run"] for e in read(path)}
    starts = [e for e in read(path) if e["event_type"] == "RECORDER_STARTED"]
    assert len(runs) == 2 and len(starts) == 2
    ok, _ = verify(path)
    assert ok, "chain must survive a restart"
    rep = health.report(path)
    assert rep["unclean_shutdown_suspected"] is True
    return "two runs distinguishable; chain intact; unclean shutdown surfaced"


@check
def test_malformed_and_regression_are_recorded(tmp):
    path = os.path.join(tmp, "j.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log)
        ing.observe(delta(5, 1000, "yes", "0.43", 1))
        ing.observe(delta(3, 1100, "yes", "0.43", 1))       # regression
        ing.observe("not-a-dict")
    types = [e["event_type"] for e in read(path)]
    assert "MALFORMED_MESSAGE" in types
    errs = [e for e in read(path) if e["event_type"] == "ERROR"]
    assert errs and errs[0]["body"]["kind"] == "sequence_regression"
    return "malformed payload and sequence regression both recorded as events"


@check
def test_timestamp_anomaly_recorded_not_corrected(tmp):
    path = os.path.join(tmp, "k.jsonl")
    with EventLog(path) as log:
        Ingestor(log).observe(delta(1, 1, "yes", "0.43", 1))   # venue ts far in the past
    anomalies = [e for e in read(path) if e["event_type"] == "TIMESTAMP_ANOMALY"]
    assert len(anomalies) == 1
    ev = [e for e in read(path) if e["event_class"] == E.WORLD][0]
    assert ev["body"]["world"]["venue_ts_ms"] == 1, "venue timestamp must not be corrected"
    return "clock disagreement recorded; venue timestamp left untouched"


@check
def test_health_report(tmp):
    path = os.path.join(tmp, "l.jsonl")
    with EventLog(path) as log:
        ing = Ingestor(log)
        ing.started({"markets": [TICKER]})
        ing.connection_opened("c1", "wss://example")
        ing.subscription_changed(["orderbook_delta"], [TICKER])
        ing.observe(snapshot(1, 1000))
        ing.observe(delta(2, 1100, "yes", "0.43", -1))
        ing.observe(delta(6, 1500, "yes", "0.43", -1))
        ing.connection_closed("test")
        ing.stopped("test")
    rep = health.report(path)
    assert rep["integrity_verified"] is True
    assert len(rep["sequence_gaps"]) == 1
    assert rep["messages_known_missing"] == 3
    assert rep["markets_observed"] == [TICKER]
    assert rep["unclean_shutdown_suspected"] is False
    assert any("queue position" in u for u in rep["known_unavailable"])
    txt = health.render(rep)
    assert "HEALTH & EVIDENCE REPORT" in txt
    return f"report: {rep['total_events']} events, 1 gap, 3 messages known missing"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-recorder-")
    failed = 0
    try:
        for fn in _checks:
            try:
                detail = fn(tmp)
                print(f"  ok  {fn.__name__}  --  {detail}")
            except AssertionError as e:
                failed += 1
                print(f"  FAIL {fn.__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'PASS' if not failed else 'FAIL'} -- {len(_checks) - failed}/{len(_checks)} "
          f"recorder checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
