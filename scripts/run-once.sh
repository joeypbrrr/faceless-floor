#!/usr/bin/env bash
# One research cycle; with --push commits data/ and pushes once.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .run
exec 9>.run/cycle.lock
flock -n 9 || { echo 'Another cycle is already running'; exit 1; }
python3 research/pipeline.py
if [[ " $* " == *" --push "* ]]; then
  git add data/live.json
  if ! git diff --cached --quiet; then
    git commit -q -m "Research snapshot $(TZ=America/New_York date '+%Y-%m-%d %-I:%M %p %Z')"
    git push -q origin main
  fi
fi
