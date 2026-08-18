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

def gather():
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ledger": ledger_status(),
        "contracts": contracts_status(),
        "evidence": evidence_status(),
        "recorder": recorder_status(),
        "repo": repo_status(),
        "records": experiments_status(),
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
    L.append("This layer reports. It does not decide — DR0005.")
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    s = gather()
    print(json.dumps(s, indent=1, default=str) if "--json" in argv else render(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
