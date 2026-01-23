-- Run this SQL in Supabase SQL Editor
-- https://app.supabase.com → Your Project → SQL Editor

-- 1. Create refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_insight(id) ON DELETE CASCADE,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked BOOLEAN DEFAULT FALSE,
    device_info TEXT
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);

-- 2. Update users_insight table with OAuth fields
ALTER TABLE users_insight 
ADD COLUMN IF NOT EXISTS google_id TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS oauth_provider TEXT,
ADD COLUMN IF NOT EXISTS profile_picture TEXT,
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_users_google_id ON users_insight(google_id);

-- 3. Verify tables exist
SELECT 'refresh_tokens table created' as status 
FROM information_schema.tables 
WHERE table_name = 'refresh_tokens';

SELECT 'users_insight updated' as status 
FROM information_schema.columns 
WHERE table_name = 'users_insight' AND column_name = 'google_id';
