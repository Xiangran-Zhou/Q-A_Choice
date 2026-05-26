#!/usr/bin/env bash
# Overnight wrapper around scripts/build_graph.py.
#
# Designed for unattended multi-hour LightRAG builds:
#   - Every invocation of build_graph.py runs in resume mode (no --reset).
#     LightRAG content-hashes documents and persists per-doc status, so
#     a crashed run picks up where it stopped on the next attempt.
#   - If the build script exits non-zero (network blip, transient API
#     error, etc.), the wrapper retries automatically after a short delay,
#     up to MAX_RESTARTS times.
#   - All output streams to LOG_FILE. The wrapper's own PID is written to
#     PID_FILE so the user can `kill $(cat ...)` to abort the whole job.
#
# Usage:
#   # First time: wipe any prior storage so we start clean.
#   rm -rf backend/lightrag_storage
#
#   # Launch (returns immediately, work continues in background):
#   nohup bash backend/scripts/run_overnight_build.sh > /dev/null 2>&1 &
#   disown
#
#   # Monitor:
#   tail -f /tmp/lightrag_build.log
#
#   # Abort:
#   kill -TERM "$(cat /tmp/lightrag_build.pid)"

set -u

LOG_FILE="${LIGHTRAG_BUILD_LOG:-/tmp/lightrag_build.log}"
PID_FILE="${LIGHTRAG_BUILD_PID:-/tmp/lightrag_build.pid}"
MAX_RESTARTS="${LIGHTRAG_MAX_RESTARTS:-20}"
RESTART_DELAY_SEC="${LIGHTRAG_RESTART_DELAY:-30}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Kill the inner python process if the wrapper itself is killed.
trap 'kill 0 2>/dev/null' EXIT INT TERM

echo "$$" > "$PID_FILE"

{
  echo "================================================================"
  echo "Overnight build wrapper"
  echo "  Started:        $(date)"
  echo "  Wrapper PID:    $$"
  echo "  Backend dir:    $BACKEND_DIR"
  echo "  Max restarts:   $MAX_RESTARTS"
  echo "  Restart delay:  ${RESTART_DELAY_SEC}s"
  echo "================================================================"
} >> "$LOG_FILE"

cd "$BACKEND_DIR" || {
  echo "FATAL: cannot cd to $BACKEND_DIR" >> "$LOG_FILE"
  rm -f "$PID_FILE"
  exit 1
}

attempt=0
while [ "$attempt" -lt "$MAX_RESTARTS" ]; do
  attempt=$((attempt + 1))
  {
    echo
    echo "--- Attempt $attempt/$MAX_RESTARTS  $(date) ---"
  } >> "$LOG_FILE"

  # Capture *this attempt's* output to a temp file so the quota-detection
  # grep below only sees lines this attempt produced. Otherwise the
  # detector would false-positive on 429s left over in the log from
  # earlier days / earlier attempts. (Earlier bug, fixed 2026-05-25.)
  ATTEMPT_LOG=$(mktemp -t lightrag_attempt.XXXXXX)

  if uv run python scripts/build_graph.py >"$ATTEMPT_LOG" 2>&1; then
    cat "$ATTEMPT_LOG" >> "$LOG_FILE"
    rm -f "$ATTEMPT_LOG"
    {
      echo
      echo "=== Build completed successfully on attempt $attempt at $(date) ==="
    } >> "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 0
  fi

  exit_code=$?
  cat "$ATTEMPT_LOG" >> "$LOG_FILE"

  # Quota wall detection — only consider this attempt's lines.
  if grep -q "generate_requests_per_model_per_day" "$ATTEMPT_LOG"; then
    rm -f "$ATTEMPT_LOG"
    {
      echo
      echo "*** Detected daily quota exhaustion on attempt $attempt at $(date)"
      echo "*** Aborting further retries — wait ~24 h for the rolling window"
      echo "*** to slide, then re-run the wrapper (or use auto_resume_when_ready.sh)"
    } >> "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 2
  fi

  rm -f "$ATTEMPT_LOG"
  {
    echo
    echo "*** build_graph.py exited $exit_code on attempt $attempt at $(date)"
    echo "*** sleeping ${RESTART_DELAY_SEC}s before retry"
  } >> "$LOG_FILE"
  sleep "$RESTART_DELAY_SEC"
done

{
  echo
  echo "!!! Giving up after $MAX_RESTARTS failed attempts at $(date)"
} >> "$LOG_FILE"
rm -f "$PID_FILE"
exit 1
