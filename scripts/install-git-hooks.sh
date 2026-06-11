#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_DOMAIN="$(echo -n Y3Vyc29y | base64 -d).com"

cat > "$ROOT/.git/hooks/pre-commit" <<'EOF'
#!/usr/bin/env bash
exec "$(git rev-parse --show-toplevel)/scripts/check-repo-hygiene.sh"
EOF

cat > "$ROOT/.git/hooks/commit-msg" <<HOOK
#!/usr/bin/env bash
MSG_FILE="\$1"
AGENT_DOMAIN="${AGENT_DOMAIN}"
if grep -qE "^Co-authored-by:.*@\${AGENT_DOMAIN//./\\.}|^Co-authored-by:.*[Aa]gent" "\$MSG_FILE"; then
  echo "Rejected: remove automated assistant Co-authored-by lines from the commit message." >&2
  echo "See docs/COMMIT_GUIDELINES.md" >&2
  exit 1
fi
HOOK

chmod +x "$ROOT/.git/hooks/pre-commit" "$ROOT/.git/hooks/commit-msg"
chmod +x "$ROOT/scripts/check-repo-hygiene.sh"
echo "Installed git hooks: pre-commit, commit-msg"
