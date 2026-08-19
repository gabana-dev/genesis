"""
Disk guard — stops the q5 recorder cleanly before the disk runs out, rather than after.

WHY THIS EXISTS
    q5 grows 6.1 GB/day and the volume has ~6 GB free. Without intervention it fills the disk
    in under a day, and a full disk means a truncated final write, a broken checkpoint sidecar,
    and an unstable machine. Losing the recording is bad; losing it AND corrupting the evidence
    chain AND wedging the laptop is worse.

    Discovered 2026-08-19. It is the operational-continuity failure named in
    research/next-phase-review-2026-08-19.md §12, arriving eight hours later as disk rather
    than as a silent cron. The collector watch checks whether collectors ADVANCE. Nothing
    checked whether they still CAN.

HOW THIS DIFFERS FROM collector_watch.py, AND WHY IT IS A SEPARATE FILE
    collector_watch reports and never acts -- DR0005. This one ACTS: it terminates a running
    experiment. That is deliberately not mixed into the orientation layer.

    The action is operational safety, never a research judgement. It does not decide whether an
    experiment is worth continuing, only that an unclean death is worse than a clean one. It
    stops exactly one declared target and nothing else.

SIGTERM, NEVER SIGKILL
    recorder/run.py has `finally` blocks that write the checkpoint. SIGTERM lets them run.
    SIGKILL would produce precisely the corruption this exists to prevent, so it is never sent
    even if the process ignores the term.

Run:  .venv/bin/python disk_guard.py [--dry-run]
"""

import os
import shutil
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

VOLUME = "/System/Volumes/Data"
LOG = os.path.expanduser("~/genesis-evidence/disk-guard.log")

WARN_GB = 3.0        # notify loudly
STOP_GB = 1.0        # stop the target cleanly

# Exactly one target. Matched on the full command line, so nothing else can be hit by accident.
TARGET_MATCH = "recorder/run.py spot-perp"
TARGET_NAME = "q5 recorder"


def free_gb():
    return shutil.disk_usage(VOLUME).free / 1e9


def find_target():
    """PIDs whose command line contains TARGET_MATCH. Empty is a valid answer, not an error."""
    out = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True).stdout
    pids = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        pid, _, cmd = line.partition(" ")
        if TARGET_MATCH in cmd and "disk_guard" not in cmd:
            try:
                pids.append(int(pid))
            except ValueError:
                pass
    return pids


def notify(title, message):
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification {message[:180]!r} with title {title!r} '
                        f'sound name "Basso"'], capture_output=True, timeout=10)
    except Exception:
        pass


def _log(line):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")
    print(line)


def stop(pids, dry_run=False):
    """SIGTERM each target, then confirm. Never escalates to SIGKILL."""
    if dry_run:
        return f"DRY RUN: would SIGTERM {pids}"
    for p in pids:
        try:
            os.kill(p, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError:
            return f"PERMISSION DENIED sending SIGTERM to {p}"
    # give the finally blocks time to write the checkpoint
    for _ in range(30):
        time.sleep(1)
        if not find_target():
            return f"stopped cleanly: {pids}"
    return (f"SIGTERM sent to {pids} but still running after 30s. "
            f"NOT escalating to SIGKILL -- that is what corrupts the log. Manual attention.")


def main(argv=None):
    argv = argv or sys.argv[1:]
    dry = "--dry-run" in argv
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        gb = free_gb()
        pids = find_target()
    except Exception:
        detail = traceback.format_exc().strip().splitlines()[-1]
        _log(f"{stamp}  GUARD FAILED  {detail}")
        notify("Genesis: disk guard FAILED", detail)
        return 1

    state = f"{gb:.2f} GB free, {TARGET_NAME} {'running ' + str(pids) if pids else 'not running'}"

    if gb <= STOP_GB and pids:
        result = stop(pids, dry)
        _log(f"{stamp}  STOP THRESHOLD  {state}\n    {result}")
        notify("Genesis: q5 STOPPED — disk full",
               f"{gb:.2f} GB free. {result}")
        return 1

    if gb <= WARN_GB:
        _log(f"{stamp}  LOW DISK  {state}")
        notify("Genesis: disk low",
               f"{gb:.2f} GB free. q5 stops automatically at {STOP_GB:.0f} GB.")
        return 1

    _log(f"{stamp}  ok  {state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
