-- Migration: Create admin_audit_logs table
-- Description: Track all admin actions (Create/Update/Delete) for compliance and security
-- Author: Senior Backend Developer
-- Date: 2025-11-21

-- Create admin_audit_logs table
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    -- Primary key
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Who performed the action
    admin_user_id UUID NOT NULL,
    admin_email VARCHAR(255) NOT NULL,
    admin_role VARCHAR(50) NOT NULL,
    
    -- What action was performed
    action VARCHAR(100) NOT NULL,  -- e.g., 'CREATE_USER', 'UPDATE_USER', 'DELETE_USER', 'UPDATE_GUIDE'
    resource_type VARCHAR(100) NOT NULL,  -- e.g., 'user', 'first_aid_guide', 'audit_log'
    resource_id VARCHAR(255),  -- ID of the affected resource
    
    -- Action details
    description TEXT,  -- Human-readable description of what happened
    changes JSONB,  -- Structured data showing what changed (before/after)
    metadata JSONB,  -- Additional context (IP address, user agent, etc.)
    
    -- HTTP request details
    http_method VARCHAR(10),  -- GET, POST, PUT, DELETE, PATCH
    endpoint VARCHAR(500),  -- API endpoint that was called
    ip_address INET,  -- Client IP address
    user_agent TEXT,  -- Client user agent
    
    -- Status and timing
    status VARCHAR(50) NOT NULL DEFAULT 'success',  -- 'success', 'failed', 'partial'
    error_message TEXT,  -- Error message if status is 'failed'
    duration_ms INTEGER,  -- How long the operation took in milliseconds
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Indexes for efficient querying
    CONSTRAINT fk_admin_user FOREIGN KEY (admin_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Create indexes for common query patterns
CREATE INDEX idx_admin_audit_logs_admin_user ON admin_audit_logs(admin_user_id);
CREATE INDEX idx_admin_audit_logs_action ON admin_audit_logs(action);
CREATE INDEX idx_admin_audit_logs_resource ON admin_audit_logs(resource_type, resource_id);
CREATE INDEX idx_admin_audit_logs_created_at ON admin_audit_logs(created_at DESC);
CREATE INDEX idx_admin_audit_logs_status ON admin_audit_logs(status);
CREATE INDEX idx_admin_audit_logs_ip ON admin_audit_logs(ip_address);

-- Create composite index for common filter combinations
CREATE INDEX idx_admin_audit_logs_filter ON admin_audit_logs(admin_user_id, action, created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE admin_audit_logs IS 'Audit trail for all admin actions in the system';
COMMENT ON COLUMN admin_audit_logs.log_id IS 'Unique identifier for the audit log entry';
COMMENT ON COLUMN admin_audit_logs.admin_user_id IS 'ID of the admin who performed the action';
COMMENT ON COLUMN admin_audit_logs.action IS 'Type of action performed (CREATE_USER, UPDATE_USER, etc.)';
COMMENT ON COLUMN admin_audit_logs.resource_type IS 'Type of resource affected (user, guide, etc.)';
COMMENT ON COLUMN admin_audit_logs.changes IS 'JSONB containing before/after state of changed fields';
COMMENT ON COLUMN admin_audit_logs.metadata IS 'Additional context like IP, user agent, request ID, etc.';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT ON admin_audit_logs TO application_user;
-- GRANT SELECT ON admin_audit_logs TO read_only_user;

-- Sample query to view recent admin actions
-- SELECT 
--     log_id,
--     admin_email,
--     action,
--     resource_type,
--     resource_id,
--     description,
--     created_at
-- FROM admin_audit_logs
-- ORDER BY created_at DESC
-- LIMIT 100;

-- Sample query to view actions by specific admin
-- SELECT 
--     action,
--     resource_type,
--     description,
--     created_at
-- FROM admin_audit_logs
-- WHERE admin_user_id = 'your-admin-uuid-here'
-- ORDER BY created_at DESC;

-- Sample query to view all changes to a specific resource
-- SELECT 
--     admin_email,
--     action,
--     changes,
--     created_at
-- FROM admin_audit_logs
-- WHERE resource_type = 'user' AND resource_id = 'your-user-uuid-here'
-- ORDER BY created_at DESC;
