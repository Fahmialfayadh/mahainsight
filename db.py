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
                viz_url: str = None, viz_urls: list = None):
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
        "viz_urls": viz_urls  # JSON array for multiple visualizations
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

