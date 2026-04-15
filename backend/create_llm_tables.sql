-- Create LLM management tables for skinaid_db_v2
-- Run with: & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d skinaid_db_v2 -f create_llm_tables.sql

CREATE TABLE IF NOT EXISTS llm_configurations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key          VARCHAR(50) NOT NULL UNIQUE,
    display_name        VARCHAR(100) NOT NULL,
    description         TEXT,
    model_name          VARCHAR(100) NOT NULL,
    temperature         FLOAT NOT NULL DEFAULT 0.3 CHECK (temperature >= 0.0 AND temperature <= 2.0),
    max_tokens          INTEGER NOT NULL DEFAULT 2000 CHECK (max_tokens >= 100 AND max_tokens <= 16000),
    top_k               INTEGER NOT NULL DEFAULT 5 CHECK (top_k >= 1 AND top_k <= 20),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_maintenance      BOOLEAN NOT NULL DEFAULT FALSE,
    maintenance_message TEXT,
    updated_by          UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_configurations_key ON llm_configurations(config_key);
CREATE INDEX IF NOT EXISTS idx_llm_configurations_active ON llm_configurations(is_active);

DROP TRIGGER IF EXISTS trg_llm_configurations_updated_at ON llm_configurations;
CREATE TRIGGER trg_llm_configurations_updated_at
    BEFORE UPDATE ON llm_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS llm_config_change_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id       UUID NOT NULL REFERENCES llm_configurations(id) ON DELETE CASCADE,
    changed_by      UUID REFERENCES users(user_id) ON DELETE SET NULL,
    change_type     VARCHAR(30) NOT NULL,
    old_values      JSONB,
    new_values      JSONB,
    reason          TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_change_logs_config ON llm_config_change_logs(config_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_change_logs_type ON llm_config_change_logs(change_type);
CREATE INDEX IF NOT EXISTS idx_llm_change_logs_user ON llm_config_change_logs(changed_by);

CREATE TABLE IF NOT EXISTS llm_usage_stats (
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

CREATE INDEX IF NOT EXISTS idx_llm_usage_stats_config ON llm_usage_stats(config_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_stats_model ON llm_usage_stats(model_name, created_at);
CREATE INDEX IF NOT EXISTS idx_llm_usage_stats_success ON llm_usage_stats(success, created_at);

-- Seed default configurations
INSERT INTO llm_configurations (config_key, display_name, description, model_name, temperature, max_tokens, top_k, is_active) VALUES
    ('synthesis', 'Tổng hợp sơ cứu (B5)', 'LLM dùng để tổng hợp hướng dẫn sơ cứu từ kết quả AI + RAG + DB.', 'gpt-4.1-mini', 0.3, 2000, 5, TRUE),
    ('chatbot_advisor', 'Chatbot Vết thương', 'LLM dùng cho Wound Advisor chatbot — tư vấn chuyên sâu về vết thương.', 'gpt-4.1-mini', 0.3, 1000, 3, TRUE),
    ('chatbot_guide', 'Chatbot Hướng dẫn App', 'LLM dùng cho App Guide chatbot — hướng dẫn người dùng sử dụng app.', 'gpt-4.1-mini', 0.7, 500, 3, TRUE)
ON CONFLICT (config_key) DO NOTHING;

-- Add permission
INSERT INTO permissions (permission_name, description, resource_type, action_type) VALUES
    ('admin:llm', 'Manage LLM configurations', 'admin', 'crud')
ON CONFLICT (permission_name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'admin' AND p.permission_name = 'admin:llm'
ON CONFLICT DO NOTHING;
