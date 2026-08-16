#!/bin/bash
# Overnight DhlA campaign driver. Runs each stage as its own process (see
# dhla_overnight_campaign.py's docstring for why), stopping and logging clearly
# if any stage fails rather than silently continuing on broken input.
set -e
PY=~/biocompiler/venv/bin/python3
SCRIPT=~/biocompiler/dhla_overnight_campaign.py
LOG=~/biocompiler/dhla_overnight.log

echo "=== DhlA overnight campaign starting $(date) ===" | tee -a "$LOG"

for STAGE in 1 2 3 4 5; do
  echo "=== Launching stage $STAGE at $(date) ===" | tee -a "$LOG"
  $PY "$SCRIPT" "$STAGE" >> "$LOG" 2>&1
  EC=$?
  if [ $EC -ne 0 ]; then
    echo "=== STAGE $STAGE FAILED (exit $EC) at $(date), stopping campaign ===" | tee -a "$LOG"
    exit $EC
  fi
  echo "=== Stage $STAGE finished cleanly at $(date) ===" | tee -a "$LOG"
done

echo "=== DhlA overnight campaign fully complete at $(date) ===" | tee -a "$LOG"
