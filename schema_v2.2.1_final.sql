-- ============================================================
-- SKINAID v2.1.1 - PostgreSQL Schema (IMPROVED & FULLY SYNCED)
-- ============================================================
-- Version: 2.2.1 (Perfectly synchronized with Python SQLModel backend)
-- Total Tables: 26
-- Vector DB: Qdrant (external, 1536d OpenAI text-embedding-3-small)
-- Cache: Redis (external)
-- Storage: MinIO (S3-compatible)
-- ============================================================
-- Improvements from v2.0 & v2.1:
--   ✅ Chat messages separated (no more JSONB bloat)
--   ✅ Push notification system added
--   ✅ AI model A/B testing support
--   ✅ Better mobile indexes
--   ✅ Rollback support for migrations
--   ✅ Audit trail for sensitive operations (Upgraded with log_type, level, description)
--   ✅ Rate limiting per device
--   🔥 (HOTFIX) AI Models fully aligned with Python backend (model_type, version_tag, name, etc.)
--   🔥 (HOTFIX) Added missing model_version_history table for auditing AI deployments
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy search

-- ============================================================
-- 0. MIGRATION BACKUP TABLES (v2.0 → v2.1)
-- ============================================================
-- These tables preserve old data during migration

CREATE TABLE IF NOT EXISTS wound_analyses (
    analysis_id UUID PRIMARY KEY,
    user_id UUID,
    session_id UUID,
    image_url TEXT,
    wound_type VARCHAR(50),
    severity VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wound_detections (
    detection_id UUID PRIMARY KEY,
    analysis_id UUID,
    wound_type VARCHAR(50),
    severity VARCHAR(50),
    created_at TIMESTAMP
);

-- ============================================================
-- 1. AUTHENTICATION TABLES (Enhanced)
-- ============================================================

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- Security
    token_version INTEGER NOT NULL DEFAULT 0,  -- Increment on password change
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Rate limiting
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP,
    
    -- Metadata
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45),
    last_active_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for login performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_locked ON users(locked_until);

CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(20),
    address TEXT,
    avatar_url TEXT,
    
    -- Preferences
    language VARCHAR(10) DEFAULT 'vi',
    timezone VARCHAR(50) DEFAULT 'Asia/Ho_Chi_Minh',
    notification_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE verification_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL REFERENCES users(email) ON UPDATE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    token_type VARCHAR(50) NOT NULL,  -- email_verify, password_reset, phone_verify
    
    -- Security
    max_uses INTEGER NOT NULL DEFAULT 1,
    use_count INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Audit
    created_ip VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for cleanup
CREATE INDEX idx_verification_tokens_expires ON verification_tokens(expires_at);
CREATE INDEX idx_verification_tokens_type ON verification_tokens(token_type, is_used);

CREATE TABLE token_blacklist (
    tokenblacklist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jti VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    token_type VARCHAR(20) NOT NULL DEFAULT 'access',  -- access, refresh
    revoked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    reason VARCHAR(100)  -- logout, password_change, security_revoke
);

-- Index for JWT validation
CREATE INDEX idx_token_blacklist_jti ON token_blacklist(jti, expires_at);
CREATE INDEX idx_token_blacklist_user ON token_blacklist(user_id, revoked_at);

CREATE TABLE token_families (
    family_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    device_id VARCHAR(100),  -- Track which device created this token chain
    
    -- Token chain
    refresh_token_jti VARCHAR(255) NOT NULL UNIQUE,
    access_token_jti VARCHAR(255),
    parent_jti VARCHAR(255),  -- Parent refresh token (for rotation)
    
    -- Lifecycle
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_reason VARCHAR(100),
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- Index for token validation
CREATE INDEX idx_token_families_refresh ON token_families(refresh_token_jti);
CREATE INDEX idx_token_families_user ON token_families(user_id, is_revoked);
CREATE INDEX idx_token_families_device ON token_families(device_id, expires_at);

-- ============================================================
-- 2. RBAC TABLES (Enhanced with audit)
-- ============================================================

CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,  -- System roles can't be deleted
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE permissions (
    permission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    permission_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    resource_type VARCHAR(50),  -- analysis, chat, user, admin
    action_type VARCHAR(20),    -- create, read, update, delete
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Temporary roles (e.g., 30-day trial admin)
    PRIMARY KEY (user_id, role_id)
);

-- Index for permission checks
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
CREATE INDEX idx_user_roles_expires ON user_roles(expires_at);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    granted_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    granted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

-- ============================================================
-- 3. GUEST SESSIONS (Mobile-ready)
-- ============================================================

CREATE TABLE guest_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Limits
    upload_count INTEGER NOT NULL DEFAULT 0,
    analysis_count INTEGER NOT NULL DEFAULT 0,
    daily_upload_limit INTEGER NOT NULL DEFAULT 10,
    
    -- Lifecycle
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_converted_to_user BOOLEAN NOT NULL DEFAULT FALSE,
    converted_user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    converted_at TIMESTAMP,
    
    -- v2.0: Mobile support
    platform VARCHAR(20),           -- web, ios, android
    app_version VARCHAR(50),
    os_version VARCHAR(50),
    device_model VARCHAR(100),
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for cleanup
CREATE INDEX idx_guest_sessions_expires ON guest_sessions(expires_at);
CREATE INDEX idx_guest_sessions_active ON guest_sessions(is_active, last_activity_at);
CREATE INDEX idx_guest_sessions_platform ON guest_sessions(platform);

-- ============================================================
-- 4. AUDIT LOGS (Enhanced for compliance & proper filtering)
-- ============================================================

CREATE TABLE audit_logs (
    audit_action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Action & Classification
    action VARCHAR(100) NOT NULL,
    log_type VARCHAR(50) DEFAULT 'user_activity', -- admin_action, user_activity, system_error
    level VARCHAR(20) DEFAULT 'info',             -- info, warning, error
    description TEXT,                             -- Human-readable description
    
    -- Resources
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    action_category VARCHAR(50),  -- auth, analysis, chat, admin, system
    
    -- Result
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message VARCHAR(500),
    error_code VARCHAR(50),
    
    -- Context
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    is_guest BOOLEAN NOT NULL DEFAULT FALSE,
    guest_session_id UUID REFERENCES guest_sessions(session_id) ON DELETE SET NULL,
    device_id VARCHAR(100),
    
    -- Details
    details JSONB,
    request_body JSONB,  -- For critical actions
    response_status INTEGER,
    
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for audit queries (Updated for new fields)
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, timestamp);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, timestamp);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_category ON audit_logs(action_category, timestamp);
CREATE INDEX idx_audit_logs_success ON audit_logs(success, timestamp);
CREATE INDEX idx_audit_logs_log_type ON audit_logs(log_type);
CREATE INDEX idx_audit_logs_level ON audit_logs(level);

-- ============================================================
-- 5. ANALYSIS TABLES (v2.1 - Production Ready)
-- ============================================================

CREATE TABLE analyses (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    guest_session_id UUID REFERENCES guest_sessions(session_id) ON DELETE SET NULL,
    
    -- Image
    image_url TEXT NOT NULL,
    image_hash VARCHAR(64),  -- SHA-256 for deduplication
    image_size_bytes INTEGER,
    image_dimensions VARCHAR(20),  -- "1920x1080"
    
    -- Status: queued, processing, analyzing, completed, failed, cancelled
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    status_reason VARCHAR(255),  -- Error message if failed
    
    -- Final results (denormalized for quick queries)
    wound_type VARCHAR(50),
    severity VARCHAR(50),
    sub_type VARCHAR(50),
    confidence FLOAT,               -- 0.0-1.0
    
    -- AI model used
    model_id UUID,
    model_version VARCHAR(50),
    
    -- Timing
    queued_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Offline support (mobile)
    is_offline BOOLEAN NOT NULL DEFAULT FALSE,
    offline_created_at TIMESTAMP,  -- When created on device
    synced_at TIMESTAMP,
    device_id VARCHAR(100),
    
    -- Metadata
    processing_attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Composite indexes for common queries
CREATE INDEX idx_analyses_user_history ON analyses(user_id, created_at DESC);
CREATE INDEX idx_analyses_guest_history ON analyses(guest_session_id, created_at DESC);
CREATE INDEX idx_analyses_status ON analyses(status, started_at);
CREATE INDEX idx_analyses_analytics ON analyses(wound_type, severity, created_at);
CREATE INDEX idx_analyses_device ON analyses(device_id, created_at);  -- Mobile sync
CREATE INDEX idx_analyses_offline ON analyses(is_offline, synced_at);  -- Sync queue
CREATE INDEX idx_analyses_hash ON analyses(image_hash);  -- Deduplication

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_analyses_updated_at
    BEFORE UPDATE ON analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE ai_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analyses(analysis_id) ON DELETE CASCADE,
    
    -- Type: classification, detail, generation
    result_type VARCHAR(20) NOT NULL,
    
    -- Model info
    model_id UUID,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    
    -- Polymorphic JSONB results
    -- classification: {class, confidence, bounding_boxes[], detections[]}
    -- detail: {wound_type, severity, sub_type, confidence, features{}}
    -- generation: {steps[], warnings[], see_doctor, sources{db[], rag[]}}
    results JSONB NOT NULL,
    
    -- Confidence breakdown (generation only)
    confidence_breakdown JSONB,     -- {final, ai, db, rag, user}
    
    -- Processing
    processing_time_ms INTEGER,
    gpu_memory_mb INTEGER,         -- For performance monitoring
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for result queries
CREATE INDEX idx_ai_results_analysis ON ai_results(analysis_id, result_type);
CREATE INDEX idx_ai_results_type ON ai_results(result_type, created_at);
CREATE INDEX idx_ai_results_model ON ai_results(model_id, model_version);
CREATE INDEX idx_ai_results_performance ON ai_results(processing_time_ms);

-- GIN index for JSONB search
CREATE INDEX idx_ai_results_jsonb ON ai_results USING GIN (results);

CREATE TABLE user_inputs (
    input_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analyses(analysis_id) ON DELETE CASCADE,
    
    -- Input
    question_template_id UUID,  -- Reference to template library
    question_text TEXT,             -- Template question (optional)
    question_type VARCHAR(50),      -- text, multiple_choice, scale, boolean
    answer JSONB NOT NULL,          -- {text, selected_options[], scale_value}
    
    -- Validation: pending, passed, rejected, expired
    validation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    validation_notes TEXT,
    validated_at TIMESTAMP,
    validated_by UUID REFERENCES users(user_id),  -- Doctor review
    
    -- Usage
    used_in_prompt BOOLEAN NOT NULL DEFAULT FALSE,
    importance_score FLOAT,         -- 0.0-1.0 for AI weighting
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_user_inputs_analysis ON user_inputs(analysis_id);
CREATE INDEX idx_user_inputs_status ON user_inputs(validation_status);
CREATE INDEX idx_user_inputs_validation ON user_inputs(validation_status, validated_at);

-- ============================================================
-- 6. DETECTIONS & KNOWLEDGE (Enhanced)
-- ============================================================

CREATE TABLE firstaid_guides (
    firstaidguide_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- wound_type: burn, bruise, abrasion, cut, acne, fungal, psoriasis, general
    wound_type VARCHAR(50) NOT NULL,
    -- severity: mild, moderate, severe, all
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('mild', 'moderate', 'severe', 'all')),
    sub_type VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    
    -- Content
    source JSONB,                   -- {type: 'medical_journal', url, citation}
    steps JSONB NOT NULL,           -- [{step, instruction, image_url}]
    dos JSONB,                      -- [{action, reason}]
    donts JSONB,                    -- [{action, reason}]
    estimated_healing_time VARCHAR(100),
    supplies_needed JSONB,          -- [{item, quantity, optional}]
    
    -- Lifecycle
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    version INTEGER NOT NULL DEFAULT 1,
    superseded_by UUID REFERENCES firstaid_guides(firstaidguide_id),
    
    -- Audit
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    reviewed_by UUID REFERENCES users(user_id),  -- Doctor review
    reviewed_at TIMESTAMP,
    
    -- v2.0: Vector search via Qdrant (768d, gemini-embedding-001)
    -- No pgvector column needed
    keywords JSONB,
    embedding_id VARCHAR(100),      -- Qdrant point ID
    
    -- Analytics
    usage_count INTEGER NOT NULL DEFAULT 0,
    helpful_count INTEGER NOT NULL DEFAULT 0,
    not_helpful_count INTEGER NOT NULL DEFAULT 0,
    cache_priority INTEGER DEFAULT 0,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE (wound_type, severity, sub_type)
);

-- Indexes for search
CREATE INDEX idx_firstaid_guides_wound ON firstaid_guides(wound_type, severity);
CREATE INDEX idx_firstaid_guides_active ON firstaid_guides(is_active, is_deleted);
CREATE INDEX idx_firstaid_guides_usage ON firstaid_guides(usage_count DESC);
CREATE INDEX idx_firstaid_guides_keywords ON firstaid_guides USING GIN (keywords);

-- Full-text search for titles
CREATE INDEX idx_firstaid_guides_title_search ON firstaid_guides USING GIN (to_tsvector('simple', title));

CREATE TABLE detections (
    detection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analyses(analysis_id) ON DELETE CASCADE,
    
    -- Classification reference
    classification_result_id UUID REFERENCES ai_results(result_id) ON DELETE SET NULL,
    
    -- Detection info
    detection_index INTEGER NOT NULL, -- 0=first wound, 1=second, etc.
    bounding_box JSONB NOT NULL,      -- {x, y, width, height, normalized}
    confidence FLOAT NOT NULL,        -- 0.0-1.0
    
    -- Detected class: skin_wound, phy_wound, normal_skin
    detected_class VARCHAR(50) NOT NULL,
    
    -- Detail results (denormalized)
    wound_type VARCHAR(50),
    severity VARCHAR(50),
    sub_type VARCHAR(50),
    detail_confidence FLOAT,
    
    -- Associated guide
    firstaidguide_id UUID REFERENCES firstaid_guides(firstaidguide_id) ON DELETE SET NULL,
    
    -- Snapshot of first-aid at detection time
    firstaid_snapshot JSONB,
    firstaid_snapshot_version INTEGER,
    
    -- Doctor validation
    is_validated BOOLEAN NOT NULL DEFAULT FALSE,
    validated_by UUID REFERENCES users(user_id),
    validated_at TIMESTAMP,
    validation_notes TEXT,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_detections_analysis ON detections(analysis_id, detection_index);
CREATE INDEX idx_detections_class ON detections(detected_class, created_at);
CREATE INDEX idx_detections_wound ON detections(wound_type, severity);
CREATE INDEX idx_detections_validation ON detections(is_validated, validated_at);

-- ============================================================
-- 7. CHATBOT (v2.1 - Separated Messages)
-- ============================================================

CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES analyses(analysis_id) ON DELETE SET NULL,
    
    -- Context
    system_prompt_version VARCHAR(20) DEFAULT 'v2',
    wound_context JSONB,            -- {wound_type, severity, detection_summary}
    user_mood VARCHAR(20),          -- anxious, calm, urgent - for tone adjustment
    
    -- Session management: active, closed, expired, escalated
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    closure_reason VARCHAR(100),    -- resolved, timeout, escalated_to_human
    
    -- Limits
    message_limit INTEGER NOT NULL DEFAULT 50,
    message_count INTEGER NOT NULL DEFAULT 0,
    
    -- Timeout: 24 hours for medical context
    last_message_at TIMESTAMP,
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours',
    
    -- Metadata
    total_tokens_used INTEGER NOT NULL DEFAULT 0,
    total_cost_usd FLOAT DEFAULT 0,
    llm_model VARCHAR(50),          -- gemini-2.0-flash
    language VARCHAR(10) DEFAULT 'vi',
    
    -- Quality
    user_rating INTEGER,            -- 1-5 stars
    user_feedback TEXT,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id, status);
CREATE INDEX idx_chat_sessions_analysis ON chat_sessions(analysis_id);
CREATE INDEX idx_chat_sessions_cleanup ON chat_sessions(status, expires_at);
CREATE INDEX idx_chat_sessions_active ON chat_sessions(status, last_message_at);

-- NEW: Separate messages table (no JSONB bloat)
CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    
    -- Message
    role VARCHAR(20) NOT NULL,      -- user, assistant, system
    content TEXT NOT NULL,
    
    -- Tokens
    tokens_used INTEGER NOT NULL DEFAULT 0,
    token_cost_usd FLOAT DEFAULT 0,
    
    -- Context
    model_used VARCHAR(50),
    temperature FLOAT DEFAULT 0.7,
    
    -- Citations (for RAG)
    sources JSONB,                  -- [{guide_id, url, excerpt}]
    
    -- Quality
    is_helpful BOOLEAN,             -- User feedback
    flagged BOOLEAN NOT NULL DEFAULT FALSE,  -- Inappropriate content
    flag_reason VARCHAR(255),
    
    -- Metadata
    processing_time_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for chat history
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX idx_chat_messages_role ON chat_messages(role, created_at);
CREATE INDEX idx_chat_messages_feedback ON chat_messages(is_helpful);
CREATE INDEX idx_chat_messages_flagged ON chat_messages(flagged);

-- Trigger to update session message_count
CREATE OR REPLACE FUNCTION update_chat_session_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_sessions 
    SET message_count = message_count + 1,
        last_message_at = NOW(),
        updated_at = NOW()
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_chat_message_insert
    AFTER INSERT ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_session_count();

-- ============================================================
-- 8. AI MODEL MANAGEMENT (v2.2.1 - FULLY ALIGNED WITH FASTAPI)
-- ============================================================

CREATE TABLE ai_models (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Model Identification
    model_type VARCHAR(50) NOT NULL,         -- e.g., 'detection', 'classification', 'segmentation'
    version_tag VARCHAR(50) NOT NULL,        -- e.g., 'v1.0.0'
    version_number INTEGER NOT NULL DEFAULT 1,
    
    -- File Storage
    file_path TEXT NOT NULL,
    file_size_bytes FLOAT,
    file_hash VARCHAR(64),                   -- SHA-256
    
    -- Model Metadata
    name VARCHAR(200),
    description TEXT,
    
    -- Performance Metrics
    metrics JSONB,                           -- {accuracy, precision, recall, confusion_matrix...}
    
    -- Status Flags
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    is_beta BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Traffic Split (for A/B testing or canary deployments)
    traffic_percentage INTEGER NOT NULL DEFAULT 0,
    
    -- Deployment Info
    deployed_at TIMESTAMP,
    deployed_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Activation Tracking (for rollback support)
    activated_at TIMESTAMP,
    previously_active_version_id UUID REFERENCES ai_models(model_id) ON DELETE SET NULL,
    
    -- Audit Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    
    UNIQUE (model_type, version_tag)
);

-- Indexes (Matching Python SQLModel fields)
CREATE INDEX ix_ai_models_type_active ON ai_models(model_type, is_active);
CREATE INDEX ix_ai_models_type_deleted ON ai_models(model_type, is_deleted);
CREATE INDEX ix_ai_models_created_at ON ai_models(created_at);
CREATE INDEX ix_ai_models_deployed_at ON ai_models(deployed_at);
CREATE INDEX ix_ai_models_activated_at ON ai_models(activated_at);
CREATE INDEX ix_ai_models_prev_active ON ai_models(previously_active_version_id);


-- NEW: Model Version History / Audit Tracking (Required by Python Backend)
CREATE TABLE model_version_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ai_models(model_id) ON DELETE CASCADE,
    
    -- Action Info (upload, activate, deactivate, rollback, delete, restore)
    action VARCHAR(50) NOT NULL,
    from_version VARCHAR(50),
    to_version VARCHAR(50),
    
    -- Actor Information
    actor_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    actor_ip VARCHAR(45),
    
    -- Details
    details JSONB,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_model_history_model_action ON model_version_history(model_id, action);
CREATE INDEX ix_model_history_created_at ON model_version_history(created_at);


-- Model performance tracking aggregated
CREATE TABLE model_performance (
    performance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ai_models(model_id) ON DELETE CASCADE,
    
    -- Date
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    hour INTEGER,  -- 0-23 for hourly metrics
    
    -- Metrics
    total_predictions INTEGER NOT NULL DEFAULT 0,
    avg_confidence FLOAT,
    avg_processing_time_ms FLOAT,
    error_count INTEGER NOT NULL DEFAULT 0,
    
    -- Accuracy (calculated daily)
    true_positives INTEGER DEFAULT 0,
    true_negatives INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    false_negatives INTEGER DEFAULT 0,
    
    -- Resources
    avg_gpu_memory_mb FLOAT,
    avg_cpu_percent FLOAT,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE (model_id, date, hour)
);

-- Indexes
CREATE INDEX idx_model_performance_model ON model_performance(model_id, date);
CREATE INDEX idx_model_performance_date ON model_performance(date, hour);

-- Trigger to aggregate daily metrics
CREATE OR REPLACE FUNCTION aggregate_model_performance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update daily aggregates
    INSERT INTO model_performance (model_id, date, total_predictions, avg_confidence, avg_processing_time_ms, error_count)
    VALUES (
        NEW.model_id,
        CURRENT_DATE,
        1,
        (SELECT AVG((results->>'confidence')::FLOAT) FROM ai_results WHERE model_id = NEW.model_id AND DATE(created_at) = CURRENT_DATE),
        NEW.processing_time_ms,
        0
    )
    ON CONFLICT (model_id, date, hour) DO UPDATE SET
        total_predictions = model_performance.total_predictions + 1,
        avg_confidence = (model_performance.avg_confidence * model_performance.total_predictions + 
                         (SELECT AVG((results->>'confidence')::FLOAT) FROM ai_results WHERE result_id = NEW.result_id)) 
                         / (model_performance.total_predictions + 1),
        avg_processing_time_ms = (model_performance.avg_processing_time_ms * model_performance.total_predictions + NEW.processing_time_ms) 
                                 / (model_performance.total_predictions + 1);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ai_result_performance
    AFTER INSERT ON ai_results
    FOR EACH ROW
    EXECUTE FUNCTION aggregate_model_performance();

-- ============================================================
-- 9. DEVICE SESSIONS (v2.1 - Enhanced Mobile)
-- ============================================================

CREATE TABLE device_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    device_id VARCHAR(100) NOT NULL,
    
    -- Device info
    platform VARCHAR(20) NOT NULL,      -- ios, android, web
    app_version VARCHAR(50),
    os_version VARCHAR(50),
    device_model VARCHAR(100),
    device_name VARCHAR(255),           -- "John's iPhone"
    
    -- Push notifications
    push_token TEXT,                    -- FCM or APNS token
    push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_notification_at TIMESTAMP,
    
    -- Offline cache
    cached_sources JSONB,               -- {model_ids[], guide_ids[], doc_ids[]}
    cache_size_mb FLOAT,
    cache_version VARCHAR(50),
    last_sync_at TIMESTAMP,
    
    -- Sync conflicts
    pending_syncs JSONB,                -- [{analysis_id, offline_data, conflict}]
    sync_status VARCHAR(20) DEFAULT 'synced',  -- synced, pending, conflicting
    
    -- Rate limiting
    rate_limit_remaining INTEGER DEFAULT 100,
    rate_limit_reset_at TIMESTAMP,
    
    -- Security
    is_trusted BOOLEAN NOT NULL DEFAULT FALSE,
    last_trusted_at TIMESTAMP,
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE (user_id, device_id)
);

-- Indexes for mobile queries
CREATE INDEX idx_device_sessions_user ON device_sessions(user_id, is_active);
CREATE INDEX idx_device_sessions_push ON device_sessions(push_enabled, is_active);
CREATE INDEX idx_device_sessions_sync ON device_sessions(user_id, last_sync_at);
CREATE INDEX idx_device_sessions_platform ON device_sessions(platform, app_version);
CREATE INDEX idx_device_sessions_rate_limit ON device_sessions(rate_limit_reset_at);

-- ============================================================
-- 10. NOTIFICATIONS (NEW - PBI-PUSH)
-- ============================================================

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    device_id VARCHAR(100),
    
    -- Content
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,  -- analysis_complete, reminder, system, chat_message
    
    -- Data
    data JSONB,                       -- {analysis_id, type, action_url}
    action_url TEXT,
    image_url TEXT,
    
    -- Delivery
    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, critical
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    
    -- Status: pending, scheduled, sent, delivered, failed
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    failure_reason VARCHAR(255),
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    
    -- Provider response
    provider VARCHAR(20),             -- fcm, apns, email
    provider_message_id VARCHAR(255),
    provider_response JSONB,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for notification queries
CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_status ON notifications(status, scheduled_at);
CREATE INDEX idx_notifications_type ON notifications(notification_type, created_at);
CREATE INDEX idx_notifications_unread ON notifications(user_id, read_at) WHERE read_at IS NULL;
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_at) WHERE status = 'scheduled';

-- ============================================================
-- 11. RATE LIMITING (NEW - PBI-RATE)
-- ============================================================

CREATE TABLE rate_limits (
    rate_limit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Key: user_id, device_id, ip_address, or endpoint
    key_type VARCHAR(20) NOT NULL,    -- user, device, ip, endpoint
    key_value VARCHAR(255) NOT NULL,
    endpoint VARCHAR(100),            -- /api/v2/analysis/upload
    
    -- Limits
    limit_value INTEGER NOT NULL,     -- Max requests
    window_seconds INTEGER NOT NULL,  -- Time window
    current_count INTEGER NOT NULL DEFAULT 0,
    
    -- Reset
    window_start_at TIMESTAMP NOT NULL DEFAULT NOW(),
    window_reset_at TIMESTAMP NOT NULL,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE (key_type, key_value, endpoint, window_reset_at)
);

-- Index for rate limit checks
CREATE INDEX idx_rate_limits_key ON rate_limits(key_type, key_value, endpoint);
CREATE INDEX idx_rate_limits_reset ON rate_limits(window_reset_at);

-- ============================================================
-- 12. KNOWLEDGE BASE ANALYTICS (NEW - PBI-ANALYTICS)
-- ============================================================

CREATE TABLE guide_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firstaidguide_id UUID NOT NULL REFERENCES firstaid_guides(firstaidguide_id) ON DELETE CASCADE,
    
    -- Date
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Usage
    view_count INTEGER NOT NULL DEFAULT 0,
    helpful_count INTEGER NOT NULL DEFAULT 0,
    not_helpful_count INTEGER NOT NULL DEFAULT 0,
    share_count INTEGER NOT NULL DEFAULT 0,
    
    -- User feedback
    avg_rating FLOAT,                 -- 1-5 stars
    feedback_count INTEGER NOT NULL DEFAULT 0,
    
    -- Source
    source_platform VARCHAR(20),      -- web, ios, android
    referrer VARCHAR(255),            -- google, facebook, direct
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE (firstaidguide_id, date, source_platform)
);

-- Indexes
CREATE INDEX idx_guide_analytics_guide ON guide_analytics(firstaidguide_id, date);
CREATE INDEX idx_guide_analytics_date ON guide_analytics(date);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default roles
INSERT INTO roles (role_name, description, is_system) VALUES
    ('user', 'Regular user - can analyze wounds and chat', TRUE),
    ('admin', 'Administrator - full system access', TRUE),
    ('doctor', 'Medical professional - can review and validate AI results', TRUE);

-- Default permissions
INSERT INTO permissions (permission_name, description, resource_type, action_type) VALUES
    ('analysis:create', 'Upload and analyze wound images', 'analysis', 'create'),
    ('analysis:read', 'View analysis results', 'analysis', 'read'),
    ('analysis:update', 'Update analysis metadata', 'analysis', 'update'),
    ('analysis:delete', 'Delete analysis records', 'analysis', 'delete'),
    ('chat:create', 'Start chatbot sessions', 'chat', 'create'),
    ('chat:read', 'View chat history', 'chat', 'read'),
    ('user:read', 'View user profiles', 'user', 'read'),
    ('user:update', 'Update own profile', 'user', 'update'),
    ('admin:users', 'Manage all users', 'admin', 'crud'),
    ('admin:models', 'Upload and manage AI models', 'admin', 'crud'),
    ('admin:dashboard', 'View admin dashboard', 'admin', 'read'),
    ('admin:knowledge', 'Manage first-aid knowledge base', 'admin', 'crud'),
    ('admin:audit', 'View audit logs', 'admin', 'read'),
    ('doctor:validate', 'Validate AI detections', 'doctor', 'update');

-- Assign permissions to roles
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r CROSS JOIN permissions p
WHERE r.role_name = 'admin';

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'user'
  AND p.permission_name IN (
    'analysis:create', 'analysis:read', 'analysis:update', 'analysis:delete',
    'chat:create', 'chat:read', 'user:read', 'user:update'
  );

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'doctor'
  AND p.permission_name IN (
    'analysis:read', 'chat:read', 'user:read', 'doctor:validate'
  );

-- ============================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================

-- Active analyses with user info
CREATE VIEW v_active_analyses AS
SELECT 
    a.analysis_id,
    COALESCE(u.email, g.session_id || ' (guest)') as user_email,
    a.status,
    a.wound_type,
    a.severity,
    a.started_at,
    a.processing_attempts
FROM analyses a
LEFT JOIN users u ON a.user_id = u.user_id
LEFT JOIN guest_sessions g ON a.guest_session_id = g.session_id
WHERE a.status IN ('queued', 'processing', 'analyzing');

-- Chat sessions with message count
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

-- Model performance dashboard (UPDATED for exact Python compatibility)
CREATE VIEW v_model_performance_dashboard AS
SELECT 
    m.model_id,
    m.name AS model_name,
    m.version_tag AS version,
    m.model_type AS stage,
    m.is_active,
    m.is_beta,
    m.traffic_percentage,
    m.is_deleted,
    mp.date,
    mp.total_predictions,
    mp.avg_confidence,
    mp.avg_processing_time_ms,
    mp.error_count,
    CASE 
        WHEN mp.total_predictions > 0 THEN 
            (mp.true_positives + mp.true_negatives)::FLOAT / mp.total_predictions
        ELSE 0 
    END as accuracy
FROM ai_models m
LEFT JOIN model_performance mp ON m.model_id = mp.model_id
WHERE mp.date >= CURRENT_DATE - INTERVAL '7 days'
AND m.is_deleted = FALSE
ORDER BY m.model_type, m.is_active DESC, mp.date DESC;

-- Unread notifications per user
CREATE VIEW v_unread_notifications AS
SELECT 
    user_id,
    COUNT(*) as unread_count,
    MAX(created_at) as latest_notification_at
FROM notifications
WHERE read_at IS NULL
GROUP BY user_id;

-- ============================================================
-- SUMMARY
-- ============================================================
-- Tables: 26 (HOTFIX: Added model_version_history, refactored ai_models)
--   Auth: users, user_profiles, verification_tokens, token_blacklist, token_families
--   RBAC: roles, permissions, user_roles, role_permissions
--   Guest: guest_sessions
--   Audit: audit_logs
--   Analysis: analyses, ai_results, user_inputs, detections
--   Knowledge: firstaid_guides, guide_analytics
--   Chatbot: chat_sessions, chat_messages
--   AI Model: ai_models, model_version_history, model_performance (REFACTORED for Python)
--   Device: device_sessions
--   Notifications: notifications
--   Rate Limiting: rate_limits
--   Backup: wound_analyses, wound_detections
--
-- Views: 4 (REFACTORED v_model_performance_dashboard for compatibility)
--   v_active_analyses, v_chat_sessions_summary, v_model_performance_dashboard, v_unread_notifications
--
-- Triggers: 3
--   trg_analyses_updated_at, trg_chat_message_insert, trg_ai_result_performance
