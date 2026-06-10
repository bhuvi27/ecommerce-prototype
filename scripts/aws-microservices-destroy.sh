#!/usr/bin/env bash
set -euo pipefail
TF_DIR="$(cd "$(dirname "$0")/../infra/terraform/aws-microservices" && pwd)"
cd "$TF_DIR"
echo "This destroys the ENTIRE microservices stack (monolith aws branch unaffected)."
read -r -p "Type destroy to continue: " ans
[[ "$ans" == "destroy" ]] || exit 1
terraform destroy
