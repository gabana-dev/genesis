#!/bin/sh
# One LIQ-2 scan. $1 is the tier: fast or deep.
#
# WHY THIS WRAPPER EXISTS. The first version put `flock -n` straight in ExecStart with
# SuccessExitStatus=1, so a lock skip and a genuine python failure produced the IDENTICAL journal
# line -- "Deactivated successfully" in zero seconds. That is the silent-pass antipattern this
# project keeps rediscovering: a job reporting success it has not earned.
#
# `flock -E 99` gives the skip its own exit code, so the two cases can never be confused again.
set -u
LOCK=/home/genesis/genesis-evidence/liqmap/.scan.lock

/usr/bin/flock -n -E 99 "$LOCK" /usr/bin/python3 /opt/genesis/market/liqmap.py "$1"
rc=$?

if [ "$rc" -eq 99 ]; then
  # Not a failure: the other tier holds the lock. -n rather than waiting, because a fast scan
  # queued behind a 2h22m deep scan would run against a market that has long since moved.
  echo "skipped: the $1 tier could not take the scan lock; another scan is in progress"
  exit 0
fi
exit "$rc"
