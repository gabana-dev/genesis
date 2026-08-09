"""
Regression checks for the audit findings F1-F3 and PARTIALs 4-8.

Written BEFORE the fixes. Every check here corresponds to a specific defect demonstrated by
an audit probe, and each asserts the property the audit showed was missing.

Fixtures are SYNTHETIC, built to the documented Kalshi payload shapes. They live here and not
in the `recorder` package, so fabricated data cannot reach a real log.

Run: .venv/bin/python tests/test_recorder_audit.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import events as E  # noqa: E402
import health  # noqa: E402
import replay  # noqa: E402
from log import EventLog, read, verify  # noqa: E402
from stream import Ingestor  # noqa: E402

T = "KXBTC15M-26AUG091400"
_checks = []


def check(fn):
    _checks.append(fn)
    return fn


def snap(seq, ts, yes=None, no=None):
    return {"type": "orderbook_snapshot", "sid": 1, "seq": seq,
            "msg": {"market_ticker": T, "ts_ms": ts,
                    "yes_dollars_fp": yes if yes is not None else [["0.50", 100]],
                    "no_dollars_fp": no if no is not None else []}}


def dl(seq, ts, price, d, side="yes"):
    return {"type": "orderbook_delta", "sid": 1, "seq": seq,
            "msg": {"market_ticker": T, "ts_ms": ts, "side": side,
                    "price_dollars": price, "delta_fp": d}}


# ---- F1: duplicates -------------------------------------------------------------------

@check
def f1_duplicate_delta_not_applied_twice(tmp):
    path = os.path.join(tmp, "f1a.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(1, 1000))
        i.observe(dl(2, 1100, "0.50", -30))
        i.observe(dl(2, 1100, "0.50", -30))          # exact duplicate
    b = replay.order_book_at(path, T)
    assert b["book"]["yes"] == {"0.5": "70"}, b["book"]
    types = [e["event_type"] for e in read(path)]
    assert "DUPLICATE_MESSAGE" in types, types
    return "identical duplicate ignored once, recorded as an anomaly"


@check
def f1_conflicting_duplicate_marks_incomplete(tmp):
    path = os.path.join(tmp, "f1b.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(1, 1000))
        i.observe(dl(2, 1100, "0.50", -30))
        i.observe(dl(2, 1100, "0.50", -55))          # same seq, different content
    b = replay.order_book_at(path, T)
    assert b["complete"] is False, b
    assert "conflict" in (b["reason"] or "").lower(), b["reason"]
    return "conflicting duplicate seq marks the interval incomplete"


@check
def f1_duplicate_snapshot(tmp):
    path = os.path.join(tmp, "f1c.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(1, 1000, yes=[["0.50", 100]]))
        i.observe(snap(1, 1000, yes=[["0.50", 100]]))
    b = replay.order_book_at(path, T)
    assert b["book"]["yes"] == {"0.5": "100"} and b["complete"], b
    return "duplicate snapshot is idempotent"


@check
def f1_duplicate_across_restart(tmp):
    path = os.path.join(tmp, "f1d.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.started({})
        i.observe(snap(1, 1000))
        i.observe(dl(2, 1100, "0.50", -30))
    with EventLog(path) as log:
        i = Ingestor(log)
        i.started({})
        i.observe(dl(2, 1100, "0.50", -30))          # replayed after restart
    b = replay.order_book_at(path, T)
    assert b["book"]["yes"] == {"0.5": "70"}, b["book"]
    assert "DUPLICATE_MESSAGE" in [e["event_type"] for e in read(path)]
    return "duplicate seq detected across a restart, not double-applied"


# ---- F2: canonical prices -------------------------------------------------------------

@check
def f2_equivalent_price_representations_agree(tmp):
    path = os.path.join(tmp, "f2a.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(1, 1000, yes=[["0.50", 100]]))
        i.observe(dl(2, 1100, 0.5, -40))             # numeric, not string
    b = replay.order_book_at(path, T)
    assert b["book"]["yes"] == {"0.5": "60"}, b["book"]
    return "'0.50' and 0.5 resolve to one level; the delta is not discarded"


@check
def f2_canonical_price_recorded_at_ingestion(tmp):
    path = os.path.join(tmp, "f2b.jsonl")
    with EventLog(path) as log:
        Ingestor(log).observe(dl(1, 1000, "0.5000", -1))
    ev = [e for e in read(path) if e["event_class"] == E.WORLD][0]
    assert ev["body"]["world"]["canonical"]["price_dollars"] == "0.5", ev["body"]["world"]
    assert ev["body"]["world"]["raw"]["msg"]["price_dollars"] == "0.5000", "raw must be verbatim"
    return "canonical price stored at ingestion; raw left untouched"


# ---- F3: truncation -------------------------------------------------------------------

@check
def f3_tail_truncation_detected(tmp):
    results = []
    for n in (1, 2, 3):
        path = os.path.join(tmp, f"f3_{n}.jsonl")
        with EventLog(path) as log:
            i = Ingestor(log)
            for s in range(1, 7):
                i.observe(dl(s, 1000 + s, "0.50", 1))
        lines = open(path).read().splitlines()
        open(path, "w").write("\n".join(lines[:-n]) + "\n")
        ok, problems = verify(path)
        assert not ok, f"truncating {n} event(s) must not verify"
        kinds = {p["kind"] for p in problems}
        assert "truncated_tail" in kinds, problems
        results.append(n)
    return f"truncation of last {results} events all detected"


@check
def f3_checkpoint_absence_is_not_silent(tmp):
    path = os.path.join(tmp, "f3c.jsonl")
    with EventLog(path) as log:
        Ingestor(log).observe(dl(1, 1000, "0.50", 1))
    os.remove(str(path) + ".checkpoint")
    ok, problems = verify(path)
    assert not ok and any(p["kind"] == "checkpoint_missing" for p in problems), problems
    return "a missing checkpoint fails verification rather than passing quietly"


# ---- 4 & 5: fill and settlement sides ---------------------------------------------------

@check
def p4_unknown_fill_side_is_not_booked(tmp):
    path = os.path.join(tmp, "p4.jsonl")
    with EventLog(path) as log:
        Ingestor(log).execution(kind="fill", market_ticker=T, raw={}, received_at=E.now(),
                                client_order_id="out-of-band", count=10,
                                price_dollars="0.60", fee_dollars="0")
    s = replay.account_state_at(path)
    assert s["positions"] == {}, s["positions"]
    assert s["cash_dollars"] == "0", s["cash_dollars"]
    assert s["complete"] is False
    assert any("unresolved" in r or "side" in r for r in s["reasons"]), s["reasons"]
    assert len(s["unresolved"]) == 1
    return "out-of-band fill is unresolved, not silently booked as a buy"


@check
def p5_no_side_settles_correctly(tmp):
    path = os.path.join(tmp, "p5.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.intent(client_order_id="n1", market_ticker=T, side="no", action="buy",
                 count=5, price_dollars="0.40", order_type="limit")
        i.execution(kind="fill", market_ticker=T, raw={}, received_at=E.now(),
                    client_order_id="n1", side="no", action="buy", count=5,
                    price_dollars="0.40", fee_dollars="0")
        i.execution(kind="settlement", market_ticker=T, raw={}, received_at=E.now(),
                    side="no", count=5, price_dollars="1.00", fee_dollars="0")
    s = replay.account_state_at(path)
    assert s["positions"] == {}, s["positions"]
    # canonical decimals strip trailing zeros: 0.40 -> 0.4, 1.00 -> 1, and -2 + 5 -> 3
    assert s["cash_dollars"] == "3", s["cash_dollars"]
    assert s["complete"] is True, s["reasons"]
    return "NO position settles and clears; no implicit YES default"


@check
def p5_settlement_without_side_is_unresolved(tmp):
    path = os.path.join(tmp, "p5b.jsonl")
    with EventLog(path) as log:
        Ingestor(log).execution(kind="settlement", market_ticker=T, raw={},
                                received_at=E.now(), count=5, price_dollars="1.00")
    s = replay.account_state_at(path)
    assert s["complete"] is False and s["cash_dollars"] == "0", s
    return "settlement lacking a side is unresolved rather than assumed"


# ---- 6: strict canonical JSON -----------------------------------------------------------

@check
def p6_nan_and_infinity_rejected(tmp):
    path = os.path.join(tmp, "p6.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe({"type": "trade", "sid": 1, "seq": 1,
                   "msg": {"market_ticker": T, "px": float("nan")}})
        i.observe({"type": "trade", "sid": 1, "seq": 2,
                   "msg": {"market_ticker": T, "px": float("inf")}})
    # The real property is strict parseability: a bare NaN/Infinity JSON literal would make
    # the hash irreproducible by a conforming parser. (A substring scan would false-positive
    # on the recorder's own explanatory text, which legitimately names them.)
    for line in open(path).read().splitlines():
        json.loads(line, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    types = [e["event_type"] for e in read(path)]
    assert types.count("MALFORMED_MESSAGE") == 2, types
    assert not [e for e in read(path) if e["event_class"] == E.WORLD]
    return "NaN and Infinity rejected as malformed; every line is strict JSON"


@check
def p6_canonicalisation_is_stable_across_processes(tmp):
    path = os.path.join(tmp, "p6b.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(1, 1000, yes=[["0.50", 100], ["0.49", 7]]))
        i.observe(dl(2, 1100, "0.50", -3))
    script = (
        "import sys;sys.path.insert(0,'recorder');"
        "from log import verify;import json;"
        f"print(json.dumps(verify({path!r})))"
    )
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                         cwd=os.path.join(os.path.dirname(__file__), ".."))
    assert out.returncode == 0, out.stderr
    ok, problems = json.loads(out.stdout)
    assert ok and not problems, (ok, problems)
    return "a separate process recomputes the same chain and verifies it"


# ---- 7: non-monotonic clock -------------------------------------------------------------

@check
def p7_clock_step_does_not_drop_events(tmp):
    path = os.path.join(tmp, "p7.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(1, 1000, yes=[["0.50", 100]]), received_at="2026-08-09T10:00:00+00:00")
        i.observe(dl(2, 1100, "0.50", -10), received_at="2026-08-09T10:00:05+00:00")
        i.observe(dl(3, 1200, "0.50", -10), received_at="2026-08-09T10:00:02+00:00")
    b = replay.order_book_at(path, T, at="2026-08-09T10:00:03+00:00")
    assert b["events_applied"] == 2, b          # snapshot + the 10:00:02 delta
    assert b["book"]["yes"] == {"0.5": "90"}, b["book"]
    later = replay.order_book_at(path, T, at="2026-08-09T10:00:06+00:00")
    assert later["book"]["yes"] == {"0.5": "80"}, later["book"]
    return "backwards clock step no longer truncates the scan; eligible events still applied"


@check
def p7_no_future_information_used(tmp):
    path = os.path.join(tmp, "p7b.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.observe(snap(1, 1000, yes=[["0.50", 100]]), received_at="2026-08-09T10:00:00+00:00")
        i.observe(dl(2, 1100, "0.50", -60), received_at="2026-08-09T10:00:09+00:00")
    b = replay.order_book_at(path, T, at="2026-08-09T10:00:05+00:00")
    assert b["book"]["yes"] == {"0.5": "100"}, b["book"]
    return "an event received after the boundary is excluded"


# ---- 8: health report -------------------------------------------------------------------

@check
def p8_health_reports_incomplete_intervals(tmp):
    path = os.path.join(tmp, "p8.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.started({"markets": [T]})
        i.connection_opened("c1", "wss://x")
        i.observe(snap(1, 1000), received_at="2026-08-09T10:00:00+00:00")
        i.observe(dl(2, 1100, "0.50", -1), received_at="2026-08-09T10:00:10+00:00")
        i.observe(dl(8, 1700, "0.50", -1), received_at="2026-08-09T10:00:20+00:00")  # gap
        i.observe(snap(9, 1800), received_at="2026-08-09T10:00:30+00:00")            # restored
        i.connection_closed("done")
        i.stopped("done")
    rep = health.report(path)
    assert "healthy_fraction" in rep and rep["healthy_fraction"] is not None
    assert 0.0 <= rep["healthy_fraction"] <= 1.0
    assert rep["incomplete_intervals"], rep
    iv = rep["incomplete_intervals"][0]
    assert iv["market_ticker"] == T and iv["reason"].startswith("sequence gap")
    assert iv["to"] is not None, "the interval must close at the restoring snapshot"
    txt = health.render(rep)
    assert "healthy" in txt.lower() and "incomplete intervals" in txt.lower()
    return (f"healthy_fraction={rep['healthy_fraction']:.3f}, "
            f"{len(rep['incomplete_intervals'])} incomplete interval(s)")


@check
def p8_unclosed_incomplete_interval_is_open_ended(tmp):
    path = os.path.join(tmp, "p8b.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log)
        i.started({})
        i.observe(snap(1, 1000), received_at="2026-08-09T10:00:00+00:00")
        i.observe(dl(9, 1900, "0.50", -1), received_at="2026-08-09T10:00:10+00:00")
    rep = health.report(path)
    iv = rep["incomplete_intervals"][0]
    assert iv["to"] is None and iv["open_ended"] is True, iv
    assert rep["healthy_fraction"] < 1.0
    return "an unrestored gap stays open-ended and reduces healthy time"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-audit-")
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
          f"audit regression checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
