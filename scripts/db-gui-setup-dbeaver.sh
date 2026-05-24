#!/usr/bin/env bash
# Install Beauty Store Postgres connections in DBeaver (LOCAL + EC2).
# Usage: ./scripts/db-gui-setup-dbeaver.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DBEAVER_WS="${DBEAVER_WORKSPACE:-$HOME/Library/DBeaverData/workspace6/General}"
DBEAVER_DIR="$DBEAVER_WS/.dbeaver"
SRC_JSON="$ROOT/config/db-gui/dbeaver-data-sources-beauty.json"
LOCAL_ENV="$ROOT/config/db-gui/local.env"

if [[ ! -f "$LOCAL_ENV" ]]; then
  echo "Missing $LOCAL_ENV — copy from config/db-gui/local.env.example and set POSTGRES_PASSWORD."
  exit 1
fi
# shellcheck source=/dev/null
source "$LOCAL_ENV"
if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
  echo "Set POSTGRES_PASSWORD in $LOCAL_ENV (same value as docker-compose.yml POSTGRES_PASSWORD)."
  exit 1
fi

if [[ -x /Applications/DBeaver.app/Contents/MacOS/dbeaver ]]; then
  DBEAVER=/Applications/DBeaver.app/Contents/MacOS/dbeaver
elif command -v dbeaver >/dev/null 2>&1; then
  DBEAVER="$(command -v dbeaver)"
else
  echo "DBeaver not found. Install: brew install --cask dbeaver-community"
  exit 1
fi

mkdir -p "$DBEAVER_DIR"
if [[ -f "$DBEAVER_DIR/data-sources.json" ]]; then
  cp "$DBEAVER_DIR/data-sources.json" "$DBEAVER_DIR/data-sources.json.bak.$(date +%Y%m%d%H%M%S)"
fi
cp "$SRC_JSON" "$DBEAVER_DIR/data-sources.json"
rm -f "$DBEAVER_DIR/data-sources-beauty.json"

"$DBEAVER" -stop -nosplash 2>/dev/null || true
sleep 2

save_password() {
  local id="$1" port="$2" name="$3"
  "$DBEAVER" -nosplash -reuseWorkspace -con \
    "driver=postgresql|host=localhost|port=${port}|database=${POSTGRES_DB}|user=${POSTGRES_USER}|password=${POSTGRES_PASSWORD}|name=${name}|folder=Beauty Store|id=${id}|create=false|save=true|connect=true" \
    >/dev/null 2>&1 || true
  sleep 10
  "$DBEAVER" -stop -nosplash 2>/dev/null || true
  sleep 1
}

save_password "beauty-store-local" "${POSTGRES_PORT:-5432}" "Beauty Store LOCAL"
save_password "beauty-store-ec2" "15432" "Beauty Store EC2"

if docker compose -f "$ROOT/docker-compose.yml" ps postgres 2>/dev/null | grep -q healthy; then
  echo "Postgres Docker: healthy"
else
  docker compose -f "$ROOT/docker-compose.yml" up -d postgres 2>/dev/null || true
  echo "Postgres Docker: started (or run: docker compose up -d)"
fi

echo ""
echo "DBeaver Connections panel should show:"
echo "  Beauty Store"
echo "    ├── Beauty Store LOCAL   (localhost:${POSTGRES_PORT:-5432})"
echo "    └── Beauty Store EC2     (localhost:15432, needs SSH tunnel)"
echo ""
echo "Expand: connection → Databases → ${POSTGRES_DB} → Schemas → public → Tables"
echo "EC2 tunnel: ./scripts/db-tunnel-ec2.sh start"
echo ""

open -a DBeaver 2>/dev/null || open -a "DBeaver Community"
