#!/usr/bin/env bash
# =================================================================
# scripts/deploy.sh — SkinAid Production Deploy Script
# =================================================================
# Usage:
#   ./scripts/deploy.sh                   # Deploy toàn bộ (build all)
#   ./scripts/deploy.sh backend           # Chỉ rebuild backend
#   ./scripts/deploy.sh frontend backend  # Rebuild 2 services
#   ./scripts/deploy.sh --skip-build      # Skip build, chỉ restart
#
# Ví dụ update chỉ frontend sau khi sửa code React:
#   ./scripts/deploy.sh frontend
# =================================================================
set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

COMPOSE_FILE="docker-compose.prod.yml"
DEPLOY_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# ── Parse arguments ───────────────────────────────────────────────
SERVICES=()
SKIP_BUILD=false
for arg in "$@"; do
    case "$arg" in
        --skip-build) SKIP_BUILD=true ;;
        --help|-h)
            echo "Usage: $0 [service...] [--skip-build]"
            echo "  service: backend | frontend | ai_ml | all (default: all)"
            exit 0
            ;;
        *) SERVICES+=("$arg") ;;
    esac
done

info "=== SkinAid Deploy [$DEPLOY_TIMESTAMP] ========================"
info "Compose file : $COMPOSE_FILE"
info "Services     : ${SERVICES[*]:-all}"
info "Skip build   : $SKIP_BUILD"
echo ""

# =================================================================
# Pre-checks
# =================================================================
info "[0/6] Pre-deploy checks..."

if [[ ! -f "$COMPOSE_FILE" ]]; then
    error "Không tìm thấy $COMPOSE_FILE. Chạy từ root project!"
    exit 1
fi

if [[ ! -f "backend/.env.prod" ]]; then
    error "backend/.env.prod không tồn tại! Tạo từ .env.example trước."
    exit 1
fi

if [[ ! -f "ai_ml/.env.prod" ]]; then
    error "ai_ml/.env.prod không tồn tại! Tạo từ .env.example trước."
    exit 1
fi

if [[ ! -f "nginx/ssl/fullchain.pem" ]] || [[ ! -f "nginx/ssl/privkey.pem" ]]; then
    warn "SSL certs chưa có trong nginx/ssl/. HTTPS sẽ không hoạt động!"
    warn "Chạy: sudo certbot certonly --standalone -d yourdomain.com"
fi

success "Pre-checks passed"

# =================================================================
# 1. Git Pull
# =================================================================
info "[1/6] Git pull latest code..."
git_status=$(git status --porcelain 2>/dev/null || echo "")
if [[ -n "$git_status" ]]; then
    warn "Có uncommitted changes. Stash hoặc commit trước khi deploy."
    git status --short
    read -p "$(echo -e "${YELLOW}Tiếp tục? [y/N]:${NC} ")" -r
    [[ "$REPLY" =~ ^[Yy]$ ]] || { error "Deploy cancelled."; exit 1; }
fi

git pull origin main --ff-only
COMMIT=$(git log -1 --oneline)
success "Git pull OK: $COMMIT"

# =================================================================
# 2. Build Docker images
# =================================================================
if [[ "$SKIP_BUILD" == true ]]; then
    warn "[2/6] Bỏ qua build (--skip-build)"
elif [[ ${#SERVICES[@]} -eq 0 ]]; then
    info "[2/6] Build tất cả services..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    success "Build all images: OK"
else
    info "[2/6] Build services: ${SERVICES[*]}..."
    docker compose -f "$COMPOSE_FILE" build --no-cache "${SERVICES[@]}"
    success "Build ${SERVICES[*]}: OK"
fi

# =================================================================
# 3. Rolling update (down + up)
# =================================================================
info "[3/6] Deploy services..."
if [[ ${#SERVICES[@]} -eq 0 ]]; then
    # Deploy toàn bộ — theo đúng thứ tự depends_on
    docker compose -f "$COMPOSE_FILE" up -d
else
    # Deploy chỉ những services được chỉ định
    docker compose -f "$COMPOSE_FILE" up -d "${SERVICES[@]}"
fi
success "docker compose up -d: OK"

# =================================================================
# 4. Wait for services to be healthy
# =================================================================
info "[4/6] Chờ services healthy (tối đa 120s)..."
TIMEOUT=120
ELAPSED=0
HEALTHY=true

check_service() {
    local name="$1" url="$2"
    local max=$TIMEOUT elapsed=0
    printf "  Waiting %-20s " "$name..."
    while ! curl -sf "$url" > /dev/null 2>&1; do
        sleep 3
        elapsed=$((elapsed + 3))
        if [[ $elapsed -ge $max ]]; then
            echo -e "${RED}TIMEOUT${NC}"
            return 1
        fi
        printf "."
    done
    echo -e " ${GREEN}OK${NC} (${elapsed}s)"
    return 0
}

# Kiểm tra từng service
check_service "backend"  "http://localhost:8000/health"  || HEALTHY=false
check_service "ai_ml"    "http://localhost:8001/health"  || HEALTHY=false
check_service "nginx"    "http://localhost/nginx-health" || HEALTHY=false

if [[ "$HEALTHY" == false ]]; then
    error "Một số services không healthy! Xem logs:"
    echo -e "  docker compose -f $COMPOSE_FILE logs --tail=50 backend"
    echo -e "  docker compose -f $COMPOSE_FILE logs --tail=50 ai_ml"
    exit 1
fi
success "Tất cả services healthy"

# =================================================================
# 5. Smoke test
# =================================================================
info "[5/6] Smoke test API..."

# Test /health
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health")
if [[ "$HTTP_CODE" == "200" ]]; then
    success "GET /health → 200 OK"
else
    warn "GET /health → $HTTP_CODE (unexpected)"
fi

# Test 404 (đảm bảo nginx routing hoạt động)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/api/v1/nonexistent-endpoint-xyz")
if [[ "$HTTP_CODE" == "404" ]]; then
    success "GET /api/v1/... → 404 (routing OK)"
else
    warn "GET /api/v1/... → $HTTP_CODE"
fi

# =================================================================
# 6. Cleanup old Docker images
# =================================================================
info "[6/6] Dọn Docker images cũ..."
PRUNED=$(docker image prune -f --filter "until=24h" 2>&1 | tail -1)
docker container prune -f > /dev/null 2>&1
success "Cleanup: $PRUNED"

# =================================================================
# Summary
# =================================================================
echo ""
echo -e "${GREEN}=================================================================${NC}"
echo -e "${GREEN}  Deploy THÀNH CÔNG!${NC}  [$DEPLOY_TIMESTAMP]"
echo -e "${GREEN}=================================================================${NC}"
docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo -e "Logs: docker compose -f $COMPOSE_FILE logs -f --tail=100"
echo ""
