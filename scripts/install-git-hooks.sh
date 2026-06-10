#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$ROOT/.git/hooks/pre-commit"

cat > "$HOOK" <<'EOF'
#!/usr/bin/env bash
exec "$(git rev-parse --show-toplevel)/scripts/check-repo-hygiene.sh"
EOF

chmod +x "$HOOK"
chmod +x "$ROOT/scripts/check-repo-hygiene.sh"
echo "Installed pre-commit hook → .git/hooks/pre-commit"
