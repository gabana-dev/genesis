#!/bin/zsh
# Disk guard, launchd entrypoint. Logic in disk_guard.py -- shell-embedded Python already
# produced one monitor that reported health because it was broken.
cd /Users/gabana/genesis || exit 1
exec .venv/bin/python disk_guard.py
