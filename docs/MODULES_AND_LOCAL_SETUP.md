# Beauty Store — Modules, Databases & Local Setup (Single Reference)

This document lists **every module**, what it does, which **database or service** it uses on your machine, and the **Docker image** (if any) that provides it locally.

---

## Architecture at a glance

```
┌─────────────────────────────────────────────────────────────────────────┐
│  YOUR MACHINE (local development)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Browser  →  http://localhost:3001   (Next.js web — NOT in Docker)      │
│           →  http://localhost:3000   (FastAPI API — NOT in Docker)       │
├─────────────────────────────────────────────────────────────────────────┤
│  docker compose (infrastructure only)                                    │
│    postgres:16-alpine  →  port 5432                                      │
│    mongo:7             →  port 27017                                     │
│    redis:7-alpine      →  port 6379                                      │
│    minio/minio         →  port 9000 (S3 API), 9001 (console)             │
│    minio/mc            →  one-shot bucket setup                            │
└─────────────────────────────────────────────────────────────────────────┘
```

| What runs where | Local process | Docker? |
|-----------------|---------------|---------|
| Web storefront | `npm run dev` in `web/` | No |
| REST API | `uvicorn` in `apps/api/` | No |
| PostgreSQL | Container `postgres` | Yes — `postgres:16-alpine` |
| MongoDB | Container `mongo` | Yes — `mongo:7` |
| Redis | Container `redis` | Yes — `redis:7-alpine` |
| Object storage (images) | Container `minio` | Yes — `minio/minio` |

---

## Module reference (one table per module)

### 1. Web storefront (`web/`)

| Item | Detail |
|------|--------|
| **Purpose** | Shop UI: browse, cart, checkout, login, orders |
| **Tech** | Next.js 14, React, TypeScript |
| **Talks to** | FastAPI at `NEXT_PUBLIC_API_URL` (default `http://localhost:3000/api/v1`) |
| **Database** | None (browser only) |
| **Docker** | None — run with `npm run dev` |
| **Local URL** | http://localhost:3001 |
| **Config** | `web/.env.local` |

---

### 2. API gateway / HTTP layer (`apps/api/app/main.py`)

| Item | Detail |
|------|--------|
| **Purpose** | Single entry: CORS, request ID, routes under `/api/v1` |
| **Tech** | FastAPI, Uvicorn |
| **Database** | None directly |
| **Docker** | None — `uvicorn app.main:app --port 3000` |
| **Local URL** | http://localhost:3000 — docs at `/docs` |
| **Health** | `/health/live`, `/health/ready` |

---

### 3. Auth & users (`apps/api/app/modules/auth/`)

| Item | Detail |
|------|--------|
| **Purpose** | Register, login, JWT access token, refresh cookie, profile, addresses |
| **Tech** | Argon2 passwords, python-jose JWT |
| **Database** | **PostgreSQL** — tables: `users`, `refresh_tokens`, `addresses` |
| **Docker image** | `postgres:16-alpine` (via `docker compose`) |
| **Connection** | `DATABASE_URL=postgresql+asyncpg://beauty:beauty@localhost:5432/beauty_store` |
| **Redis** | No |
| **MongoDB** | No |
| **API paths** | `/api/v1/auth/*` |

---

### 4. Catalog (`apps/api/app/modules/catalog/`)

| Item | Detail |
|------|--------|
| **Purpose** | Public categories, product list (cursor), product by slug |
| **Tech** | Motor (async MongoDB driver) |
| **Database** | **MongoDB** — collections: `categories`, `products` |
| **Docker image** | `mongo:7` (via `docker compose`) |
| **Connection** | `MONGODB_URI=mongodb://localhost:27017`, DB name `beauty_catalog` |
| **Cache** | **Redis** — keys `catalog:categories`, `catalog:products:*` (TTL ~120s) |
| **Docker image (cache)** | `redis:7-alpine` |
| **PostgreSQL** | No |
| **API paths** | `/api/v1/catalog/*` |

---

### 5. Admin / product onboarding (`apps/api/app/modules/admin/`)

| Item | Detail |
|------|--------|
| **Purpose** | Create category/product, upload images, update product (admin role) |
| **Tech** | Same as Catalog + boto3 S3 client |
| **Database** | **MongoDB** (products/categories) |
| **Object storage** | **MinIO** (S3-compatible) — bucket `beauty-products` |
| **Docker images** | `mongo:7`, `minio/minio`, `minio/mc` (bucket init) |
| **MinIO ports** | API http://localhost:9000 — Console http://localhost:9001 |
| **Credentials** | `minioadmin` / `minioadmin` (local only) |
| **Public URLs** | `S3_PUBLIC_URL=http://localhost:9000/beauty-products` |
| **Cache invalidation** | Clears Redis catalog keys on write |
| **API paths** | `/api/v1/admin/*` (requires `Authorization: Bearer` + `admin` role) |

---

### 6. Cart (`apps/api/app/modules/cart/`)

| Item | Detail |
|------|--------|
| **Purpose** | Add/update/remove lines; guest cart (cookie) vs logged-in cart |
| **Tech** | SQLAlchemy + Redis |
| **Database (logged-in)** | **PostgreSQL** — `carts`, `cart_items` |
| **Database (guest)** | **Redis** — key `cart:{guest_id}` (also cookie `cart_id`) |
| **Docker** | `postgres:16-alpine`, `redis:7-alpine` |
| **Catalog read** | Calls Catalog module (Mongo) for price/name at add time |
| **API paths** | `/api/v1/cart/*` |

---

### 7. Order & checkout (`apps/api/app/modules/order/`)

| Item | Detail |
|------|--------|
| **Purpose** | Checkout, order history, order detail; idempotency on checkout |
| **Tech** | SQLAlchemy |
| **Database** | **PostgreSQL** — `orders`, `order_items`, `idempotency_keys` |
| **Docker** | `postgres:16-alpine` |
| **Queue** | Writes **outbox** row (same Postgres) for async email |
| **Depends on** | Cart module, Payment module |
| **API paths** | `/api/v1/orders/*` |

---

### 8. Payment — Razorpay (`apps/api/app/modules/payment/`)

| Item | Detail |
|------|--------|
| **Purpose** | Create Razorpay order, webhook, mock pay (dev) |
| **Tech** | `razorpay` Python SDK, HMAC webhook verify |
| **Database** | **PostgreSQL** — `payments` |
| **External** | Razorpay API (internet) when keys set |
| **Docker** | None for Razorpay |
| **Local without keys** | Mock order id + `POST /orders/{id}/mock-pay` |
| **API paths** | `/api/v1/payments/webhook`, used from checkout |

---

### 9. Notification (`apps/api/app/modules/notification/`)

| Item | Detail |
|------|--------|
| **Purpose** | Order confirmation email |
| **Tech** | `aiosmtplib` (optional SMTP) |
| **Database** | None |
| **Trigger** | Outbox worker after `order.confirmed` |
| **Local default** | Logs email to console if SMTP not configured |

---

### 10. Background workers (`apps/api/app/modules/workers/`)

| Item | Detail |
|------|--------|
| **Purpose** | Outbox poller (every 5s), expire stale orders (hourly), payment reconciliation (15m) |
| **Tech** | APScheduler (runs inside API process) |
| **Database** | **PostgreSQL** — `outbox_events` |
| **Docker** | `postgres:16-alpine` |
| **Redis / Mongo** | No |

---

### 11. Shared health (`apps/api/app/shared/health/`)

| Item | Detail |
|------|--------|
| **Purpose** | Liveness + readiness (Postgres, Mongo, Redis pings) |
| **Paths** | `/health/live`, `/health/ready` |

---

## Docker Compose service map

| Compose service | Image | Host port | Used by modules |
|-----------------|-------|-----------|-----------------|
| `postgres` | `postgres:16-alpine` | 5432 | Auth, Cart, Order, Payment, Workers |
| `mongo` | `mongo:7` | 27017 | Catalog, Admin |
| `redis` | `redis:7-alpine` | 6379 | Catalog (cache), Cart (guest) |
| `minio` | `minio/minio:latest` | 9000, 9001 | Admin (images) |
| `minio-init` | `minio/mc:latest` | — | Creates public bucket once |

Start all: `docker compose up -d` from project root.

---

## Environment files (local)

| File | Used by |
|------|---------|
| `apps/api/.env` | FastAPI (copy from `apps/api/.env.example`) |
| `web/.env.local` | Next.js (`NEXT_PUBLIC_API_URL`, Razorpay key for UI) |
| `docker-compose.yml` | Infrastructure defaults (user/password `beauty`) |

---

## Seed data (local)

Run once after migrations:

```bash
cd apps/api && source .venv/bin/activate && python -m scripts.seed
```

| Data | Store | Count |
|------|-------|-------|
| Categories (oil, facewash) | MongoDB | 2 |
| Products (coconut oil, neem facewash, etc.) | MongoDB | 5 |
| Admin user | PostgreSQL | 1 (`admin@beauty-store.local`) |

---

## Ports cheat sheet (local)

| Port | Service |
|------|---------|
| 3001 | Next.js web |
| 3000 | FastAPI API |
| 5432 | PostgreSQL |
| 27017 | MongoDB |
| 6379 | Redis |
| 9000 | MinIO S3 API |
| 9001 | MinIO web console |

---

## Production vs local (GitHub Pages note)

| Component | Local | Public internet (free tier) |
|-----------|-------|----------------------------|
| Web | `localhost:3001` | **GitHub Pages** (static site) — see [DEPLOY_GITHUB_PAGES.md](./DEPLOY_GITHUB_PAGES.md) |
| API | `localhost:3000` | **Not on GitHub Pages** — host on [Render](https://render.com) free tier (see `render.yaml`) |
| Postgres / Mongo / Redis | Docker | Render / MongoDB Atlas / Upstash free tiers |

GitHub Pages hosts **only the frontend**. The API must be deployed separately; the web app calls it via `NEXT_PUBLIC_API_URL`.

---

## Related docs

- [README.md](../README.md) — quick start
- [DEPLOY_GITHUB_PAGES.md](./DEPLOY_GITHUB_PAGES.md) — publish web for others to try
- [packages/contracts/openapi.yaml](../packages/contracts/openapi.yaml) — API sketch
