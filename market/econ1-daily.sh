#!/bin/zsh
# ECON-1 daily forward collection. Installed in the user crontab; see CONTRACT-economics.md.
# Appends only; never evaluates. Reading the result is a deliberate human act, gated by K1.
cd /Users/gabana/genesis || exit 1
LOG=~/genesis-evidence/econ1/collect.log
mkdir -p ~/genesis-evidence/econ1
{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  .venv/bin/python -c "import sys; sys.path.insert(0,'market'); import econ1, json; print(json.dumps(econ1.collect()))"
} >> "$LOG" 2>&1
