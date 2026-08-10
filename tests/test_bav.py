"""
BAV-1 implementation checks, against `recorder/CONTRACT-book-agreement.md`.

These test the deterministic parts only — schedule generation, the comparison interval,
metrics, trial classification, and the anti-circularity rule. No live run is performed here.

Each check names the contract section it enforces, so a future reader can tell whether the
code still implements the contract or has drifted from it.

Run: .venv/bin/python tests/test_bav.py
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recorder"))

import bav  # noqa: E402
import dialects  # noqa: E402
import events as E  # noqa: E402
import replay  # noqa: E402
from log import EventLog, read as read_all  # noqa: E402
from stream import Ingestor  # noqa: E402

SYM = "BTCUSDT"
_checks = []


def check(fn):
    _checks.append(fn)
    return fn


# ---- contract 12.5: schedule ----------------------------------------------------------

@check
def schedule_is_deterministic_from_seed(tmp):
    a = bav.build_schedule(1234)
    b = bav.build_schedule(1234)
    c = bav.build_schedule(9999)
    assert a == b, "same seed must give the same schedule"
    assert a != c, "different seed must give a different schedule"
    return "schedule is a pure function of the seed"


@check
def schedule_shape_matches_contract(tmp):
    s = bav.build_schedule(7)
    assert len(s) == 60, len(s)
    ctrl = [x for x in s if x["controlled"]]
    assert len(ctrl) == 14, f"expected 14 controlled, got {len(ctrl)}"
    assert all(x["slot"] > 5 for x in ctrl), "slots 1-5 are warm-up and never controlled"
    gaps = [b["slot"] - a["slot"] for a, b in zip(ctrl, ctrl[1:])]
    assert min(gaps) >= 2, f"controlled slots must never be adjacent, gaps={gaps}"
    spacings = [b["at"] - a["at"] for a, b in zip(s, s[1:])]
    assert all(20.0 <= g <= 60.0 for g in spacings), (min(spacings), max(spacings))
    return f"60 slots, 14 controlled, min gap {min(gaps)} slots, spacing within [20,60]s"


@check
def timeline_places_probe_inside_the_dwell(tmp):
    s = bav.build_schedule(42)
    tl = bav.timeline(s)
    ctrl = next(x for x in s if x["controlled"])
    acts = {k: t for t, k, sl in tl if sl["slot"] == ctrl["slot"]}
    assert acts["probe"] - acts["close"] == 5.0, acts
    assert acts["reopen"] - acts["close"] == 20.0, acts
    assert acts["close"] < acts["probe"] < acts["reopen"], acts
    return "close -> +5s probe -> +20s reopen; probe strictly inside the dwell"


# ---- contract 3: anti-circularity -----------------------------------------------------

@check
def probe_observations_never_enter_reconstruction(tmp):
    path = os.path.join(tmp, "circ.jsonl")
    depth = {"e": "depthUpdate", "E": 1, "s": SYM, "U": 1, "u": 1,
             "b": [["100.00", "1.00000000"]], "a": [["101.00", "2.00000000"]]}
    probe = {"lastUpdateId": 99, "bids": [["100.00", "999.0"]], "asks": [["101.00", "999.0"]]}
    with EventLog(path) as log:
        i = Ingestor(log, dialect=dialects.BINANCE)
        i.observe(depth)
        i.observe(probe, request={"symbol": SYM, "probe_id": "BAV-001",
                                  "role": "comparison_probe"})
    b = replay.order_book_at(path, SYM)
    assert b["book"]["bids"] == {"100": "1"}, b["book"]
    assert b["book"]["asks"] == {"101": "2"}, b["book"]
    return "a probe payload cannot influence the book it is used to evaluate"


@check
def anchor_observations_do_enter_reconstruction(tmp):
    path = os.path.join(tmp, "anch.jsonl")
    anchor = {"lastUpdateId": 5, "bids": [["100.00", "7.0"]], "asks": [["101.00", "8.0"]]}
    with EventLog(path) as log:
        Ingestor(log, dialect=dialects.BINANCE).observe(
            anchor, request={"symbol": SYM, "role": "anchor"})
    b = replay.order_book_at(path, SYM)
    assert b["book"]["bids"] == {"100": "7"} and b["complete"] is True, b
    return "an anchor (no probe_id) still anchors the book"


# ---- INVARIANT 17: anchor validity ----------------------------------------------------

@check
def empty_anchor_cannot_establish_completeness(tmp):
    """The exact defect that escaped cab4602."""
    path = os.path.join(tmp, "inv17a.jsonl")
    empty = {"lastUpdateId": 5, "bids": [], "asks": []}
    with EventLog(path) as log:
        Ingestor(log, dialect=dialects.BINANCE).observe(
            empty, request={"symbol": SYM, "role": "anchor"})
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is False, b
    assert "INVALID" in (b["reason"] or ""), b["reason"]
    types = [e["event_type"] for e in read_all(path)]
    assert "ANCHOR_RECEIVED" in types and "ANCHOR_INVALID" in types, types
    return "an empty anchor establishes nothing and is flagged ANCHOR_INVALID"


@check
def one_sided_anchor_cannot_establish_completeness(tmp):
    path = os.path.join(tmp, "inv17b.jsonl")
    one = {"lastUpdateId": 5, "bids": [["100.0", "1.0"]], "asks": []}
    with EventLog(path) as log:
        Ingestor(log, dialect=dialects.BINANCE).observe(
            one, request={"symbol": SYM, "role": "anchor"})
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is False and "INVALID" in (b["reason"] or ""), b
    return "a one-sided anchor establishes nothing"


@check
def anchor_received_is_not_anchor_valid(tmp):
    path = os.path.join(tmp, "inv17c.jsonl")
    with EventLog(path) as log:
        i = Ingestor(log, dialect=dialects.BINANCE)
        i.observe({"lastUpdateId": 1, "bids": [], "asks": []},
                  request={"symbol": SYM, "role": "anchor"})
        i.observe({"lastUpdateId": 2, "bids": [["100.0", "1.0"]], "asks": [["101.0", "2.0"]]},
                  request={"symbol": SYM, "role": "anchor"})
    recv = [e["body"] for e in read_all(path) if e["event_type"] == "ANCHOR_RECEIVED"]
    assert len(recv) == 2, len(recv)
    assert recv[0]["anchor_valid"] is False and recv[1]["anchor_valid"] is True, recv
    b = replay.order_book_at(path, SYM)
    assert b["complete"] is True and b["book"]["bids"] == {"100": "1"}, b
    return "anchor_received and anchor_valid are distinct states, both recorded"


# ---- contract 6 and 7: interval and metrics -------------------------------------------

@check
def comparison_interval_excludes_rest_truncation(tmp):
    from decimal import Decimal
    replay_book = {"bids": {"100": "1", "99": "1", "98": "1", "97": "1"},
                   "asks": {"101": "1", "102": "1", "103": "1", "104": "1"}}
    rest_bids = {"100": Decimal("1"), "99": Decimal("1")}          # truncated at 99
    rest_asks = {"101": Decimal("1"), "102": Decimal("1")}         # truncated at 102
    out = bav.compare(replay_book, rest_bids, rest_asks)
    assert out["interval_floor_bids"] == "99", out["interval_floor_bids"]
    assert out["interval_ceil_asks"] == "102", out["interval_ceil_asks"]
    assert out["m3_jaccard_bids"] == 1.0, out["m3_jaccard_bids"]
    assert out["m5_replay_only_bids"] == 0, out
    return "REST truncation does not count as disagreement; Jaccard 1.0 inside the interval"


@check
def top_of_book_disagreement_is_never_hidden(tmp):
    from decimal import Decimal
    replay_book = {"bids": {"100.5": "1", "100": "1", "99": "1"}, "asks": {"101": "1", "102": "1"}}
    rest_bids = {"100": Decimal("1"), "99": Decimal("1")}
    rest_asks = {"101": Decimal("1"), "102": Decimal("1")}
    out = bav.compare(replay_book, rest_bids, rest_asks)
    assert out["m1_best_bid_ask_agree"] is False, out
    assert out["m5_replay_only_bids"] == 1, out
    return "a better bid in one book only is caught by M1, not hidden by the interval"


@check
def missing_levels_excluded_from_m4_and_m6_counted_in_m5(tmp):
    from decimal import Decimal
    replay_book = {"bids": {"100": "1", "99": "5"}, "asks": {"101": "1"}}
    rest_bids = {"100": Decimal("1"), "99.5": Decimal("3")}
    rest_asks = {"101": Decimal("1")}
    out = bav.compare(replay_book, rest_bids, rest_asks)
    # floor_bids = max(min(rest)=99.5, min(replay)=99) = 99.5, so replay's 99 is outside
    # the common range and correctly excluded; REST's 99.5 is inside and unmatched.
    assert out["interval_floor_bids"] == "99.5", out["interval_floor_bids"]
    assert out["m4_rel_median_bids"] == 0.0, out["m4_rel_median_bids"]
    assert out["m5_rest_only_bids"] == 1 and out["m5_replay_only_bids"] == 0, out
    return "an unmatched level inside the interval is counted in M5 and excluded from M4/M6"


@check
def m6_absolute_error_distinguishes_scale(tmp):
    from decimal import Decimal
    rb = {"bids": {"100": "0.0002"}, "asks": {"101": "1000"}}
    rest_bids, rest_asks = {"100": Decimal("0.0001")}, {"101": Decimal("1001")}
    out = bav.compare(rb, rest_bids, rest_asks)
    assert out["m4_rel_median_bids"] == 1.0, out["m4_rel_median_bids"]     # 100% on a tiny qty
    assert out["m6_abs_median_bids"] == 0.0001, out["m6_abs_median_bids"]
    assert abs(out["m4_rel_median_asks"] - 0.000999) < 1e-5, out["m4_rel_median_asks"]
    assert out["m6_abs_median_asks"] == 1.0, out["m6_abs_median_asks"]
    return "M6 separates a huge % on a tiny size from a tiny % on a huge size"


# ---- contract 10: classification ------------------------------------------------------

@check
def three_completeness_outcomes(tmp):
    book_full = {"bids": {"100": "1"}, "asks": {"101": "1"}}
    book_empty = {"bids": {}, "asks": {}}
    cmp_ok = {"levels_rest_bids": 500, "levels_rest_asks": 500, "crossed": False}
    assert bav.classify(True, book_full, {}, 50, cmp_ok) == ("complete", None)
    assert bav.classify(False, book_full, {}, 50, cmp_ok) == ("incomplete_with_book", None)
    assert bav.classify(False, book_empty, {}, 50, None)[0] == "incomplete_no_book"
    return "complete / incomplete_with_book / incomplete_no_book all distinguished"


@check
def one_sided_book_is_not_a_replayable_book(tmp):
    one_side = {"bids": {"100": "1"}, "asks": {}}
    out, _ = bav.classify(False, one_side, {}, 50, None)
    assert out == "incomplete_no_book", out
    return "a one-sided book cannot yield M1/M2, so it is not replayable"


@check
def complete_over_empty_book_is_flagged_as_defect(tmp):
    out, reason = bav.classify(True, {"bids": {}, "asks": {}}, {}, 50, None)
    assert out == "no_book" and "DEFECT" in reason, (out, reason)
    return "claiming complete over an empty book is reported as a defect, not a data point"


@check
def exclusions_are_applied(tmp):
    book = {"bids": {"100": "1"}, "asks": {"101": "1"}}
    thin = {"levels_rest_bids": 10, "levels_rest_asks": 10, "crossed": False}
    crossed = {"levels_rest_bids": 500, "levels_rest_asks": 500, "crossed": True}
    assert bav.classify(True, book, {}, 5000, thin)[0] == "skew_excluded"
    assert bav.classify(True, book, None, 50, thin)[0] == "probe_failed"
    assert bav.classify(True, book, {}, 50, thin)[1] == "thin_book"
    assert bav.classify(True, book, {}, 50, crossed)[1] == "crossed"
    return "skew>2000ms, failed probe, thin book and crossed book all excluded per contract"


# ---- contract 12.1 and 13: insufficiency ----------------------------------------------

@check
def fewer_than_ten_usable_is_insufficient_not_null(tmp):
    def trial(outcome, deliberate=True, excluded=None):
        return {"probe_id": "x", "outcome": outcome, "deliberate": deliberate,
                "excluded": excluded, "skew_ms": 50.0,
                "metrics": {"m1_best_bid_ask_agree": True,
                            "m4_rel_median_bids": 0.0, "m4_rel_median_asks": 0.0}}
    nine = bav._report([trial("incomplete_with_book") for _ in range(9)])
    ten = bav._report([trial("incomplete_with_book") for _ in range(10)])
    assert nine["question_b_status"] == "INSUFFICIENT", nine["question_b_status"]
    assert ten["question_b_status"] != "INSUFFICIENT", ten["question_b_status"]
    assert "5-SECOND STALENESS" in ten["scope_note"]
    return "9 usable -> INSUFFICIENT; 10 -> reportable; scope note always present"


@check
def excluded_incomplete_probes_do_not_count_as_usable(tmp):
    t = [{"probe_id": "x", "outcome": "incomplete_with_book", "deliberate": True,
          "excluded": "thin_book", "skew_ms": 50.0, "metrics": None} for _ in range(12)]
    rep = bav._report(t)
    assert rep["usable_incomplete"] == 0, rep["usable_incomplete"]
    assert rep["question_b_status"] == "INSUFFICIENT"
    return "an excluded incomplete probe is not usable evidence"


@check
def cells_keep_natural_and_deliberate_separate(tmp):
    t = [{"probe_id": "a", "outcome": "incomplete_with_book", "deliberate": True,
          "excluded": None, "skew_ms": 10.0, "metrics": {"m1_best_bid_ask_agree": True}},
         {"probe_id": "b", "outcome": "incomplete_with_book", "deliberate": False,
          "excluded": None, "skew_ms": 10.0, "metrics": {"m1_best_bid_ask_agree": True}}]
    rep = bav._report(t)
    assert rep["cells"]["incomplete_with_book / deliberate"] == 1, rep["cells"]
    assert rep["cells"]["incomplete_with_book / natural"] == 1, rep["cells"]
    return "natural and deliberate are never pooled in the cells"


def main():
    tmp = tempfile.mkdtemp(prefix="genesis-bav-")
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
          f"BAV-1 contract checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
