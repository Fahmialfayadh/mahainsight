"""
Database Migration Script for JWT Authentication
Creates refresh_tokens table and updates users_insight table with OAuth fields.
"""
from db import get_supabase

def run_migration():
    """Run database migration for JWT authentication."""
    supabase = get_supabase()
    
    print("Starting database migration...")
    
    # SQL for creating refresh_tokens table
    create_refresh_tokens_sql = """
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
    """
    
    # SQL for updating users_insight table
    update_users_sql = """
    ALTER TABLE users_insight 
    ADD COLUMN IF NOT EXISTS google_id TEXT UNIQUE,
    ADD COLUMN IF NOT EXISTS oauth_provider TEXT,
    ADD COLUMN IF NOT EXISTS profile_picture TEXT,
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;
    
    CREATE INDEX IF NOT EXISTS idx_users_google_id ON users_insight(google_id);
    """
    
    try:
        # Execute migrations using Supabase RPC or direct SQL
        # Note: Supabase Python client doesn't directly support DDL
        # You'll need to run these SQL commands in Supabase SQL Editor
        
        print("\n" + "="*60)
        print("MIGRATION SQL - Run this in Supabase SQL Editor:")
        print("="*60)
        print("\n-- Create refresh_tokens table:")
        print(create_refresh_tokens_sql)
        print("\n-- Update users_insight table:")
        print(update_users_sql)
        print("="*60)
        print("\nPlease run the above SQL in your Supabase dashboard.")
        print("Go to: https://app.supabase.com → Your Project → SQL Editor")
        print("="*60)
        
    except Exception as e:
        print(f"Migration error: {e}")
        print("Please run the SQL commands manually in Supabase SQL Editor.")

if __name__ == "__main__":
    run_migration()
