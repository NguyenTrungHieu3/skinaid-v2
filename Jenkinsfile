// =================================================================
// Jenkinsfile — SkinAid CI/CD Pipeline
// =================================================================
// Trigger: merge vào nhánh 'production' trên GitHub
//
// Pipeline stages:
//   1. Checkout       — lấy code từ Git
//   2. Validate       — kiểm tra .env.prod tồn tại
//   3. Test           — chạy unit test (nếu có)
//   4. Build          — docker compose build service thay đổi
//   5. Deploy         — docker compose up -d
//   6. Health Check   — verify các /health endpoint
//   7. Notify         — gửi kết quả về Slack/Telegram (tuỳ chọn)
//
// Yêu cầu Jenkins plugins:
//   - Git Plugin
//   - Pipeline Plugin
//   - AnsiColor Plugin (cho màu terminal)
//   - Slack Notification / Telegram Plugin (nếu dùng notify)
//
// Credentials cần thêm vào Jenkins:
//   - GITHUB_CREDENTIALS : SSH key hoặc PAT để pull private repo
//   - TELEGRAM_BOT_TOKEN : Token bot Telegram (tuỳ chọn)
//   - TELEGRAM_CHAT_ID   : Chat ID Telegram (tuỳ chọn)
// =================================================================

pipeline {
    // Chạy trên Jenkins agent mặc định
    // Jenkins container mount Docker socket → có thể gọi docker compose
    agent any

    // ── Chỉ trigger khi push vào nhánh production ────────────────
    options {
        // Giữ tối đa 10 build logs
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Timeout toàn bộ pipeline = 45 phút (build torch lâu)
        timeout(time: 45, unit: 'MINUTES')
        // Hiển thị màu ANSI trong console
        ansiColor('xterm')
        // Không build 2 lần cùng lúc cho cùng 1 branch
        disableConcurrentBuilds()
    }

    // ── Environment variables ─────────────────────────────────────
    environment {
        COMPOSE_FILE        = 'docker-compose.prod.yml'
        DEPLOY_DIR          = '/opt/skinaid'          // Đường dẫn trên EC2
        DOCKER_BUILDKIT     = '1'                     // BuildKit nhanh hơn
        COMPOSE_DOCKER_CLI_BUILD = '1'
        // Slack/Telegram sẽ được đọc từ Jenkins Credentials
        // TELEGRAM_BOT_TOKEN = credentials('TELEGRAM_BOT_TOKEN')
        // TELEGRAM_CHAT_ID   = credentials('TELEGRAM_CHAT_ID')
    }

    stages {

        // ============================================================
        // Stage 1: Checkout
        // ============================================================
        stage('📥 Checkout') {
            steps {
                echo '\033[34m[STAGE 1/6] Checking out source code...\033[0m'

                // Xoá workspace cũ và checkout code mới
                cleanWs()
                checkout scm

                script {
                    // Lưu thông tin commit để dùng sau
                    env.GIT_COMMIT_MSG = sh(
                        script: 'git log -1 --format="%s" HEAD',
                        returnStdout: true
                    ).trim()
                    env.GIT_AUTHOR = sh(
                        script: 'git log -1 --format="%an" HEAD',
                        returnStdout: true
                    ).trim()
                    env.GIT_SHORT_SHA = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()

                    echo "Commit: ${env.GIT_SHORT_SHA} — ${env.GIT_COMMIT_MSG}"
                    echo "Author: ${env.GIT_AUTHOR}"
                }
            }
        }

        // ============================================================
        // Stage 2: Validate
        // ============================================================
        stage('✅ Validate') {
            steps {
                echo '\033[34m[STAGE 2/6] Validating configuration...\033[0m'

                sh '''
                    echo "=== Checking required files ==="

                    # Kiểm tra .env.prod files (phải có trên server, không commit vào git)
                    for f in "backend/.env.prod" "ai_ml/.env.prod"; do
                        if [ ! -f "$DEPLOY_DIR/$f" ]; then
                            echo "ERROR: $DEPLOY_DIR/$f not found!"
                            echo "Create it from .env.example first."
                            exit 1
                        fi
                        echo "OK: $f"
                    done

                    # Kiểm tra SSL certs
                    for cert in "nginx/ssl/fullchain.pem" "nginx/ssl/privkey.pem"; do
                        if [ ! -f "$DEPLOY_DIR/$cert" ]; then
                            echo "WARN: SSL cert missing: $cert"
                        else
                            echo "OK: $cert"
                        fi
                    done

                    # Kiểm tra docker compose file hợp lệ
                    docker compose -f "$DEPLOY_DIR/$COMPOSE_FILE" config --quiet
                    echo "OK: docker-compose.prod.yml syntax valid"
                '''
            }
        }

        // ============================================================
        // Stage 3: Test (Optional — thêm test thật vào đây)
        // ============================================================
        stage('🧪 Test') {
            steps {
                echo '\033[34m[STAGE 3/6] Running tests...\033[0m'

                sh '''
                    echo "=== Backend unit tests ==="
                    # Nếu có pytest tests:
                    # docker run --rm \
                    #   -v $(pwd)/backend:/app \
                    #   -w /app \
                    #   python:3.11-slim \
                    #   bash -c "pip install -r requirements.txt -q && pytest tests/ -v --tb=short"

                    # Hiện tại: skip nếu chưa có tests
                    echo "No tests configured yet — skipping."
                    echo "Add pytest tests to backend/tests/ to enable."
                '''
            }
        }

        // ============================================================
        // Stage 4: Build Docker Images
        // ============================================================
        stage('🔨 Build') {
            steps {
                echo '\033[34m[STAGE 4/6] Building Docker images...\033[0m'

                script {
                    // Xác định services nào thay đổi so với commit trước
                    def changedFiles = sh(
                        script: 'git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only HEAD 2>/dev/null || echo "all"',
                        returnStdout: true
                    ).trim()

                    echo "Changed files:\n${changedFiles}"

                    def buildServices = []

                    if (changedFiles.contains('ai_ml/') || changedFiles == 'all') {
                        buildServices.add('ai_ml')
                    }
                    if (changedFiles.contains('backend/') || changedFiles == 'all') {
                        buildServices.add('backend')
                    }
                    if (changedFiles.contains('frontend/') || changedFiles == 'all') {
                        buildServices.add('frontend')
                    }
                    // nginx config thay đổi → không cần rebuild image, chỉ reload
                    if (changedFiles.contains('nginx/') && !buildServices.contains('frontend')) {
                        buildServices.add('nginx_reload')
                    }

                    if (buildServices.isEmpty()) {
                        echo "Không có service nào cần rebuild (chỉ docs/scripts thay đổi)"
                        env.SKIP_DEPLOY = 'true'
                        return
                    }

                    env.BUILD_SERVICES = buildServices
                        .findAll { it != 'nginx_reload' }
                        .join(' ')
                    env.NGINX_RELOAD = buildServices.contains('nginx_reload') ? 'true' : 'false'

                    echo "Services to build: ${env.BUILD_SERVICES}"
                }

                sh '''
                    cd $DEPLOY_DIR

                    # Sync code từ workspace Jenkins sang deploy dir
                    rsync -av --exclude='.git' \
                        --exclude='node_modules' \
                        --exclude='__pycache__' \
                        --exclude='.env*' \
                        --exclude='nginx/ssl' \
                        $WORKSPACE/ $DEPLOY_DIR/

                    if [ -z "$BUILD_SERVICES" ]; then
                        echo "Nothing to build — skipping docker build"
                        exit 0
                    fi

                    echo "=== Building: $BUILD_SERVICES ==="
                    docker compose -f $COMPOSE_FILE build \
                        --no-cache \
                        --parallel \
                        $BUILD_SERVICES

                    echo "Build complete ✓"
                '''
            }
        }

        // ============================================================
        // Stage 5: Deploy
        // ============================================================
        stage('🚀 Deploy') {
            when {
                not { environment name: 'SKIP_DEPLOY', value: 'true' }
            }
            steps {
                echo '\033[34m[STAGE 5/6] Deploying to production...\033[0m'

                sh '''
                    cd $DEPLOY_DIR

                    echo "=== Starting services ==="
                    docker compose -f $COMPOSE_FILE up -d

                    # Reload nginx nếu chỉ config thay đổi (không cần rebuild)
                    if [ "$NGINX_RELOAD" = "true" ]; then
                        echo "Reloading nginx config..."
                        docker exec skinaid_nginx nginx -s reload
                    fi

                    echo "Deploy UP: OK ✓"
                '''
            }
        }

        // ============================================================
        // Stage 6: Health Check
        // ============================================================
        stage('❤️  Health Check') {
            when {
                not { environment name: 'SKIP_DEPLOY', value: 'true' }
            }
            steps {
                echo '\033[34m[STAGE 6/6] Verifying all services...\033[0m'

                sh '''
                    echo "=== Health checks (timeout 120s) ==="

                    check_health() {
                        local NAME="$1"
                        local URL="$2"
                        local TRIES=0
                        local MAX=40  # 40 × 3s = 120s

                        printf "  %-25s " "$NAME"
                        while ! curl -sf "$URL" > /dev/null 2>&1; do
                            TRIES=$((TRIES + 1))
                            if [ $TRIES -ge $MAX ]; then
                                echo "TIMEOUT ✗"
                                return 1
                            fi
                            sleep 3
                            printf "."
                        done
                        echo " OK ✓ (${TRIES}×3s)"
                        return 0
                    }

                    FAILED=0
                    check_health "backend"   "http://localhost:8000/health"  || FAILED=1
                    check_health "ai_ml"     "http://localhost:8001/health"  || FAILED=1
                    check_health "nginx"     "http://localhost/nginx-health" || FAILED=1

                    if [ $FAILED -eq 1 ]; then
                        echo ""
                        echo "=== Failed service logs ==="
                        docker compose -f $COMPOSE_FILE logs --tail=30 backend || true
                        docker compose -f $COMPOSE_FILE logs --tail=30 ai_ml   || true
                        exit 1
                    fi

                    echo ""
                    echo "=== Container status ==="
                    docker compose -f $COMPOSE_FILE ps

                    echo ""
                    echo "All services healthy ✓"
                '''
            }
        }
    }

    // ── Post actions ─────────────────────────────────────────────
    post {
        success {
            echo '\033[32m=== PIPELINE SUCCEEDED ===\033[0m'

            // Dọn images cũ sau deploy thành công
            sh 'docker image prune -f --filter "until=24h" || true'
            sh 'docker container prune -f || true'

            // Gửi thông báo Telegram (bỏ comment để bật)
            // sh '''
            //   curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            //     -d chat_id="${TELEGRAM_CHAT_ID}" \
            //     -d parse_mode="Markdown" \
            //     -d text="✅ *SkinAid Deploy SUCCESS*%0A%0A*Commit:* \`${GIT_SHORT_SHA}\` ${GIT_COMMIT_MSG}%0A*Author:* ${GIT_AUTHOR}%0A*Branch:* production%0A*Build:* #${BUILD_NUMBER}" || true
            // '''
        }

        failure {
            echo '\033[31m=== PIPELINE FAILED ===\033[0m'

            // Rollback: restart với image trước đó
            sh '''
                echo "=== Rolling back to previous containers ==="
                cd $DEPLOY_DIR
                docker compose -f $COMPOSE_FILE up -d || true
                echo "Rollback attempted."
            '''

            // Gửi thông báo Telegram (bỏ comment để bật)
            // sh '''
            //   curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            //     -d chat_id="${TELEGRAM_CHAT_ID}" \
            //     -d parse_mode="Markdown" \
            //     -d text="❌ *SkinAid Deploy FAILED*%0A%0A*Commit:* \`${GIT_SHORT_SHA}\` ${GIT_COMMIT_MSG}%0A*Author:* ${GIT_AUTHOR}%0A*Build:* #${BUILD_NUMBER}%0ASee: ${BUILD_URL}" || true
            // '''
        }

        always {
            // Lưu deploy log
            sh '''
                echo "Build #${BUILD_NUMBER} | $(date) | ${GIT_SHORT_SHA}" \
                    >> /opt/skinaid/deploy-history.log || true
            '''
        }
    }
}
