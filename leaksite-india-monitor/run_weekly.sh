#!/usr/bin/env bash
# Weekly unattended run for leaksite-india-monitor.
#
# Fetches both feeds live (a cron running --offline would re-analyse the same cached
# JSON forever and never see a new victim), writes a timestamped log, and prints a
# short delta so the log is worth reading: new review-queue rows, and the India count.
#
# Install:  crontab -e   ->   30 6 * * 1  /path/to/run_weekly.sh
# Manual:   ./run_weekly.sh

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$REPO/logs"
LOG="$LOG_DIR/$(date -u +%Y%m%dT%H%M%SZ).log"
LOCK="$REPO/.run_weekly.lock"
KEEP_LOGS=26          # ~6 months of weekly logs
KEEP_RAW_DAYS=120     # raw cache older than this is dropped (window is 90 days)

mkdir -p "$LOG_DIR"

# The run takes ~4 minutes (1 req/min rate limit). Never let two overlap: both would
# write review_queue.csv and the second could clobber the first's appended rows.
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "$(date -uIs) another run holds the lock — skipping" >> "$LOG"
  exit 0
fi

cd "$REPO" || exit 1

{
  echo "=== leaksite-india-monitor weekly run $(date -uIs)"

  before_queue=$(wc -l < review_queue.csv 2>/dev/null || echo 0)
  before_verdicts=$(python3 -c "
import csv,sys
try:
    rows=list(csv.DictReader(open('review_queue.csv')))
    print(sum(1 for r in rows if (r.get('my_verdict') or '').strip()))
except Exception: print(0)" 2>/dev/null)

  python3 leaksite_india_monitor.py
  status=$?

  after_queue=$(wc -l < review_queue.csv 2>/dev/null || echo 0)
  after_verdicts=$(python3 -c "
import csv
rows=list(csv.DictReader(open('review_queue.csv')))
print(sum(1 for r in rows if (r.get('my_verdict') or '').strip()))" 2>/dev/null)

  echo
  echo "=== delta"
  echo "exit status:        $status"
  echo "review queue rows:  $before_queue -> $after_queue  (new: $(( after_queue - before_queue )))"
  echo "verdicts on file:   $before_verdicts -> $after_verdicts"
  if [ "$after_queue" -gt "$before_queue" ]; then
    echo "ACTION: $(( after_queue - before_queue )) new row(s) need a verdict."
    echo "        python3 review_server.py  ->  http://127.0.0.1:8765/review_editor.html"
  fi

  # Prune: raw responses older than the window are dead weight, but keep the newest
  # file per tag regardless so --offline always has something to work from.
  for dir in raw/*/; do
    [ -d "$dir" ] || continue
    for tag in $(ls "$dir" | sed 's/^[^_]*__//' | sort -u); do
      ls -t "$dir"*"__$tag" 2>/dev/null | tail -n +2 | while read -r old; do
        [ -n "$(find "$old" -mtime +$KEEP_RAW_DAYS 2>/dev/null)" ] && rm -f "$old"
      done
    done
  done

  ls -t "$LOG_DIR"/*.log 2>/dev/null | tail -n +$((KEEP_LOGS + 1)) | xargs -r rm -f

  echo "=== done $(date -uIs)"
  exit $status
} >> "$LOG" 2>&1
