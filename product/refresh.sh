#!/bin/zsh
# Regenerate the Genesis surfaces from the latest position snapshot.
# Data first, then pages -- the pages are built FROM the JSON, so the order matters.
cd /Users/gabana/genesis || exit 1
LOG=~/genesis-evidence/product/refresh.log
mkdir -p ~/genesis-evidence/product
{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  .venv/bin/python product/generate.py && .venv/bin/python product/site.py
} >> "$LOG" 2>&1
