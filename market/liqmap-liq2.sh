#!/bin/zsh
# LIQ-2 two-tier forced-flow map. See market/CONTRACT-liquidation-map-2.md.
#   deep  -- every 6h, whole frozen universe (~2h22m), re-ranks the fast set
#   fast  -- hourly, top 300 by position notional (~8m)
# Appends only; never evaluates. K1 gates any read at 270 observations over >=30 days.
# The lock matters: a deep scan runs for hours and a fast scan starting inside it would
# double the request rate and throttle both.
TIER=${1:-fast}
cd /Users/gabana/genesis || exit 1
LOCK=~/genesis-evidence/liqmap/scan.lock
mkdir -p ~/genesis-evidence/liqmap
# A bare mkdir lock cannot survive a crash: the EXIT trap does not fire when the process is
# killed by shutdown, and the leftover directory then blocks every scan forever. That happened
# on 2026-08-19 -- a reboot during a fast scan cost 4 hours of archive that cannot be
# backfilled. So the lock carries its owner's PID and is reclaimed when the owner is gone or
# the lock is older than any legitimate scan.
MAX_LOCK_AGE=10800          # 3h: a deep scan takes ~2h22m, so anything older is dead
if ! mkdir "$LOCK" 2>/dev/null; then
  OWNER=$(cat "$LOCK/pid" 2>/dev/null)
  AGE=$(( $(date +%s) - $(stat -f %m "$LOCK" 2>/dev/null || date +%s) ))
  if [[ -n "$OWNER" ]] && kill -0 "$OWNER" 2>/dev/null && (( AGE < MAX_LOCK_AGE )); then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $TIER skipped: scan $OWNER in progress (${AGE}s)"       >> ~/genesis-evidence/liqmap/collect2.log
    exit 0
  fi
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) RECLAIMED stale lock (owner=${OWNER:-none} age=${AGE}s)"     >> ~/genesis-evidence/liqmap/collect2.log
  rm -rf "$LOCK"
  mkdir "$LOCK" || exit 0
fi
echo $$ > "$LOCK/pid"
trap 'rm -rf "$LOCK"' EXIT
{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) $TIER ==="
  .venv/bin/python market/liqmap.py "$TIER"
} >> ~/genesis-evidence/liqmap/collect2.log 2>&1
