#!/bin/zsh
# One alert pass. Scheduled every 5 minutes.
#
# The token lives in ~/genesis-private/alerts/env, never in this repo -- the repo is public.
# Without it the engine cannot deliver, so this exits loudly rather than logging a quiet success:
# a watch that cannot check is a failed watch.
cd /Users/gabana/genesis || exit 1
ENVFILE=~/genesis-private/alerts/env
[[ -f $ENVFILE ]] || { echo "$(date -u +%FT%TZ) NO ENV FILE at $ENVFILE" >&2; exit 1; }
set -a; source $ENVFILE; set +a

LOG=~/genesis-private/alerts/run.log
{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  .venv/bin/python product/alerts.py
} >> "$LOG" 2>&1
