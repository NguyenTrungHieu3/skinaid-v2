// =================================================================
// Jenkinsfile — SkinAid CI/CD Pipeline (Production)
// =================================================================
//
// Architecture:
//   GitHub (production branch)
//     → Jenkins (port 19904, container)
//       → docker compose -f docker-compose.prod.yml
//         → skinaid_nginx      (80/443)
//         → skinaid_frontend   (React + nginx:alpine)
//         → skinaid_backend    (FastAPI :8000)
//         → skinaid_ai         (uvicorn :8001)
//         → skinaid_postgres   (PostgreSQL 16)
//         → skinaid_redis      (Redis 7)
//         → skinaid_qdrant     (Qdrant v1.13)
//
// Server: AWS EC2 — 2 vCPU, 8 GB RAM, 68 GB disk
// Deploy dir: /opt/skinaid
//
// Required files on server (NOT in git):
//   /opt/skinaid/.env                  — VITE_* + DB_* + REDIS_*
//   /opt/skinaid/backend/.env.prod     — backend secrets
//   /opt/skinaid/ai_ml/.env.prod       — ai_ml secrets
//   /opt/skinaid/nginx/ssl/fullchain.pem
//   /opt/skinaid/nginx/ssl/privkey.pem
//
// Jenkins credential required:
//   ID: github-ssh  (SSH Username with private key)
//
// Stages:
//   1. Checkout      — pull code nhánh production
//   2. Validate      — kiểm tra env files + SSL còn hạn
//   3. Detect        — so sánh diff với commit đang chạy trên server
//   4. Test          — pytest backend (unit tests, bỏ qua integration)
//   5. Build         — docker compose build service thay đổi
//   6. Deploy        — docker compose up -d
//   7. Health Check  — poll từng service đến khi healthy
// =================================================================

pipeline {
    agent any

    triggers {
        // Webhook là trigger chính — poll là safety net nếu webhook fail
        pollSCM('H/5 * * * *')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // 60 phút: torch load weights lần đầu có thể mất 10-20 phút
        timeout(time: 60, unit: 'MINUTES')
        ansiColor('xterm')
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    environment {
        DEPLOY_DIR               = '/opt/skinaid'
        COMPOSE_FILE             = 'docker-compose.prod.yml'
        BRANCH                   = 'production'
        REPO_URL                 = 'git@github.com:NguyenTrungHieu3/skinaid-v2.git'
        DOCKER_BUILDKIT          = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'
    }

    stages {

        // ============================================================
        // Stage 1: Checkout
        // ============================================================
        stage('Checkout') {
            when {
                anyOf {
                    branch 'production'
                    triggeredBy 'UserIdCause'  // cho phép trigger thủ công từ UI
                }
            }
            steps {
                echo '\033[34m[1/7] Checkout source code...\033[0m'
                cleanWs()

                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${BRANCH}"]],
                    userRemoteConfigs: [[
                        url: "${REPO_URL}",
                        credentialsId: 'github-ssh'
                    ]],
                    extensions: [
                        // Shallow clone depth=1 — tiết kiệm bandwidth + thời gian
                        [$class: 'CloneOption', depth: 1, shallow: true, noTags: true],
                    ]
                ])

                script {
                    env.GIT_SHORT_SHA  = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.GIT_COMMIT_MSG = sh(script: 'git log -1 --format="%s"', returnStdout: true).trim()
                    env.GIT_AUTHOR     = sh(script: 'git log -1 --format="%an"', returnStdout: true).trim()

                    echo "Branch  : ${BRANCH}"
                    echo "Commit  : ${env.GIT_SHORT_SHA} — ${env.GIT_COMMIT_MSG}"
                    echo "Author  : ${env.GIT_AUTHOR}"
                    echo "Build # : ${BUILD_NUMBER}"
                }
            }
        }

        // ============================================================
        // Stage 2: Validate
        // Kiểm tra tất cả file cần thiết + SSL còn hạn trước khi làm gì
        // ============================================================
        stage('Validate') {
            steps {
                echo '\033[34m[2/7] Validating server configuration...\033[0m'
                sh '''
                    FAILED=0

                    check_file() {
                        if [ ! -f "$1" ]; then
                            echo "  ERROR: $1 not found"
                            FAILED=1
                        else
                            echo "  OK   : $1"
                        fi
                    }

                    check_file "$DEPLOY_DIR/.env"
                    check_file "$DEPLOY_DIR/backend/.env.prod"
                    check_file "$DEPLOY_DIR/ai_ml/.env.prod"
                    check_file "$DEPLOY_DIR/nginx/ssl/fullchain.pem"
                    check_file "$DEPLOY_DIR/nginx/ssl/privkey.pem"

                    # Kiểm tra key bắt buộc trong .env gốc
                    for KEY in VITE_API_URL VITE_BACKEND_URL DB_USER DB_PASSWORD DB_NAME REDIS_PASSWORD; do
                        if ! grep -q "^${KEY}=" "$DEPLOY_DIR/.env" 2>/dev/null; then
                            echo "  ERROR: $KEY missing in .env"
                            FAILED=1
                        fi
                    done

                    # Kiểm tra SSL còn hạn
                    if [ -f "$DEPLOY_DIR/nginx/ssl/fullchain.pem" ]; then
                        EXPIRY=$(openssl x509 -enddate -noout \
                            -in "$DEPLOY_DIR/nginx/ssl/fullchain.pem" | cut -d= -f2)
                        EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || echo 0)
                        DAYS=$(( (EXPIRY_EPOCH - $(date +%s)) / 86400 ))
                        if [ "$DAYS" -lt 0 ]; then
                            echo "  ERROR: SSL cert ĐÃ HẾT HẠN — renew ngay!"
                            FAILED=1
                        elif [ "$DAYS" -lt 30 ]; then
                            echo "  WARN : SSL cert còn $DAYS ngày — nên renew sớm"
                        else
                            echo "  OK   : SSL cert còn $DAYS ngày"
                        fi
                    fi

                    # Cảnh báo disk space < 5 GB
                    FREE_GB=$(df -BG / | awk 'NR==2{gsub("G",""); print $4}')
                    if [ "$FREE_GB" -lt 5 ]; then
                        echo "  WARN : Disk chỉ còn ${FREE_GB}GB — có thể fail khi build image"
                    else
                        echo "  OK   : Disk còn ${FREE_GB}GB"
                    fi

                    [ $FAILED -eq 0 ] || { echo; echo "Validation FAILED — fix errors above."; exit 1; }
                    echo "Validation passed ✓"
                '''
            }
        }

        // ============================================================
        // Stage 3: Detect Changes
        // So sánh workspace (commit mới) với commit đang chạy trên server
        // Tránh build lại image không cần thiết — EC2 2 vCPU cần tiết kiệm
        // ============================================================
        stage('Detect Changes') {
            steps {
                echo '\033[34m[3/7] Detecting changed services...\033[0m'
                script {
                    def serverSha = sh(
                        script: "git -C ${DEPLOY_DIR} rev-parse HEAD 2>/dev/null || echo 'none'",
                        returnStdout: true
                    ).trim()

                    def changedFiles
                    if (serverSha == 'none') {
                        changedFiles = 'all'
                        echo "First deploy → build all services"
                    } else if (serverSha == env.GIT_SHORT_SHA) {
                        changedFiles = ''
                        echo "Server đang chạy commit này rồi — skip build"
                    } else {
                        // Fetch thêm history để diff được (shallow clone chỉ có 1 commit)
                        sh "git fetch --depth=50 origin ${BRANCH} 2>/dev/null || true"
                        changedFiles = sh(
                            script: "git diff --name-only ${serverSha} HEAD 2>/dev/null || echo 'all'",
                            returnStdout: true
                        ).trim()
                        if (changedFiles.isEmpty()) changedFiles = 'all'
                        echo "Changed files:\n${changedFiles}"
                    }

                    def buildList = []
                    boolean buildAll = (changedFiles == 'all')

                    if (buildAll || changedFiles.contains('ai_ml/'))   buildList.add('ai_ml')
                    if (buildAll || changedFiles.contains('backend/'))  buildList.add('backend')
                    if (buildAll || changedFiles.contains('frontend/')) buildList.add('frontend')

                    env.NGINX_CHANGED  = changedFiles.contains('nginx/') ? 'true' : 'false'
                    env.BUILD_SERVICES = buildList.join(' ')
                    env.SKIP_BUILD     = buildList.isEmpty() ? 'true' : 'false'
                    env.SKIP_DEPLOY    = (buildList.isEmpty() && env.NGINX_CHANGED == 'false') ? 'true' : 'false'
                    env.RUN_TESTS      = (buildAll || changedFiles.contains('backend/')) ? 'true' : 'false'

                    echo "Build services : ${env.BUILD_SERVICES ?: '(none)'}"
                    echo "Nginx reload   : ${env.NGINX_CHANGED}"
                    echo "Run tests      : ${env.RUN_TESTS}"
                    echo "Skip deploy    : ${env.SKIP_DEPLOY}"
                }
            }
        }

        // ============================================================
        // Stage 4: Test
        // Chạy trong container tạm, dùng Redis DB index 1 (tránh ảnh hưởng prod)
        // Bỏ qua integration tests (cần external services)
        // ============================================================
        stage('Test') {
            when {
                environment name: 'RUN_TESTS', value: 'true'
            }
            steps {
                echo '\033[34m[4/7] Running backend unit tests...\033[0m'
                sh '''
                    set -a
                    . "$DEPLOY_DIR/.env"
                    . "$DEPLOY_DIR/backend/.env.prod"
                    set +a

                    # Lần đầu deploy image chưa tồn tại → skip test
                    if ! docker image inspect skinaid-backend:latest > /dev/null 2>&1; then
                        echo "Image skinaid-backend:latest chưa có — skip tests (first deploy)"
                        exit 0
                    fi

                    docker run --rm \
                        --network skinaid_skinaid_internal \
                        -e DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}" \
                        -e REDIS_URL="redis://:${REDIS_PASSWORD}@redis:6379/1" \
                        -e TESTING=true \
                        -v "$DEPLOY_DIR/backend":/app \
                        -w /app \
                        skinaid-backend:latest \
                        sh -c "
                            pip install pytest pytest-asyncio httpx --quiet 2>/dev/null
                            python -m pytest tests/ -v --tb=short \
                                --ignore=tests/auth/integration \
                                -x
                        "

                    echo "Tests passed ✓"
                '''
            }
        }

        // ============================================================
        // Stage 5: Build
        // Build chỉ service thay đổi, parallel (tiết kiệm CPU)
        // QUAN TRỌNG: Frontend Vite bake VITE_* vào bundle lúc build
        // → phải truyền qua --build-arg, không phải runtime env
        // ============================================================
        stage('Build') {
            when {
                environment name: 'SKIP_BUILD', value: 'false'
            }
            steps {
                echo '\033[34m[5/7] Syncing code and building: ${BUILD_SERVICES}...\033[0m'
                sh '''
                    cd "$DEPLOY_DIR"

                    # Sync code — git reset KHÔNG xóa file untracked (.env, ssl/)
                    git fetch origin ${BRANCH}
                    git reset --hard origin/${BRANCH}

                    # Confirm file quan trọng vẫn còn sau reset
                    for f in ".env" "backend/.env.prod" "ai_ml/.env.prod" \
                             "nginx/ssl/fullchain.pem" "nginx/ssl/privkey.pem"; do
                        [ -f "$DEPLOY_DIR/$f" ] \
                            && echo "  Preserved: $f ✓" \
                            || echo "  WARN: $f missing sau reset!"
                    done

                    # Load env:
                    #   .env             → VITE_API_URL, VITE_BACKEND_URL, DB_*, REDIS_*
                    #   backend/.env.prod → SECRET_KEY, JWT_* và các secrets khác
                    set -a
                    . "$DEPLOY_DIR/.env"
                    . "$DEPLOY_DIR/backend/.env.prod"
                    set +a

                    echo "  VITE_API_URL     = $VITE_API_URL"
                    echo "  VITE_BACKEND_URL = $VITE_BACKEND_URL"

                    # Build parallel — frontend cần --build-arg để Vite bake URL vào bundle
                    docker compose -f "$COMPOSE_FILE" build \
                        --parallel \
                        --build-arg VITE_API_URL="$VITE_API_URL" \
                        --build-arg VITE_BACKEND_URL="$VITE_BACKEND_URL" \
                        $BUILD_SERVICES

                    echo "Build complete ✓"
                '''
            }
        }

        // ============================================================
        // Stage 6: Deploy
        // ============================================================
        stage('Deploy') {
            when {
                environment name: 'SKIP_DEPLOY', value: 'false'
            }
            steps {
                echo '\033[34m[6/7] Deploying to production...\033[0m'
                sh '''
                    cd "$DEPLOY_DIR"

                    set -a
                    . "$DEPLOY_DIR/.env"
                    . "$DEPLOY_DIR/backend/.env.prod"
                    set +a

                    # Up tất cả service — chỉ recreate container có image mới
                    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

                    # Nếu chỉ nginx config thay đổi (không rebuild image) → reload config
                    if [ "$NGINX_CHANGED" = "true" ] && [ "$SKIP_BUILD" = "true" ]; then
                        echo "Reloading nginx config..."
                        docker exec skinaid_nginx nginx -t \
                            && docker exec skinaid_nginx nginx -s reload \
                            && echo "Nginx reloaded ✓" \
                            || { echo "ERROR: nginx config invalid!"; exit 1; }
                    fi

                    echo "Deploy complete ✓"
                '''
            }
        }

        // ============================================================
        // Stage 7: Health Check
        // Timeout riêng cho từng service:
        //   - AI service: 150s (torch load model weights chậm)
        //   - Backend:    100s
        //   - Nginx:       50s
        // ============================================================
        stage('Health Check') {
            when {
                environment name: 'SKIP_DEPLOY', value: 'false'
            }
            steps {
                echo '\033[34m[7/7] Verifying all services are healthy...\033[0m'
                sh '''
                    echo "Waiting 30s for services to stabilize..."
                    sleep 30

                    # poll_health <name> <container> <cmd> <max_retries>
                    # Mỗi retry cách 5s
                    poll_health() {
                        local NAME="$1" CTR="$2" CMD="$3" MAX="${4:-20}"
                        local TRIES=0
                        printf "  %-22s " "$NAME"
                        while ! docker exec "$CTR" sh -c "$CMD" > /dev/null 2>&1; do
                            TRIES=$((TRIES + 1))
                            [ $TRIES -ge $MAX ] && { echo "TIMEOUT ✗"; return 1; }
                            sleep 5
                            printf "."
                        done
                        echo " OK ✓"
                        return 0
                    }

                    FAILED=0

                    # Backend FastAPI: /health
                    poll_health "backend   :8000" "skinaid_backend" \
                        "curl -sf http://localhost:8000/health" 20 || FAILED=1

                    # AI service: check_health.py (ada di /app/ — confirmed)
                    # Max 30 retries = 150s untuk torch model loading
                    poll_health "ai_ml     :8001" "skinaid_ai" \
                        "python3 /app/check_health.py" 30 || FAILED=1

                    # Nginx: /nginx-health
                    poll_health "nginx      :443" "skinaid_nginx" \
                        "wget -qO- http://localhost/nginx-health" 10 || FAILED=1

                    # Frontend: HTML berisi judul SkinAid
                    poll_health "frontend  →nginx" "skinaid_nginx" \
                        "wget -qO- http://localhost/ | grep -q 'SkinAid'" 10 || FAILED=1

                    echo ""

                    if [ $FAILED -eq 1 ]; then
                        echo "=== HEALTH CHECK FAILED — Service logs ==="
                        echo "--- skinaid_backend (last 40 lines) ---"
                        docker logs skinaid_backend --tail=40 2>&1 || true
                        echo "--- skinaid_ai (last 40 lines) ---"
                        docker logs skinaid_ai --tail=40 2>&1 || true
                        echo "--- skinaid_nginx (last 20 lines) ---"
                        docker logs skinaid_nginx --tail=20 2>&1 || true
                        exit 1
                    fi

                    echo "=== All containers status ==="
                    cd "$DEPLOY_DIR"
                    docker compose -f "$COMPOSE_FILE" ps

                    echo ""
                    echo "All services healthy ✓"
                    echo "Live: https://skinaid.xyz"
                '''
            }
        }
    }

    // ── Post actions ────────────────────────────────────────────────
    post {
        success {
            echo '\033[32m=== PIPELINE SUCCEEDED ===\033[0m'
            sh '''
                # Prune image cũ hơn 48h — giữ image đang chạy
                docker image prune -f --filter "until=48h" || true
                docker container prune -f || true

                echo "$(date '+%Y-%m-%d %H:%M:%S') | SUCCESS | #${BUILD_NUMBER} | ${GIT_SHORT_SHA} | ${GIT_COMMIT_MSG} | ${GIT_AUTHOR}" \
                    >> "$DEPLOY_DIR/deploy-history.log"
            '''
        }

        failure {
            echo '\033[31m=== PIPELINE FAILED — Rolling back... ===\033[0m'
            sh '''
                cd "$DEPLOY_DIR"

                set -a
                [ -f .env ] && . .env
                [ -f backend/.env.prod ] && . backend/.env.prod
                set +a

                # Rollback: restart với image hiện tại (không build mới)
                docker compose -f "$COMPOSE_FILE" up -d || true

                echo "$(date '+%Y-%m-%d %H:%M:%S') | FAILED  | #${BUILD_NUMBER} | ${GIT_SHORT_SHA:-unknown} | ${GIT_COMMIT_MSG:-?}" \
                    >> "$DEPLOY_DIR/deploy-history.log" || true
            '''
        }

        always {
            // Dọn Jenkins workspace sau mỗi build (tiết kiệm disk EC2)
            cleanWs()
        }
    }
}