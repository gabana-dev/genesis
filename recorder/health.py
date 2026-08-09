"""
Recorder health and evidence report.

This is not decoration. Any future evaluation that cites the log must cite this beside it,
because it states what the record does and does not cover. An evaluation over a period the
recorder did not fully observe is not evidence, and this report is what makes that visible.
"""

from collections import Counter

import events as E
from log import read, verify
from replay import _ts


def report(path) -> dict:
    counts_by_class = Counter()
    counts_by_type = Counter()
    gaps, reconnects, errors, anomalies, malformed = [], [], [], [], []
    subscriptions = []
    runs = []
    first_t = last_t = None
    markets = set()
    total = 0

    for ev in read(path):
        total += 1
        t = _ts(ev)
        first_t = t if first_t is None else min(first_t, t)
        last_t = t if last_t is None else max(last_t, t)

        cls, typ, body = ev["event_class"], ev["event_type"], ev.get("body", {})
        counts_by_class[cls] += 1
        counts_by_type[typ] += 1

        if cls == E.WORLD:
            mt = body.get("world", {}).get("market_ticker")
            if mt:
                markets.add(mt)
        elif cls == E.RECORDER:
            if typ == "SEQUENCE_GAP":
                gaps.append({"at": t, **body})
            elif typ in ("CONNECTION_OPENED", "CONNECTION_CLOSED"):
                reconnects.append({"at": t, "type": typ, **body})
            elif typ == "SUBSCRIPTION_CHANGED":
                subscriptions.append({"at": t, **body})
            elif typ == "ERROR":
                errors.append({"at": t, **body})
            elif typ == "TIMESTAMP_ANOMALY":
                anomalies.append({"at": t, **body})
            elif typ == "MALFORMED_MESSAGE":
                malformed.append({"at": t, "detail": body.get("detail")})
            elif typ in ("RECORDER_STARTED", "RECORDER_STOPPED"):
                runs.append({"at": t, "type": typ, "recorder_run": ev["recorder_run"]})

    integrity_ok, problems = verify(path)
    missing = sum(g["missing_to"] - g["missing_from"] + 1 for g in gaps
                  if g.get("missing_to") is not None and g.get("missing_from") is not None)
    intervals, healthy = _completeness(path, first_t, last_t)

    starts = [r for r in runs if r["type"] == "RECORDER_STARTED"]
    stops = [r for r in runs if r["type"] == "RECORDER_STOPPED"]

    return {
        "log_path": str(path),
        "observed_from": first_t,
        "observed_to": last_t,
        "total_events": total,
        "events_by_class": dict(counts_by_class),
        "events_by_type": dict(counts_by_type),
        "markets_observed": sorted(markets),
        "subscriptions": subscriptions,
        "sequence_gaps": gaps,
        "messages_known_missing": missing,
        "reconnects": reconnects,
        "errors": errors,
        "timestamp_anomalies": anomalies,
        "malformed_messages": malformed,
        "recorder_runs": runs,
        "clean_shutdowns": len(stops),
        "starts": len(starts),
        "unclean_shutdown_suspected": len(starts) > len(stops),
        "integrity_verified": integrity_ok,
        "integrity_problems": problems,
        "incomplete_intervals": intervals,
        "healthy_fraction": healthy,
        "known_unavailable": [
            "queue position (not exposed by the venue; counterfactual fills unrepresentable)",
            "settlement reference values (BRTI licence-gated; settlement is OBSERVED, "
            "not INDEPENDENTLY VERIFIED)",
        ],
        "assumptions": [
            "sequence scope assumed per-subscription (sid), falling back to "
            "(channel, market_ticker) -- unconfirmed against a live feed",
        ],
    }


def _completeness(path, first_t, last_t):
    """
    Per-market intervals during which the recorded book is NOT known to be complete, and the
    fraction of the observation span that is.

    An interval opens at anything that breaks continuity -- a sequence gap, a conflicting
    duplicate, a reconnect, a recorder restart -- and closes only at the next authoritative
    snapshot for that market. An interval never closed stays open-ended, which is the honest
    representation of "we stopped observing and never re-established completeness".
    """
    open_iv = {}
    intervals = []

    def open_for(markets, at, reason):
        for m in markets:
            if m not in open_iv:
                open_iv[m] = {"market_ticker": m, "from": at, "to": None,
                              "reason": reason, "open_ended": True}

    for ev in read(path):
        t = _ts(ev)
        cls, typ, body = ev["event_class"], ev["event_type"], ev.get("body", {})

        if cls == E.RECORDER:
            mt = body.get("market_ticker")
            if typ == "SEQUENCE_GAP":
                open_for([mt], t, f"sequence gap {body.get('missing_from')}-"
                                  f"{body.get('missing_to')}")
            elif typ == "DUPLICATE_MESSAGE" and body.get("conflict"):
                open_for([mt], t, f"conflicting duplicate at seq {body.get('seq')}")
            elif typ in ("CONNECTION_OPENED", "RECORDER_STARTED", "CONNECTION_CLOSED"):
                open_for(list(open_iv.keys()) or [None], t, typ)
                open_iv.setdefault(None, {"market_ticker": None, "from": t, "to": None,
                                          "reason": typ, "open_ended": True})
        elif cls == E.WORLD and typ == "orderbook_snapshot":
            mt = body.get("world", {}).get("market_ticker")
            for k in (mt, None):
                iv = open_iv.pop(k, None)
                if iv is not None:
                    iv["to"], iv["open_ended"] = t, False
                    intervals.append(iv)

    intervals.extend(open_iv.values())
    intervals.sort(key=lambda i: i["from"])

    healthy = None
    if first_t and last_t:
        span = _seconds(first_t, last_t)
        if span > 0:
            bad = sum(_seconds(i["from"], i["to"] or last_t) for i in intervals)
            healthy = max(0.0, min(1.0, 1.0 - bad / span))
        else:
            healthy = 0.0 if intervals else 1.0
    return intervals, healthy


def _seconds(a, b):
    from datetime import datetime
    try:
        return max(0.0, (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds())
    except (ValueError, TypeError):
        return 0.0


def render(rep: dict) -> str:
    lines = [
        "GENESIS RECORDER — HEALTH & EVIDENCE REPORT",
        "=" * 64,
        f"log                  {rep['log_path']}",
        f"observed from        {rep['observed_from']}",
        f"observed to          {rep['observed_to']}",
        f"total events         {rep['total_events']}",
        f"markets              {', '.join(rep['markets_observed']) or '(none)'}",
        "",
        "events by class",
    ]
    for k, v in sorted(rep["events_by_class"].items()):
        lines.append(f"  {k:<14} {v}")
    lines += [
        "",
        f"sequence gaps        {len(rep['sequence_gaps'])}"
        f"  (messages known missing: {rep['messages_known_missing']})",
        f"reconnects           {len(rep['reconnects'])}",
        f"errors               {len(rep['errors'])}",
        f"timestamp anomalies  {len(rep['timestamp_anomalies'])}",
        f"malformed messages   {len(rep['malformed_messages'])}",
        f"recorder starts      {rep['starts']}   clean shutdowns: {rep['clean_shutdowns']}",
        f"unclean shutdown     {rep['unclean_shutdown_suspected']}",
        f"integrity verified   {rep['integrity_verified']}",
        (f"healthy time         {rep['healthy_fraction']:.1%}"
         if rep.get("healthy_fraction") is not None else "healthy time         unknown"),
        f"incomplete intervals {len(rep.get('incomplete_intervals') or [])}",
    ]
    for iv in (rep.get("incomplete_intervals") or [])[:20]:
        lines.append(f"  {iv['from']} -> {iv['to'] or 'OPEN-ENDED'}  "
                     f"{iv['market_ticker'] or '(all markets)'}  {iv['reason']}")
    if rep["integrity_problems"]:
        lines.append(f"  problems: {rep['integrity_problems']}")
    lines += ["", "known unavailable"]
    lines += [f"  - {x}" for x in rep["known_unavailable"]]
    lines += ["", "assumptions"]
    lines += [f"  - {x}" for x in rep["assumptions"]]
    if rep["sequence_gaps"]:
        lines += ["", "gap detail"]
        for g in rep["sequence_gaps"][:20]:
            lines.append(f"  {g['at']}  {g.get('market_ticker')}  "
                         f"missing {g.get('missing_from')}..{g.get('missing_to')}")
    return "\n".join(lines)
