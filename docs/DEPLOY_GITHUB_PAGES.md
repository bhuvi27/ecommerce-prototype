# Deploy web to GitHub Pages (free)

GitHub Pages hosts **static files only** — the Next.js shop UI. Your **Python API and databases** are not run on GitHub Pages; use [Render](https://render.com) (free tier) for the API so visitors get a working shop.

## What gets published

| Published on GitHub Pages | Not on GitHub Pages |
|---------------------------|---------------------|
| Shop UI (browse, cart, checkout screens) | FastAPI backend |
| Login/register forms | PostgreSQL, MongoDB, Redis |
| | MinIO, Razorpay webhooks |

After deploy, set `NEXT_PUBLIC_API_URL` to your Render API URL so the live site can load products and checkout.

For **AWS learning** with an EC2 backend, see [DEPLOY_AWS.md](DEPLOY_AWS.md). You can keep this Pages URL and switch the API target via a manual workflow run (below).

---

## Step 1 — Push code to GitHub

If the repo is not on GitHub yet:

```bash
cd /path/to/shree_hari
git init
git add .
git commit -m "Beauty store: FastAPI + Next.js"
```

On https://github.com/new create a repository named e.g. `shree-hari-beauty` (public).

```bash
git remote add origin https://github.com/YOUR_USERNAME/shree-hari-beauty.git
git branch -M main
git push -u origin main
```

---

## Step 2 — Enable GitHub Pages

1. Open your repo on GitHub → **Settings** → **Pages**
2. Under **Build and deployment** → Source: **GitHub Actions**
3. Push to `main` — workflow `.github/workflows/deploy-pages.yml` builds and deploys the site

Your site URL will be:

`https://YOUR_USERNAME.github.io/REPO_NAME/`

Example: `https://shamit.github.io/shree-hari-beauty/`

---

## Step 3 — API for a working demo (Render, free)

1. Sign up at https://render.com with GitHub
2. **New → Blueprint** → connect this repo → Render reads `render.yaml`
3. Set environment variables in Render dashboard (or use defaults from blueprint)
4. After deploy, copy the API URL e.g. `https://beauty-store-api.onrender.com`

On GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **Variables**:

| Name | Value |
|------|--------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-API.onrender.com/api/v1` |

Re-run the **Deploy GitHub Pages** workflow (Actions tab → workflow → Re-run).

### Switch API backend (Render vs AWS)

The shop UI is rebuilt with a fixed `NEXT_PUBLIC_API_URL` at build time.

| Backend | When to use | How |
|---------|-------------|-----|
| **Render** (default) | Public demo, always on | Push to `main`, or set repo variable `NEXT_PUBLIC_API_URL` |
| **AWS EC2** | Learning / testing | Actions → **Deploy GitHub Pages** → **Run workflow** → set **api_url** to `http://YOUR_ELASTIC_IP:3000/api/v1` |

Set `CORS_ORIGINS` on whichever API is active to include `https://YOUR_USERNAME.github.io`. See [DEPLOY_AWS.md](DEPLOY_AWS.md) for EC2 setup.

---

## Step 4 — Verify

- Open `https://YOUR_USERNAME.github.io/REPO_NAME/`
- Home page should list products (if API is up and CORS allows your Pages origin)
- Add to cart → checkout → mock pay (if Razorpay keys not set on API)

---

## CORS (if API on Render)

In Render env for the API service set:

```
CORS_ORIGINS=https://YOUR_USERNAME.github.io
```

Or include the full path origin with repo name.

---

## Why the live UI looks old but products changed

| What | Where it lives | Updates when |
|------|----------------|--------------|
| Product list (no creams, etc.) | **Render API** + MongoDB | You redeploy API / run seed |
| Checkout, COD, addresses, cart UI | **GitHub Pages** static build | **Deploy GitHub Pages** workflow succeeds |

If the UI still shows mock payment or old checkout, the **Pages build failed** or did not run. Check **Actions** → **Deploy GitHub Pages** → latest run must be green.

Common fix: `cd web && npm run build` must pass locally before push. A TypeScript error blocks the new UI from publishing.

## Updating the product catalog

Products and categories come from the **API database** (MongoDB), not from the static Pages build alone.

1. Change `apps/api/scripts/seed.py` and push to `main`
2. Re-run seed on the API: `cd apps/api && python -m scripts.seed` (local) or redeploy Render (build runs seed automatically)
3. Re-run **Deploy GitHub Pages** workflow so the shop UI text and static product pages match

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Old products still show on live site | Redeploy API (re-seed MongoDB) + hard-refresh browser (Cmd+Shift+R) |
| Blank page / 404 on refresh | `basePath` is set automatically in CI from repo name |
| No products | API down or wrong `NEXT_PUBLIC_API_URL` |
| CORS error in browser | Add GitHub Pages URL to `CORS_ORIGINS` on API |
| Images broken on Pages | Product images use external URLs (Unsplash) in seed — OK for demo |

---

## Manual deploy (optional)

```bash
cd web
export GITHUB_PAGES=true
export NEXT_PUBLIC_BASE_PATH=/REPO_NAME
export NEXT_PUBLIC_API_URL=https://your-api.onrender.com/api/v1
npm run build
# output in web/out — upload to gh-pages branch or use Actions
```
