#!/bin/zsh
# The subscription bot. Runs continuously; launchd restarts it if it dies.
cd /Users/gabana/genesis || exit 1
ENVFILE=~/genesis-private/alerts/env
[[ -f $ENVFILE ]] || { echo "$(date -u +%FT%TZ) NO ENV FILE at $ENVFILE" >&2; exit 1; }
set -a; source $ENVFILE; set +a
exec .venv/bin/python product/alertbot.py
