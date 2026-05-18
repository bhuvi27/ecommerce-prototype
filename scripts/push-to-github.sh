#!/bin/bash
# Push this project to GitHub and enable Pages (run after creating an empty repo on github.com)
set -e
REPO_URL="${1:?Usage: ./scripts/push-to-github.sh https://github.com/USERNAME/REPO.git}"

git init 2>/dev/null || true
git add .
git commit -m "Beauty store: FastAPI backend, Next.js web, docs and GitHub Pages" || true
git branch -M main
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"
git push -u origin main

echo ""
echo "Done. Next steps:"
echo "1. GitHub repo → Settings → Pages → Source: GitHub Actions"
echo "2. Wait for 'Deploy GitHub Pages' workflow to finish"
echo "3. Site: https://YOUR_USERNAME.github.io/REPO_NAME/"
echo "4. For live API: deploy render.yaml on Render.com, then set repo Variable NEXT_PUBLIC_API_URL"
