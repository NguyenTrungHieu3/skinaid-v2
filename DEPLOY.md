# SkinAid — Hướng dẫn Deploy Production (AWS EC2)

> **Tài liệu này dành cho lần deploy đầu tiên và các lần update tiếp theo.**  
> Tech stack: FastAPI (backend) · FastAPI (AI service) · React + Vite (frontend) · PostgreSQL · Redis · Qdrant · Nginx · Docker Compose

---

## 🖥️ Cấu hình EC2 khuyến nghị

| Component | Spec tối thiểu | Spec khuyến nghị |
|-----------|---------------|-----------------|
| **Instance type** | `t3.large` (2 vCPU / 8 GB) | `t3.xlarge` (4 vCPU / 16 GB) |
| **OS** | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| **Storage** | 50 GB gp3 | 100 GB gp3 |
| **Region** | ap-southeast-1 (Singapore) | ap-southeast-1 |

> **Tại sao cần nhiều RAM?**  
> AI service (`torch` + YOLO + EfficientNet) cần ~2 GB RAM. Backend cần ~1 GB. Cộng dịch vụ khác → tổng ~4.5 GB → cần ít nhất `t3.large` (8 GB).

---

## 🔒 Security Group Rules

Tạo Security Group với các inbound rules sau:

| Type | Protocol | Port | Source | Mục đích |
|------|----------|------|--------|---------|
| SSH | TCP | 22 | `YOUR_IP/32` | Quản trị server |
| HTTP | TCP | 80 | `0.0.0.0/0` | Let's Encrypt + redirect HTTPS |
| HTTPS | TCP | 443 | `0.0.0.0/0` | Traffic chính |

> **⚠️ KHÔNG mở:** 5432 (PostgreSQL), 6379 (Redis), 6333 (Qdrant), 8000 (Backend), 8001 (AI). Chỉ Nginx mới expose ra ngoài.

---

## 🔗 Elastic IP

**Tại sao cần Elastic IP?**  
Public IP của EC2 thay đổi mỗi lần restart. Elastic IP là IP tĩnh, cần thiết để:
- Trỏ domain (A record) ổn định
- SSL certificate hợp lệ (Let's Encrypt gắn với domain)

**Cách gắn Elastic IP:**
1. AWS Console → EC2 → **Elastic IPs** → **Allocate Elastic IP address**
2. Chọn IP vừa tạo → **Actions** → **Associate Elastic IP address**
3. Chọn EC2 instance → **Associate**

---

## 🚀 Lần deploy đầu tiên (Step-by-step)

### Bước 1 — SSH vào EC2

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<ELASTIC_IP>
```

### Bước 2 — Clone repository

```bash
cd /opt
sudo git clone https://github.com/your-org/skinaid-v2.git skinaid
sudo chown -R ubuntu:ubuntu skinaid
cd skinaid
```

### Bước 3 — Tạo file environment

```bash
cp .env.example backend/.env.prod
nano backend/.env.prod

cp .env.example ai_ml/.env.prod
nano ai_ml/.env.prod
```

**Các giá trị BẮT BUỘC phải thay (tìm `CHANGE_ME`):**

| Variable | Mô tả |
|----------|-------|
| `DB_PASSWORD` | Mật khẩu PostgreSQL mạnh |
| `SECRET_KEY` | JWT secret key, ≥ 32 ký tự ngẫu nhiên |
| `OPEN_API_KEY` | OpenAI API key |
| `SMTP_PASSWORD` | Gmail App Password |
| `GEOAPIFY_API_KEY` | Geoapify Map API |
| `AI_API_KEY` | Internal key backend → AI service |
| `BASE_URL` | `https://yourdomain.com` |
| `CORS_ORIGINS` | `https://yourdomain.com` |
| `VITE_API_URL` | `https://yourdomain.com/api/v1` |
| `VITE_BACKEND_URL` | `https://yourdomain.com` |

**Tạo SECRET_KEY ngẫu nhiên:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Bước 4 — Chạy setup-ec2.sh

```bash
chmod +x scripts/setup-ec2.sh
sudo ./scripts/setup-ec2.sh
exit  # logout
ssh -i your-key.pem ubuntu@<ELASTIC_IP>  # login lại để docker group có hiệu lực
```

### Bước 5 — Trỏ DNS và lấy SSL cert

```bash
# Phải trỏ A record trước:
# yourdomain.com → <ELASTIC_IP>
dig +short yourdomain.com  # xác nhận DNS đã propagate

# Lấy SSL cert
sudo certbot certonly --standalone \
    -d yourdomain.com \
    -d www.yourdomain.com \
    --email your@email.com \
    --agree-tos --no-eff-email

# Copy certs
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
sudo chown ubuntu:ubuntu nginx/ssl/*.pem
```

**Tự động renew cert:**
```bash
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/skinaid/nginx/ssl/ && cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/skinaid/nginx/ssl/ && docker exec skinaid_nginx nginx -s reload") | crontab -
```

### Bước 6 — Cập nhật domain trong nginx.conf

```bash
sed -i 's/yourdomain.com/YOUR_ACTUAL_DOMAIN.com/g' nginx/nginx.conf
sed -i 's/yourdomain.com/YOUR_ACTUAL_DOMAIN.com/g' nginx/nginx.prod.conf
```

### Bước 7 — Build và khởi động

```bash
chmod +x scripts/deploy.sh

# Lần đầu: build tất cả (mất 15-30 phút do torch nặng)
docker compose -f docker-compose.prod.yml up -d --build

# Theo dõi startup
docker compose -f docker-compose.prod.yml logs -f --tail=50
```

### Bước 8 — Verify

```bash
curl -s https://yourdomain.com/health | python3 -m json.tool
curl -s https://yourdomain.com/nginx-health
docker compose -f docker-compose.prod.yml ps
```

---

## 🔄 Update Code (Sau lần đầu)

```bash
cd /opt/skinaid

./scripts/deploy.sh                # Deploy tất cả
./scripts/deploy.sh backend        # Chỉ backend
./scripts/deploy.sh frontend       # Chỉ frontend
./scripts/deploy.sh --skip-build   # Restart mà không build lại
```

---

## 💾 Data Persistence

Docker volumes lưu tại `/var/lib/docker/volumes/` trên EC2 host:

| Volume | Chứa gì |
|--------|---------|
| `skinaid-v2_postgres_data` | Database PostgreSQL |
| `skinaid-v2_redis_data` | Redis cache + sessions |
| `skinaid-v2_qdrant_data` | Vector embeddings |
| `skinaid-v2_backend_uploads` | Ảnh scan của users |
| `skinaid-v2_ai_model_weights` | Model weights |

### Backup

```bash
mkdir -p backups

# Backup Qdrant vectors
docker run --rm \
    -v skinaid-v2_qdrant_data:/data \
    -v $(pwd)/backups:/backup \
    ubuntu \
    tar czf /backup/qdrant-backup-$(date +%Y%m%d).tar.gz /data

# Backup PostgreSQL
docker exec skinaid_postgres \
    pg_dump -U $DB_USER $DB_NAME \
    | gzip > backups/postgres-backup-$(date +%Y%m%d).sql.gz

# Backup uploaded images
docker run --rm \
    -v skinaid-v2_backend_uploads:/data \
    -v $(pwd)/backups:/backup \
    ubuntu \
    tar czf /backup/uploads-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore

```bash
# Restore Qdrant
docker run --rm \
    -v skinaid-v2_qdrant_data:/data \
    -v $(pwd)/backups:/backup \
    ubuntu \
    bash -c "cd / && tar xzf /backup/qdrant-backup-20240101.tar.gz"

# Restore PostgreSQL
gunzip < backups/postgres-backup-20240101.sql.gz \
    | docker exec -i skinaid_postgres psql -U $DB_USER $DB_NAME
```

---

## 📊 Monitoring

```bash
# Logs realtime
docker compose -f docker-compose.prod.yml logs -f --tail=100
docker compose -f docker-compose.prod.yml logs -f --tail=100 backend
docker compose -f docker-compose.prod.yml logs -f --tail=100 ai_ml

# Resource usage
docker stats
docker compose -f docker-compose.prod.yml ps

# Container health
docker inspect --format='{{.Name}}: {{.State.Health.Status}}' \
    $(docker compose -f docker-compose.prod.yml ps -q)
```

**Alerting khuyến nghị:**
- **UptimeRobot** (free): Monitor `https://yourdomain.com/health` mỗi 5 phút, alert email/Telegram
- **AWS CloudWatch**: CPU, RAM, disk alarms
- **Grafana + Prometheus**: Full observability (self-hosted)

---

## 🛠️ Troubleshooting

| Triệu chứng | Nguyên nhân | Fix |
|-------------|------------|-----|
| AI service không start | Model file không có / path sai | `docker exec skinaid_ai ls -lh /app/models/` |
| Backend 500 | DB chưa ready | `docker inspect skinaid_postgres | grep Health -A5` |
| Nginx 502 | Backend chưa start | `docker compose restart nginx` |
| Hết disk | Images cũ / logs | `docker image prune -f` |
| SSL lỗi | Cert hết hạn | `certbot renew` |

---

## 📋 Quick Reference

```bash
docker compose -f docker-compose.prod.yml up -d          # Start all
docker compose -f docker-compose.prod.yml down            # Stop all
docker compose -f docker-compose.prod.yml restart backend # Restart 1 service
docker compose -f docker-compose.prod.yml logs -f backend # Logs
./scripts/deploy.sh backend                               # Deploy update
docker exec skinaid_postgres pg_dump -U postgres skinaid_db > backup.sql
```
