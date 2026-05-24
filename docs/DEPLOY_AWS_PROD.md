# Deploy AWS production (S3 + CloudFront + EC2)

Separate AWS deployment for the beauty store. Your **Render + GitHub Pages demo on `main` is unchanged**.

| Environment | Branch | Frontend | Backend | URL |
|-------------|--------|----------|---------|-----|
| **Demo (live)** | `main` | GitHub Pages | Render | `https://bhuvi27.github.io/shamit-beauty-store/` |
| **AWS prod** | `aws` | S3 + CloudFront | EC2 + Docker | `https://xxxxxxxx.cloudfront.net` |

---

## Architecture

```
Browser → CloudFront (HTTPS)
            ├─ /*           → S3 (static Next.js UI)
            └─ /api/v1/*    → EC2 :3000 (FastAPI + Postgres/Mongo/Redis/MinIO)
```

CloudFront gives one HTTPS URL for both UI and API, so browsers never hit mixed-content errors (HTTPS page → HTTP EC2).

---

## Prerequisites

- AWS CLI configured (`aws configure`, region `ap-south-1`)
- Terraform ≥ 1.5
- EC2 API running ([DEPLOY_AWS.md](DEPLOY_AWS.md) or `./scripts/aws-setup.sh`)
- GitHub repo with an `aws` branch

---

## Step 1 — Create the `aws` branch

```bash
git checkout main
git pull
git checkout -b aws
# merge or cherry-pick AWS prod commits, then push:
git push -u origin aws
```

Periodically sync app fixes from main:

```bash
git checkout aws
git merge main
git push
```

---

## Step 2 — EC2 API (backend)

If EC2 is **not** running:

```bash
./scripts/aws-setup.sh
```

Save the Elastic IP:

```bash
cd infra/terraform/ec2-learning
terraform output -raw elastic_ip
```

Verify API:

```bash
curl "http://ELASTIC_IP:3000/health/ready"
curl "http://ELASTIC_IP:3000/api/v1/catalog/products"
```

---

## Step 3 — Terraform: S3 + CloudFront

```bash
cd infra/terraform/aws-prod
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — set ec2_origin_ip to your Elastic IP
terraform init
terraform plan
terraform apply
```

Save outputs:

```bash
terraform output cloudfront_url
terraform output s3_bucket_name
terraform output cloudfront_distribution_id
terraform output next_public_api_url
terraform output cors_origin
```

Example CloudFront URL: `https://d111111abcdef8.cloudfront.net`

---

## Step 4 — Update CORS on EC2

SSH to EC2 and edit `apps/api/.env.aws`:

```bash
CORS_ORIGINS=https://bhuvi27.github.io,https://d111111abcdef8.cloudfront.net,http://localhost:3001
```

Use the `cors_origin` value from Terraform output (no trailing slash).

Restart API:

```bash
cd /opt/beauty-store   # or your clone path
docker compose -f docker-compose.prod.yml up -d api
```

---

## Step 5 — Deploy UI to S3

### Manual (first time or local test)

```bash
cd web
export STATIC_EXPORT=true
export NEXT_PUBLIC_API_URL="https://YOUR_CLOUDFRONT_DOMAIN.cloudfront.net/api/v1"
npm run build

aws s3 sync out/ s3://YOUR_UI_BUCKET/ --delete
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

Or use the npm script:

```bash
NEXT_PUBLIC_API_URL="https://dxxx.cloudfront.net/api/v1" npm run build:aws
```

### GitHub Actions (automated on `aws` branch)

Configure **Settings → Secrets and variables → Actions**:

**Secrets:**

| Name | Value |
|------|--------|
| `AWS_ACCESS_KEY_ID` | IAM access key with S3 + CloudFront permissions |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |

**Variables:**

| Name | Example |
|------|---------|
| `AWS_REGION` | `ap-south-1` |
| `AWS_UI_BUCKET` | from `terraform output s3_bucket_name` |
| `AWS_CLOUDFRONT_DISTRIBUTION_ID` | from `terraform output cloudfront_distribution_id` |
| `NEXT_PUBLIC_API_URL` | from `terraform output -raw next_public_api_url` |

Push to `aws` (or run **Deploy AWS** workflow manually). Workflow file: [`.github/workflows/deploy-aws.yml`](../.github/workflows/deploy-aws.yml).

---

## Step 6 — Verify end-to-end

- [ ] `https://YOUR_CLOUDFRONT_DOMAIN.cloudfront.net/` lists products
- [ ] Product page loads (e.g. `/products/coconut-oil/`)
- [ ] Add to cart → checkout → mock payment works
- [ ] No CORS errors in browser DevTools
- [ ] GitHub Pages demo on `main` still works (unchanged)

Test API through CloudFront:

```bash
curl "https://YOUR_CLOUDFRONT_DOMAIN.cloudfront.net/api/v1/catalog/products"
curl "https://YOUR_CLOUDFRONT_DOMAIN.cloudfront.net/health/ready"
```

---

## Branch strategy

| Branch | Deploys to | API |
|--------|------------|-----|
| `main` | GitHub Pages only | Render (via repo variable or default) |
| `aws` | S3 + CloudFront | EC2 via CloudFront `/api/v1/*` |

The Pages workflow ([`deploy-pages.yml`](../.github/workflows/deploy-pages.yml)) runs **only on `main`**. The AWS workflow runs **only on `aws`**. They never conflict.

---

## Updating the app

**UI (aws branch):**

```bash
git push origin aws   # triggers deploy-aws workflow
```

**API (EC2):**

```bash
ssh ec2-user@ELASTIC_IP
cd /opt/beauty-store
git pull
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml up -d api
```

After catalog changes in `scripts/seed.py`:

```bash
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.seed
```

---

## Cost and cleanup

- **EC2 t3.micro:** ~$0/month first 12 months (Free Tier), then ~$8–12/month if always on
- **CloudFront + S3:** usually a few dollars/month for low traffic
- **Stop EC2 when not learning:** `aws ec2 stop-instances --instance-ids INSTANCE_ID`
- **Destroy CloudFront + S3 stack:** `cd infra/terraform/aws-prod && terraform destroy`
- **Destroy EC2:** `cd infra/terraform/ec2-learning && terraform destroy`

Render + GitHub Pages on `main` keep working regardless.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Blank page on CloudFront | Check S3 sync; invalidate cache `/*` |
| Products stuck on Loading | CORS — add CloudFront URL to `CORS_ORIGINS` on EC2 |
| 502 from `/api/v1/*` | EC2 API down; check `docker compose ps` and security group port 3000 |
| Old UI after deploy | Run CloudFront invalidation |
| Pages demo broken | Ensure you did not change `main` deploy or Render URL |

---

## Related docs

- [DEPLOY_GITHUB_PAGES.md](DEPLOY_GITHUB_PAGES.md) — free demo on `main`
- [DEPLOY_AWS.md](DEPLOY_AWS.md) — EC2 learning setup
- [MODULES_AND_LOCAL_SETUP.md](MODULES_AND_LOCAL_SETUP.md) — local development
