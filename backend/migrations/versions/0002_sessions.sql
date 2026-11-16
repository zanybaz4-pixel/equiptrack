CREATE TABLE auth_sessions (
    token_hash varchar(64) PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    expires_at timestamptz NOT NULL
);
CREATE INDEX auth_sessions_expiry_idx ON auth_sessions(expires_at);
CREATE INDEX auth_sessions_user_idx ON auth_sessions(user_id);

DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'equiptrack_app') THEN
        GRANT SELECT, INSERT, UPDATE ON users TO equiptrack_app;
        GRANT SELECT, INSERT, DELETE ON auth_sessions TO equiptrack_app;
        GRANT INSERT, UPDATE ON equipment_categories, equipment_items TO equiptrack_app;
        GRANT INSERT, UPDATE ON borrowing_requests, loan_records TO equiptrack_app;
        GRANT SELECT, INSERT ON audit_logs TO equiptrack_app;
    END IF;
END $$;
