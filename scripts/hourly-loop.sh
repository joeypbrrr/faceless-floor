#!/usr/bin/env bash
# Single supervised hourly runner. flock guarantees only one instance.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p .run
exec 8>.run/scheduler.lock
flock -n 8 || { echo 'Faceless Floor scheduler already running'; exit 1; }
echo $$ > .run/runner.pid
trap 'rm -f .run/runner.pid; exit 0' TERM INT
while true; do
  start=$(date +%s)
  export NEXT_CYCLE_EPOCH=$(( start + 3600 ))
  echo "[$(date '+%F %T %Z')] cycle start" 
  ./scripts/run-once.sh --push || echo "[$(date '+%F %T %Z')] cycle failed"
  echo "$NEXT_CYCLE_EPOCH" > .run/next-cycle-epoch
  waitfor=$(( NEXT_CYCLE_EPOCH - $(date +%s) )); (( waitfor < 60 )) && waitfor=60
  sleep "$waitfor" & wait $!
done
