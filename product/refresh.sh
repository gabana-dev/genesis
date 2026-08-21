#!/bin/zsh
# Regenerate the Genesis surfaces from the latest position snapshot.
#
# Data first, then pages -- the pages are built FROM the JSON, so the order matters. generate.py
# writes into web/public/data/, which the Astro build copies into docs/ alongside the HTML.
#
# `build:fast` skips `astro check`: the types cannot change between data refreshes, and the data
# contract itself is validated at build time by web/src/lib/data.ts regardless. A renamed field in
# the engine fails this build rather than publishing a page that renders `undefined%`.
# launchd runs with a minimal environment. node lives in /usr/local/bin and the build cannot
# resolve it from a bare PATH, so pin it rather than depend on a login shell's profile.
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
cd /Users/gabana/genesis || exit 1
LOG=~/genesis-evidence/product/refresh.log
mkdir -p ~/genesis-evidence/product
{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  .venv/bin/python product/generate.py \
    && (cd web && npm run build:fast) \
    || { echo "  BUILD FAILED — not publishing"; exit 1; }
  # Publish only when the output actually changed. Committing an identical rebuild every 15
  # minutes would bury the real history under thousands of empty commits.
  if [[ -n "$(git status --porcelain docs web/public/data)" ]]; then
    # BOTH halves are needed and each fixed a real failure:
    #   `git add` picks up files that are new (a first-ever alerts.html is untracked, and
    #     --only alone silently skipped it, publishing a page the site linked but never shipped).
    #   `--only` scopes the commit to these paths, because plain `git commit` commits the WHOLE
    #     index -- this job once swept a half-finished refactor's staged deletions into a
    #     "site: refresh" commit and pushed it.
    # -m comes BEFORE the `--`, or the message is parsed as a pathspec and the commit fails.
    git add -- docs web/public/data
    git commit -q --only -m "site: refresh $(date -u +%Y-%m-%dT%H:%MZ)" -- docs web/public/data \
      || { echo "  COMMIT FAILED — not publishing"; exit 1; }
    git push -q && echo "  published" || { echo "  PUSH FAILED"; exit 1; }
  else
    echo "  no change"
  fi
} >> "$LOG" 2>&1
