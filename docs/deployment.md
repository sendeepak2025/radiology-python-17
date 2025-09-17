# Kiro-mini Deployment Guide

This guide covers deploying Kiro-mini in production environments.

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8 GB
- Storage: 100 GB SSD
- Network: 1 Gbps

**Recommended Requirements:**
- CPU: 8 cores
- RAM: 16 GB
- Storage: 500 GB SSD
- Network: 10 Gbps

### Software Dependencies

- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 12+
- Redis 6+
- Nginx (for reverse proxy)
- SSL certificates

## Production Deployment

### 1. Environment Setup

Create production environment file:

```bash
# Create production directory
mkdir -p /opt/kiro-mini
cd /opt/kiro-mini

# Create environment file
cat > .env.prod << EOF
# Database Configuration
DATABASE_URL=postgresql://kiro_user:secure_password@postgres:5432/kiro_mini_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_POOL_SIZE=10

# Security
SECRET_KEY=your_very_secure_secret_key_here
WEBHOOK_SECRET=your_webhook_secret_here
JWT_SECRET_KEY=your_jwt_secret_here

# External Services
ORTHANC_URL=http://orthanc:8042
ORTHANC_USERNAME=orthanc
ORTHANC_PASSWORD=orthanc_password
AI_SERVICE_URL=http://ai-service:8080
AI_SERVICE_API_KEY=your_ai_api_key

# Performance Settings
MAX_WORKERS=8
QUEUE_BATCH_SIZE=20
WORKER_CONCURRENCY=4

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# CORS Settings
CORS_ORIGINS=["https://your-frontend-domain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Backup Settings
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"
BACKUP_RETENTION_DAYS=30
EOF
```

### 2. Docker Compose Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: kiro_mini_prod
      POSTGRES_USER: kiro_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kiro_user -d kiro_mini_prod"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    env_file:
      - .env.prod
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: python worker_manager.py
    env_file:
      - .env.prod
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
    restart: unless-stopped

  orthanc:
    image: orthancteam/orthanc:latest
    ports:
      - "4242:4242"
      - "8042:8042"
    volumes:
      - orthanc_data:/var/lib/orthanc/db
      - ./orthanc.json:/etc/orthanc/orthanc.json
    restart: unless-stopped
    environment:
      ORTHANC_USERNAME: orthanc
      ORTHANC_PASSWORD: orthanc_password

volumes:
  postgres_data:
  redis_data:
  orthanc_data:

networks:
  default:
    driver: bridge
```

### 3. Production Dockerfile

Create `Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r app && useradd -r -g app app

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### 4. Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        least_conn;
        server backend:8000 max_fails=3 fail_timeout=30s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=1r/s;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Upload endpoints
        location /upload/ {
            limit_req zone=upload burst=5 nodelay;
            client_max_body_size 100M;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 300s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }

        # Health check
        location /health {
            proxy_pass http://backend;
            access_log off;
        }

        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### 5. Database Migration and Setup

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Create initial admin user (optional)
docker-compose -f docker-compose.prod.yml exec backend python scripts/create_admin_user.py

# Verify database setup
docker-compose -f docker-compose.prod.yml exec postgres psql -U kiro_user -d kiro_mini_prod -c "\dt"
```

### 6. SSL Certificate Setup

Using Let's Encrypt with Certbot:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Set up auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 7. Monitoring Setup

Create `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin_password
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

## Backup and Recovery

### 1. Database Backup

Create backup script `scripts/backup_db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/opt/kiro-mini/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="kiro_mini_backup_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U kiro_user kiro_mini_prod > $BACKUP_DIR/$BACKUP_FILE

# Compress backup
gzip $BACKUP_DIR/$BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

### 2. Automated Backup with Cron

```bash
# Add to crontab
0 2 * * * /opt/kiro-mini/scripts/backup_db.sh >> /var/log/kiro-backup.log 2>&1
```

### 3. Database Recovery

```bash
# Stop services
docker-compose -f docker-compose.prod.yml stop backend worker

# Restore database
gunzip -c /opt/kiro-mini/backups/kiro_mini_backup_YYYYMMDD_HHMMSS.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U kiro_user kiro_mini_prod

# Start services
docker-compose -f docker-compose.prod.yml start backend worker
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow specific services (adjust as needed)
sudo ufw allow from 10.0.0.0/8 to any port 5432  # PostgreSQL
sudo ufw allow from 10.0.0.0/8 to any port 6379  # Redis

# Enable firewall
sudo ufw enable
```

### 2. System Updates

```bash
# Set up automatic security updates
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. Log Monitoring

```bash
# Install fail2ban
sudo apt-get install fail2ban

# Configure fail2ban for nginx
sudo cat > /etc/fail2ban/jail.local << EOF
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /opt/kiro-mini/logs/nginx/error.log
maxretry = 3
bantime = 3600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /opt/kiro-mini/logs/nginx/error.log
maxretry = 10
bantime = 600
EOF

sudo systemctl restart fail2ban
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_studies_patient_id ON studies(patient_id);
CREATE INDEX CONCURRENTLY idx_studies_study_date ON studies(study_date);
CREATE INDEX CONCURRENTLY idx_reports_study_uid ON reports(study_uid);
CREATE INDEX CONCURRENTLY idx_reports_status ON reports(status);
CREATE INDEX CONCURRENTLY idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX CONCURRENTLY idx_audit_logs_user_id ON audit_logs(user_id);

-- Update table statistics
ANALYZE;
```

### 2. Redis Configuration

Add to Redis configuration:

```
# Memory optimization
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
tcp-keepalive 300
timeout 0
```

### 3. Application Tuning

Update `.env.prod`:

```bash
# Connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
REDIS_POOL_SIZE=10

# Worker configuration
MAX_WORKERS=8
WORKER_CONCURRENCY=4
QUEUE_BATCH_SIZE=20

# Caching
CACHE_TTL=3600
ENABLE_QUERY_CACHE=true
```

## Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database credentials secured
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Security hardening applied

### Deployment
- [ ] Build and test Docker images
- [ ] Deploy to staging environment
- [ ] Run integration tests
- [ ] Deploy to production
- [ ] Run database migrations
- [ ] Verify all services are running
- [ ] Test critical workflows

### Post-deployment
- [ ] Monitor system metrics
- [ ] Check application logs
- [ ] Verify backup processes
- [ ] Test disaster recovery
- [ ] Update documentation
- [ ] Notify stakeholders

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

**Database connection issues:**
```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec postgres psql -U kiro_user -d kiro_mini_prod -c "SELECT 1;"
```

**High memory usage:**
```bash
# Check container resource usage
docker stats

# Adjust memory limits in docker-compose.prod.yml
```

**SSL certificate issues:**
```bash
# Check certificate validity
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout

# Renew certificate
sudo certbot renew
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend services
docker-compose -f docker-compose.prod.yml up -d --scale backend=5

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

### Load Balancer Configuration

For multiple servers, use a load balancer like HAProxy or AWS ALB:

```
# HAProxy configuration example
backend kiro_backend
    balance roundrobin
    server kiro1 10.0.1.10:8000 check
    server kiro2 10.0.1.11:8000 check
    server kiro3 10.0.1.12:8000 check
```

This deployment guide provides a comprehensive approach to deploying Kiro-mini in production environments with proper security, monitoring, and scalability considerations.