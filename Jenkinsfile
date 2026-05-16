// =================================================================
// Jenkinsfile — SkinAid CI/CD Pipeline (Production)
// =================================================================
//
// Server   : AWS EC2 — 2 vCPU, 8 GB RAM, 68 GB disk
// Deploy   : /opt/skinaid
// Domain   : https://skinaid.xyz
// Trigger  : GitHub Webhook (push → production branch)
//            Fallback: pollSCM mỗi 5 phút
//
// Required files on server (NOT in git):
//   /opt/skinaid/.env                  — VITE_* + DB_* + REDIS_*
//   /opt/skinaid/backend/.env.prod     — backend secrets (SECRET_KEY, JWT, ...)
//   /opt/skinaid/ai_ml/.env.prod       — ai_ml secrets
//   /opt/skinaid/nginx/ssl/fullchain.pem
//   /opt/skinaid/nginx/ssl/privkey.pem
//
// Jenkins credential:
//   ID: github-ssh  (SSH Username with private key)
// =================================================================

pipeline {
    agent any

    triggers {
        pollSCM('H/5 * * * *')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
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
        // Không dùng when { branch } vì không phải Multibranch Pipeline
        // ============================================================
        stage('Checkout') {
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

                    for KEY in VITE_API_URL VITE_BACKEND_URL DB_USER DB_PASSWORD DB_NAME REDIS_PASSWORD; do
                        if ! grep -q "^${KEY}=" "$DEPLOY_DIR/.env" 2>/dev/null; then
                            echo "  ERROR: $KEY missing in .env"
                            FAILED=1
                        fi
                    done

                    if [ -f "$DEPLOY_DIR/nginx/ssl/fullchain.pem" ]; then
                        EXPIRY=$(openssl x509 -enddate -noout \
                            -in "$DEPLOY_DIR/nginx/ssl/fullchain.pem" | cut -d= -f2)
                        EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || echo 0)
                        DAYS=$(( (EXPIRY_EPOCH - $(date +%s)) / 86400 ))
                        if [ "$DAYS" -lt 0 ]; then
                            echo "  ERROR: SSL cert ĐÃ HẾT HẠN!"
                            FAILED=1
                        elif [ "$DAYS" -lt 30 ]; then
                            echo "  WARN : SSL cert còn $DAYS ngày — nên renew sớm"
                        else
                            echo "  OK   : SSL cert còn $DAYS ngày"
                        fi
                    fi

                    FREE_GB=$(df -BG / | awk 'NR==2{gsub("G",""); print $4}')
                    if [ "$FREE_GB" -lt 5 ]; then
                        echo "  WARN : Disk chỉ còn ${FREE_GB}GB"
                    else
                        echo "  OK   : Disk còn ${FREE_GB}GB"
                    fi

                    [ $FAILED -eq 0 ] || { echo "Validation FAILED"; exit 1; }
                    echo "Validation passed ✓"
                '''
            }
        }

        // ============================================================
        // Stage 3: Detect Changes
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
                    } else {
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
        // Mount toàn bộ backend/.env.prod vào container thay vì
        // truyền từng biến → đảm bảo SECRET_KEY và tất cả config có đủ
        // ============================================================
        stage('Test') {
            when {
                environment name: 'RUN_TESTS', value: 'true'
            }
            steps {
                echo '\033[34m[4/7] Running backend unit tests...\033[0m'
                sh '''
                    # Lần đầu deploy image chưa tồn tại → skip
                    if ! docker image inspect skinaid-backend:latest > /dev/null 2>&1; then
                        echo "Image skinaid-backend:latest chưa có — skip tests (first deploy)"
                        exit 0
                    fi

                    # Mount env file trực tiếp → app nhận đủ tất cả config
                    # Dùng Redis DB 1 (tránh ảnh hưởng data production ở DB 0)
                    docker run --rm \
                        --network skinaid_skinaid_internal \
                        --env-file "$DEPLOY_DIR/backend/.env.prod" \
                        -e REDIS_URL="redis://:$(grep ^REDIS_PASSWORD= $DEPLOY_DIR/.env | cut -d= -f2)@redis:6379/1" \
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
        // ============================================================
        stage('Build') {
            when {
                environment name: 'SKIP_BUILD', value: 'false'
            }
            steps {
                echo '\033[34m[5/7] Syncing code and building: ${BUILD_SERVICES}...\033[0m'
                sh '''
                    cd "$DEPLOY_DIR"

                    git fetch origin ${BRANCH}
                    git reset --hard origin/${BRANCH}

                    # Confirm file untracked vẫn còn sau reset
                    for f in ".env" "backend/.env.prod" "ai_ml/.env.prod" \
                             "nginx/ssl/fullchain.pem" "nginx/ssl/privkey.pem"; do
                        [ -f "$DEPLOY_DIR/$f" ] \
                            && echo "  Preserved: $f ✓" \
                            || echo "  WARN: $f missing sau reset!"
                    done

                    # Load env — .env gốc có VITE_* cần cho frontend build
                    set -a
                    . "$DEPLOY_DIR/.env"
                    . "$DEPLOY_DIR/backend/.env.prod"
                    set +a

                    echo "  VITE_API_URL     = $VITE_API_URL"
                    echo "  VITE_BACKEND_URL = $VITE_BACKEND_URL"

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

                    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

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

                    poll_health "backend   :8000" "skinaid_backend" \
                        "curl -sf http://localhost:8000/health" 20 || FAILED=1

                    poll_health "ai_ml     :8001" "skinaid_ai" \
                        "python3 /app/check_health.py" 30 || FAILED=1

                    poll_health "nginx      :80 " "skinaid_nginx" \
                        "wget -qO- http://localhost/nginx-health" 10 || FAILED=1

                    # Frontend: kiểm tra qua HTTPS trực tiếp vào frontend container
                    poll_health "frontend  →nginx" "skinaid_frontend" \
                        "wget -qO- http://localhost/ | grep -q 'SkinAid'" 10 || FAILED=1

                    echo ""

                    if [ $FAILED -eq 1 ]; then
                        echo "=== HEALTH CHECK FAILED — Service logs ==="
                        docker logs skinaid_backend --tail=40 2>&1 || true
                        echo "---"
                        docker logs skinaid_ai      --tail=40 2>&1 || true
                        echo "---"
                        docker logs skinaid_nginx   --tail=20 2>&1 || true
                        exit 1
                    fi

                    echo "=== Container status ==="
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
                docker image prune -f --filter "until=48h" || true
                docker container prune -f || true

                echo "$(date '+%Y-%m-%d %H:%M:%S') | SUCCESS | #${BUILD_NUMBER} | ${GIT_SHORT_SHA} | ${GIT_COMMIT_MSG} | ${GIT_AUTHOR}" \
                    >> "$DEPLOY_DIR/deploy-history.log"
            '''
        }

        failure {
            echo '\033[31m=== PIPELINE FAILED — Rolling back... ===\033[0m'
            sh '''
                # Dùng đường dẫn tuyệt đối — post block không có working dir cố định
                set -a
                [ -f "$DEPLOY_DIR/.env" ]              && . "$DEPLOY_DIR/.env"
                [ -f "$DEPLOY_DIR/backend/.env.prod" ] && . "$DEPLOY_DIR/backend/.env.prod"
                set +a

                cd "$DEPLOY_DIR"
                docker compose -f "$COMPOSE_FILE" up -d || true

                echo "$(date '+%Y-%m-%d %H:%M:%S') | FAILED  | #${BUILD_NUMBER} | ${GIT_SHORT_SHA:-unknown} | ${GIT_COMMIT_MSG:-?}" \
                    >> "$DEPLOY_DIR/deploy-history.log" || true
            '''
        }

        always {
            cleanWs()
        }
    }
}