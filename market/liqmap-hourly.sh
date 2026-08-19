#!/bin/zsh
# LIQ-1 hourly snapshot. See market/CONTRACT-liquidation-map.md.
# Appends only; never evaluates. K1 gates any read at 270 observations over >=30 days.
cd /Users/gabana/genesis || exit 1
LOG=~/genesis-evidence/liqmap/collect.log
mkdir -p ~/genesis-evidence/liqmap
{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  .venv/bin/python -c "import sys; sys.path.insert(0,'market'); import liqmap, json; print(json.dumps(liqmap.collect()))"
} >> "$LOG" 2>&1
