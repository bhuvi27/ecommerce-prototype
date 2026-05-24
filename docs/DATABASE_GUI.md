# Database GUI — local and EC2

Use the **same three apps** for both environments. Switch by connection host/port.

| App | Postgres | MongoDB | Redis |
|-----|----------|---------|-------|
| **DBeaver** | Yes | — | — |
| **MongoDB Compass** | — | Yes | — |
| **Redis Insight** | — | — | Yes |

Installed via Homebrew: `dbeaver-community`, `mongodb-compass`, `redis-insight`.

---

## Quick start

```bash
# View LOCAL data (Mac Docker must be running: docker compose up -d)
./scripts/db-gui.sh local

# View EC2 data (starts SSH tunnel automatically)
./scripts/db-gui.sh ec2

# Print all connection strings
./scripts/db-gui.sh connections

# Fix DBeaver (Postgres): install LOCAL + EC2 in left Connections tree
./scripts/db-gui-setup-dbeaver.sh

# Stop EC2 tunnel when done
./scripts/db-tunnel-ec2.sh stop
```

---

## Connection profiles

Copy env templates once:

```bash
cp config/db-gui/local.env.example config/db-gui/local.env
cp config/db-gui/ec2.env.example config/db-gui/ec2.env
# Edit both files: set POSTGRES_PASSWORD (and EC2_HOST for ec2.env)
```

### Local (`config/db-gui/local.env`)

| Database | Connect to |
|----------|------------|
| Postgres | `localhost:5432` — db `beauty_store`, user `beauty` (password in `local.env`, not committed) |
| MongoDB | `mongodb://localhost:27017/beauty_catalog` |
| Redis | `localhost:6379` |

### EC2 (`config/db-gui/ec2.env`)

Requires tunnel: `./scripts/db-tunnel-ec2.sh start`

| Database | Connect to |
|----------|------------|
| Postgres | `localhost:15432` — db `beauty_store`, user `beauty` (password in `ec2.env`) |
| MongoDB | `mongodb://localhost:27018/beauty_catalog` |
| Redis | `localhost:16379` |

Different local ports (15432, 27018, 16379) avoid clashing with local Docker.

---

## One-time GUI setup (save both profiles)

### DBeaver — two Postgres connections (automated)

```bash
./scripts/db-gui-setup-dbeaver.sh
```

Left **Connections** panel:

```
Beauty Store
  ├── Beauty Store LOCAL   (localhost:5432)
  └── Beauty Store EC2     (localhost:15432)
```

**Browse tables:** connect → **Databases → beauty_store → Schemas → public → Tables**

**Run SQL:** right-click connection → **SQL Editor → New SQL Script**

| Connection | Host | Port | User | Password | Database |
|------------|------|------|------|----------|----------|
| Beauty Store LOCAL | localhost | 5432 | beauty | beauty | beauty_store |
| Beauty Store EC2 | localhost | 15432 | beauty | beauty | beauty_store |

EC2 requires `./scripts/db-tunnel-ec2.sh start` first.

### MongoDB Compass — two favorites

1. **LOCAL**: `mongodb://localhost:27017/beauty_catalog`
2. **EC2**: `mongodb://localhost:27018/beauty_catalog` (tunnel required)

Save both as favorites.

### Redis Insight — two databases

1. **LOCAL**: Host `localhost`, Port `6379`, name `beauty-local`
2. **EC2**: Host `localhost`, Port `16379`, name `beauty-ec2` (tunnel required)

---

## Useful tables / collections

| Postgres tables | Mongo collections |
|-------------------|-------------------|
| `users`, `orders`, `order_items`, `addresses` | `products`, `categories` |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| DBeaver left panel (Connections tree) missing | **Window → Show View → Connections**, or **Window → Reset Perspective**. You may have closed the panel with the X on the left tab bar. |
| DBeaver shows connection but no tables | Expand **Schemas → public → Tables** (not only the connection name). Double-click connection to connect first. |
| DBeaver SCRAM / no password | Run `./scripts/db-gui-setup-dbeaver.sh` (reads `config/db-gui/local.env`). Or edit connection → **Authentication** → set user/password from your `.env` files, check **Save password**. |
| DBeaver duplicate LOCAL/EC2 entries | Delete extras in Connections panel. Only keep one `data-sources.json` (remove `data-sources-beauty.json` from `.dbeaver` if present). |
| DBeaver old `beauty_store` / `postgres` entries | Right-click → Delete in DBeaver; re-run setup script. |
| EC2 Postgres connection refused | Run `./scripts/db-tunnel-ec2.sh start` |
| Local connection refused | Run `docker compose up -d` on your Mac |
| EC2 still fails after tunnel | EC2 compose must expose DB on `127.0.0.1` (see `docker-compose.prod.yml`) |

See also [DEPLOY_AWS.md](DEPLOY_AWS.md).
