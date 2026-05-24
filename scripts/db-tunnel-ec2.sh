#!/usr/bin/env bash
# SSH tunnel: EC2 Docker databases → your Mac (for GUI tools).
# Usage: ./scripts/db-tunnel-ec2.sh start | stop | status
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EC2_ENV="$ROOT/config/db-gui/ec2.env"
if [[ ! -f "$EC2_ENV" ]]; then
  echo "Missing $EC2_ENV — run: cp config/db-gui/ec2.env.example config/db-gui/ec2.env"
  exit 1
fi
# shellcheck source=/dev/null
source "$EC2_ENV"

PID_FILE="$ROOT/.db-tunnel-ec2.pid"
KEY_PATH="$ROOT/$SSH_KEY"

start() {
  if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Tunnel already running (PID $(cat "$PID_FILE"))"
    status
    return 0
  fi

  if [[ ! -f "$KEY_PATH" ]]; then
    echo "Missing SSH key: $KEY_PATH"
    exit 1
  fi

  ssh -f -N \
    -o StrictHostKeyChecking=no \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -i "$KEY_PATH" \
    -L "${POSTGRES_PORT}:127.0.0.1:5432" \
    -L "27018:127.0.0.1:27017" \
    -L "${REDIS_PORT}:127.0.0.1:6379" \
  "ec2-user@${EC2_HOST}"

  sleep 1
  pid=$(pgrep -f "ssh.*${EC2_HOST}.*${POSTGRES_PORT}:127.0.0.1:5432" | head -1 || true)
  if [[ -n "$pid" ]]; then
    echo "$pid" > "$PID_FILE"
  fi

  echo "EC2 database tunnel started."
  echo ""
  echo "  Postgres:  localhost:${POSTGRES_PORT}  (db: ${POSTGRES_DB}, user: ${POSTGRES_USER})"
  echo "  MongoDB:   mongodb://localhost:27018/beauty_catalog"
  echo "  Redis:     localhost:${REDIS_PORT}"
  echo ""
  echo "Open GUI: ./scripts/db-gui.sh ec2"
}

stop() {
  if [[ -f "$PID_FILE" ]]; then
    kill "$(cat "$PID_FILE")" 2>/dev/null || true
    rm -f "$PID_FILE"
  fi
  pkill -f "ssh.*${EC2_HOST}.*${POSTGRES_PORT}:127.0.0.1:5432" 2>/dev/null || true
  echo "EC2 database tunnel stopped."
}

status() {
  pid=""
  if [[ -f "$PID_FILE" ]]; then
    pid=$(cat "$PID_FILE")
  fi
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    :
  else
    pid=$(pgrep -f "ssh.*${EC2_HOST}.*${POSTGRES_PORT}:127.0.0.1:5432" | head -1 || true)
  fi
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "Tunnel: running (PID $pid)"
    echo "  Postgres localhost:${POSTGRES_PORT} | Mongo localhost:27018 | Redis localhost:${REDIS_PORT}"
  else
    echo "Tunnel: not running (use: ./scripts/db-tunnel-ec2.sh start)"
  fi
}

case "${1:-start}" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  *) echo "Usage: $0 start|stop|status"; exit 1 ;;
esac
