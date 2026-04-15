-- ============================================================
-- SKINAID - PostgreSQL Schema (MERGED FINAL)
-- ============================================================
-- Version: 3.4.0
-- Merged from:
--   skinaid_v2.2  (branch: chatbot)
--   schema_v3_final (branch: model-management)
--   questionnaires module (branch: questionnaire-management)
--   llm management module (branch: llm-management)
--
-- Merge rules applied:
--   users                → v3_final  (+last_active_at)
--   audit_logs           → v3_final  (+log_type, level, description, 2 indexes)
--   ai_results           → v2.2      (-gpu_memory_mb)
--   firstaid_guides      → v2.2      (lean: no doctor review / analytics / embedding)
--   ai_models            → v3_final  (full redesign for model lifecycle)
--   model_version_history→ v3_final  (new table)
--   model_performance    → DROPPED   (no service writes to it)
--   device_sessions      → v3_final  (-rate_limit_remaining, -rate_limit_reset_at)
--   questionnaires       → NEW       (3 tables: questionnaires, questions, answer_options)
--   llm_configurations   → NEW       (4 tables: configurations, change_logs, usage_stats, budget)
--   Views                → 3 views   (v_model_performance_dashboard dropped with model_performance)
--
-- Fixes v3.4.0:
--   🟢 llm_budget_settings        → bảng singleton lưu budget tháng + giá token
--   🟢 llm section                → đánh dấu 4 bảng: configurations, change_logs, usage_stats, budget_settings
--   🟢 Total tables               → 27 (was 26)
--
-- Fixes v3.3.0:
--   🟢 questionnaires            → thêm 3 bảng mới: questionnaires, questions, answer_options
--   🟢 partial unique index      → chỉ cho phép 1 questionnaire active per wound_type
--   🟢 models_registry           → đã include Questionnaire, Question, AnswerOption
--
-- Fixes v3.2.0:
--   🔴 analyses.model_id          → thêm FK REFERENCES ai_models
--   🔴 ai_results.model_id        → bỏ cột, giữ snapshot string
--   🔴 chat_sessions.user_id      → nullable + guest_session_id + CHECK + guest_message_limit
--   🟡 rag_documents              → thêm file_size_bytes, indexed_at
--   🟡 analyses                   → thêm is_deleted, deleted_at
--   🟢 user_inputs                → bỏ question_template_id
--   🟢 verification_tokens        → bỏ updated_at
--   🟢 trigger chat               → cộng dồn total_tokens_used + total_cost_usd
--
-- Total Tables: 27
-- External:
--   Qdrant : skinaid_knowledge_base (1536d, OpenAI text-embedding-3-small)
--            rag_documents.rag_document_id = Qdrant payload.document_id
--   Redis  : session, jwt_blacklist, rate_limit, ai_result_cache, notification_queue
--   MinIO  : skinaid-models, skinaid-images
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- UTILITY
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 1. AUTHENTICATION
-- ============================================================

-- Source: v3_final — added last_active_at
CREATE TABLE users (
    user_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name             VARCHAR(255) NOT NULL UNIQUE,
    email                 VARCHAR(255) NOT NULL UNIQUE,
    hashed_password       VARCHAR(255) NOT NULL,

    -- Security
    token_version         INTEGER NOT NULL DEFAULT 0,
    is_active             BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified           BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted            BOOLEAN NOT NULL DEFAULT FALSE,

    -- Brute-force protection
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until          TIMESTAMP,

    -- Metadata
    last_login_at         TIMESTAMP,
    last_login_ip         VARCHAR(45),
    last_active_at        TIMESTAMP,          -- v3_final: track last activity
    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email  ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_locked ON users(locked_until);

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE user_profiles (
    user_id              UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    full_name            VARCHAR(255),
    phone                VARCHAR(20),
    date_of_birth        DATE,
    gender               VARCHAR(20),
    address              TEXT,
    avatar_url           TEXT,

    language             VARCHAR(10)  DEFAULT 'vi',
    timezone             VARCHAR(50)  DEFAULT 'Asia/Ho_Chi_Minh',
    notification_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE verification_tokens (
    token_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email      VARCHAR(255) NOT NULL REFERENCES users(email) ON UPDATE CASCADE,
    token      VARCHAR(255) NOT NULL UNIQUE,
    -- email_verify | password_reset | phone_verify
    token_type VARCHAR(50)  NOT NULL,

    max_uses   INTEGER NOT NULL DEFAULT 1,
    use_count  INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    is_used    BOOLEAN NOT NULL DEFAULT FALSE,

    created_ip VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
    -- updated_at bỏ — verification_token là immutable sau khi tạo, không cần trigger
);

CREATE INDEX idx_verification_tokens_expires ON verification_tokens(expires_at);
CREATE INDEX idx_verification_tokens_type    ON verification_tokens(token_type, is_used);

-- NOTE: JWT blacklist lives in Redis.
-- Key pattern: SET blacklist:{jti} 1 EX {remaining_ttl_seconds}
-- Check:       EXISTS blacklist:{jti}


CREATE TABLE token_families (
    family_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    device_id         VARCHAR(100),

    refresh_token_jti VARCHAR(255) NOT NULL UNIQUE,
    access_token_jti  VARCHAR(255),
    parent_jti        VARCHAR(255),

    is_revoked        BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_reason    VARCHAR(100),

    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at        TIMESTAMP NOT NULL
);

CREATE INDEX idx_token_families_refresh ON token_families(refresh_token_jti);
CREATE INDEX idx_token_families_user    ON token_families(user_id, is_revoked);
CREATE INDEX idx_token_families_device  ON token_families(device_id, expires_at);

-- ============================================================
-- 2. RBAC
-- ============================================================

CREATE TABLE roles (
    role_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name   VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    is_system   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE permissions (
    permission_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    permission_name VARCHAR(100) NOT NULL UNIQUE,
    description     TEXT,
    resource_type   VARCHAR(50),
    action_type     VARCHAR(20),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);


CREATE TABLE user_roles (
    user_id     UUID REFERENCES users(user_id) ON DELETE CASCADE,
    role_id     UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user    ON user_roles(user_id);
CREATE INDEX idx_user_roles_role    ON user_roles(role_id);
CREATE INDEX idx_user_roles_expires ON user_roles(expires_at);


CREATE TABLE role_permissions (
    role_id       UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    granted_by    UUID REFERENCES users(user_id) ON DELETE SET NULL,
    granted_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

-- ============================================================
-- 3. GUEST SESSIONS
-- ============================================================

CREATE TABLE guest_sessions (
    session_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address           VARCHAR(45),
    user_agent           TEXT,

    upload_count         INTEGER NOT NULL DEFAULT 0,
    analysis_count       INTEGER NOT NULL DEFAULT 0,
    daily_upload_limit   INTEGER NOT NULL DEFAULT 10,

    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    is_converted_to_user BOOLEAN NOT NULL DEFAULT FALSE,
    converted_user_id    UUID REFERENCES users(user_id) ON DELETE SET NULL,
    converted_at         TIMESTAMP,

    platform             VARCHAR(20),
    app_version          VARCHAR(50),
    os_version           VARCHAR(50),
    device_model         VARCHAR(100),

    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at           TIMESTAMP NOT NULL,
    last_activity_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_guest_sessions_expires  ON guest_sessions(expires_at);
CREATE INDEX idx_guest_sessions_active   ON guest_sessions(is_active, last_activity_at);
CREATE INDEX idx_guest_sessions_platform ON guest_sessions(platform);

-- ============================================================
-- 4. AUDIT LOGS
-- ============================================================

-- Source: v3_final — added log_type, level, description + 2 indexes
CREATE TABLE audit_logs (
    audit_action_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID REFERENCES users(user_id) ON DELETE SET NULL,

    action           VARCHAR(100) NOT NULL,
    -- admin_action | user_activity | system_error
    log_type         VARCHAR(50) DEFAULT 'user_activity',
    -- info | warning | error
    level            VARCHAR(20) DEFAULT 'info',
    description      TEXT,

    resource_type    VARCHAR(50),
    resource_id      VARCHAR(255),
    -- auth | analysis | chat | admin | system
    action_category  VARCHAR(50),

    success          BOOLEAN NOT NULL DEFAULT TRUE,
    error_message    VARCHAR(500),
    error_code       VARCHAR(50),

    ip_address       VARCHAR(45),
    user_agent       VARCHAR(500),
    is_guest         BOOLEAN NOT NULL DEFAULT FALSE,
    guest_session_id UUID REFERENCES guest_sessions(session_id) ON DELETE SET NULL,
    device_id        VARCHAR(100),

    details          JSONB,
    request_body     JSONB,
    response_status  INTEGER,

    timestamp        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user     ON audit_logs(user_id, timestamp);
CREATE INDEX idx_audit_logs_action   ON audit_logs(action, timestamp);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_category ON audit_logs(action_category, timestamp);
CREATE INDEX idx_audit_logs_success  ON audit_logs(success, timestamp);
CREATE INDEX idx_audit_logs_log_type ON audit_logs(log_type);
CREATE INDEX idx_audit_logs_level    ON audit_logs(level);

-- ============================================================
-- 5. ANALYSES
-- ============================================================

CREATE TABLE analyses (
    analysis_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID REFERENCES users(user_id) ON DELETE SET NULL,
    guest_session_id    UUID REFERENCES guest_sessions(session_id) ON DELETE SET NULL,

    image_url           TEXT NOT NULL,
    image_hash          VARCHAR(64),
    image_size_bytes    INTEGER,
    image_dimensions    VARCHAR(20),

    -- queued | processing | analyzing | completed | failed | cancelled
    status              VARCHAR(20) NOT NULL DEFAULT 'queued',
    status_reason       VARCHAR(255),

    wound_type          VARCHAR(50),
    severity            VARCHAR(50),
    sub_type            VARCHAR(50),
    confidence          FLOAT,

    model_id            UUID,   -- FK added after ai_models table: see ALTER TABLE below
    model_version       VARCHAR(50),    -- snapshot: giữ lại version string tại thời điểm phân tích

    queued_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at          TIMESTAMP,
    completed_at        TIMESTAMP,

    is_offline          BOOLEAN NOT NULL DEFAULT FALSE,
    offline_created_at  TIMESTAMP,
    synced_at           TIMESTAMP,
    device_id           VARCHAR(100),

    processing_attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts        INTEGER NOT NULL DEFAULT 3,

    -- Soft delete
    is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMP,

    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analyses_user_history  ON analyses(user_id, created_at DESC);
CREATE INDEX idx_analyses_guest_history ON analyses(guest_session_id, created_at DESC);
CREATE INDEX idx_analyses_status        ON analyses(status, started_at);
CREATE INDEX idx_analyses_analytics     ON analyses(wound_type, severity, created_at);
CREATE INDEX idx_analyses_device        ON analyses(device_id, created_at);
CREATE INDEX idx_analyses_offline       ON analyses(is_offline, synced_at);
CREATE INDEX idx_analyses_hash          ON analyses(image_hash);

CREATE TRIGGER trg_analyses_updated_at
    BEFORE UPDATE ON analyses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- Source: v2.2 — gpu_memory_mb removed (AI service never returns this value)
CREATE TABLE ai_results (
    result_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id          UUID NOT NULL REFERENCES analyses(analysis_id) ON DELETE CASCADE,

    -- classification | detail | generation
    result_type          VARCHAR(20) NOT NULL,

    -- Model info lưu dạng snapshot string — không dùng FK để tránh mất audit khi model bị xóa
    model_name           VARCHAR(100) NOT NULL,
    model_version        VARCHAR(50)  NOT NULL,

    -- classification: {class, confidence, bounding_boxes[], detections[]}
    -- detail:         {wound_type, severity, sub_type, confidence, features{}}
    -- generation:     {steps[], warnings[], see_doctor, sources{db[], rag[]}}
    results              JSONB NOT NULL,

    confidence_breakdown JSONB,
    processing_time_ms   INTEGER,

    created_at           TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_results_analysis    ON ai_results(analysis_id, result_type);
CREATE INDEX idx_ai_results_type        ON ai_results(result_type, created_at);
CREATE INDEX idx_ai_results_model       ON ai_results(model_name, model_version);
CREATE INDEX idx_ai_results_performance ON ai_results(processing_time_ms);
CREATE INDEX idx_ai_results_jsonb       ON ai_results USING GIN (results);


CREATE TABLE user_inputs (
    input_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id          UUID NOT NULL REFERENCES analyses(analysis_id) ON DELETE CASCADE,

    -- question_template_id đã bỏ — không có bảng question_templates trong schema
    question_text        TEXT,
    -- text | multiple_choice | scale | boolean
    question_type        VARCHAR(50),
    answer               JSONB NOT NULL,

    -- pending | passed | rejected | expired
    validation_status    VARCHAR(20) NOT NULL DEFAULT 'pending',
    validation_notes     TEXT,
    validated_at         TIMESTAMP,
    validated_by         UUID REFERENCES users(user_id),

    used_in_prompt       BOOLEAN NOT NULL DEFAULT FALSE,
    importance_score     FLOAT,

    created_at           TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_inputs_analysis   ON user_inputs(analysis_id);
CREATE INDEX idx_user_inputs_status     ON user_inputs(validation_status);
CREATE INDEX idx_user_inputs_validation ON user_inputs(validation_status, validated_at);

-- ============================================================
-- 6. KNOWLEDGE BASE
-- ============================================================

-- Source: v2.2 — lean version
-- Removed: superseded_by, reviewed_by, reviewed_at (doctor review workflow not implemented)
-- Removed: embedding_id, keywords (Qdrant manages its own IDs and vector search)
-- Removed: usage_count, helpful_count, not_helpful_count, cache_priority (no service increments these)
CREATE TABLE firstaid_guides (
    firstaidguide_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- burn | bruise | abrasion | cut | acne | fungal | psoriasis | general
    wound_type             VARCHAR(50) NOT NULL,
    -- mild | moderate | severe | all
    severity               VARCHAR(50) NOT NULL CHECK (severity IN ('mild', 'moderate', 'severe', 'all')),
    sub_type               VARCHAR(50),
    title                  VARCHAR(255) NOT NULL,

    source                 JSONB,
    steps                  JSONB NOT NULL,
    dos                    JSONB,
    donts                  JSONB,
    estimated_healing_time VARCHAR(100),
    supplies_needed        JSONB,

    is_active              BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted             BOOLEAN NOT NULL DEFAULT FALSE,
    version                INTEGER NOT NULL DEFAULT 1,

    created_by             UUID REFERENCES users(user_id) ON DELETE SET NULL,

    created_at             TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (wound_type, severity, sub_type)
);

CREATE INDEX idx_firstaid_guides_wound        ON firstaid_guides(wound_type, severity);
CREATE INDEX idx_firstaid_guides_active       ON firstaid_guides(is_active, is_deleted);
CREATE INDEX idx_firstaid_guides_title_search ON firstaid_guides USING GIN (to_tsvector('simple', title));

CREATE TRIGGER trg_firstaid_guides_updated_at
    BEFORE UPDATE ON firstaid_guides
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE detections (
    detection_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id               UUID NOT NULL REFERENCES analyses(analysis_id) ON DELETE CASCADE,
    classification_result_id  UUID REFERENCES ai_results(result_id) ON DELETE SET NULL,

    detection_index           INTEGER NOT NULL,
    bounding_box              JSONB NOT NULL,
    confidence                FLOAT NOT NULL,

    -- skin_wound | phy_wound | normal_skin
    detected_class            VARCHAR(50) NOT NULL,

    wound_type                VARCHAR(50),
    severity                  VARCHAR(50),
    sub_type                  VARCHAR(50),
    detail_confidence         FLOAT,

    firstaidguide_id          UUID REFERENCES firstaid_guides(firstaidguide_id) ON DELETE SET NULL,
    firstaid_snapshot         JSONB,
    firstaid_snapshot_version INTEGER,

    is_validated              BOOLEAN NOT NULL DEFAULT FALSE,
    validated_by              UUID REFERENCES users(user_id),
    validated_at              TIMESTAMP,
    validation_notes          TEXT,

    created_at                TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_detections_analysis   ON detections(analysis_id, detection_index);
CREATE INDEX idx_detections_class      ON detections(detected_class, created_at);
CREATE INDEX idx_detections_wound      ON detections(wound_type, severity);
CREATE INDEX idx_detections_validation ON detections(is_validated, validated_at);

-- ============================================================
-- 7. CHATBOT
-- ============================================================

CREATE TABLE chat_sessions (
    session_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Nullable: guest cũng được chat có giới hạn
    user_id               UUID REFERENCES users(user_id) ON DELETE CASCADE,
    guest_session_id      UUID REFERENCES guest_sessions(session_id) ON DELETE CASCADE,
    analysis_id           UUID REFERENCES analyses(analysis_id) ON DELETE SET NULL,

    -- CHECK: phải có ít nhất một trong hai
    CONSTRAINT chk_chat_session_owner CHECK (
        user_id IS NOT NULL OR guest_session_id IS NOT NULL
    ),

    system_prompt_version VARCHAR(20) DEFAULT 'v2',
    wound_context         JSONB,
    -- anxious | calm | urgent
    user_mood             VARCHAR(20),

    -- active | closed | expired | escalated
    status                VARCHAR(20) NOT NULL DEFAULT 'active',
    closure_reason        VARCHAR(100),

    message_limit         INTEGER NOT NULL DEFAULT 50,
    -- Guest bị giới hạn thấp hơn, service tự set khi tạo session
    guest_message_limit   INTEGER NOT NULL DEFAULT 10,
    message_count         INTEGER NOT NULL DEFAULT 0,

    last_message_at       TIMESTAMP,
    expires_at            TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours',

    total_tokens_used     INTEGER NOT NULL DEFAULT 0,
    -- total_cost_usd được tự động cộng dồn bởi trigger trg_chat_message_insert
    total_cost_usd        FLOAT NOT NULL DEFAULT 0,
    llm_model             VARCHAR(50),
    language              VARCHAR(10) DEFAULT 'vi',

    user_rating           INTEGER,
    user_feedback         TEXT,

    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user     ON chat_sessions(user_id, status);
CREATE INDEX idx_chat_sessions_guest    ON chat_sessions(guest_session_id, status);
CREATE INDEX idx_chat_sessions_analysis ON chat_sessions(analysis_id);
CREATE INDEX idx_chat_sessions_cleanup  ON chat_sessions(status, expires_at);
CREATE INDEX idx_chat_sessions_active   ON chat_sessions(status, last_message_at);

CREATE TRIGGER trg_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE chat_messages (
    message_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id         UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,

    -- user | assistant | system
    role               VARCHAR(20) NOT NULL,
    content            TEXT NOT NULL,

    tokens_used        INTEGER NOT NULL DEFAULT 0,
    token_cost_usd     FLOAT DEFAULT 0,

    model_used         VARCHAR(50),
    temperature        FLOAT DEFAULT 0.7,

    -- RAG citations: [{guide_id, url, excerpt}]
    sources            JSONB,

    is_helpful         BOOLEAN,
    flagged            BOOLEAN NOT NULL DEFAULT FALSE,
    flag_reason        VARCHAR(255),

    processing_time_ms INTEGER,
    created_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session        ON chat_messages(session_id, created_at);
CREATE INDEX idx_chat_messages_role           ON chat_messages(role, created_at);
CREATE INDEX idx_chat_messages_feedback       ON chat_messages(is_helpful);
CREATE INDEX idx_chat_messages_flagged        ON chat_messages(flagged);
CREATE INDEX idx_chat_messages_content_search ON chat_messages USING GIN (to_tsvector('simple', content));

-- Auto-increment session message_count, total_tokens_used, total_cost_usd on insert
CREATE OR REPLACE FUNCTION update_chat_session_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_sessions
    SET message_count     = message_count + 1,
        last_message_at   = NOW(),
        total_tokens_used = total_tokens_used + NEW.tokens_used,
        total_cost_usd    = total_cost_usd + COALESCE(NEW.token_cost_usd, 0),
        updated_at        = NOW()
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_chat_message_insert
    AFTER INSERT ON chat_messages
    FOR EACH ROW EXECUTE FUNCTION update_chat_session_count();

-- ============================================================
-- 8. AI MODEL MANAGEMENT
-- ============================================================

-- Source: v3_final — full redesign for model lifecycle management
CREATE TABLE ai_models (
    model_id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Model identification
    model_type                  VARCHAR(50) NOT NULL,
    version_tag                 VARCHAR(50) NOT NULL,
    version_number              INTEGER NOT NULL DEFAULT 1,

    -- File storage
    file_path                   TEXT NOT NULL,
    file_size_bytes             FLOAT,
    file_hash                   VARCHAR(64),

    -- Metadata
    name                        VARCHAR(200),
    description                 TEXT,

    -- Performance metrics (JSONB — flexible per model type)
    metrics                     JSONB,

    -- Status flags
    is_active                   BOOLEAN NOT NULL DEFAULT FALSE,
    is_beta                     BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted                  BOOLEAN NOT NULL DEFAULT FALSE,

    -- Traffic split (A/B testing)
    traffic_percentage          INTEGER NOT NULL DEFAULT 0,

    -- Deployment info
    deployed_at                 TIMESTAMP,
    deployed_by                 UUID REFERENCES users(user_id) ON DELETE SET NULL,

    -- Activation tracking
    activated_at                TIMESTAMP,
    previously_active_version_id UUID REFERENCES ai_models(model_id) ON DELETE SET NULL,

    -- Audit timestamps
    created_at                  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at                  TIMESTAMP,
    deleted_by                  UUID REFERENCES users(user_id) ON DELETE SET NULL,

    UNIQUE (model_type, version_tag)
);

CREATE INDEX ix_ai_models_type_active  ON ai_models(model_type, is_active);
CREATE INDEX ix_ai_models_type_deleted ON ai_models(model_type, is_deleted);
CREATE INDEX ix_ai_models_created_at   ON ai_models(created_at);
CREATE INDEX ix_ai_models_deployed_at  ON ai_models(deployed_at);
CREATE INDEX ix_ai_models_activated_at ON ai_models(activated_at);
CREATE INDEX ix_ai_models_prev_active  ON ai_models(previously_active_version_id);

CREATE TRIGGER trg_ai_models_updated_at
    BEFORE UPDATE ON ai_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- Source: v3_final — audit trail for every action on a model
CREATE TABLE model_version_history (
    history_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id    UUID NOT NULL REFERENCES ai_models(model_id) ON DELETE CASCADE,

    action      VARCHAR(50) NOT NULL,
    from_version VARCHAR(50),
    to_version   VARCHAR(50),

    actor_id    UUID REFERENCES users(user_id) ON DELETE SET NULL,
    actor_ip    VARCHAR(45),

    details     JSONB,

    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_model_history_model_action ON model_version_history(model_id, action);
CREATE INDEX ix_model_history_created_at   ON model_version_history(created_at);

-- Fix forward-reference: analyses.model_id → ai_models
ALTER TABLE analyses
    ADD CONSTRAINT fk_analyses_model_id
    FOREIGN KEY (model_id) REFERENCES ai_models(model_id) ON DELETE SET NULL;

CREATE INDEX idx_analyses_model ON analyses(model_id);

-- ============================================================
-- 9. DEVICE SESSIONS
-- ============================================================

CREATE TABLE device_sessions (
    session_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID REFERENCES users(user_id) ON DELETE CASCADE,
    device_id            VARCHAR(100) NOT NULL,

    -- ios | android | web
    platform             VARCHAR(20) NOT NULL,
    app_version          VARCHAR(50),
    os_version           VARCHAR(50),
    device_model         VARCHAR(100),
    device_name          VARCHAR(255),

    push_token           TEXT,
    push_enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    last_notification_at TIMESTAMP,

    cached_sources       JSONB,
    cache_size_mb        FLOAT,
    cache_version        VARCHAR(50),
    last_sync_at         TIMESTAMP,

    pending_syncs        JSONB,
    -- synced | pending | conflicting
    sync_status          VARCHAR(20) DEFAULT 'synced',

    is_trusted           BOOLEAN NOT NULL DEFAULT FALSE,
    last_trusted_at      TIMESTAMP,

    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    last_activity_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, device_id)
);

CREATE INDEX idx_device_sessions_user     ON device_sessions(user_id, is_active);
CREATE INDEX idx_device_sessions_push     ON device_sessions(push_enabled, is_active);
CREATE INDEX idx_device_sessions_sync     ON device_sessions(user_id, last_sync_at);
CREATE INDEX idx_device_sessions_platform ON device_sessions(platform, app_version);

CREATE TRIGGER trg_device_sessions_updated_at
    BEFORE UPDATE ON device_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 10. NOTIFICATIONS
-- ============================================================

CREATE TABLE notifications (
    notification_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID REFERENCES users(user_id) ON DELETE CASCADE,
    device_id           VARCHAR(100),

    title               VARCHAR(255) NOT NULL,
    body                TEXT NOT NULL,
    -- analysis_complete | reminder | system | chat_message
    notification_type   VARCHAR(50) NOT NULL,

    data                JSONB,
    action_url          TEXT,
    image_url           TEXT,

    -- low | normal | high | critical
    priority            VARCHAR(20) DEFAULT 'normal',
    scheduled_at        TIMESTAMP,
    sent_at             TIMESTAMP,
    delivered_at        TIMESTAMP,
    read_at             TIMESTAMP,

    -- pending | scheduled | sent | delivered | failed
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    failure_reason      VARCHAR(255),
    retry_count         INTEGER NOT NULL DEFAULT 0,
    max_retries         INTEGER NOT NULL DEFAULT 3,

    -- fcm | apns | email
    provider            VARCHAR(20),
    provider_message_id VARCHAR(255),
    provider_response   JSONB,

    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user      ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_status    ON notifications(status, scheduled_at);
CREATE INDEX idx_notifications_type      ON notifications(notification_type, created_at);
CREATE INDEX idx_notifications_unread    ON notifications(user_id, read_at) WHERE read_at IS NULL;
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_at) WHERE status = 'scheduled';

CREATE TRIGGER trg_notifications_updated_at
    BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 11. RAG DOCUMENTS
-- ============================================================

CREATE TABLE rag_documents (
    rag_document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    file_name       VARCHAR(500)  NOT NULL,
    -- Extension không có dấu chấm: pdf | md | txt | docx | html | csv
    file_type       VARCHAR(20)   NOT NULL,
    file_size_bytes BIGINT,                  -- dùng để validate upload limit & hiển thị UI
    storage_path    VARCHAR(1000) NOT NULL,

    -- pending | indexing | indexed | failed | deleted
    status          VARCHAR(20)   NOT NULL DEFAULT 'pending',
    chunk_count     INTEGER       NOT NULL DEFAULT 0,
    error_message   VARCHAR(2000),
    indexed_at      TIMESTAMP,               -- thời điểm index xong vào Qdrant, NULL nếu chưa indexed

    -- Metadata tùy chỉnh: wound_type filter, source, language, v.v.
    doc_metadata    JSONB,

    uploaded_by     UUID REFERENCES users(user_id) ON DELETE SET NULL,

    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_documents_file_name   ON rag_documents(file_name);
CREATE INDEX idx_rag_documents_status      ON rag_documents(status);
CREATE INDEX idx_rag_documents_type_status ON rag_documents(file_type, status);
CREATE INDEX idx_rag_documents_uploaded_by ON rag_documents(uploaded_by, created_at);

CREATE TRIGGER trg_rag_documents_updated_at
    BEFORE UPDATE ON rag_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 12. QUESTIONNAIRE MANAGEMENT (NEW in v3.3.0)
-- ============================================================
-- Module for admin to manage triage questionnaires per wound type.
-- Each wound_type can have at most 1 active questionnaire (enforced by partial unique index).
-- Structure: Questionnaire → Questions (ordered) → AnswerOptions (ordered, with triage_level)

CREATE TABLE questionnaires (
    questionnaire_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wound_type        VARCHAR(50) NOT NULL,
    title             VARCHAR(255) NOT NULL,
    description       TEXT,

    -- Default FALSE = draft mode. Only 1 active per wound_type (see partial unique index below)
    is_active         BOOLEAN NOT NULL DEFAULT FALSE,

    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Partial unique index: chỉ cho phép 1 questionnaire active per wound_type
-- Khi activate 1 questionnaire, service phải deactivate các bản khác cùng wound_type trước
CREATE UNIQUE INDEX uq_questionnaires_active_wound_type
    ON questionnaires(wound_type) WHERE is_active = TRUE;

CREATE INDEX idx_questionnaires_wound_type ON questionnaires(wound_type);
CREATE INDEX idx_questionnaires_active     ON questionnaires(is_active);

CREATE TRIGGER trg_questionnaires_updated_at
    BEFORE UPDATE ON questionnaires
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE questions (
    question_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    questionnaire_id   UUID NOT NULL REFERENCES questionnaires(questionnaire_id) ON DELETE CASCADE,

    question_text      TEXT NOT NULL,
    order_index        INTEGER NOT NULL DEFAULT 0,
    is_multiple_choice BOOLEAN NOT NULL DEFAULT FALSE,
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,

    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_questions_questionnaire ON questions(questionnaire_id, order_index);
CREATE INDEX idx_questions_active        ON questions(is_active);

CREATE TRIGGER trg_questions_updated_at
    BEFORE UPDATE ON questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE answer_options (
    answer_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id    UUID NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,

    answer_text    TEXT NOT NULL,
    -- green (nhẹ) | yellow (trung bình) | red (nghiêm trọng)
    triage_level   VARCHAR(20) NOT NULL CHECK (triage_level IN ('green', 'yellow', 'red')),
    icon_or_color  VARCHAR(50),
    order_index    INTEGER NOT NULL DEFAULT 0,

    -- Flexible metadata: tags, scoring weights, additional context
    metadata_tags  JSONB,

    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_answer_options_question     ON answer_options(question_id, order_index);
CREATE INDEX idx_answer_options_triage_level ON answer_options(triage_level);

CREATE TRIGGER trg_answer_options_updated_at
    BEFORE UPDATE ON answer_options
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 13. LLM CONFIGURATION MANAGEMENT (NEW in v3.4.0)
-- ============================================================
-- Module for admin to manage LLM model configurations at runtime.
-- 3 config keys: synthesis (B5 pipeline), chatbot_advisor, chatbot_guide
-- API key stays in .env — only non-sensitive params stored in DB.
-- DB values override .env defaults; if no DB row exists, .env is used.

CREATE TABLE llm_configurations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Unique key identifying the LLM use-case
    -- synthesis | chatbot_advisor | chatbot_guide
    config_key          VARCHAR(50) NOT NULL UNIQUE,
    display_name        VARCHAR(100) NOT NULL,
    description         TEXT,

    -- Model selection
    model_name          VARCHAR(100) NOT NULL,

    -- Tuning parameters
    temperature         FLOAT NOT NULL DEFAULT 0.3
        CHECK (temperature >= 0.0 AND temperature <= 2.0),
    max_tokens          INTEGER NOT NULL DEFAULT 2000
        CHECK (max_tokens >= 100 AND max_tokens <= 16000),
    top_k               INTEGER NOT NULL DEFAULT 5
        CHECK (top_k >= 1 AND top_k <= 20),

    -- Status flags
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_maintenance      BOOLEAN NOT NULL DEFAULT FALSE,
    maintenance_message TEXT,

    -- Audit
    updated_by          UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_llm_configurations_key    ON llm_configurations(config_key);
CREATE INDEX idx_llm_configurations_active ON llm_configurations(is_active);

CREATE TRIGGER trg_llm_configurations_updated_at
    BEFORE UPDATE ON llm_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE llm_config_change_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id       UUID NOT NULL REFERENCES llm_configurations(id) ON DELETE CASCADE,

    -- admin who made the change
    changed_by      UUID REFERENCES users(user_id) ON DELETE SET NULL,

    -- model_change | param_update | activate | deactivate | maintenance_on | maintenance_off
    change_type     VARCHAR(30) NOT NULL,

    old_values      JSONB,
    new_values      JSONB,
    reason          TEXT,

    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_llm_change_logs_config  ON llm_config_change_logs(config_id, created_at DESC);
CREATE INDEX idx_llm_change_logs_type    ON llm_config_change_logs(change_type);
CREATE INDEX idx_llm_change_logs_user    ON llm_config_change_logs(changed_by);


CREATE TABLE llm_usage_stats (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    config_key          VARCHAR(50) NOT NULL,
    model_name          VARCHAR(100) NOT NULL,

    tokens_prompt       INTEGER NOT NULL DEFAULT 0,
    tokens_completion   INTEGER NOT NULL DEFAULT 0,
    tokens_total        INTEGER NOT NULL DEFAULT 0,

    response_time_ms    INTEGER NOT NULL DEFAULT 0,

    success             BOOLEAN NOT NULL DEFAULT TRUE,
    error_message       TEXT,

    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_llm_usage_stats_config  ON llm_usage_stats(config_key, created_at DESC);
CREATE INDEX idx_llm_usage_stats_model   ON llm_usage_stats(model_name, created_at);
CREATE INDEX idx_llm_usage_stats_success ON llm_usage_stats(success, created_at);


-- Singleton table: budget cap & token pricing for cost estimation.
-- Only 1 row should exist. Admin updates via UI when OpenAI pricing changes.
CREATE TABLE llm_budget_settings (
    id                          UUID PRIMARY KEY,

    -- Monthly spend cap (USD). 0 = unlimited.
    monthly_budget_usd          FLOAT NOT NULL DEFAULT 0,

    -- Per-1K-token pricing (USD), set by admin based on current OpenAI tier
    price_per_1k_input_tokens   FLOAT NOT NULL DEFAULT 0.40,
    price_per_1k_output_tokens  FLOAT NOT NULL DEFAULT 1.60,
    currency                    VARCHAR(10) NOT NULL DEFAULT 'USD',

    updated_by                  UUID REFERENCES users(user_id) ON DELETE SET NULL,
    updated_at                  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- SEED DATA
-- ============================================================

INSERT INTO roles (role_name, description, is_system) VALUES
    ('user',   'Regular user — can analyze wounds and chat', TRUE),
    ('admin',  'Administrator — full system access',         TRUE),
    ('doctor', 'Medical professional — validate AI results', TRUE);

INSERT INTO permissions (permission_name, description, resource_type, action_type) VALUES
    ('analysis:create',  'Upload and analyze wound images',     'analysis', 'create'),
    ('analysis:read',    'View analysis results',               'analysis', 'read'),
    ('analysis:update',  'Update analysis metadata',            'analysis', 'update'),
    ('analysis:delete',  'Delete analysis records',             'analysis', 'delete'),
    ('chat:create',      'Start chatbot sessions',              'chat',     'create'),
    ('chat:read',        'View chat history',                   'chat',     'read'),
    ('user:read',        'View user profiles',                  'user',     'read'),
    ('user:update',      'Update own profile',                  'user',     'update'),
    ('admin:users',      'Manage all users',                    'admin',    'crud'),
    ('admin:models',     'Upload and manage AI models',         'admin',    'crud'),
    ('admin:dashboard',  'View admin dashboard',                'admin',    'read'),
    ('admin:knowledge',  'Manage first-aid knowledge base',     'admin',    'crud'),
    ('admin:audit',      'View audit logs',                     'admin',    'read'),
    ('admin:questionnaires', 'Manage triage questionnaires',    'admin',    'crud'),
    ('admin:llm',        'Manage LLM configurations',           'admin',    'crud'),
    ('doctor:validate',  'Validate AI detections',              'doctor',   'update');

-- Admin gets everything
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r CROSS JOIN permissions p
WHERE r.role_name = 'admin';

-- User subset
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'user'
  AND p.permission_name IN (
      'analysis:create', 'analysis:read', 'analysis:update', 'analysis:delete',
      'chat:create', 'chat:read', 'user:read', 'user:update'
  );

-- Doctor subset
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'doctor'
  AND p.permission_name IN (
      'analysis:read', 'chat:read', 'user:read', 'doctor:validate'
  );

-- ============================================================
-- LLM DEFAULT CONFIGURATIONS (SEED)
-- ============================================================
INSERT INTO llm_configurations (config_key, display_name, description, model_name, temperature, max_tokens, top_k, is_active) VALUES
    ('synthesis',
     'Tổng hợp sơ cứu (B5)',
     'LLM dùng để tổng hợp hướng dẫn sơ cứu từ kết quả AI + RAG + DB. Pipeline: phân tích ảnh → RAG retrieval → LLM synthesis → validation.',
     'gpt-4.1-mini', 0.3, 2000, 5, TRUE),

    ('chatbot_advisor',
     'Chatbot Vết thương',
     'LLM dùng cho Wound Advisor chatbot — tư vấn chuyên sâu về vết thương dựa trên kết quả phân tích.',
     'gpt-4.1-mini', 0.3, 1000, 3, TRUE),

    ('chatbot_guide',
     'Chatbot Hướng dẫn App',
     'LLM dùng cho App Guide chatbot — hướng dẫn người dùng cách sử dụng ứng dụng SkinAid.',
     'gpt-4.1-mini', 0.7, 500, 3, TRUE);

-- Default budget: $10/month, GPT-4.1-mini pricing
INSERT INTO llm_budget_settings (id, monthly_budget_usd, price_per_1k_input_tokens, price_per_1k_output_tokens)
VALUES (gen_random_uuid(), 10.0, 0.40, 1.60);

-- ============================================================
-- VIEWS
-- ============================================================

CREATE VIEW v_active_analyses AS
SELECT
    a.analysis_id,
    COALESCE(u.email, g.session_id || ' (guest)') AS user_email,
    a.status,
    a.wound_type,
    a.severity,
    a.started_at,
    a.processing_attempts
FROM analyses a
LEFT JOIN users         u ON a.user_id          = u.user_id
LEFT JOIN guest_sessions g ON a.guest_session_id = g.session_id
WHERE a.status IN ('queued', 'processing', 'analyzing');


CREATE VIEW v_chat_sessions_summary AS
SELECT
    cs.session_id,
    cs.user_id,
    cs.status,
    cs.message_count,
    cs.last_message_at,
    cs.total_tokens_used,
    cs.user_rating,
    u.email
FROM chat_sessions cs
LEFT JOIN users u ON cs.user_id = u.user_id
ORDER BY cs.last_message_at DESC;


CREATE VIEW v_unread_notifications AS
SELECT
    user_id,
    COUNT(*)        AS unread_count,
    MAX(created_at) AS latest_notification_at
FROM notifications
WHERE read_at IS NULL
GROUP BY user_id;


-- View: Questionnaire summary for admin dashboard
CREATE VIEW v_questionnaire_summary AS
SELECT
    q.questionnaire_id,
    q.wound_type,
    q.title,
    q.is_active,
    COUNT(DISTINCT qu.question_id) AS question_count,
    COUNT(DISTINCT ao.answer_id)   AS answer_count,
    q.created_at,
    q.updated_at
FROM questionnaires q
LEFT JOIN questions qu ON qu.questionnaire_id = q.questionnaire_id
LEFT JOIN answer_options ao ON ao.question_id = qu.question_id
GROUP BY q.questionnaire_id, q.wound_type, q.title, q.is_active, q.created_at, q.updated_at;

-- ============================================================
-- SUMMARY
-- ============================================================
-- Tables: 27
--   Auth:          users, user_profiles, verification_tokens, token_families
--   RBAC:          roles, permissions, user_roles, role_permissions
--   Guest:         guest_sessions
--   Audit:         audit_logs
--   Analysis:      analyses, ai_results, user_inputs, detections
--   Knowledge:     firstaid_guides
--   Chatbot:       chat_sessions, chat_messages
--   AI Model:      ai_models, model_version_history
--   Device:        device_sessions
--   Notifications: notifications
--   RAG:           rag_documents
--   Questionnaire: questionnaires, questions, answer_options   ← NEW v3.3.0
--   LLM:           llm_configurations, llm_config_change_logs,
--                  llm_usage_stats, llm_budget_settings        ← NEW v3.4.0
--
-- Views: 4
--   v_active_analyses, v_chat_sessions_summary, v_unread_notifications,
--   v_questionnaire_summary   ← NEW v3.3.0
--
-- Triggers: 15
--   updated_at (×13): users, user_profiles, roles, analyses, firstaid_guides,
--                     chat_sessions, ai_models, device_sessions, notifications,
--                     rag_documents, questionnaires, questions, answer_options
--   trg_chat_message_insert: auto-increment message_count + total_tokens_used + total_cost_usd
--   trg_llm_configurations_updated_at: auto-update updated_at   ← NEW v3.4.0
--
-- Partial unique indexes: 1
--   uq_questionnaires_active_wound_type: only 1 active questionnaire per wound_type
--
-- Fixes applied (v3.3.0 → v3.4.0):
--   🟢 llm_configurations         → runtime LLM config (model, temperature, etc.)
--   🟢 llm_config_change_logs     → audit trail for config changes
--   🟢 llm_usage_stats            → per-request token/latency tracking
--   🟢 llm_budget_settings        → singleton budget + token pricing
--   🟢 permission                 → admin:llm
--   🟢 seed data                  → 3 default configs + 1 budget row
--
-- Redis keys (replaces removed tables):
--   blacklist:{jti}                              TTL = token expiry
--   rate:{key_type}:{value}:{endpoint}:{window}  INCR + EXPIRE
-- ============================================================
