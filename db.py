"""
Database module for Supabase connection and helper functions.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "mahainsight-files"

_supabase_client: Client = None


def get_supabase() -> Client:
    """Get or create Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


# ============== POST OPERATIONS ==============

def get_all_posts():
    """Get all posts ordered by creation date (newest first)."""
    supabase = get_supabase()
    response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
    return response.data


def get_post_by_slug(slug: str):
    """Get a single post by its slug."""
    supabase = get_supabase()
    response = supabase.table("posts").select("*").eq("slug", slug).single().execute()
    return response.data


def create_post(title: str, slug: str, content_md: str, source_link: str, 
                source_name: str, data_url: str = None, thumbnail_url: str = None,
                viz_url: str = None, viz_urls: list = None, petasight_link: str = None):
    """Create a new post.
    
    viz_urls should be a list of dicts: [{"url": "...", "title": "..."}, ...]
    """
    supabase = get_supabase()
    data = {
        "title": title,
        "slug": slug,
        "content_md": content_md,
        "source_link": source_link,
        "source_name": source_name,
        "data_url": data_url,
        "thumbnail_url": thumbnail_url,
        "viz_url": viz_url,
        "viz_urls": viz_urls,  # JSON array for multiple visualizations
        "petasight_link": petasight_link
    }
    response = supabase.table("posts").insert(data).execute()
    return response.data


def update_post(post_id: int, **kwargs):
    """Update an existing post by ID."""
    supabase = get_supabase()
    response = supabase.table("posts").update(kwargs).eq("id", post_id).execute()
    return response.data


def delete_post(post_id: int):
    """Delete a post by ID."""
    supabase = get_supabase()
    response = supabase.table("posts").delete().eq("id", post_id).execute()
    return response.data


# ============== STORAGE OPERATIONS ==============

def upload_file(file_data: bytes, filename: str, folder: str = "datasets") -> str:
    """
    Upload a file to Supabase Storage.
    
    Args:
        file_data: Binary content of the file
        filename: Name of the file
        folder: Folder in bucket (datasets, images, or visualizations)
    
    Returns:
        Public URL of the uploaded file
    """
    import uuid
    
    supabase = get_supabase()
    
    # Add unique prefix to prevent duplicate filename errors
    unique_id = uuid.uuid4().hex[:8]
    name_parts = filename.rsplit('.', 1)
    if len(name_parts) == 2:
        unique_filename = f"{name_parts[0]}_{unique_id}.{name_parts[1]}"
    else:
        unique_filename = f"{filename}_{unique_id}"
    
    file_path = f"{folder}/{unique_filename}"
    
    # Upload to storage
    supabase.storage.from_(BUCKET_NAME).upload(
        file_path,
        file_data,
        {"content-type": get_content_type(filename)}
    )
    
    # Get public URL
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
    return public_url


def delete_file(file_path: str):
    """Delete a file from Supabase Storage."""
    supabase = get_supabase()
    supabase.storage.from_(BUCKET_NAME).remove([file_path])


def get_content_type(filename: str) -> str:
    """Get MIME type based on file extension."""
    ext = filename.lower().split('.')[-1]
    content_types = {
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'html': 'text/html',  # For Plotly HTML visualizations
        'htm': 'text/html'
    }
    return content_types.get(ext, 'application/octet-stream')


# ============== USER OPERATIONS ==============

def create_user(email: str, password_hash: str, full_name: str = None, is_admin: bool = False):
    """Create a new user in users_insight table."""
    supabase = get_supabase()
    data = {
        "email": email,
        "password_hash": password_hash,
        "full_name": full_name,
        "is_admin": is_admin
    }
    response = supabase.table("users_insight").insert(data).execute()
    return response.data


def get_user_by_email(email: str):
    """Get user by email from users_insight table."""
    supabase = get_supabase()
    response = supabase.table("users_insight").select("*").eq("email", email).single().execute()
    return response.data


def get_user_by_id(user_id: int):
    """Get user by ID from users_insight table."""
    supabase = get_supabase()
    response = supabase.table("users_insight").select("*").eq("id", user_id).single().execute()
    return response.data


def get_all_users():
    """Get all users ordered by ID."""
    supabase = get_supabase()
    response = supabase.table("users_insight").select("*").order("id").execute()
    return response.data


def update_user_profile(user_id: int, full_name: str, email: str):
    """
    Update user's full name and email.
    """
    supabase = get_supabase()
    data = {
        "full_name": full_name,
        "email": email
    }
    response = supabase.table("users_insight").update(data).eq("id", user_id).execute()
    return response.data


def set_admin_status(user_id: int, is_admin: bool):
    """Update admin status for a user."""
    supabase = get_supabase()
    response = supabase.table("users_insight").update({"is_admin": is_admin}).eq("id", user_id).execute()
    return response.data


# ============== AI USAGE OPERATIONS ==============

def get_user_ai_usage(user_id: int, post_id: int):
    """
    Get current usage count for a user on a specific post within the last 24 hours.
    Resets count if 24 hours have passed.
    """
    supabase = get_supabase()
    
    # Check for existing record
    try:
        response = supabase.table("user_ai_usage").select("*").eq("user_id", user_id).eq("post_id", post_id).single().execute()
        record = response.data
        
        if record:
            from datetime import datetime, timezone, timedelta
            
            # Parse last_used_at (Supabase returns ISO string)
            last_used = datetimefromisoformat(record["last_used_at"].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            # If more than 24 hours, reset usage
            if now - last_used > timedelta(hours=24):
                supabase.table("user_ai_usage").update({
                    "usage_count": 0,
                    "last_used_at": now.isoformat()
                }).eq("id", record["id"]).execute()
                return 0
            
            return record["usage_count"]
            
        return 0
        
    except Exception:
        # likely no record found
        return 0


def increment_user_ai_usage(user_id: int, post_id: int):
    """
    Increment usage count for a user on a post.
    Creates record if not exists.
    """
    supabase = get_supabase()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    
    try:
        # Check if exists
        response = supabase.table("user_ai_usage").select("*").eq("user_id", user_id).eq("post_id", post_id).single().execute()
        record = response.data
        
        if record:
            # Update existing
            new_count = record["usage_count"] + 1
            supabase.table("user_ai_usage").update({
                "usage_count": new_count,
                "last_used_at": now
            }).eq("id", record["id"]).execute()
        else:
            # Create new
            supabase.table("user_ai_usage").insert({
                "user_id": user_id,
                "post_id": post_id,
                "usage_count": 1,
                "last_used_at": now
            }).execute()
            
    except Exception:
        # Handle case where record doesn't exist but select failed (should be caught above, but safety fallback)
        supabase.table("user_ai_usage").insert({
            "user_id": user_id,
            "post_id": post_id,
            "usage_count": 1,
            "last_used_at": now
        }).execute()

def datetimefromisoformat(iso_str):
    """Helper for older python versions if needed, though 3.10+ has generic fromisoformat"""
    from datetime import datetime
    try:
        return datetime.fromisoformat(iso_str)
    except:
        # Fallback for simple TZ handling if fromisoformat is strict
        return datetime.strptime(iso_str.split('.')[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


# ============== REFRESH TOKEN OPERATIONS ==============

def create_refresh_token(user_id: int, token_hash: str, expires_at, device_info: str = None):
    """
    Store a refresh token in the database.
    
    Args:
        user_id: User ID
        token_hash: SHA-256 hash of the refresh token
        expires_at: Expiration datetime
        device_info: Optional device/browser info
        
    Returns:
        Created token record
    """
    supabase = get_supabase()
    data = {
        "user_id": user_id,
        "token_hash": token_hash,
        "expires_at": expires_at.isoformat() if hasattr(expires_at, 'isoformat') else expires_at,
        "revoked": False,
        "device_info": device_info
    }
    response = supabase.table("refresh_tokens").insert(data).execute()
    return response.data


def get_refresh_token(token_hash: str):
    """
    Get refresh token record by hash.
    
    Args:
        token_hash: SHA-256 hash of the token
        
    Returns:
        Token record or None
    """
    supabase = get_supabase()
    try:
        response = supabase.table("refresh_tokens").select("*").eq("token_hash", token_hash).eq("revoked", False).single().execute()
        return response.data
    except:
        return None


def revoke_refresh_token(token_hash: str):
    """
    Revoke a refresh token.
    
    Args:
        token_hash: SHA-256 hash of the token
    """
    supabase = get_supabase()
    supabase.table("refresh_tokens").update({"revoked": True}).eq("token_hash", token_hash).execute()


def revoke_all_user_tokens(user_id: int):
    """
    Revoke all refresh tokens for a user (logout all devices).
    
    Args:
        user_id: User ID
    """
    supabase = get_supabase()
    supabase.table("refresh_tokens").update({"revoked": True}).eq("user_id", user_id).execute()


def cleanup_expired_tokens():
    """
    Delete expired and revoked refresh tokens.
    Should be called periodically (e.g., daily cron job).
    """
    from datetime import datetime, timezone
    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    
    # Delete tokens that are expired or revoked
    supabase.table("refresh_tokens").delete().lt("expires_at", now).execute()
    supabase.table("refresh_tokens").delete().eq("revoked", True).execute()


# ============== OAUTH USER OPERATIONS ==============

def update_user_oauth(user_id: int, google_id: str, profile_data: dict):
    """
    Update user with Google OAuth information.
    
    Args:
        user_id: User ID
        google_id: Google user ID
        profile_data: Google profile dictionary
    """
    supabase = get_supabase()
    data = {
        "google_id": google_id,
        "oauth_provider": "google",
        "profile_picture": profile_data.get("picture"),
    }
    response = supabase.table("users_insight").update(data).eq("id", user_id).execute()
    return response.data


def get_user_by_google_id(google_id: str):
    """
    Get user by Google ID.
    
    Args:
        google_id: Google user ID
        
    Returns:
        User record or None
    """
    supabase = get_supabase()
    try:
        response = supabase.table("users_insight").select("*").eq("google_id", google_id).single().execute()
        return response.data
    except:
        return None

