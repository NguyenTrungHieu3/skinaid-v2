#!/usr/bin/env bash
# =================================================================
# scripts/setup-jenkins.sh — Cài Jenkins và cấu hình CI/CD
# =================================================================
# Chạy trên EC2 SAU KHI đã chạy setup-ec2.sh
# Usage: chmod +x scripts/setup-jenkins.sh && ./scripts/setup-jenkins.sh
# =================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

DEPLOY_DIR="/opt/skinaid"
JENKINS_HOME="/var/lib/docker/volumes/skinaid_jenkins_data/_data"

info "=== Jenkins CI/CD Setup ========================================"

# =================================================================
# 1. Mở port 8080 trên UFW cho Jenkins UI
# =================================================================
info "[1/5] Mở port 8080 cho Jenkins UI..."
# Chỉ mở cho IP của bạn — KHÔNG mở public
read -p "$(echo -e "${YELLOW}Nhập YOUR_IP để mở Jenkins UI (ví dụ: 203.0.113.50):${NC} ")" \
    YOUR_IP

if [[ -z "$YOUR_IP" ]]; then
    warn "Bỏ qua — Jenkins UI sẽ không truy cập được từ bên ngoài"
    warn "Dùng SSH tunnel thay thế: ssh -L 8080:localhost:8080 ubuntu@<EC2_IP>"
else
    sudo ufw allow from "$YOUR_IP" to any port 8080 proto tcp \
        comment "Jenkins UI - ${YOUR_IP}"
    success "Port 8080 open cho $YOUR_IP"
fi

# =================================================================
# 2. Khởi động Jenkins container
# =================================================================
info "[2/5] Khởi động Jenkins container..."
cd "$DEPLOY_DIR"

docker compose -f docker-compose.jenkins.yml up -d

info "Chờ Jenkins khởi động (tối đa 2 phút)..."
TRIES=0
while ! curl -sf http://localhost:8080/login > /dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [ $TRIES -gt 40 ]; then
        error "Jenkins không start được sau 2 phút. Xem logs:"
        docker compose -f docker-compose.jenkins.yml logs --tail=30
        exit 1
    fi
    sleep 3
    printf "."
done
echo ""
success "Jenkins đang chạy tại http://localhost:8080"

# =================================================================
# 3. Lấy initial admin password
# =================================================================
info "[3/5] Lấy Initial Admin Password..."
sleep 5  # Đợi file được ghi

ADMIN_PASSWORD=""
if docker exec skinaid_jenkins test -f /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null; then
    ADMIN_PASSWORD=$(docker exec skinaid_jenkins \
        cat /var/jenkins_home/secrets/initialAdminPassword)
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Jenkins Initial Admin Password:           ║${NC}"
    echo -e "${GREEN}║                                            ║${NC}"
    echo -e "${GREEN}║  ${YELLOW}${ADMIN_PASSWORD}${GREEN}  ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
else
    warn "Password file chưa ready. Lấy thủ công:"
    echo "  docker exec skinaid_jenkins cat /var/jenkins_home/secrets/initialAdminPassword"
fi

# =================================================================
# 4. Cấu hình SSH key cho Jenkins pull GitHub
# =================================================================
info "[4/5] Tạo SSH key cho Jenkins → GitHub..."

# Tạo SSH key trong Jenkins container
docker exec skinaid_jenkins bash -c "
    mkdir -p /var/jenkins_home/.ssh
    if [ ! -f /var/jenkins_home/.ssh/id_ed25519 ]; then
        ssh-keygen -t ed25519 -C 'jenkins@skinaid-ci' \
            -f /var/jenkins_home/.ssh/id_ed25519 -N ''
        chmod 700 /var/jenkins_home/.ssh
        chmod 600 /var/jenkins_home/.ssh/id_ed25519
        echo 'StrictHostKeyChecking no' >> /var/jenkins_home/.ssh/config
    fi
"

echo ""
echo -e "${YELLOW}=== GitHub Deploy Key (thêm vào repo Settings → Deploy Keys) ===${NC}"
docker exec skinaid_jenkins cat /var/jenkins_home/.ssh/id_ed25519.pub
echo ""
echo -e "${YELLOW}Tên key: SkinAid Jenkins CI${NC}"
echo -e "${YELLOW}Read access: ✅ (không cần write)${NC}"

# =================================================================
# 5. Hướng dẫn tiếp theo
# =================================================================
info "[5/5] Hoàn tất setup cơ bản"

echo ""
echo -e "${GREEN}=================================================================${NC}"
echo -e "${GREEN}  Jenkins Setup HOÀN TẤT!${NC}"
echo -e "${GREEN}=================================================================${NC}"
echo ""
echo -e "${YELLOW}BƯỚC TIẾP THEO (thực hiện thủ công trên Jenkins UI):${NC}"
echo ""
echo -e "  1. Truy cập Jenkins: http://<EC2_IP>:8080"
echo -e "     Hoặc SSH tunnel: ssh -L 8080:localhost:8080 ubuntu@<EC2_IP>"
echo ""
echo -e "  2. Đăng nhập bằng password ở trên"
echo ""
echo -e "  3. Install suggested plugins (bấm 'Install suggested plugins')"
echo ""
echo -e "  4. Tạo Jenkins Pipeline job:"
echo -e "     New Item → 'SkinAid-Production' → Pipeline → OK"
echo -e "     → Definition: 'Pipeline script from SCM'"
echo -e "     → SCM: Git"
echo -e "     → Repository URL: git@github.com:your-org/skinaid-v2.git"
echo -e "     → Credentials: thêm SSH key từ /var/jenkins_home/.ssh/id_ed25519"
echo -e "     → Branches: */production"
echo -e "     → Script Path: Jenkinsfile"
echo ""
echo -e "  5. Thêm webhook trên GitHub:"
echo -e "     Repo → Settings → Webhooks → Add webhook"
echo -e "     Payload URL: http://<EC2_IP>:8080/github-webhook/"
echo -e "     Content type: application/json"
echo -e "     Events: Pushes (hoặc Pull request merges)"
echo ""
echo -e "  6. Test pipeline:"
echo -e "     Build Now → xem Console Output"
echo ""
echo -e "${YELLOW}Để tắt Jenkins:${NC}"
echo -e "  docker compose -f docker-compose.jenkins.yml down"
echo ""
