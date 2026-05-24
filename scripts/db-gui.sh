#!/usr/bin/env bash
# Open database GUI tools with connection info for local or EC2.
# Usage: ./scripts/db-gui.sh local | ec2 | connections
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

require_env() {
  local f="$1"
  if [[ ! -f "$f" ]]; then
    echo "Missing $f — run: cp ${f}.example $f"
    exit 1
  fi
}

print_connections() {
  local env_file="$1"
  local label="$2"
  # shellcheck source=/dev/null
  source "$env_file"
  echo ""
  echo "=== $label ==="
  echo "  Postgres:  ${POSTGRES_HOST}:${POSTGRES_PORT}  db=${POSTGRES_DB}  user=${POSTGRES_USER}  (password in config/db-gui/*.env)"
  echo "  MongoDB:   ${MONGODB_URI}"
  echo "  Redis:     ${REDIS_HOST}:${REDIS_PORT}"
  echo "  DBeaver:   ${POSTGRES_JDBC:-jdbc:postgresql://${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}}"
}

open_apps() {
  local mongo_uri="$1"
  local redis_port="$2"

  open -a "DBeaver" 2>/dev/null || open -a "DBeaver Community" 2>/dev/null || true
  open -a "MongoDB Compass" "mongodb-compass://${mongo_uri#mongodb://}" 2>/dev/null || \
    open -a "MongoDB Compass" 2>/dev/null || true
  open -a "Redis Insight" 2>/dev/null || true

  echo ""
  echo "Opened DBeaver, MongoDB Compass, Redis Insight."
  echo "Redis Insight: Add Database → Host ${REDIS_HOST:-localhost} Port ${redis_port}"
}

case "${1:-connections}" in
  local)
    require_env "$ROOT/config/db-gui/local.env"
    print_connections "$ROOT/config/db-gui/local.env" "LOCAL (Mac Docker)"
    open_apps "mongodb://localhost:27017/beauty_catalog" 6379
  ;;
  ec2)
    require_env "$ROOT/config/db-gui/ec2.env"
    "$ROOT/scripts/db-tunnel-ec2.sh" start
    print_connections "$ROOT/config/db-gui/ec2.env" "EC2 (via SSH tunnel)"
    # shellcheck source=/dev/null
    source "$ROOT/config/db-gui/ec2.env"
    open_apps "$MONGODB_URI" "$REDIS_PORT"
  ;;
  connections)
    print_connections "$ROOT/config/db-gui/local.env" "LOCAL (Mac Docker)"
    print_connections "$ROOT/config/db-gui/ec2.env" "EC2 (run ./scripts/db-tunnel-ec2.sh start first)"
    echo ""
    echo "Commands:"
    echo "  ./scripts/db-gui.sh local   — view local Docker data"
    echo "  ./scripts/db-gui.sh ec2     — tunnel + view AWS EC2 data"
    echo "  ./scripts/db-tunnel-ec2.sh stop"
  ;;
  *)
    echo "Usage: $0 local|ec2|connections"
    exit 1
  ;;
esac
