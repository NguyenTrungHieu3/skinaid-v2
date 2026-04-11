#!/usr/bin/env bash
# =================================================================
# scripts/setup-ec2.sh — SkinAid EC2 One-time Setup
# =================================================================
# Chạy 1 lần duy nhất trên EC2 mới tạo (Ubuntu 22.04 LTS)
# Usage: chmod +x scripts/setup-ec2.sh && sudo ./scripts/setup-ec2.sh
#
# Sau khi script hoàn tất, cần làm thêm:
#   1. Điền .env.prod từ .env.example
#   2. Lấy SSL cert (certbot)
#   3. docker compose -f docker-compose.prod.yml up -d --build
# =================================================================
set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Check root ────────────────────────────────────────────────────
if [[ "$EUID" -ne 0 ]]; then
    error "Script phải chạy bằng sudo: sudo ./scripts/setup-ec2.sh"
    exit 1
fi

info "=== SkinAid EC2 Setup Started ================================="
info "Distro: $(lsb_release -d | cut -f2)"
info "Kernel: $(uname -r)"
echo ""

# =================================================================
# 1. System update
# =================================================================
info "[1/8] Cập nhật hệ thống..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    curl wget git unzip htop \
    ca-certificates gnupg lsb-release \
    ufw fail2ban
success "System packages installed"

# =================================================================
# 2. Install Docker Engine
# =================================================================
info "[2/8] Cài Docker Engine..."
if command -v docker &> /dev/null; then
    warn "Docker đã được cài: $(docker --version)"
else
    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin

    # Start and enable Docker
    systemctl enable docker
    systemctl start docker
    success "Docker installed: $(docker --version)"
fi

# Add ubuntu user to docker group (avoid sudo for docker commands)
if id "ubuntu" &> /dev/null; then
    usermod -aG docker ubuntu
    success "User 'ubuntu' added to docker group"
fi

# =================================================================
# 3. Install Certbot (Let's Encrypt)
# =================================================================
info "[3/8] Cài Certbot (Let's Encrypt)..."
if command -v certbot &> /dev/null; then
    warn "Certbot đã được cài: $(certbot --version)"
else
    apt-get install -y -qq snapd
    snap install core
    snap refresh core
    snap install --classic certbot
    ln -sf /snap/bin/certbot /usr/bin/certbot
    success "Certbot installed: $(certbot --version)"
fi

# =================================================================
# 4. Configure UFW Firewall
# =================================================================
info "[4/8] Cấu hình UFW Firewall..."

ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# SSH — KHÔNG đóng port này trước khi enable UFW!
ufw allow 22/tcp comment "SSH"
# HTTP — Let's Encrypt ACME challenge + redirect to HTTPS
ufw allow 80/tcp comment "HTTP"
# HTTPS — Main traffic
ufw allow 443/tcp comment "HTTPS"

# Không mở:
# 5432 (PostgreSQL)   — internal only
# 6379 (Redis)        — internal only
# 6333 (Qdrant)       — internal only
# 8000 (Backend)      — internal only, nginx proxy
# 8001 (AI service)   — internal only, backend proxy

ufw --force enable
success "UFW enabled: 22 (SSH), 80 (HTTP), 443 (HTTPS)"
ufw status verbose

# =================================================================
# 5. Configure Fail2ban (brute force protection)
# =================================================================
info "[5/8] Cấu hình Fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port    = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s
EOF
systemctl enable fail2ban
systemctl restart fail2ban
success "Fail2ban configured (SSH brute force protection)"

# =================================================================
# 6. Create project directories
# =================================================================
info "[6/8] Tạo thư mục project..."
PROJECT_DIR="/opt/skinaid"
mkdir -p "$PROJECT_DIR"/{nginx/ssl,scripts}

# Docker volume data directories (cho backup dễ hơn)
mkdir -p /opt/skinaid-data/{postgres,redis,qdrant,uploads,logs}
chmod 750 /opt/skinaid-data

success "Directories created: $PROJECT_DIR"

# =================================================================
# 7. Create Docker network (nếu chưa có)
# =================================================================
info "[7/8] Tạo Docker network..."
if docker network ls | grep -q "skinaid_internal"; then
    warn "Network 'skinaid_internal' đã tồn tại"
else
    docker network create skinaid_internal
    success "Network 'skinaid_internal' created"
fi

# =================================================================
# 8. System tuning cho production
# =================================================================
info "[8/8] System tuning..."

# Tăng file descriptor limit (cho nhiều connections)
cat >> /etc/security/limits.conf << 'EOF'
* soft nofile 65536
* hard nofile 65536
EOF

# Tăng max connections cho nginx
cat > /etc/sysctl.d/99-skinaid.conf << 'EOF'
# TCP keep-alive
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
# Allow TIME_WAIT reuse
net.ipv4.tcp_tw_reuse = 1
EOF
sysctl -p /etc/sysctl.d/99-skinaid.conf 2>/dev/null || true

success "System tuning applied"

# =================================================================
# Summary
# =================================================================
echo ""
echo -e "${GREEN}=================================================================${NC}"
echo -e "${GREEN}  EC2 Setup HOÀN TẤT!${NC}"
echo -e "${GREEN}=================================================================${NC}"
echo ""
echo -e "Các bước tiếp theo:"
echo -e "  ${YELLOW}1.${NC} Clone repo vào /opt/skinaid:"
echo -e "     git clone <repo-url> /opt/skinaid"
echo -e "     cd /opt/skinaid"
echo ""
echo -e "  ${YELLOW}2.${NC} Tạo .env.prod:"
echo -e "     cp .env.example backend/.env.prod"
echo -e "     cp .env.example ai_ml/.env.prod"
echo -e "     # Điền giá trị thật vào từng file"
echo ""
echo -e "  ${YELLOW}3.${NC} Lấy SSL cert (cần trỏ DNS trước!):"
echo -e "     sudo certbot certonly --standalone -d yourdomain.com"
echo -e "     sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/"
echo -e "     sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/"
echo ""
echo -e "  ${YELLOW}4.${NC} Deploy:"
echo -e "     chmod +x scripts/deploy.sh"
echo -e "     ./scripts/deploy.sh"
echo ""
echo -e "  ${YELLOW}Note:${NC} Logout và login lại để docker group có hiệu lực"
echo ""
