"""
Genesis orientation layer — where the project stands, read-only.

Authorised by DR0005 (research/decisions/0005-orientation-layer.md).

WHAT IT MAY NOT DO, AND WHY
    It reports. It does not decide. It may not declare a trial, record a result, amend a
    contract, choose a direction, or write anything at all. Every path here is a read.

    That boundary is the decision, not an implementation detail. The ledger is worth something
    because a human declares before running and cannot un-declare; a tool that declared on
    your behalf would remove the constraint that gives the count its meaning. See DR0005 for
    the full argument, including why "knows what it wants" is excluded on is/ought grounds.

WHAT IT IS AIMED AT
    Three real failures, all of them a status claim the available evidence did not support:

      - EXEC-1's E3 was first computed at the wrong horizon and offset, because a summary was
        read instead of the declared question. So outstanding trials print their QUESTION.
      - A committed checkpoint recorded 3,673 events against an actual 580,658 for a week,
        with nothing announcing it. So committed checkpoints are matched against live ones.
      - `health.py` exited 0 without reading anything. So this prints what it could NOT
        check, rather than staying silent and looking healthy.

    Where it cannot determine something it says so. Silence is never a pass.

Usage:  .venv/bin/python status.py [--json]
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
EVIDENCE = os.path.expanduser("~/genesis-evidence")

UNKNOWN = "could not determine"


def _run(*args, cwd=ROOT):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30)
        return p.stdout.strip() if p.returncode == 0 else None
    except Exception:
        return None


def _age(iso):
    """Human age of an ISO timestamp, or None."""
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        d = datetime.now(timezone.utc) - t
        h = d.total_seconds() / 3600
        return f"{h:.1f}h ago" if h < 48 else f"{h/24:.1f}d ago"
    except Exception:
        return None


# ---- ledger ---------------------------------------------------------------------------

def ledger_status():
    sys.path.insert(0, os.path.join(ROOT, "market"))
    try:
        import ledger as L
    except Exception as e:
        return {"error": f"{UNKNOWN}: ledger import failed ({e!r})"}
    try:
        led = L.Ledger()
        if not os.path.exists(led.path):
            return {"error": f"{UNKNOWN}: no ledger at {led.path}"}
        outstanding = led.outstanding()
        return {
            "path": led.path,
            "verify": led.verify(),
            "declared": led.count(),
            "recorded": led.count() - len(outstanding),
            "outstanding": [
                {"trial_id": t["trial_id"], "family": t["family"], "question": t["question"]}
                for t in outstanding
            ],
        }
    except Exception as e:
        return {"error": f"{UNKNOWN}: {e!r}"}


# ---- contracts ------------------------------------------------------------------------

def contracts_status():
    out = []
    for d in ("market", "recorder"):
        p = os.path.join(ROOT, d)
        if not os.path.isdir(p):
            continue
        for f in sorted(os.listdir(p)):
            if not f.startswith("CONTRACT"):
                continue
            full = os.path.join(p, f)
            digest = hashlib.sha256(open(full, "rb").read()).hexdigest()
            # A contract is frozen if git has it and the working copy is unmodified.
            dirty = _run("git", "status", "--porcelain", "--", f"{d}/{f}")
            out.append({"path": f"{d}/{f}", "sha256": digest,
                        "modified_since_commit": bool(dirty)})
    return out


# ---- evidence -------------------------------------------------------------------------

def evidence_status():
    """
    Live logs and their sidecar checkpoints, plus whether every COMMITTED checkpoint still
    corresponds to a live one. Never scans a log -- these are stat and sidecar reads only.
    """
    live, live_hashes = [], {}
    if os.path.isdir(EVIDENCE):
        for dirpath, _, files in os.walk(EVIDENCE):
            for f in sorted(files):
                if not f.endswith(".jsonl"):
                    continue
                logp = os.path.join(dirpath, f)
                cp = logp + ".checkpoint"
                rec = {"log": os.path.relpath(logp, EVIDENCE),
                       "size_bytes": os.path.getsize(logp),
                       "log_mtime": datetime.fromtimestamp(
                           os.path.getmtime(logp), timezone.utc).isoformat()}
                if os.path.exists(cp):
                    try:
                        c = json.load(open(cp))
                        rec["events"] = c.get("event_count")
                        rec["checkpoint_updated"] = c.get("updated_at")
                        rec["checkpoint_age"] = _age(c.get("updated_at", ""))
                        rec["checkpoint_behind_log"] = (
                            os.path.getmtime(cp) < os.path.getmtime(logp) - 60)
                        live_hashes[c.get("last_hash")] = rec["log"]
                    except Exception as e:
                        rec["checkpoint"] = f"{UNKNOWN}: unreadable ({e!r})"
                else:
                    rec["checkpoint"] = "MISSING"
                live.append(rec)
    else:
        return {"error": f"{UNKNOWN}: no evidence directory at {EVIDENCE}"}

    committed = []
    for d in ("market/evidence", "recorder/evidence"):
        p = os.path.join(ROOT, d)
        if not os.path.isdir(p):
            continue
        for dirpath, _, files in os.walk(p):
            for f in sorted(files):
                if not f.endswith(".checkpoint"):
                    continue
                fp = os.path.join(dirpath, f)
                try:
                    c = json.load(open(fp))
                except Exception as e:
                    committed.append({"file": os.path.relpath(fp, ROOT),
                                      "state": f"{UNKNOWN}: unreadable ({e!r})"})
                    continue
                h = c.get("last_hash")
                committed.append({
                    "file": os.path.relpath(fp, ROOT),
                    "events": c.get("event_count"),
                    "matches_live": live_hashes.get(h),
                    "state": "current" if h in live_hashes else "NO LIVE LOG AT THIS HASH",
                })
    return {"live": live, "committed": committed}


# ---- recorder -------------------------------------------------------------------------

def recorder_status():
    out = _run("pgrep", "-af", "recorder/run.py")
    if out is None:
        return {"running": False, "detail": "no recorder process found"}
    return {"running": True, "processes": out.splitlines()}


# ---- repository -----------------------------------------------------------------------

def repo_status():
    dirty = _run("git", "status", "--porcelain")
    last = _run("git", "log", "-1", "--format=%h %ad %s", "--date=short")
    return {
        "last_commit": last or UNKNOWN,
        "uncommitted": [l for l in (dirty or "").splitlines() if l.strip()],
        "clean": dirty == "" if dirty is not None else None,
    }


def experiments_status():
    d = os.path.join(ROOT, "research", "experiments")
    ex = sorted(f for f in os.listdir(d) if f[0].isdigit()) if os.path.isdir(d) else []
    dd = os.path.join(ROOT, "research", "decisions")
    de = sorted(f for f in os.listdir(dd) if f[0].isdigit()) if os.path.isdir(dd) else []
    return {"experiments": ex, "decisions": de}


# ---- report ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Forward collectors
# ---------------------------------------------------------------------------------------
#
# Genesis became a COLLECTION project on 2026-08-19. Every remaining open question now
# depends on unattended jobs running for weeks or months, and nothing was watching them.
#
# The failure this is aimed at is specific and was named in
# research/next-phase-review-2026-08-19.md: a cron that fires on schedule and appends
# NOTHING. ECON-1 needs ~90 days; a silent stall discovered at read time in November costs
# the project's most valuable experiment and the three months with it.
#
# So two independent things are checked per collector, because either can fail alone:
#   RAN      -- the job's log was touched within its cadence (did cron fire at all?)
#   ADVANCED -- the newest record in the data is younger than its cadence (did it produce?)
#
# Stateless by construction: staleness is read from record timestamps already in the data,
# never from a watermark this module would have to write. DR0005 forbids writing anything.

COLLECTORS = [
    {"name": "econ1", "cadence_h": 24,
     "log": f"{EVIDENCE}/econ1/collect.log",
     "data": f"{EVIDENCE}/econ1/observations.jsonl",
     # ECON-1 evaluates decision points from 2026-08-20 at a 1-day horizon, so the first
     # outcome is only KNOWN on the 21st. Before then an empty file is correct, not broken.
     "advance_from": "2026-08-21",
     "why": "ECON-1 forward test; ~270 points, first read ~mid-Nov"},
    {"name": "liqmap", "cadence_h": 2,
     "log": f"{EVIDENCE}/liqmap/collect2.log",
     "data": f"{EVIDENCE}/liqmap/snapshots-liq2.jsonl",
     "why": "LIQ-2 archive; clearinghouseState has no history, an uncollected hour is lost"},
    {"name": "hl2", "cadence_h": 1,
     # A long-running recorder writes recorder.out only at start and stop, so using it as the
     # RAN signal reports a healthy recorder as stalled forever. For continuous recorders the
     # data file IS the liveness signal -- the same choice already made for q5.
     "log": f"{EVIDENCE}/hl2/btc-l2book.jsonl",
     "data": f"{EVIDENCE}/hl2/btc-l2book.jsonl",
     "why": "Hyperliquid book at nSigFigs=3 (+/-2.7%); tests whether Binance depth physics transfers"},
    {"name": "q5", "cadence_h": 1,
     "log": f"{EVIDENCE}/q5/btcusdt-q5.jsonl",
     "data": f"{EVIDENCE}/q5/btcusdt-q5.jsonl",
     # A collector that has finished its job must stop being an alarm. q5 closes ~25 Aug and
     # without this would report STALLED forever, which trains the reader to ignore the
     # monitor -- the failure mode that makes monitors worthless.
     "advance_until": "2026-08-26",
     "why": "COND-1 recording; closes ~25 Aug"},
]


def _last_append(path):
    """
    When the data file was last APPENDED TO, in epoch seconds.

    Deliberately mtime rather than a parsed record timestamp. The first version of this read
    the tail 64 KB and parsed the last JSON line; LIQ-2 rows carry 2,342 positions and run to
    ~500 KB each, so the tail was a truncated line, the parse failed, and a healthy collector
    was reported STALLED. A monitor that cries wolf is worse than no monitor.

    mtime is also the signal that actually matters here: a job that fires and appends nothing
    leaves mtime untouched, which is exactly the failure this is aimed at.
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    return os.path.getmtime(path)


def collectors_status():
    now = datetime.now(timezone.utc).timestamp()
    out = []
    for c in COLLECTORS:
        rec = {"name": c["name"], "why": c["why"], "cadence_h": c["cadence_h"]}
        # grace of 2x cadence: one missed run is late, two is a stall worth waking someone for
        limit = c["cadence_h"] * 3600 * 2

        if os.path.exists(c["log"]):
            age = now - os.path.getmtime(c["log"])
            rec["ran_h_ago"] = round(age / 3600, 2)
            rec["ran"] = "OK" if age <= limit else "STALLED"
        else:
            rec["ran"] = UNKNOWN
            rec["ran_detail"] = "no log; the job has never run"

        newest = _last_append(c["data"])
        due = True
        if c.get("advance_from"):
            start = datetime.fromisoformat(c["advance_from"] + "T00:00:00+00:00").timestamp()
            due = now >= start
            rec["advance_due_from"] = c["advance_from"]
        ended = False
        if c.get("advance_until"):
            stop = datetime.fromisoformat(c["advance_until"] + "T00:00:00+00:00").timestamp()
            ended = now >= stop
            rec["advance_due_until"] = c["advance_until"]
        if ended:
            rec["advanced"] = "complete"
            rec["ran"] = "complete"
        elif not due:
            rec["advanced"] = "not yet due"
        elif newest is None:
            rec["advanced"] = "STALLED"
            rec["advanced_detail"] = "no records, and data was due by now"
        else:
            age = now - newest
            rec["advanced_h_ago"] = round(age / 3600, 2)
            rec["advanced"] = "OK" if age <= limit else "STALLED"

        rec["verdict"] = ("complete" if rec.get("advanced") == "complete"
                          else "STALLED" if "STALLED" in (rec.get("ran"), rec.get("advanced"))
                          else UNKNOWN if UNKNOWN in (rec.get("ran"), rec.get("advanced"))
                          else "OK")
        out.append(rec)
    return out


def gather():
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ledger": ledger_status(),
        "contracts": contracts_status(),
        "evidence": evidence_status(),
        "recorder": recorder_status(),
        "repo": repo_status(),
        "records": experiments_status(),
        "collectors": collectors_status(),
    }


def render(s):
    L = ["GENESIS — WHERE THINGS STAND", "=" * 64, f"generated  {s['generated_at']}", ""]

    lg = s["ledger"]
    L.append("TRIAL LEDGER")
    if "error" in lg:
        L.append(f"  {lg['error']}")
    else:
        ok = lg["verify"].get("ok")
        L.append(f"  chain     {'verified' if ok else 'FAILED: ' + str(lg['verify'])}")
        L.append(f"  declared  {lg['declared']}   recorded {lg['recorded']}   "
                 f"outstanding {len(lg['outstanding'])}")
        for t in lg["outstanding"]:
            L.append(f"    OUTSTANDING {t['trial_id']}  {t['family']}")
            L.append(f"      asks: {t['question']}")
    L.append("")

    L.append("CONTRACTS")
    for c in s["contracts"]:
        flag = "  MODIFIED SINCE COMMIT" if c["modified_since_commit"] else ""
        L.append(f"  {c['path']:<34} {c['sha256'][:16]}…{flag}")
    L.append("")

    ev = s["evidence"]
    L.append("EVIDENCE")
    if "error" in ev:
        L.append(f"  {ev['error']}")
    else:
        for r in ev["live"]:
            size = f"{r['size_bytes']/1e9:.2f} GB" if r["size_bytes"] > 1e9 else \
                   f"{r['size_bytes']/1e6:.1f} MB"
            L.append(f"  {r['log']:<34} {size:>9}  events {r.get('events', '?')}"
                     f"  cp {r.get('checkpoint_age') or r.get('checkpoint', '?')}")
            if r.get("checkpoint_behind_log"):
                L.append("      ^ checkpoint is OLDER than the log — it may not describe it")
        L.append("  committed checkpoints:")
        for c in ev["committed"]:
            mark = "ok" if c.get("state") == "current" else "**"
            L.append(f"    {mark} {c['file']:<44} {c.get('state')}")
    L.append("")

    rc = s["recorder"]
    L.append("RECORDER")
    if rc["running"]:
        for p in rc["processes"]:
            L.append(f"  RUNNING  {p}")
    else:
        L.append("  not running")
    L.append("")

    rp = s["repo"]
    L.append("REPOSITORY")
    L.append(f"  last commit  {rp['last_commit']}")
    if rp["uncommitted"]:
        L.append(f"  UNCOMMITTED  {len(rp['uncommitted'])} file(s):")
        for u in rp["uncommitted"]:
            L.append(f"    {u}")
    else:
        L.append("  working tree clean")
    L.append("")

    L.append("RECORDS")
    L.append(f"  experiments  {len(s['records']['experiments'])}  "
             f"(latest {s['records']['experiments'][-1] if s['records']['experiments'] else '—'})")
    L.append(f"  decisions    {len(s['records']['decisions'])}  "
             f"(latest {s['records']['decisions'][-1] if s['records']['decisions'] else '—'})")
    L.append("")
    L.append("Provenance:  .venv/bin/python provenance.py            what rests on what")
    L.append("             provenance.py --rests-on <file>          before retracting anything")
    L.append("")
    L.append("This layer reports. It does not decide — DR0005.")
    L.append("")
    L.append("FORWARD COLLECTORS")
    for c in s.get("collectors", []):
        mark = {"OK": "  ok  ", "STALLED": "  !!  ",
                "complete": "  --  "}.get(c["verdict"], "  ??  ")
        L.append(f"{mark}{c['name']:<8} {c['verdict']}")
        L.append(f"          ran {c.get('ran')}"
                 + (f" ({c['ran_h_ago']}h ago)" if "ran_h_ago" in c else "")
                 + f"   advanced {c.get('advanced')}"
                 + (f" ({c['advanced_h_ago']}h ago)" if "advanced_h_ago" in c else ""))
        for k in ("ran_detail", "advanced_detail"):
            if k in c:
                L.append(f"          {c[k]}")
        L.append(f"          {c['why']}")

    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    s = gather()
    print(json.dumps(s, indent=1, default=str) if "--json" in argv else render(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
