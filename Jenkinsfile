// =================================================================
// Jenkinsfile — SkinAid CI/CD Pipeline
// =================================================================
// Trigger: push vào nhánh 'production' trên GitHub
//          + GitHub Webhook → Jenkins /github-webhook/
//          + Fallback: pollSCM mỗi 2 phút (safety net)
//
// Pipeline stages:
//   1. Checkout       — lấy code từ Git (nhánh production)
//   2. Validate       — kiểm tra .env.prod + SSL tồn tại trên server
//   3. Test           — chạy unit test (nếu có)
//   4. Sync & Build   — rsync code → /opt/skinaid, docker compose build
//   5. Deploy         — docker compose up -d
//   6. Health Check   — verify các /health endpoint
//
// Yêu cầu Jenkins:
//   Plugins  : Git, Pipeline, AnsiColor, GitHub Integration, Workspace Cleanup
//   Credential: 'github-ssh' — SSH key để pull private repo
//
// Cách thêm credential:
//   Jenkins → Manage Jenkins → Credentials → System → Global
//   → Add: "SSH Username with private key"
//       ID       : github-ssh
//       Username : git
//       Key      : paste nội dung ~/.ssh/id_rsa của server
// =================================================================

pipeline {
    agent any

    // ── Chỉ build khi push vào nhánh production ─────────────────
    // - GitHub Webhook là trigger chính (cần cài Jenkins URL vào GitHub repo)
    // - pollSCM là backup: quét mỗi 2 phút nếu webhook fail
    triggers {
        // Fallback polling — kiểm tra mỗi 2 phút
        // Khi đã có Webhook hoạt động, comment dòng này để tiết kiệm tài nguyên
        pollSCM('H/2 * * * *')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 45, unit: 'MINUTES')
        ansiColor('xterm')
        disableConcurrentBuilds()
        // Xoá workspace trước mỗi build để tránh stale code
        skipDefaultCheckout(true)
    }

    // ── Environment variables ────────────────────────────────────
    environment {
        COMPOSE_FILE             = 'docker-compose.prod.yml'
        DEPLOY_DIR               = '/opt/skinaid'
        DOCKER_BUILDKIT          = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'
        // Repo SSH URL — thay <your-github-username> đúng tên user/org
        REPO_URL                 = 'git@github.com:NguyenTrungHieu3/skinaid-v2.git'
        BRANCH                   = 'production'
    }

    stages {

        // ============================================================
        // Stage 1: Checkout — chỉ lấy nhánh production
        // ============================================================
        stage('📥 Checkout') {
            // Chỉ chạy khi branch là production
            when {
                anyOf {
                    branch 'production'
                    // Cho phép chạy manual build (triggered from UI)
                    triggeredBy 'UserIdCause'
                }
            }
            steps {
                echo '\033[34m[STAGE 1/6] Checking out source code from production branch...\033[0m'

                cleanWs()

                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${BRANCH}"]],
                    userRemoteConfigs: [[
                        url           : "${REPO_URL}",
                        credentialsId : 'github-ssh'
                    ]],
                    extensions: [
                        // Clone nhanh hơn (chỉ 1 commit gần nhất)
                        [$class: 'CloneOption', depth: 1, shallow: true]
                    ]
                ])

                script {
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

                    echo "✔ Branch   : ${BRANCH}"
                    echo "✔ Commit   : ${env.GIT_SHORT_SHA} — ${env.GIT_COMMIT_MSG}"
                    echo "✔ Author   : ${env.GIT_AUTHOR}"
                    echo "✔ Build #  : ${BUILD_NUMBER}"
                }
            }
        }

        // ============================================================
        // Stage 2: Validate — kiểm tra file cần thiết TRÊN SERVER
        // ============================================================
        stage('✅ Validate') {
            steps {
                echo '\033[34m[STAGE 2/6] Validating server configuration...\033[0m'

                sh '''
                    echo "=== Checking required files on server ==="

                    # .env.prod phải có sẵn trên server (không commit vào git)
                    for f in "backend/.env.prod" "ai_ml/.env.prod"; do
                        FULL_PATH="$DEPLOY_DIR/$f"
                        if [ ! -f "$FULL_PATH" ]; then
                            echo "ERROR: $FULL_PATH not found!"
                            echo "Tạo file từ .env.example trước khi chạy pipeline:"
                            echo "  cp $DEPLOY_DIR/$f.example $FULL_PATH && nano $FULL_PATH"
                            exit 1
                        fi
                        echo "OK: $f ✓"
                    done

                    # SSL certs (warning, không fail)
                    for cert in "nginx/ssl/fullchain.pem" "nginx/ssl/privkey.pem"; do
                        if [ ! -f "$DEPLOY_DIR/$cert" ]; then
                            echo "WARN: SSL cert missing: $DEPLOY_DIR/$cert (HTTP only)"
                        else
                            echo "OK: $cert ✓"
                        fi
                    done

                    echo "=== Validation passed ==="
                '''
            }
        }

        // ============================================================
        // Stage 3: Test (Optional)
        // ============================================================
        stage('🧪 Test') {
            steps {
                echo '\033[34m[STAGE 3/6] Running tests...\033[0m'

                sh '''
                    # Thêm pytest hoặc test runner thực ở đây khi có test
                    # Ví dụ:
                    # docker run --rm \
                    #   -v $(pwd)/backend:/app -w /app \
                    #   python:3.11-slim \
                    #   bash -c "pip install -r requirements.txt -q && pytest tests/ -v --tb=short"

                    echo "No tests configured yet — skipping."
                    echo "Add tests to backend/tests/ to enable this stage."
                '''
            }
        }

        // ============================================================
        // Stage 4: Sync Code + Build Docker Images
        // ============================================================
        stage('🔨 Sync & Build') {
            steps {
                echo '\033[34m[STAGE 4/6] Syncing code and building images...\033[0m'

                script {
                    // Phát hiện service nào thay đổi so với commit trước
                    def changedFiles = sh(
                        script: 'git diff --name-only HEAD~1 HEAD 2>/dev/null || echo "all"',
                        returnStdout: true
                    ).trim()

                    echo "Changed files:\n${changedFiles}"

                    def buildServices = []

                    if (changedFiles == 'all' || changedFiles.contains('ai_ml/')) {
                        buildServices.add('ai_ml')
                    }
                    if (changedFiles == 'all' || changedFiles.contains('backend/')) {
                        buildServices.add('backend')
                    }
                    if (changedFiles == 'all' || changedFiles.contains('frontend/')) {
                        buildServices.add('frontend')
                    }

                    // nginx config thay đổi → chỉ reload, không rebuild
                    env.NGINX_RELOAD = (changedFiles.contains('nginx/') && !buildServices.contains('frontend')) ? 'true' : 'false'

                    if (buildServices.isEmpty()) {
                        echo "Không có Docker service nào thay đổi — skip build"
                        env.BUILD_SERVICES = ''
                        env.SKIP_DEPLOY = 'true'
                    } else {
                        env.BUILD_SERVICES = buildServices.join(' ')
                        env.SKIP_DEPLOY = 'false'
                    }

                    echo "Services to build: ${env.BUILD_SERVICES ?: '(none)'}"
                }

                sh '''
                    echo "=== Syncing code to $DEPLOY_DIR ==="

                    # Đảm bảo DEPLOY_DIR tồn tại
                    mkdir -p $DEPLOY_DIR

                    # rsync code từ Jenkins workspace → deploy dir
                    # Giữ lại .env.prod và nginx/ssl (không sync từ git)
                    rsync -av --delete \
                        --exclude='.git/' \
                        --exclude='node_modules/' \
                        --exclude='__pycache__/' \
                        --exclude='*.pyc' \
                        --exclude='.env*' \
                        --exclude='nginx/ssl/' \
                        $WORKSPACE/ $DEPLOY_DIR/

                    echo "Sync complete ✓"

                    # Build Docker images nếu có service cần rebuild
                    if [ -z "$BUILD_SERVICES" ]; then
                        echo "Nothing to build — skipping docker build"
                        exit 0
                    fi

                    echo "=== Building: $BUILD_SERVICES ==="
                    cd $DEPLOY_DIR

                    # Load env từ .env.prod (cho VITE_API_URL, DB_USER, v.v.)
                    set -a && [ -f backend/.env.prod ] && . backend/.env.prod ; set +a

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

                    # Load env variables từ .env.prod của backend (DB_USER, DB_PASSWORD, ...)
                    set -a && [ -f backend/.env.prod ] && . backend/.env.prod; set +a

                    echo "=== Starting services ==="
                    docker compose -f $COMPOSE_FILE up -d --remove-orphans

                    # Reload nginx config nếu chỉ nginx thay đổi (không cần rebuild)
                    if [ "$NGINX_RELOAD" = "true" ]; then
                        echo "Reloading nginx config..."
                        docker exec skinaid_nginx nginx -s reload || true
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
                echo '\033[34m[STAGE 6/6] Verifying all services are healthy...\033[0m'

                sh '''
                    echo "=== Waiting for services to start (30s) ==="
                    sleep 30

                    check_health() {
                        local NAME="$1"
                        local URL="$2"
                        local TRIES=0
                        local MAX=20    # 20 × 5s = 100s

                        printf "  %-20s " "$NAME"
                        while ! curl -sf "$URL" > /dev/null 2>&1; do
                            TRIES=$((TRIES + 1))
                            if [ $TRIES -ge $MAX ]; then
                                echo "TIMEOUT ✗"
                                return 1
                            fi
                            sleep 5
                            printf "."
                        done
                        echo " OK ✓ (${TRIES}×5s)"
                        return 0
                    }

                    FAILED=0
                    check_health "backend"  "http://localhost:8000/health"  || FAILED=1
                    check_health "ai_ml"    "http://localhost:8001/health"  || FAILED=1
                    check_health "nginx"    "http://localhost/nginx-health" || FAILED=1

                    if [ $FAILED -eq 1 ]; then
                        echo ""
                        echo "=== Failed service logs (last 50 lines) ==="
                        cd $DEPLOY_DIR
                        docker compose -f $COMPOSE_FILE logs --tail=50 backend || true
                        docker compose -f $COMPOSE_FILE logs --tail=50 ai_ml   || true
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

    // ── Post actions ────────────────────────────────────────────
    post {
        success {
            echo '\033[32m=== ✅ PIPELINE SUCCEEDED ===\033[0m'

            sh '''
                # Dọn dẹp image cũ sau deploy thành công
                docker image prune -f --filter "until=24h" || true
                docker container prune -f || true
            '''

            // Gửi thông báo Telegram (bỏ comment để bật, cần thêm credentials)
            // sh '''
            //   curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            //     -d chat_id="${TELEGRAM_CHAT_ID}" \
            //     -d parse_mode="Markdown" \
            //     -d text="✅ *SkinAid Deploy SUCCESS*%0A%0A*Commit:* \`${GIT_SHORT_SHA}\` ${GIT_COMMIT_MSG}%0A*By:* ${GIT_AUTHOR}%0A*Build:* #${BUILD_NUMBER}" || true
            // '''
        }

        failure {
            echo '\033[31m=== ❌ PIPELINE FAILED ===\033[0m'

            sh '''
                echo "=== Attempting rollback... ==="
                cd $DEPLOY_DIR
                # Khởi động lại với image hiện tại (không build lại)
                docker compose -f $COMPOSE_FILE up -d || true
                echo "Rollback attempted."
            '''

            // Gửi thông báo Telegram khi fail (bỏ comment)
            // sh '''
            //   curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            //     -d chat_id="${TELEGRAM_CHAT_ID}" \
            //     -d parse_mode="Markdown" \
            //     -d text="❌ *SkinAid Deploy FAILED*%0A*Build:* #${BUILD_NUMBER}%0A*Log:* ${BUILD_URL}" || true
            // '''
        }

        always {
            sh '''
                # Ghi log lịch sử deploy
                echo "Build #${BUILD_NUMBER} | $(date '+%Y-%m-%d %H:%M:%S') | ${GIT_SHORT_SHA:-unknown}" \
                    >> /opt/skinaid/deploy-history.log || true
            '''
        }
    }
}
