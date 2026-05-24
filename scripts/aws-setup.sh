#!/usr/bin/env bash
# One-shot AWS learning deploy: Mumbai (ap-south-1) EC2 + Docker stack.
# Prerequisites: IAM access keys configured (see docs/DEPLOY_AWS.md Step 1).
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

yellow "=== Shree Hari Beauty Store — AWS setup (region: $REGION) ==="

if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
  red "AWS CLI is not configured or credentials are invalid."
  echo ""
  echo "Do this once in the AWS Console (Mumbai ap-south-1):"
  echo "  1. IAM → Users → Create user (e.g. beauty-store-admin)"
  echo "  2. Attach policy: AdministratorAccess"
  echo "  3. Security credentials → Create access key → CLI"
  echo "  4. Run: aws configure"
  echo "     Region: ap-south-1"
  echo "     Output: json"
  echo ""
  echo "Or export for this session:"
  echo "  export AWS_ACCESS_KEY_ID=..."
  echo "  export AWS_SECRET_ACCESS_KEY=..."
  echo "  export AWS_DEFAULT_REGION=ap-south-1"
  exit 1
fi

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
green "AWS account: $ACCOUNT | region: $REGION"

if [[ ! -f "$TF_DIR/terraform.tfvars" ]]; then
  MY_IP="$(curl -4 -s https://ifconfig.me || curl -s https://api.ipify.org)"
  yellow "Creating terraform.tfvars (SSH allowed from $MY_IP/32)"
  cp "$TF_DIR/terraform.tfvars.example" "$TF_DIR/terraform.tfvars"
  sed -i.bak "s|YOUR_IP/32|$MY_IP/32|" "$TF_DIR/terraform.tfvars"
  rm -f "$TF_DIR/terraform.tfvars.bak"
fi

cd "$TF_DIR"
yellow "Terraform init..."
terraform init -input=false

yellow "Terraform plan..."
terraform plan -out=tfplan

yellow "Terraform apply (creates EC2 in Mumbai + auto-deploys app via user_data)..."
terraform apply -input=false tfplan

ELASTIC_IP=$(terraform output -raw elastic_ip)
API_URL=$(terraform output -raw api_url)
HEALTH=$(terraform output -raw health_url)
SSH_CMD=$(terraform output -raw ssh_command)

green "Elastic IP: $ELASTIC_IP"
green "API URL:    $API_URL"
green "Health:     $HEALTH"
echo "SSH:          $SSH_CMD"

yellow "Waiting for API to become healthy (user_data installs Docker + app, ~5–10 min)..."
for i in $(seq 1 60); do
  if curl -sf "$HEALTH" >/dev/null 2>&1; then
    green "API is healthy!"
  if curl -sf "http://$ELASTIC_IP:3000/api/v1/catalog/products" >/dev/null 2>&1; then
      green "Products endpoint OK."
    fi
    echo ""
    green "=== Done ==="
    echo "GitHub Pages: Actions → Deploy GitHub Pages → Run workflow"
    echo "  api_url = $API_URL"
    echo ""
    echo "Note: GitHub Pages is HTTPS; HTTP API may be blocked in browser (mixed content)."
    echo "Use Render for public demo, or test API with: curl $HEALTH"
    exit 0
  fi
  printf '.'
  sleep 15
done

echo ""
yellow "API not ready yet. Check progress on EC2:"
echo "  $SSH_CMD"
echo "  sudo tail -f /var/log/cloud-init-output.log"
echo "  docker compose -f /opt/beauty-store/docker-compose.prod.yml ps"
