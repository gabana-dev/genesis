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
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $TIER skipped: scan in progress" >> ~/genesis-evidence/liqmap/collect2.log
  exit 0
fi
trap 'rmdir "$LOCK"' EXIT
{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) $TIER ==="
  .venv/bin/python market/liqmap.py "$TIER"
} >> ~/genesis-evidence/liqmap/collect2.log 2>&1
