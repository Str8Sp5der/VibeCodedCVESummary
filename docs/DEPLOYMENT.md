# Deployment Guide - CVE Database Application

**Version**: 1.0.0  
**Last Updated**: 2024-02-15

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Development Deployment](#development-deployment)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Database Setup](#database-setup)
7. [Environment Configuration](#environment-configuration)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Scaling](#scaling)

---

## System Requirements

### Minimum Requirements

| Component | Development | Production |
|-----------|-------------|-----------|
| **CPU** | 2 cores | 4 cores (8+ recommended) |
| **RAM** | 4 GB | 8 GB (16+ recommended) |
| **Disk** | 20 GB | 100 GB (with database growth) |
| **OS** | Linux, macOS, Windows | Linux (Ubuntu 20.04+, CentOS 8+) |
| **Network** | - | 100 Mbps+ connection |

### Software Prerequisites

```bash
# Core requirements
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Docker 20.10+ (optional)
- Docker Compose 1.29+ (optional)

# Development tools
- Git 2.30+
- pip (Python package manager)
- npm (Node package manager)
```

### Installation Verification

```bash
# Verify Python
python --version  # Should be 3.11+

# Verify Node.js
node --version    # Should be 18+

# Verify PostgreSQL
psql --version    # Should be 13+

# Verify Docker (if using)
docker --version
docker-compose --version
```

---

## Pre-Deployment Checklist

- [ ] Source code cloned from repository
- [ ] All environment files (.env) configured
- [ ] Database credentials verified
- [ ] API keys obtained (NVD, Exploit-DB)
- [ ] SSL certificates ready (production)
- [ ] Domain name DNS configured (production)
- [ ] Security group/firewall rules defined
- [ ] Backup strategy documented
- [ ] Monitoring tools configured
- [ ] Load balancer configured (if scaling)

---

## Development Deployment

### Quick Start (Local Development)

```bash
# 1. Clone repository
git clone https://github.com/your-repo/cve-database.git
cd cve-database

# 2. Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Install Node dependencies
cd frontend
npm install
cd ..

# 5. Create .env file
cp backend/.env.example backend/.env
# Edit backend/.env with your settings

# 6. Initialize database
python -c "from backend.database import init_db, engine; init_db(engine)"

# 7. Start backend (Terminal 1)
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 8. Start frontend (Terminal 2)
cd frontend
npm run dev

# 9. Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Backend Start

```bash
# Option 1: Development mode (auto-reload)
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Option 2: Production mode (single worker)
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1

# Option 3: Production mode (multiple workers)
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop
```

### Manual Frontend Start

```bash
# Development
npm run dev

# Production build
npm run build
npm run preview  # Preview production build locally
```

---

## Production Deployment

### Architecture

```
┌─────────────────────────────────────────────┐
│          Domain: api.cve-app.com            │
│              (DNS A record)                 │
└────────────────────┬────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │   Load Balancer       │
         │  (AWS ELB / nginx)    │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼──┐        ┌───▼──┐        ┌───▼──┐
│ App1 │        │ App2 │        │ App3 │
│:8000 │        │:8000 │        │:8000 │
└───┬──┘        └───┬──┘        └───┬──┘
    │                │                │
    └────────────────┼────────────────┘
                     │
            ┌────────▼────────┐
            │   PostgreSQL    │
            │   Primary DB    │
            └─────────────────┘
```

### Production Environment Setup

```bash
# 1. Create production directory structure
mkdir -p /opt/cve-app/{backend,frontend,config,logs}
cd /opt/cve-app

# 2. Clone repository
git clone https://github.com/your-repo/cve-database.git .

# 3. Configure production environment
cp backend/.env.example backend/.env.prod
nano backend/.env.prod  # Edit with production values

# 4. Create systemd service files
sudo tee /etc/systemd/system/cve-app-backend.service > /dev/null <<EOF
[Unit]
Description=CVE Database Backend
After=network.target postgresql.service

[Service]
Type=notify
User=cve-app
WorkingDirectory=/opt/cve-app/backend
Environment="PATH=/opt/cve-app/venv/bin"
EnvironmentFile=/opt/cve-app/backend/.env.prod
ExecStart=/opt/cve-app/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 5. Create frontend service
sudo tee /etc/systemd/system/cve-app-frontend.service > /dev/null <<EOF
[Unit]
Description=CVE Database Frontend
After=network.target cve-app-backend.service

[Service]
Type=simple
User=cve-app
WorkingDirectory=/opt/cve-app/frontend
EnvironmentFile=/opt/cve-app/frontend/.env.prod
ExecStart=/usr/bin/npm run preview
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 6. Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable cve-app-backend cve-app-frontend
sudo systemctl start cve-app-backend cve-app-frontend

# 7. Verify services
sudo systemctl status cve-app-backend cve-app-frontend
```

### Nginx Reverse Proxy Configuration

```nginx
# /etc/nginx/sites-available/cve-app

upstream backend {
    server localhost:8000 weight=1;
    server localhost:8000 weight=1;  # Multiple backends for load balancing
    keepalive 32;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    listen [::]:80;
    
    # Redirect HTTP to HTTPS
    server_name api.cve-app.com cve-app.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    server_name api.cve-app.com;
    
    # SSL Certificates (from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/cve-app.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cve-app.com/privkey.pem;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Logging
    access_log /var/log/nginx/cve-app-access.log combined;
    error_log /var/log/nginx/cve-app-error.log;
    
    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Admin endpoints
    location /admin/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Auth endpoints
    location /auth/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # OpenAPI docs
    location /docs {
        proxy_pass http://backend;
    }
    
    location /redoc {
        proxy_pass http://backend;
    }
    
    location /openapi.json {
        proxy_pass http://backend;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    server_name cve-app.com;
    
    # SSL (same certificates)
    ssl_certificate /etc/letsencrypt/live/cve-app.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cve-app.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable Nginx site:
```bash
sudo ln -s /etc/nginx/sites-available/cve-app /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### SSL Certificate Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone \
  -d api.cve-app.com \
  -d cve-app.com \
  --agree-tos \
  --email admin@cve-app.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renewal
sudo certbot renew --dry-run
```

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: cve-db-prod
    environment:
      POSTGRES_DB: cve_db
      POSTGRES_USER: cve_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "-c max_connections=100 -c shared_buffers=256MB"
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cve_user -d cve_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cve-network
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: cve-api-prod
    environment:
      DATABASE_URL: postgresql+psycopg2://cve_user:${DB_PASSWORD}@postgres:5432/cve_db
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      NVD_API_KEY: ${NVD_API_KEY}
      EXPLOIT_DB_API_KEY: ${EXPLOIT_DB_API_KEY}
      DEBUG: "false"
      ALLOWED_ORIGINS: "https://cve-app.com,https://api.cve-app.com"
    depends_on:
      postgres:
        condition: service_healthy
    expose:
      - 8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - cve-network
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        VITE_API_URL: "https://api.cve-app.com"
    container_name: cve-web-prod
    expose:
      - 3000
    depends_on:
      - backend
    networks:
      - cve-network
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  postgres_data_prod:
    driver: local

networks:
  cve-network:
    driver: bridge
```

Deploy:
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

---

## Database Setup

### PostgreSQL Initial Setup

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE cve_db;
CREATE USER cve_user WITH PASSWORD 'strong_password_here';
ALTER ROLE cve_user SET client_encoding TO 'utf8';
ALTER ROLE cve_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE cve_user SET default_transaction_deferrable TO on;
ALTER ROLE cve_user SET default_transaction_is default TO off;
GRANT ALL PRIVILEGES ON DATABASE cve_db TO cve_user;
\q
```

### Database Backup Strategy

```bash
# Manual backup
pg_dump -U cve_user -d cve_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backup (crontab)
0 2 * * * pg_dump -U cve_user -d cve_db | gzip > /backups/cve_db_$(date +\%Y\%m\%d).sql.gz

# Backup retention (keep 30 days)
0 3 * * * find /backups -name "cve_db_*.sql.gz" -mtime +30 -delete

# Restore from backup
psql -U cve_user -d cve_db < backup_20240215_020000.sql
```

### Database Optimization

```sql
-- Run after initial data load
VACUUM ANALYZE;

-- Index maintenance
REINDEX DATABASE cve_db;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Environment Configuration

### Backend .env.prod

```bash
# .env.prod - Production configuration

# Database
DATABASE_URL=postgresql+psycopg2://cve_user:password@db-host:5432/cve_db

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-min-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Security
DEBUG=false
ALLOWED_ORIGINS=https://cve-app.com,https://api.cve-app.com

# API Keys
NVD_API_KEY=your-nvd-api-key
EXPLOIT_DB_API_KEY=your-exploitdb-api-key

# Encryption
ENCRYPTION_KEY=your-encryption-key-base64-encoded

# Sync Configuration
DELTA_SYNC_INTERVAL=10  # minutes
FULL_SYNC_INTERVAL=1440  # minutes (24 hours)

# Rate Limiting
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_LOGIN_PER_HOUR=10

# Logging
LOG_LEVEL=INFO
```

### Frontend .env.prod

```bash
# .env.prod - Production configuration

VITE_API_URL=https://api.cve-app.com
VITE_APP_TITLE=CVE Database
VITE_APP_VERSION=1.0.0
```

Generate secure keys:
```bash
# Generate JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Monitoring & Maintenance

### Application Monitoring

```bash
# Monitor backend logs
tail -f /var/log/cve-app/backend.log

# Monitor frontend logs
tail -f /var/log/cve-app/frontend.log

# Check service status
systemctl status cve-app-backend cve-app-frontend

# Monitor system resources
top
htop
free -m
df -h
```

### Health Checks

```bash
# Backend health
curl https://api.cve-app.com/health

# Frontend status
curl https://cve-app.com

# Database connection
psql -U cve_user -d cve_db -c "SELECT NOW();"
```

### Scheduled Maintenance

```bash
# Weekly security updates
0 3 * * 0 apt update && apt upgrade -y

# Monthly database optimization
0 4 1 * * PGPASSWORD=password pg_dump -U cve_user cve_db | PGPASSWORD=password psql -U cve_user cve_db

# Log rotation
0 0 * * * logrotate -f /etc/logrotate.d/cve-app
```

---

## Troubleshooting

### Common Issues

#### Backend fails to connect to database
```bash
# Test PostgreSQL connection
psql -h localhost -U cve_user -d cve_db

# Check DATABASE_URL format
echo $DATABASE_URL

# Verify PostgreSQL is running
systemctl status postgresql
```

#### Frontend not loading
```bash
# Check frontend build
npm run build

# Verify Nginx proxy
curl -v http://localhost:3000

# Check Nginx logs
tail -f /var/log/nginx/cve-app-error.log
```

#### Rate limiting not working
```bash
# Verify middleware is loaded
grep -n "rate_limit" backend/app.py

# Test rate limit
for i in {1..15}; do curl https://api.cve-app.com/api/cves; done
# Should see 429 status on requests > 10
```

#### NVD Sync fails
```bash
# Check API key
curl -H "apiKey: $NVD_API_KEY" https://services.nvd.nist.gov/rest/json/cves/1.0

# Check sync logs
grep "nvd_sync" /var/log/cve-app/backend.log

# Manually trigger sync
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST https://api.cve-app.com/admin/sync/trigger
```

#### Database grows too large
```bash
# Analyze database size
psql -U cve_user -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database ORDER BY pg_database_size(pg_database.datname) DESC;"

# Vacuum and analyze
VACUUM ANALYZE;

# Remove old audit logs (keep 90 days)
DELETE FROM audit_logs WHERE timestamp < NOW() - INTERVAL '90 days';
```

---

## Scaling

### Horizontal Scaling

```bash
# Deploy multiple backend instances (Docker Swarm or Kubernetes)

# Docker Swarm example
docker service create \
  --name cve-backend \
  --replicas 3 \
  --publish 8000:8000 \
  my-registry/cve-backend:latest

# Kubernetes example (kubectl)
kubectl scale deployment cve-backend-deployment --replicas=5
```

### Vertical Scaling

Upgrade server resources:
- Increase CPU cores (currently 2 → 8)
- Increase RAM (currently 4GB → 16GB)
- Upgrade storage (currently 20GB → 100GB+)
- Enable SSD for database

Then restart services:
```bash
systemctl restart cve-app-backend cve-app-frontend postgresql
```

---

**Deployment Guide Version**: 1.0.0  
**Last Updated**: 2024-02-15

For additional support, see [README.md](../README.md) or [SECURITY.md](./SECURITY.md)
