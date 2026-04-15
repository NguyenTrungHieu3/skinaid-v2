-- Add budget settings table for LLM cost management
-- Run with: & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d skinaid_db_v2 -f add_llm_budget.sql

CREATE TABLE IF NOT EXISTS llm_budget_settings (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monthly_budget_usd          FLOAT NOT NULL DEFAULT 0,
    price_per_1k_input_tokens   FLOAT NOT NULL DEFAULT 0.40,
    price_per_1k_output_tokens  FLOAT NOT NULL DEFAULT 1.60,
    currency                    VARCHAR(10) NOT NULL DEFAULT 'USD',
    updated_by                  UUID REFERENCES users(user_id) ON DELETE SET NULL,
    updated_at                  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Seed singleton row
INSERT INTO llm_budget_settings (monthly_budget_usd, price_per_1k_input_tokens, price_per_1k_output_tokens)
VALUES (10.0, 0.40, 1.60)
ON CONFLICT DO NOTHING;
