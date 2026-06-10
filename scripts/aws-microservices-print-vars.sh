#!/usr/bin/env bash
set -euo pipefail
TF_DIR="$(cd "$(dirname "$0")/../infra/terraform/aws-microservices" && pwd)"
cd "$TF_DIR"
echo "GitHub Actions variables (Settings → Secrets and variables → Actions):"
echo "  MS_AWS_REGION                  = $(terraform output -raw aws_region 2>/dev/null || echo ap-south-1)"
echo "  MS_UI_BUCKET                   = $(terraform output -raw ui_bucket_name)"
echo "  MS_CLOUDFRONT_DISTRIBUTION_ID  = $(terraform output -raw cloudfront_distribution_id)"
echo "  MS_NEXT_PUBLIC_API_URL         = $(terraform output -raw next_public_api_url)"
echo ""
echo "Shop URL: $(terraform output -raw cloudfront_url)"
echo "CORS_ORIGINS on ECS tasks should include: $(terraform output -raw cors_origin)"
