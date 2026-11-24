CREATE TABLE password_reset_tokens (
    token_hash varchar(64) PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    CONSTRAINT password_reset_expiry CHECK (expires_at > created_at)
);
CREATE INDEX password_reset_user_idx ON password_reset_tokens(user_id);
CREATE INDEX password_reset_expiry_idx ON password_reset_tokens(expires_at);

CREATE TABLE password_reset_limits (
    email_hash varchar(64) PRIMARY KEY,
    window_started_at timestamptz NOT NULL,
    last_requested_at timestamptz NOT NULL,
    attempts integer NOT NULL CHECK (attempts BETWEEN 1 AND 5)
);
CREATE INDEX password_reset_limits_age_idx ON password_reset_limits(last_requested_at);

DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'equiptrack_app') THEN
        GRANT SELECT, INSERT, DELETE ON password_reset_tokens TO equiptrack_app;
        GRANT SELECT, INSERT, UPDATE, DELETE ON password_reset_limits TO equiptrack_app;
    END IF;
END $$;
