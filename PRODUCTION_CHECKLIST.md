# ✅ Production Deployment Checklist

## 1️⃣ Update Environment Variables (.env di Server)

```bash
# Set ke production
FLASK_ENV=production

# Update Google OAuth redirect URI
GOOGLE_REDIRECT_URI=https://insight.mahalabs.space/api/auth/google/callback
```

## 2️⃣ Update Google Cloud Console

1. Go to: https://console.cloud.google.com
2. Select project → APIs & Services → Credentials
3. Click your OAuth Client ID
4. Under **Authorized redirect URIs**, add:
   ```
   https://insight.mahalabs.space/api/auth/google/callback
   ```
5. Click **Save**

## 3️⃣ Run Database Migration (Supabase)

Go to Supabase SQL Editor and run:

```sql
-- Create refresh_tokens table
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

-- Update users_insight table
ALTER TABLE users_insight 
ADD COLUMN IF NOT EXISTS google_id TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS oauth_provider TEXT,
ADD COLUMN IF NOT EXISTS profile_picture TEXT,
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_users_google_id ON users_insight(google_id);
```

## 4️⃣ Verify Production Config

✅ **SameSite Cookies:**
- Development (localhost): `Lax` (works without HTTPS)
- Production (HTTPS): `None` (for cross-site)
- ✅ Otomatis detect berdasarkan `FLASK_ENV`

✅ **Secure Cookies:**
- Development: `False`
- Production: `True` (HTTPS required)
- ✅ Otomatis detect berdasarkan `FLASK_ENV`

✅ **Token Expiry:**
- Access token: 15 minutes
- Refresh token: 30 days
- ✅ Token rotation: Active

## 5️⃣ Deploy Commands

```bash
# Push to repo
git add .
git commit -m "Production ready with Google OAuth"
git push origin main

# Deploy ke hosting (Railway/Vercel/etc)
# Follow hosting platform instructions
```

## 6️⃣ Post-Deployment Tests

### Test 1: Email Login
- ✅ Go to https://insight.mahalabs.space/login
- ✅ Login with email/password
- ✅ Should see name in navbar

### Test 2: Google OAuth
- ✅ Click "Masuk dengan Google"
- ✅ Complete Google login
- ✅ Should redirect to homepage logged in
- ✅ Name should appear in navbar

### Test 3: Cookie Security
- ✅ Open DevTools → Application → Cookies
- ✅ Check `access_token`: HttpOnly=true, Secure=true, SameSite=None
- ✅ Check `refresh_token`: HttpOnly=true, Secure=true, SameSite=None

### Test 4: Auto Refresh
- ✅ Stay logged in 14+ minutes
- ✅ Navigate to another page
- ✅ Should still be logged in

## ✅ READY TO DEPLOY!

Production URL: https://insight.mahalabs.space
