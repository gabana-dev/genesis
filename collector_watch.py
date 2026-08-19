"""
Genesis collector watch — turns the orientation layer's collector report into an alarm.

WHY THIS EXISTS
    Genesis became a COLLECTION project on 2026-08-19: ECON-1 needs ~90 days of unattended
    daily runs before its first admissible read. A cron that fires on schedule while appending
    nothing would surface only in November, costing the project's most valuable experiment and
    the three months with it. See research/next-phase-review-2026-08-19.md §12.

    status.py reports on demand. This makes a stall LOUD, which a report nobody runs cannot do.

WHAT IT MAY NOT DO
    Report only — DR0005. It never restarts, repairs, or writes to any evidence file. Its only
    side effects are its own log and a desktop notification.

SILENCE IS NEVER A PASS
    The first version of this was shell with embedded Python. The Python had a quoting error,
    failed on every run, and the script exited 0 and logged "all collectors ok" -- a monitor
    that reported health because it was broken. Every failure path here is therefore LOUD:
    if the check cannot be performed, that is an alarm, not a pass.

Run:  .venv/bin/python collector_watch.py          (exit 0 healthy, 1 alarm)
"""

import os
import sys
import traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LOG = os.path.expanduser("~/genesis-evidence/collector-watch.log")
HEALTHY = ("OK", "complete")


def problems():
    """Lines describing anything not healthy. Raises rather than returning empty on failure."""
    import status
    collectors = status.collectors_status()
    if not collectors:
        raise RuntimeError("collectors_status() returned nothing; the watch cannot verify")
    return [f"{c['name']}: {c['verdict']} "
            f"(ran {c.get('ran')}, advanced {c.get('advanced')})"
            for c in collectors if c["verdict"] not in HEALTHY]


def notify(title, message):
    """Desktop notification. Best-effort: its failure must never mask a real alarm."""
    try:
        import subprocess
        subprocess.run(
            ["osascript", "-e",
             f'display notification {message[:180]!r} with title {title!r} '
             f'sound name "Basso"'],
            capture_output=True, timeout=10)
    except Exception:
        pass


def main():
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        bad = problems()
    except Exception:
        # A watch that cannot check is a failed watch, and it says so.
        detail = traceback.format_exc().strip().splitlines()[-1]
        line = f"{stamp}  WATCH FAILED  {detail}"
        print(line)
        _append(line)
        notify("Genesis: collector watch FAILED", detail)
        return 1

    if bad:
        line = f"{stamp}  STALLED\n    " + "\n    ".join(bad)
        print(line)
        _append(line)
        notify("Genesis: collector stalled", "; ".join(bad))
        return 1

    line = f"{stamp}  all collectors ok"
    print(line)
    _append(line)
    return 0


def _append(line):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    sys.exit(main())
