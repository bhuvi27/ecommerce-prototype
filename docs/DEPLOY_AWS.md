# Deploy API to AWS (learning, ~$0 on Free Tier)

This guide runs the **full backend** (FastAPI + Postgres + Mongo + Redis + MinIO) on a single **EC2 t3.micro** instance. The **shop UI stays on GitHub Pages** (free) — same as [DEPLOY_GITHUB_PAGES.md](DEPLOY_GITHUB_PAGES.md).

Use this path to **learn AWS cheaply**. Keep [Render](https://render.com) as the always-on free demo API when the EC2 instance is stopped.

---

## Architecture

```
Browser → GitHub Pages (static Next.js)
              ↓ NEXT_PUBLIC_API_URL
         EC2 Elastic IP :3000 (FastAPI)
              ↓ docker compose
         Postgres, Mongo, Redis, MinIO
```

| Component | Where |
|-----------|--------|
| Shop UI | GitHub Pages (unchanged) |
| API + databases | EC2 + [`docker-compose.prod.yml`](../docker-compose.prod.yml) |
| Infrastructure | Terraform in [`infra/terraform/ec2-learning/`](../infra/terraform/ec2-learning/) |

**Estimated cost:** ~$0/month for the first 12 months on a new AWS account (Free Tier). After that, ~$8–12/month if left running 24/7. **Stop the instance** when not learning to avoid charges.

---

## Prerequisites

- AWS account (new accounts get Free Tier + up to $200 credits)
- GitHub repo with this project pushed
- GitHub Pages already working ([DEPLOY_GITHUB_PAGES.md](DEPLOY_GITHUB_PAGES.md))
- On your laptop: AWS CLI, Terraform ≥ 1.5, SSH client

Install tools (macOS):

```bash
brew install awscli
brew tap hashicorp/tap && brew install hashicorp/tap/terraform
```

### Which AWS signup plan?

Choose **Free plan** for learning — no charges until you upgrade. You still add a card for verification; AWS won't bill it on the Free plan. See [AWS Free Tier plans](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).

**Region:** use **`ap-south-1` (Mumbai)** for India.

---

## Quick setup (automated)

After Step 1 (IAM user + `aws configure` with region `ap-south-1`):

```bash
./scripts/aws-setup.sh
```

This script:

1. Creates EC2 t3.micro in Mumbai with Elastic IP
2. Generates SSH key (`infra/terraform/ec2-learning/beauty-store-learning.pem`)
3. Bootstraps Docker, clones the repo, runs migrations + seed, starts the API
4. Waits for `/health/ready`

Then point GitHub Pages at the API URL printed at the end (Actions → Deploy GitHub Pages → `api_url`).

---

## Step 1 — Secure your AWS account

1. Sign up at https://aws.amazon.com (credit card required; Free Tier still applies).
2. Enable **MFA** on the root account (IAM → Security credentials).
3. Create an **IAM user** for daily use (not root):
   - IAM → Users → Create user → enable **Programmatic access** + **Console access**
   - Attach policy: `AdministratorAccess` (OK for learning; use narrower policies in production)
4. Save the **Access Key ID** and **Secret Access Key**.

Configure AWS CLI locally:

```bash
aws configure
# AWS Access Key ID: ...
# AWS Secret Access Key: ...
# Default region: ap-south-1
# Default output: json
```

Verify:

```bash
aws sts get-caller-identity
```

---

## Step 2 — Billing alarm (do this first)

1. AWS Console → **Billing** → **Billing preferences** → enable **Receive Billing Alerts**
2. **CloudWatch** → **Alarms** → **Create alarm** → **Billing** metric
3. Threshold: **$5** or **$10** → SNS email notification

This warns you before unexpected charges.

---

## Step 3 — Create an SSH key pair

1. EC2 console → **Key pairs** → **Create key pair**
2. Name: e.g. `beauty-store-learning`
3. Type: RSA, format: `.pem`
4. Save the downloaded `.pem` file to `~/.ssh/` and restrict permissions:

```bash
chmod 400 ~/.ssh/beauty-store-learning.pem
```

Note the **key pair name** — you need it for Terraform.

---

## Step 4 — Provision EC2 with Terraform

```bash
cd infra/terraform/ec2-learning
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

| Variable | Example | Notes |
|----------|---------|-------|
| `ssh_key_name` | `beauty-store-learning` | From Step 3 |
| `allowed_ssh_cidr` | `203.0.113.10/32` | Your public IP — run `curl ifconfig.me` |
| `allowed_api_cidr` | `0.0.0.0/0` | Public API for GitHub Pages; or restrict to your IP while testing |

Apply:

```bash
terraform init
terraform plan
terraform apply
```

Save the outputs:

```bash
terraform output elastic_ip
terraform output api_url
terraform output health_url
```

Example API URL: `http://54.123.45.67:3000/api/v1`

Wait ~2 minutes after apply for `user_data` to finish installing Docker.

---

## Step 5 — Deploy the app on EC2

SSH into the instance:

```bash
ssh -i ~/.ssh/beauty-store-learning.pem ec2-user@ELASTIC_IP
```

On the EC2 instance:

```bash
# Clone your repo (public repo — for private repos use a deploy key or SCP files)
cd /opt/beauty-store
git clone https://github.com/YOUR_USERNAME/REPO_NAME.git .
# Or: git pull if already cloned

# Configure API environment
cp apps/api/.env.aws.example apps/api/.env.aws
nano apps/api/.env.aws
```

Edit `apps/api/.env.aws`:

- `CORS_ORIGINS` — your GitHub Pages origin, e.g. `https://YOUR_USERNAME.github.io`
- `JWT_ACCESS_SECRET` / `JWT_REFRESH_SECRET` — long random strings
- `S3_PUBLIC_URL` — replace `ELASTIC_IP` with your Elastic IP from Terraform

Start infrastructure, migrate, seed, then run API:

```bash
docker compose -f docker-compose.prod.yml up -d postgres mongo redis minio
docker compose -f docker-compose.prod.yml run --rm minio-init

docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.seed

docker compose -f docker-compose.prod.yml up -d api
docker compose -f docker-compose.prod.yml ps
```

Verify from your laptop:

```bash
curl http://ELASTIC_IP:3000/health/ready
curl http://ELASTIC_IP:3000/api/v1/catalog/products
```

---

## Step 6 — Point GitHub Pages at the AWS API

`NEXT_PUBLIC_API_URL` is set at **build time**. To test AWS without changing the default Render demo:

1. GitHub repo → **Actions** → **Deploy GitHub Pages** → **Run workflow**
2. Set **api_url** to: `http://ELASTIC_IP:3000/api/v1`
3. Wait for the workflow to finish (green)
4. Open `https://YOUR_USERNAME.github.io/REPO_NAME/` — products should load from EC2

Pushes to `main` still use the Render URL (or repo variable `NEXT_PUBLIC_API_URL`) unless you run the workflow manually with a custom `api_url`.

---

## Step 7 — Verify end-to-end

- [ ] `http://ELASTIC_IP:3000/health/ready` returns healthy
- [ ] GitHub Pages home page lists products
- [ ] Add to cart → checkout → mock payment works
- [ ] No CORS errors in browser DevTools console

---

## Updating the app

SSH to EC2:

```bash
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

## Stop charges when done learning

**Option A — Stop instance (keeps data, small EIP charge if stopped long-term):**

```bash
aws ec2 stop-instances --instance-ids $(terraform output -raw instance_id)
```

**Option B — Destroy everything:**

```bash
cd infra/terraform/ec2-learning
terraform destroy
```

Render + GitHub Pages continue working as your free demo.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| SSH connection refused | Check `allowed_ssh_cidr` matches your current IP; update `terraform.tfvars` and `terraform apply` |
| API not reachable | Security group allows 3000; `docker compose ps` shows api running |
| CORS error on Pages | Set `CORS_ORIGINS=https://YOUR_USERNAME.github.io` in `apps/api/.env.aws`, restart api container |
| Mixed content (HTTPS page → HTTP API) | Browsers block this. For AWS learning, test API with curl or use Render for public demo. Phase 1.5: add HTTPS (nginx/Caddy) on EC2 |
| No products | Run seed again; check Mongo is up: `docker compose -f docker-compose.prod.yml logs mongo` |
| Terraform auth error | Re-run `aws configure`; check IAM user permissions |

---

## Phase 2 — Production AWS (later)

When you publish for real, migrate off single EC2 to managed services. See [`infra/terraform/`](../infra/terraform/) (ECS, RDS, S3 modules) and budget ~$80–150/month minimum.

| Learning (EC2) | Production |
|----------------|------------|
| Docker Postgres | RDS PostgreSQL |
| Docker Mongo | MongoDB Atlas |
| Docker Redis | ElastiCache |
| MinIO | S3 + CloudFront |
| EC2 compose | ECS Fargate + ALB |
| GitHub Pages | GitHub Pages or CloudFront + S3 |

---

## Related docs

- [DEPLOY_GITHUB_PAGES.md](DEPLOY_GITHUB_PAGES.md) — free frontend + Render API demo
- [MODULES_AND_LOCAL_SETUP.md](MODULES_AND_LOCAL_SETUP.md) — local development reference
