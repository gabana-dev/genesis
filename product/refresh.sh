#!/bin/zsh
# Regenerate the Genesis surfaces from the latest position snapshot.
# Data first, then pages -- the pages are built FROM the JSON, so the order matters.
cd /Users/gabana/genesis || exit 1
LOG=~/genesis-evidence/product/refresh.log
mkdir -p ~/genesis-evidence/product
{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  .venv/bin/python product/generate.py && .venv/bin/python product/site.py
  # Publish only when the data actually changed. Committing an identical rebuild every 15
  # minutes would bury the real history under thousands of empty commits.
  if [[ -n "$(git status --porcelain docs)" ]]; then
    git add docs
    git commit -q -m "site: refresh $(date -u +%Y-%m-%dT%H:%MZ)"
    git push -q && echo "  published"
  else
    echo "  no change"
  fi
} >> "$LOG" 2>&1
