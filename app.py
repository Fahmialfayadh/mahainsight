"""
MahaInsight - Data Analyst Portfolio
Flask application for publishing data analysis insights.
"""
import os
import re
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
import markdown2

from db import (
    get_all_posts, get_post_by_slug, create_post, 
    update_post, delete_post, upload_file
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default-secret-key")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")


# ============== HELPERS ==============

def login_required(f):
    """Decorator to require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def render_markdown(content: str) -> str:
    """Convert Markdown to HTML."""
    return markdown2.markdown(content, extras=[
        "fenced-code-blocks", 
        "tables", 
        "strike",
        "break-on-newline"  # Convert single newlines to <br>
    ])


def strip_markdown(text: str) -> str:
    """Remove markdown syntax for plain text preview."""
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    # Remove links but keep text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[.*?\]\(.+?\)', '', text)
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # Remove list markers
    text = re.sub(r'^[\-\*\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    # Clean up whitespace
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ============== PUBLIC ROUTES ==============

@app.route("/")
def index():
    """Homepage - List all articles."""
    posts = get_all_posts()
    # Add plain text preview for each post
    for post in posts:
        post["preview"] = strip_markdown(post.get("content_md", ""))[:150]
    return render_template("index.html", posts=posts)


@app.route("/post/<slug>")
def detail(slug):
    """Article detail page."""
    post = get_post_by_slug(slug)
    if not post:
        flash("Artikel tidak ditemukan.", "error")
        return redirect(url_for("index"))
    
    # Render markdown content to HTML
    post["content_html"] = render_markdown(post["content_md"])
    return render_template("detail.html", post=post)


# ============== AUTH ROUTES ==============

@app.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page."""
    if session.get("logged_in"):
        return redirect(url_for("admin"))
    
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASS:
            session["logged_in"] = True
            flash("Login berhasil!", "success")
            return redirect(url_for("admin"))
        else:
            flash("Password salah!", "error")
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout and clear session."""
    session.clear()
    flash("Anda telah logout.", "info")
    return redirect(url_for("index"))


# ============== ADMIN ROUTES ==============

@app.route("/admin")
@login_required
def admin():
    """Admin dashboard - List all posts for management."""
    posts = get_all_posts()
    return render_template("admin.html", posts=posts)


@app.route("/admin/create", methods=["GET", "POST"])
@login_required
def admin_create():
    """Create new post."""
    if request.method == "POST":
        title = request.form.get("title")
        slug = request.form.get("slug") or slugify(title)
        content_md = request.form.get("content_md")
        source_name = request.form.get("source_name")
        source_link = request.form.get("source_link")
        
        data_url = None
        thumbnail_url = None
        
        # Handle file uploads
        if "data_file" in request.files:
            data_file = request.files["data_file"]
            if data_file.filename:
                data_url = upload_file(
                    data_file.read(), 
                    data_file.filename, 
                    folder="datasets"
                )
        
        if "thumbnail_file" in request.files:
            thumb_file = request.files["thumbnail_file"]
            if thumb_file.filename:
                thumbnail_url = upload_file(
                    thumb_file.read(), 
                    thumb_file.filename, 
                    folder="images"
                )
        
        try:
            create_post(
                title=title,
                slug=slug,
                content_md=content_md,
                source_name=source_name,
                source_link=source_link,
                data_url=data_url,
                thumbnail_url=thumbnail_url
            )
            flash("Artikel berhasil dibuat!", "success")
            return redirect(url_for("admin"))
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
    
    return render_template("admin_create.html")


@app.route("/admin/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def admin_edit(post_id):
    """Edit existing post."""
    posts = get_all_posts()
    post = next((p for p in posts if p["id"] == post_id), None)
    
    if not post:
        flash("Artikel tidak ditemukan.", "error")
        return redirect(url_for("admin"))
    
    if request.method == "POST":
        updates = {
            "title": request.form.get("title"),
            "slug": request.form.get("slug"),
            "content_md": request.form.get("content_md"),
            "source_name": request.form.get("source_name"),
            "source_link": request.form.get("source_link"),
        }
        
        # Handle file uploads (only if new files provided)
        if "data_file" in request.files:
            data_file = request.files["data_file"]
            if data_file.filename:
                updates["data_url"] = upload_file(
                    data_file.read(), 
                    data_file.filename, 
                    folder="datasets"
                )
        
        if "thumbnail_file" in request.files:
            thumb_file = request.files["thumbnail_file"]
            if thumb_file.filename:
                updates["thumbnail_url"] = upload_file(
                    thumb_file.read(), 
                    thumb_file.filename, 
                    folder="images"
                )
        
        try:
            update_post(post_id, **updates)
            flash("Artikel berhasil diupdate!", "success")
            return redirect(url_for("admin"))
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
    
    return render_template("admin_edit.html", post=post)


@app.route("/admin/delete/<int:post_id>", methods=["POST"])
@login_required
def admin_delete(post_id):
    """Delete a post."""
    try:
        delete_post(post_id)
        flash("Artikel berhasil dihapus!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    return redirect(url_for("admin"))


# ============== RUN ==============

if __name__ == "__main__":
    app.run(debug=True)
