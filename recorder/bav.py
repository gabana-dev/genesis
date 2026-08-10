"""
BAV-1 — Book Agreement Validation. Implements `CONTRACT-book-agreement.md` exactly.

Engineering validation under DR0003. Not a research experiment, not a trading integration,
and nothing here bears on hypothesis 0001.

Every constant below is fixed by the contract and must not be tuned:

    60 probe slots, 5 warm-up slots, 14 controlled interruptions
    probe spacing uniform [20, 60] s
    controlled dwell 20 s, probe fired 5 s after close, reconnect 15 s later
    skew exclusion  > 2000 ms
    thin book       < 100 levels per side
    required usable incomplete probes: 10

The schedule is a deterministic function of (seed, run start). Probe timing cannot be chosen
after seeing the stream, and the seed is written into the manifest inside the hash chain.
"""

import asyncio
import json
import random
import statistics
import time
import urllib.request
import uuid
from decimal import Decimal

import binance
import events as E
import replay as R
from log import read

# ---- contract constants (do not tune) -------------------------------------------------
N_SLOTS = 60
WARMUP_SLOTS = 5
N_CONTROLLED = 14
SPACING_LO, SPACING_HI = 20.0, 60.0
DWELL = 20.0
PROBE_OFFSET = 5.0          # after close; reconnect at DWELL - PROBE_OFFSET later
SKEW_EXCLUDE_MS = 2000.0
THIN_BOOK_LEVELS = 100
REQUIRED_USABLE_INCOMPLETE = 10
SKEW_BUCKETS = ((0, 100), (100, 300), (300, 1000), (1000, SKEW_EXCLUDE_MS))


def build_schedule(seed, n_slots=N_SLOTS, warmup=WARMUP_SLOTS, n_controlled=N_CONTROLLED):
    """
    Contract 12.5. Deterministic from the seed alone.

    Slots 1..warmup are never controlled. The remainder is partitioned into `n_controlled`
    contiguous blocks and one slot is drawn uniformly within each, which spreads the
    interruptions and guarantees they are never adjacent.
    """
    rng = random.Random(seed)
    offsets, t = [], 0.0
    for _ in range(n_slots):
        t += rng.uniform(SPACING_LO, SPACING_HI)
        offsets.append(t)

    eligible = list(range(warmup + 1, n_slots))          # slot numbers 6..59
    block = len(eligible) / float(n_controlled)
    controlled, previous = [], None
    for b in range(n_controlled):
        lo = int(b * block)
        hi = max(lo + 1, int((b + 1) * block))
        candidates = [eligible[j] for j in range(lo, min(hi, len(eligible)))
                      if previous is None or eligible[j] - previous >= 2]
        # Contract 12.5 requires controlled slots never be adjacent. The draw is still
        # seeded and deterministic; only slots that would violate the rule are removed.
        if not candidates:
            candidates = [eligible[min(hi, len(eligible)) - 1]]
        chosen = candidates[rng.randrange(len(candidates))]
        controlled.append(chosen)
        previous = chosen
    controlled = set(controlled)

    return [{"slot": i + 1, "at": offsets[i], "controlled": (i + 1) in controlled}
            for i in range(n_slots)]


def timeline(schedule):
    """Expand the schedule into ordered actions. Contract 12.3."""
    events = []
    for s in schedule:
        if s["controlled"]:
            events.append((s["at"] - PROBE_OFFSET, "close", s))
            events.append((s["at"], "probe", s))
            events.append((s["at"] - PROBE_OFFSET + DWELL, "reopen", s))
        else:
            events.append((s["at"], "probe", s))
    events.sort(key=lambda e: e[0])
    return events


# ---- run ------------------------------------------------------------------------------

def _fetch(symbol):
    """Blocking REST fetch; returns (payload, status, error, sent_at, received_at)."""
    url = binance.REST_SNAPSHOT.format(symbol=symbol.upper())
    sent = E.now()
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return payload, resp.status, None, sent, E.now()
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}", sent, E.now()


async def run(ingestor, symbol, schedule, min_seconds=0.0):
    """Record the stream, firing probes and controlled interruptions on schedule."""
    import websockets

    loop = asyncio.get_running_loop()
    url = binance.WS_URL.format(symbol=symbol.lower())
    t0 = loop.time()
    actions = timeline(schedule)
    idx = 0
    ws = None
    probe_n = 0

    async def connect():
        nonlocal ws
        cid = str(uuid.uuid4())
        ws = await websockets.connect(url, max_size=binance.MAX_FRAME)
        ingestor.connection_opened(cid, url)
        ingestor.subscription_changed(["depth"], [symbol.upper()])
        # Anchor participates in reconstruction: no probe_id.
        snap, status, err, _, _ = await asyncio.to_thread(_fetch, symbol)
        if snap is not None:
            ingestor.observe(snap, request={"url": binance.REST_SNAPSHOT.format(
                symbol=symbol.upper()), "symbol": symbol.upper(), "role": "anchor"})
        else:
            ingestor.error("anchor_fetch_failed", err)

    async def disconnect(reason, deliberate):
        nonlocal ws
        if deliberate:
            ingestor.log.append(E.RECORDER, "RECONNECT_FORCED",
                                {"reason": reason, "deliberate": True})
        if ws is not None:
            try:
                await ws.close()
            except Exception:
                pass
            ws = None
        ingestor.connection_closed(reason)

    async def fire_probe(slot):
        nonlocal probe_n
        probe_n += 1
        probe_id = f"BAV-{probe_n:03d}"
        payload, status, err, sent, received = await asyncio.to_thread(_fetch, symbol)
        req = {"url": binance.REST_SNAPSHOT.format(symbol=symbol.upper()),
               "symbol": symbol.upper(), "role": "comparison_probe",
               "probe_id": probe_id, "slot": slot["slot"],
               "deliberate": bool(slot["controlled"]),
               "request_sent_at": sent, "response_received_at": received,
               "http_status": status, "error": err}
        if payload is None:
            ingestor.log.append(E.RECORDER, "PROBE_FAILED", req)
        else:
            # probe_id present => excluded from reconstruction (contract section 3)
            ingestor.observe(payload, received_at=received, request=req)

    await connect()
    try:
        while idx < len(actions) or (loop.time() - t0) < min_seconds:
            if idx >= len(actions):
                # Contract 12.1: keep recording to the declared minimum. No probes remain.
                if ws is None:
                    await connect()
                try:
                    payload = await asyncio.wait_for(ws.recv(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                except Exception as exc:
                    ingestor.error(type(exc).__name__, exc)
                    await disconnect(f"natural: {type(exc).__name__}", False)
                    await asyncio.sleep(1.0)
                    continue
                received_at = E.now()
                try:
                    raw = json.loads(payload)
                except json.JSONDecodeError as exc:
                    ingestor.malformed(payload, exc)
                    continue
                ingestor.observe(raw, received_at=received_at)
                continue

            when, kind, slot = actions[idx]
            now = loop.time() - t0
            if now >= when:
                idx += 1
                if kind == "close":
                    await disconnect("controlled interruption (BAV-1 contract 12.3)", True)
                elif kind == "reopen":
                    await connect()
                elif kind == "probe":
                    await fire_probe(slot)
                continue

            if ws is None:                       # dwell: nothing to read
                await asyncio.sleep(min(0.25, max(0.01, when - now)))
                continue
            try:
                payload = await asyncio.wait_for(ws.recv(), timeout=max(0.01, when - now))
            except asyncio.TimeoutError:
                continue
            except Exception as exc:
                ingestor.error(type(exc).__name__, exc)
                await disconnect(f"natural: {type(exc).__name__}", False)
                await asyncio.sleep(1.0)
                await connect()
                continue
            received_at = E.now()
            try:
                raw = json.loads(payload)
            except json.JSONDecodeError as exc:
                ingestor.malformed(payload, exc)
                continue
            ingestor.observe(raw, received_at=received_at)
    finally:
        await disconnect("run complete", False)


# ---- analysis -------------------------------------------------------------------------

def _ms(a, b):
    from datetime import datetime
    return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() * 1000.0


def _levels(side_pairs):
    """
    D-B (BAV-1 run 1). REST prices arrive raw ("65153.99000000"); replay keys are canonical
    ("65130"). Comparing the two as strings gave an empty intersection by construction, so
    M3/M4/M5/M6 measured nothing while M1/M2 -- which convert to Decimal first -- still
    worked. Contract section 6 defines the interval over price SETS, so canonicalising here
    is conformance, not a redefinition. SPEC invariant 9 requires it independently.
    """
    return {E.canon_price(p): Decimal(q) for p, q in side_pairs if Decimal(q) > 0}


def _rest_book(payload):
    return (_levels(payload.get("bids") or []), _levels(payload.get("asks") or []))


def compare(replay_book, rest_bids, rest_asks):
    """Contract sections 6 and 7. No discretion here: the interval and metrics are fixed."""
    pb = {p: Decimal(q) for p, q in (replay_book.get("bids") or {}).items() if Decimal(q) > 0}
    pa = {p: Decimal(q) for p, q in (replay_book.get("asks") or {}).items() if Decimal(q) > 0}
    if not (pb and pa and rest_bids and rest_asks):
        return None

    f = lambda s: [Decimal(x) for x in s]
    floor_bids = max(min(f(rest_bids)), min(f(pb)))
    ceil_asks = min(max(f(rest_asks)), max(f(pa)))

    A_b = {p for p in rest_bids if Decimal(p) >= floor_bids}
    B_b = {p for p in pb if Decimal(p) >= floor_bids}
    A_a = {p for p in rest_asks if Decimal(p) <= ceil_asks}
    B_a = {p for p in pa if Decimal(p) <= ceil_asks}

    best_bid_r, best_bid_p = max(f(rest_bids)), max(f(pb))
    best_ask_r, best_ask_p = min(f(rest_asks)), min(f(pa))

    out = {
        "m1_best_bid_ask_agree": bool(best_bid_r == best_bid_p and best_ask_r == best_ask_p),
        "m2_spread_agree": bool((best_ask_r - best_bid_r) == (best_ask_p - best_bid_p)),
        "crossed": bool(best_bid_r >= best_ask_r or best_bid_p >= best_ask_p),
        "best_bid_rest": str(best_bid_r), "best_bid_replay": str(best_bid_p),
        "best_ask_rest": str(best_ask_r), "best_ask_replay": str(best_ask_p),
        "interval_floor_bids": str(floor_bids), "interval_ceil_asks": str(ceil_asks),
    }
    for name, Aset, Bset, rest_side, rep_side in (
            ("bids", A_b, B_b, rest_bids, pb), ("asks", A_a, B_a, rest_asks, pa)):
        union = Aset | Bset
        shared = Aset & Bset
        rel, absol = [], []
        for p in shared:
            qr, qp = rest_side[p], rep_side[p]
            absol.append(abs(qp - qr))
            if qr > 0:
                rel.append(abs(qp - qr) / qr)
        out[f"m3_jaccard_{name}"] = (len(shared) / len(union)) if union else None
        out[f"m4_rel_median_{name}"] = float(statistics.median(rel)) if rel else None
        out[f"m4_rel_p95_{name}"] = float(_p95(rel)) if rel else None
        out[f"m6_abs_median_{name}"] = float(statistics.median(absol)) if absol else None
        out[f"m6_abs_p95_{name}"] = float(_p95(absol)) if absol else None
        out[f"m5_replay_only_{name}"] = len(Bset - Aset)
        out[f"m5_rest_only_{name}"] = len(Aset - Bset)
        out[f"levels_rest_{name}"] = len(rest_side)
        out[f"levels_replay_{name}"] = len(rep_side)
    return out


def _p95(xs):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))]


def classify(status_complete, book, rest_payload, skew_ms, cmp_out):
    """Contract 10.1-10.3. Returns (outcome, excluded_reason_or_None)."""
    if rest_payload is None:
        return "probe_failed", "rest request failed"
    if skew_ms is not None and skew_ms > SKEW_EXCLUDE_MS:
        return "skew_excluded", f"skew {skew_ms:.0f}ms > {SKEW_EXCLUDE_MS:.0f}ms"

    has_book = bool(book and book.get("bids") and book.get("asks"))
    if not status_complete:
        outcome = "incomplete_with_book" if has_book else "incomplete_no_book"
    else:
        if not has_book:
            return "no_book", "DEFECT: recorder claimed complete over an empty book"
        outcome = "complete"

    if outcome == "incomplete_no_book":
        return outcome, None
    if cmp_out is None:
        return outcome, "no comparable book"
    thin = (min(cmp_out["levels_rest_bids"], cmp_out["levels_rest_asks"])
            < THIN_BOOK_LEVELS)
    if cmp_out["crossed"]:
        return outcome, "crossed"
    if thin:
        return outcome, "thin_book"
    return outcome, None


def analyse(log_path, symbol):
    """Read a BAV-1 log and produce the pre-registered report. Pure function of the log."""
    trials = []
    for ev in read(log_path):
        body = ev.get("body", {})
        req = (body.get("observation", {}) or {}).get("request") or {}
        if ev["event_type"] == "PROBE_FAILED":
            trials.append({"probe_id": body.get("probe_id"), "outcome": "probe_failed",
                           "deliberate": body.get("deliberate"), "excluded": "rest request failed",
                           "error": body.get("error")})
            continue
        if not req.get("probe_id"):
            continue

        boundary = req["response_received_at"]
        skew = _ms(req["request_sent_at"], boundary)
        book = R.order_book_at(log_path, symbol, at=boundary)
        rest_bids, rest_asks = _rest_book(body["world"]["raw"])
        cmp_out = compare(book["book"], rest_bids, rest_asks)
        outcome, excluded = classify(book["complete"], book["book"],
                                     body["world"]["raw"], skew, cmp_out)
        trials.append({
            "probe_id": req["probe_id"], "slot": req.get("slot"),
            "deliberate": bool(req.get("deliberate")),
            "request_sent_at": req["request_sent_at"], "response_received_at": boundary,
            "skew_ms": skew, "recorder_complete": book["complete"],
            "recorder_reason": book["reason"], "replay_comparison_timestamp": boundary,
            "http_status": req.get("http_status"), "outcome": outcome,
            "excluded": excluded, "metrics": cmp_out,
        })
    return _report(trials)


def _bucket(skew):
    for lo, hi in SKEW_BUCKETS:
        if lo <= skew < hi:
            return f"{int(lo)}-{int(hi)}ms"
    return f">{int(SKEW_EXCLUDE_MS)}ms"


def _report(trials):
    cells = {}
    for t in trials:
        nat = "deliberate" if t.get("deliberate") else "natural"
        cells.setdefault(f"{t['outcome']} / {nat}", 0)
        cells[f"{t['outcome']} / {nat}"] += 1

    usable = [t for t in trials
              if t["outcome"] == "incomplete_with_book" and not t.get("excluded")]
    complete_ok = [t for t in trials if t["outcome"] == "complete" and not t.get("excluded")]
    low_skew = [t for t in complete_ok if t["skew_ms"] < 300]
    m1_rate = (sum(1 for t in low_skew if t["metrics"]["m1_best_bid_ask_agree"]) / len(low_skew)
               if low_skew else None)
    med_rel = _median_metric(low_skew, "m4_rel_median")

    if len(usable) < REQUIRED_USABLE_INCOMPLETE:
        qb = "INSUFFICIENT"
    else:
        qb = "REPORTED"          # direction is stated from the numbers, not decided here

    excluded = [t for t in trials if t.get("excluded")]
    return {
        "trials": trials,
        "n_trials": len(trials),
        "cells": cells,
        "usable_incomplete": len(usable),
        "required_usable_incomplete": REQUIRED_USABLE_INCOMPLETE,
        "question_b_status": qb,
        "complete_lowskew_n": len(low_skew),
        "complete_lowskew_m1_rate": m1_rate,
        "complete_lowskew_median_rel_error": med_rel,
        "incomplete_m1_rate": (sum(1 for t in usable if t["metrics"]["m1_best_bid_ask_agree"])
                               / len(usable)) if usable else None,
        "incomplete_median_rel_error": _median_metric(usable, "m4_rel_median"),
        "skew_buckets": _skew_table(trials),
        "excluded_n": len(excluded),
        "excluded_reasons": {r: sum(1 for t in excluded if t["excluded"] == r)
                             for r in {t["excluded"] for t in excluded}},
        "thresholds": {"m1_rate_min": 0.95, "median_rel_error_max": 0.01,
                       "note": "pre-committed engineering acceptance thresholds; "
                               "not natural or universal boundaries"},
        "scope_note": ("A null on the controlled condition is a null AT THE PRE-REGISTERED "
                       "5-SECOND STALENESS INTERVAL. It does not establish that completeness "
                       "status is non-informative at other staleness durations or under "
                       "naturally occurring interruptions."),
        "limitation": ("Validates consistency between two Binance-delivered representations. "
                       "Does not establish that either is ground truth."),
    }


def _median_metric(trials, key):
    vals = []
    for t in trials:
        m = t.get("metrics") or {}
        for side in ("bids", "asks"):
            v = m.get(f"{key}_{side}")
            if v is not None:
                vals.append(v)
    return float(statistics.median(vals)) if vals else None


def _skew_table(trials):
    out = {}
    for t in trials:
        if t.get("skew_ms") is None:
            continue
        b = _bucket(t["skew_ms"])
        out.setdefault(b, {"n": 0, "m1": 0})
        out[b]["n"] += 1
        m = t.get("metrics") or {}
        if m.get("m1_best_bid_ask_agree"):
            out[b]["m1"] += 1
    return out
