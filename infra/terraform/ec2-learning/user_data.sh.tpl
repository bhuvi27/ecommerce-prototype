#!/bin/bash
set -euxo pipefail

dnf update -y
dnf install -y docker git openssl
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/download/v2.29.2/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
ln -sf /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
JWT_ACCESS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
JWT_REFRESH=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)

mkdir -p /opt/beauty-store
chown ec2-user:ec2-user /opt/beauty-store
sudo -u ec2-user git clone "${github_repo_url}" /opt/beauty-store

cd /opt/beauty-store
cp apps/api/.env.aws.example apps/api/.env.aws

sed -i "s|https://YOUR_USERNAME.github.io|${github_pages_origin}|g" apps/api/.env.aws
sed -i "s|ELASTIC_IP|$PUBLIC_IP|g" apps/api/.env.aws
sed -i "s|change-me-to-a-random-32-char-string|$JWT_ACCESS|" apps/api/.env.aws
sed -i "s|change-me-to-another-random-32-char-string|$JWT_REFRESH|" apps/api/.env.aws

docker compose -f docker-compose.prod.yml up -d postgres mongo redis minio
docker compose -f docker-compose.prod.yml run --rm minio-init
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.seed
docker compose -f docker-compose.prod.yml up -d api

echo "Beauty store API deployed at http://$PUBLIC_IP:3000" > /var/log/beauty-store-deploy.log
