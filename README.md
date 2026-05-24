# Shree Hari Beauty Store

Modular monolith beauty e-commerce: **Python FastAPI** backend + **Next.js** web UI.

## Documentation (single reference)

| Doc | What it covers |
|-----|----------------|
| **[docs/MODULES_AND_LOCAL_SETUP.md](docs/MODULES_AND_LOCAL_SETUP.md)** | Every module, database, Docker image, ports, env files |
| **[docs/DEPLOY_GITHUB_PAGES.md](docs/DEPLOY_GITHUB_PAGES.md)** | Publish the web for others (free GitHub Pages + optional Render API) |
| **[docs/DATABASE_GUI.md](docs/DATABASE_GUI.md)** | DBeaver / Compass / Redis Insight — local vs EC2 connections |
| **[docs/DEPLOY_AWS.md](docs/DEPLOY_AWS.md)** | Learn AWS cheaply (EC2 + Docker in Mumbai; run `./scripts/aws-setup.sh`) |
| **[docs/DEPLOY_AWS_PROD.md](docs/DEPLOY_AWS_PROD.md)** | AWS production UI (S3 + CloudFront on `aws` branch; EC2 API) |

## Stack

| Layer | Tech |
|-------|------|
| API | FastAPI, SQLAlchemy, Alembic |
| Users / Orders | PostgreSQL |
| Catalog | MongoDB |
| Cart cache | Redis |
| Images | MinIO (S3-compatible) |
| Payments | Razorpay (mock mode without keys) |
| Web | Next.js 14 |

## Quick start (local end-to-end)

### 1. Start infrastructure

```bash
docker compose up -d
```

### 2. Backend setup

Requires **Python 3.11–3.14**. On Python 3.14:

```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
```

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # or use provided .env
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --port 3000
```

### 3. Frontend setup (new terminal)

```bash
cd web
npm install
npm run dev
```

Open **http://localhost:3001**

### Default admin

- Email: `admin@beauty-store.local`
- Password: `Admin123!`

## End-to-end flow (no Razorpay keys)

1. Browse products on home page (3 seeded items: oils + facewash)
2. Open a product → Add to cart
3. Cart → Checkout → fill shipping → **Pay Now**
4. Dev mode auto-completes payment via mock endpoint
5. Order detail shows **confirmed**
6. Register/login to see order history

## With Razorpay test keys

Set in `apps/api/.env` and `web/.env.local`:

```
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_test_...
```

Checkout opens Razorpay widget; webhook hits `POST /api/v1/payments/webhook`.

## API docs

- Swagger: http://localhost:3000/docs
- Health: http://localhost:3000/health/ready

## Project layout

```
apps/api/          FastAPI modular monolith
web/               Next.js storefront
infra/terraform/   AWS modules (ec2-learning, aws-prod S3+CloudFront; full stack for production later)
docker-compose.yml Postgres, Mongo, Redis, MinIO (local)
docker-compose.prod.yml  Same stack + API for EC2 deploy
```

## Modules (future microservices)

- `auth` — JWT + refresh cookies, addresses
- `catalog` — Mongo products, Redis cache
- `cart` — Redis + Postgres
- `order` + `payment` — checkout, idempotency, Razorpay
- `notification` — email via outbox worker
- `admin` — product onboarding
