import sys
sys.path.insert(0, '/home/data/kuliah/project/mahainsight')

# Test if we can create tokens
from auth.jwt_utils import generate_access_token, generate_refresh_token

print("Testing JWT token generation...")
try:
    access_token = generate_access_token(1, "test@gmail.com", False)
    print(f"✅ Access token: {access_token[:50]}...")
    
    refresh_token, hash = generate_refresh_token(1)
    print(f"✅ Refresh token: {refresh_token[:50]}...")
    print(f"✅ Token hash: {hash[:50]}...")
    print("\n✅ JWT tokens work!")
except Exception as e:
    print(f"❌ Error: {e}")

# Test database connection
print("\nTesting database...")
try:
    from db import get_supabase
    supabase = get_supabase()
    print("✅ Database connection OK")
    
    # Test refresh_tokens table exists
    result = supabase.table("refresh_tokens").select("*").limit(1).execute()
    print(f"✅ refresh_tokens table exists (rows: {len(result.data)})")
except Exception as e:
    print(f"❌ Database error: {e}")
