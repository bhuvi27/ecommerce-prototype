# Deploy web to GitHub Pages (free)

GitHub Pages hosts **static files only** — the Next.js shop UI. Your **Python API and databases** are not run on GitHub Pages; use [Render](https://render.com) (free tier) for the API so visitors get a working shop.

## What gets published

| Published on GitHub Pages | Not on GitHub Pages |
|---------------------------|---------------------|
| Shop UI (browse, cart, checkout screens) | FastAPI backend |
| Login/register forms | PostgreSQL, MongoDB, Redis |
| | MinIO, Razorpay webhooks |

After deploy, set `NEXT_PUBLIC_API_URL` to your Render API URL so the live site can load products and checkout.

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

## Troubleshooting

| Issue | Fix |
|-------|-----|
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
