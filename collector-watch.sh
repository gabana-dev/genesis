#!/bin/zsh
# Genesis collector watch, cron entrypoint. Logic lives in collector_watch.py so that a
# quoting error cannot make the check silently pass -- which is exactly what the first
# shell-embedded version did. Reports only; DR0005.
cd /Users/gabana/genesis || exit 1
exec .venv/bin/python collector_watch.py
