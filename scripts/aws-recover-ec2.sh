#!/usr/bin/env bash
# Recover a stuck AWS learning EC2 instance (impaired reachability / API timeout).
# Uses stop/start (not reboot) and waits for /health/ready on the Elastic IP.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform/ec2-learning"
REGION="${AWS_REGION:-ap-south-1}"

red() { printf '\033[0;31m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { red "Missing: $1"; exit 1; }
}

need_cmd aws
need_cmd terraform
need_cmd curl

cd "$TF_DIR"
INSTANCE_ID=$(terraform output -raw instance_id)
ELASTIC_IP=$(terraform output -raw elastic_ip)
HEALTH_URL=$(terraform output -raw health_url)

yellow "Instance: $INSTANCE_ID | IP: $ELASTIC_IP"

STATUS_JSON=$(aws ec2 describe-instance-status \
  --region "$REGION" \
  --instance-ids "$INSTANCE_ID" \
  --include-all-instances \
  --output json)

STATE=$(echo "$STATUS_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['InstanceStatuses'][0]['InstanceState']['Name'])")
REACH=$(echo "$STATUS_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
details = d['InstanceStatuses'][0].get('InstanceStatus', {}).get('Details', [])
print(next((x['Status'] for x in details if x.get('Name') == 'reachability'), 'unknown'))
")

echo "State: $STATE | Instance reachability: $REACH"

if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
  green "API already healthy at $HEALTH_URL"
  exit 0
fi

yellow "API not responding — stopping instance..."
aws ec2 stop-instances --region "$REGION" --instance-ids "$INSTANCE_ID" >/dev/null
aws ec2 wait instance-stopped --region "$REGION" --instance-ids "$INSTANCE_ID"

yellow "Starting instance..."
aws ec2 start-instances --region "$REGION" --instance-ids "$INSTANCE_ID" >/dev/null
aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"

yellow "Waiting for API health (docker stack may take 2–5 min after boot)..."
for i in $(seq 1 40); do
  if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    green "API recovered: $HEALTH_URL"
    CF_URL=$(cd "$ROOT/infra/terraform/aws-prod" && terraform output -raw cloudfront_url 2>/dev/null || true)
    if [[ -n "$CF_URL" ]] && curl -sf "$CF_URL/health/ready" >/dev/null 2>&1; then
      green "CloudFront OK: $CF_URL"
    fi
    exit 0
  fi
  printf '.'
  sleep 15
done

echo ""
red "API still not healthy. SSH in and check docker:"
terraform output -raw ssh_command
echo "  docker compose -f /opt/beauty-store/docker-compose.prod.yml ps"
echo "  systemctl status beauty-store.service"
exit 1
