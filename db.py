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
                source_name: str, data_url: str = None, thumbnail_url: str = None):
    """Create a new post."""
    supabase = get_supabase()
    data = {
        "title": title,
        "slug": slug,
        "content_md": content_md,
        "source_link": source_link,
        "source_name": source_name,
        "data_url": data_url,
        "thumbnail_url": thumbnail_url
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
        folder: Folder in bucket (datasets or images)
    
    Returns:
        Public URL of the uploaded file
    """
    supabase = get_supabase()
    file_path = f"{folder}/{filename}"
    
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
        'webp': 'image/webp'
    }
    return content_types.get(ext, 'application/octet-stream')
