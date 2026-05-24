#!/usr/bin/env bash
# Print GitHub Actions secrets/variables for AWS prod deploy.
# Run after: cd infra/terraform/aws-prod && terraform apply
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform/aws-prod"

cd "$TF_DIR"

echo "=== GitHub repo → Settings → Secrets and variables → Actions ==="
echo ""
echo "Secrets (create new):"
echo "  AWS_ACCESS_KEY_ID     = from IAM user beauty-store-github-deploy"
echo "  AWS_SECRET_ACCESS_KEY = from IAM user beauty-store-github-deploy"
echo ""
echo "Variables (create new):"
echo "  AWS_REGION                      = ap-south-1"
echo "  AWS_UI_BUCKET                   = $(terraform output -raw s3_bucket_name 2>/dev/null || echo '<terraform output s3_bucket_name>')"
echo "  AWS_CLOUDFRONT_DISTRIBUTION_ID  = $(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo '<terraform output cloudfront_distribution_id>')"
echo "  NEXT_PUBLIC_API_URL             = $(terraform output -raw next_public_api_url 2>/dev/null || echo '<terraform output next_public_api_url>')"
echo ""
echo "Live shop URL: $(terraform output -raw cloudfront_url 2>/dev/null || echo 'n/a')"
