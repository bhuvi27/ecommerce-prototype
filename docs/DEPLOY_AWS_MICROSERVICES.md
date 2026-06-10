# Deploy AWS Microservices (Flipkart-style learning stack)

Separate HTTPS URL from the monolith on `aws` branch. Uses **ECS Fargate**, **RDS PostgreSQL**, **ElastiCache Redis**, **Amazon MSK (Kafka)**, **Cognito**, **S3 + CloudFront**.

| Environment | Branch | URL |
|-------------|--------|-----|
| Monolith AWS | `aws` | existing CloudFront URL |
| **Microservices** | **`aws-microservices`** | new `*.cloudfront.net` from terraform output |

## Architecture

- **Sync HTTP**: browse, add-to-cart, checkout (user waits for response)
- **Async Kafka**: `order.created`, `payment.completed`, `order.confirmed` → notification worker
- **Multi-pod**: state in Redis/RDS; ALB routes to any healthy ECS task

### Request flow

1. **Browse** — CloudFront (static UI) + `/api/v1/catalog/*` → catalog service (MongoDB, Redis cache)
2. **Cart** — `/api/v1/cart*` → cart service (Redis for guests, Postgres for logged-in users)
3. **Checkout** — `POST /api/v1/orders/checkout` → order service (fetches cart over HTTP, writes Postgres, publishes Kafka events)
4. **Payment** — COD confirms in order service; Razorpay flows use payment service + webhooks
5. **Notifications** — notification worker consumes Kafka and sends email

## Prerequisites

- AWS CLI configured (`ap-south-1`)
- Terraform >= 1.5
- Docker (build images locally or use GitHub Actions)

## Step 1 — Provision infrastructure

```bash
./scripts/aws-microservices-setup.sh
```

Or manually:

```bash
cd infra/terraform/aws-microservices
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

## Step 2 — Build and push container images

```bash
AWS_REGION=ap-south-1
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"
PREFIX=beauty-ms-dev

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $REGISTRY

for svc in auth catalog cart order payment notification; do
  docker build -f apps/services/$svc/Dockerfile -t $REGISTRY/$PREFIX/$svc:latest .
  docker push $REGISTRY/$PREFIX/$svc:latest
done
```

ECS services pull `:latest` from ECR. Wait 2–5 minutes for tasks to become healthy.

## Step 3 — Run database migrations

Connect to RDS (bastion or one-off ECS task) and run:

```bash
cd apps/api && alembic upgrade head && python -m scripts.seed
```

Or exec into an auth/order task with `DATABASE_URL` set.

## Step 4 — Deploy shop UI

```bash
./scripts/aws-microservices-print-vars.sh
```

Set GitHub Actions variables (`MS_*`), push to `aws-microservices`, or build locally:

```bash
cd web
NEXT_PUBLIC_API_URL=https://YOUR_CLOUDFRONT_DOMAIN/api/v1 STATIC_EXPORT=true npm run build
aws s3 sync out/ s3://YOUR_UI_BUCKET/ --delete
aws cloudfront create-invalidation --distribution-id ID --paths "/*"
```

## Local development (before AWS)

Uses Bitnami Kafka instead of MSK:

```bash
docker compose -f docker-compose.microservices.yml up --build
```

| Service | Port |
|---------|------|
| auth | 8001 |
| catalog | 8002 |
| cart | 8003 |
| order | 8004 |
| payment | 8005 |

Point web at one service or add a local reverse proxy for `/api/v1/*`.

## AWS console learning checklist

1. **RDS** — endpoints, schemas, connections
2. **ElastiCache** — Redis cluster, cart keys
3. **MSK** — brokers, topics, consumer groups
4. **Cognito** — user pool, app client
5. **ECS** — tasks, logs, service discovery (mongo)
6. **CloudWatch** — trace checkout across services

## Cost (~2 days demo)

| Service | ~48h |
|---------|------|
| MSK (2× kafka.t3.small) | $4–6 |
| RDS + ElastiCache + ALB + Fargate | $12–18 |
| CloudFront + S3 | ~$1 |
| Cognito | $0 |
| **Total** | **~$22–30** |

## Shutdown (save budget)

```bash
./scripts/aws-microservices-destroy.sh
# or: cd infra/terraform/aws-microservices && terraform destroy
```

Monolith on `aws` branch is **not** affected (separate Terraform state).

## OCP → AWS mapping

| OCP | AWS |
|-----|-----|
| Kafka pod | Amazon MSK |
| Redis pod | ElastiCache |
| Postgres pod | RDS |
| Deployment | ECS Fargate |
| Route | ALB + CloudFront |
