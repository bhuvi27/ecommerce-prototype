#!/usr/bin/env bash
# Provision AWS microservices stack (MSK + RDS + ElastiCache + ECS + CloudFront).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform/aws-microservices"
REGION="${AWS_REGION:-ap-south-1}"

echo "=== Beauty Store AWS Microservices ==="
echo "Region: $REGION"

if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
  echo "Configure AWS CLI first: aws configure"
  exit 1
fi

if [[ ! -f "$TF_DIR/terraform.tfvars" ]]; then
  cp "$TF_DIR/terraform.tfvars.example" "$TF_DIR/terraform.tfvars"
  echo "Created terraform.tfvars — edit if needed."
fi

cd "$TF_DIR"
terraform init -input=false
terraform plan -out=tfplan
echo ""
read -r -p "Apply terraform? [y/N] " ans
[[ "$ans" == "y" || "$ans" == "Y" ]] || exit 0
terraform apply -input=false tfplan

echo ""
"$ROOT/scripts/aws-microservices-print-vars.sh"
echo ""
echo "Next: build/push images (see docs/DEPLOY_AWS_MICROSERVICES.md)"
