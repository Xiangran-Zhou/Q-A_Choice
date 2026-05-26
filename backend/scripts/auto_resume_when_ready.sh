#!/usr/bin/env bash
# Polls the Gemini API once an hour with a tiny test request. When the
# request succeeds (rolling 24-hour quota window has slid enough to
# re-admit traffic), launches run_overnight_build.sh and exits.
#
# Intended use: after run_overnight_build.sh aborted with exit 2
# (daily quota wall), kick this off in the background instead of
# trying to manually time when the window will reopen.
#
# Usage:
#   nohup bash backend/scripts/auto_resume_when_ready.sh > /dev/null 2>&1 &
#   disown
#
# Monitor:
#   tail -f /tmp/lightrag_autoresume.log
#
# Abort:
#   kill -TERM "$(cat /tmp/lightrag_autoresume.pid)"

set -u

LOG_FILE="${LIGHTRAG_AUTORESUME_LOG:-/tmp/lightrag_autoresume.log}"
PID_FILE="${LIGHTRAG_AUTORESUME_PID:-/tmp/lightrag_autoresume.pid}"
POLL_INTERVAL_SEC="${LIGHTRAG_POLL_INTERVAL:-3600}"  # default 1 hour
MAX_POLLS="${LIGHTRAG_MAX_POLLS:-48}"                # safety cap: 48 polls = 2 days

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$(cd "$BACKEND_DIR/.." && pwd)"

trap 'kill 0 2>/dev/null' EXIT INT TERM

echo "$$" > "$PID_FILE"

{
  echo "================================================================"
  echo "Auto-resume polling started"
  echo "  Started:        $(date)"
  echo "  Wrapper PID:    $$"
  echo "  Poll interval:  ${POLL_INTERVAL_SEC}s"
  echo "  Max polls:      $MAX_POLLS"
  echo "  Will launch:    $SCRIPT_DIR/run_overnight_build.sh once quota clears"
  echo "================================================================"
} >> "$LOG_FILE"

cd "$BACKEND_DIR" || {
  echo "FATAL: cannot cd to $BACKEND_DIR" >> "$LOG_FILE"
  rm -f "$PID_FILE"
  exit 1
}

poll=0
while [ "$poll" -lt "$MAX_POLLS" ]; do
  poll=$((poll + 1))
  {
    echo
    echo "[Poll $poll/$MAX_POLLS]  $(date)"
  } >> "$LOG_FILE"

  # One small Gemini call. Uses google.genai directly with a unique
  # nonce prompt to bypass any caching layer.
  # Exit codes:
  #   0 → quota available, time to launch
  #   1 → quota still exhausted, keep polling
  #   2 → some other error, log and keep polling (don't kill the whole thing)
  #
  # NB: we capture $? *before* any subsequent `if` test. The earlier shape
  # (`if uv run ...; then ...; fi; status=$?`) silently reset $? to 0 after
  # the fi, producing a misleading "Unexpected status=0" log line on
  # quota-exhausted polls (fixed 2026-05-25).
  uv run python -c "
import os, sys, time
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv(usecwd=True))
from google import genai

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
nonce = int(time.time())
try:
    r = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f'Reply with the digit {nonce % 10}',
    )
    sys.exit(0)
except Exception as e:
    msg = str(e)
    if 'generate_requests_per_model_per_day' in msg or 'RESOURCE_EXHAUSTED' in msg:
        sys.exit(1)
    sys.stderr.write(f'Unexpected error: {msg}\n')
    sys.exit(2)
" >> "$LOG_FILE" 2>&1
  poll_status=$?

  if [ "$poll_status" -eq 0 ]; then
    {
      echo
      echo "=== Quota cleared on poll $poll at $(date). Launching build wrapper. ==="
    } >> "$LOG_FILE"

    # Launch the build wrapper detached so it survives this script exiting.
    nohup bash "$SCRIPT_DIR/run_overnight_build.sh" > /dev/null 2>&1 &
    disown
    sleep 3
    {
      echo "Build wrapper launched. PID: $(cat /tmp/lightrag_build.pid 2>/dev/null || echo 'unknown')"
      echo "Auto-resume finished its job at $(date)"
    } >> "$LOG_FILE"

    rm -f "$PID_FILE"
    exit 0
  elif [ "$poll_status" -eq 1 ]; then
    echo "  Still quota-exhausted, sleeping ${POLL_INTERVAL_SEC}s" >> "$LOG_FILE"
  else
    echo "  Unexpected exit $poll_status, sleeping anyway and retrying" >> "$LOG_FILE"
  fi
  sleep "$POLL_INTERVAL_SEC"
done

{
  echo
  echo "!!! Quota still not cleared after $MAX_POLLS polls. Giving up at $(date)"
} >> "$LOG_FILE"
rm -f "$PID_FILE"
exit 1
