"""
MahaInsight - Data Analyst Portfolio
Flask application for publishing data analysis insights.
"""
import os
import re
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from dotenv import load_dotenv
import markdown2
import pandas as pd
import plotly.express as px
import plotly.io as pio
import requests
from io import StringIO
import json

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


@app.route("/viz-proxy")
def viz_proxy():
    """
    Proxy endpoint to serve Plotly HTML files with correct headers.
    Optimized with caching for better performance.
    """
    from flask import Response
    import hashlib
    
    viz_url = request.args.get("url")
    if not viz_url:
        return "URL parameter required", 400
    
    try:
        # Fetch HTML from Supabase
        response = requests.get(viz_url, timeout=30)
        response.raise_for_status()
        
        content = response.content
        
        # Generate ETag for caching
        etag = hashlib.md5(content).hexdigest()
        
        # Check if client has cached version
        if request.headers.get('If-None-Match') == etag:
            return Response(status=304)
        
        # Serve with aggressive caching headers
        return Response(
            content,
            mimetype='text/html',
            headers={
                'Content-Type': 'text/html; charset=utf-8',
                'X-Frame-Options': 'SAMEORIGIN',
                'Cache-Control': 'public, max-age=86400, immutable',  # 24 hours
                'ETag': etag,
                'Vary': 'Accept-Encoding'
            }
        )
    except requests.RequestException as e:
        return f"Error fetching visualization: {str(e)}", 500


@app.route("/api/plotly-chart")
def plotly_chart():
    """
    Generate Plotly chart from CSV data URL.
    Supports multiple chart types with auto-detection.
    
    Query params:
    - url: CSV file URL
    - chart_type: 'auto', 'map', 'bar', 'line', 'scatter', 'pie' (default: 'auto')
    - x: column name for x-axis (optional)
    - y: column name for y-axis (optional)
    - color: column name for color (optional)
    """
    data_url = request.args.get("url")
    chart_type = request.args.get("chart_type", "auto")
    x_col = request.args.get("x")
    y_col = request.args.get("y")
    color_col = request.args.get("color")
    
    if not data_url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    try:
        # Fetch CSV data
        response = requests.get(data_url, timeout=10)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        
        if df.empty:
            return jsonify({"error": "Dataset is empty"}), 400
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Auto-detect chart type based on columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        text_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Country detection for choropleth maps
        country_keywords = ['country', 'negara', 'nation', 'state', 'province', 'region', 
                           'country_code', 'iso_code', 'iso', 'location', 'lokasi']
        country_col = None
        for col in text_cols:
            if any(kw in col.lower() for kw in country_keywords):
                country_col = col
                break
        
        # If auto, detect best chart type
        if chart_type == "auto":
            if country_col and len(numeric_cols) > 0:
                chart_type = "map"
            elif len(numeric_cols) >= 2:
                chart_type = "scatter"
            elif len(numeric_cols) >= 1 and len(text_cols) >= 1:
                chart_type = "bar"
            else:
                chart_type = "table"
        
        # Generate chart based on type
        fig = None
        
        if chart_type == "map" and country_col:
            # Choropleth world map
            value_col = y_col or (numeric_cols[0] if numeric_cols else None)
            if value_col:
                fig = px.choropleth(
                    df,
                    locations=country_col,
                    locationmode="country names",
                    color=value_col,
                    hover_name=country_col,
                    color_continuous_scale="Viridis",
                    title=f"World Map: {value_col} by {country_col}"
                )
                fig.update_layout(
                    geo=dict(
                        showframe=False,
                        showcoastlines=True,
                        projection_type='equirectangular'
                    )
                )
        
        elif chart_type == "scatter":
            x = x_col or (numeric_cols[0] if len(numeric_cols) > 0 else None)
            y = y_col or (numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0])
            color = color_col or (text_cols[0] if text_cols else None)
            
            if x and y:
                fig = px.scatter(
                    df, x=x, y=y, color=color,
                    title=f"Scatter: {y} vs {x}",
                    hover_data=df.columns[:5].tolist()
                )
        
        elif chart_type == "line":
            x = x_col or (df.columns[0] if len(df.columns) > 0 else None)
            y = y_col or (numeric_cols[0] if numeric_cols else None)
            
            if x and y:
                fig = px.line(
                    df, x=x, y=y,
                    title=f"Line: {y} over {x}"
                )
        
        elif chart_type == "bar":
            x = x_col or (text_cols[0] if text_cols else df.columns[0])
            y = y_col or (numeric_cols[0] if numeric_cols else None)
            
            if x and y:
                # Limit to top 20 for readability
                df_plot = df.nlargest(20, y) if len(df) > 20 else df
                fig = px.bar(
                    df_plot, x=x, y=y, color=color_col,
                    title=f"Bar Chart: {y} by {x}"
                )
        
        elif chart_type == "pie":
            names = x_col or (text_cols[0] if text_cols else None)
            values = y_col or (numeric_cols[0] if numeric_cols else None)
            
            if names and values:
                # Limit to top 10 for pie chart
                df_plot = df.nlargest(10, values) if len(df) > 10 else df
                fig = px.pie(
                    df_plot, names=names, values=values,
                    title=f"Distribution: {values} by {names}"
                )
        
        if fig is None:
            # Fallback: show data summary
            return jsonify({
                "error": "Could not generate chart",
                "columns": df.columns.tolist(),
                "numeric_columns": numeric_cols,
                "text_columns": text_cols,
                "suggestion": "Try specifying x, y, and chart_type parameters"
            }), 400
        
        # Apply consistent styling
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=60, b=20),
            font=dict(family="Inter, sans-serif"),
            title_font=dict(size=18, family="Outfit, sans-serif"),
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Inter, sans-serif"
            )
        )
        
        # Convert to JSON for frontend
        chart_json = json.loads(pio.to_json(fig))
        
        return jsonify({
            "success": True,
            "chart": chart_json,
            "metadata": {
                "chart_type": chart_type,
                "rows": len(df),
                "columns": df.columns.tolist()
            }
        })
        
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500
    except pd.errors.EmptyDataError:
        return jsonify({"error": "CSV file is empty"}), 400
    except Exception as e:
        return jsonify({"error": f"Error processing data: {str(e)}"}), 500


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
        viz_urls = []
        
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
        
        # Handle multiple Plotly HTML visualization files
        viz_files = request.files.getlist("viz_files[]")
        viz_titles = request.form.getlist("viz_titles[]")
        
        for i, viz_file in enumerate(viz_files):
            if viz_file and viz_file.filename:
                url = upload_file(
                    viz_file.read(),
                    viz_file.filename,
                    folder="visualizations"
                )
                title_text = viz_titles[i] if i < len(viz_titles) and viz_titles[i] else f"Visualisasi {i+1}"
                viz_urls.append({
                    "url": url,
                    "title": title_text
                })
        
        try:
            create_post(
                title=title,
                slug=slug,
                content_md=content_md,
                source_name=source_name,
                source_link=source_link,
                data_url=data_url,
                thumbnail_url=thumbnail_url,
                viz_urls=viz_urls if viz_urls else None
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
        
        # Handle multiple Plotly HTML visualization files
        viz_files = request.files.getlist("viz_files[]")
        viz_titles = request.form.getlist("viz_titles[]")
        
        new_viz_urls = []
        for i, viz_file in enumerate(viz_files):
            if viz_file and viz_file.filename:
                url = upload_file(
                    viz_file.read(),
                    viz_file.filename,
                    folder="visualizations"
                )
                title_text = viz_titles[i] if i < len(viz_titles) and viz_titles[i] else f"Visualisasi {i+1}"
                new_viz_urls.append({
                    "url": url,
                    "title": title_text
                })
        
        # Handle deletion of existing visualizations
        delete_indices_str = request.form.get("delete_viz_indices", "")
        delete_indices = []
        if delete_indices_str:
            delete_indices = [int(x) for x in delete_indices_str.split(",") if x.strip()]
        
        # Get current viz_urls
        existing = post.get("viz_urls") or []
        
        # Remove deleted items (process in reverse to maintain indices)
        if delete_indices:
            existing = [viz for i, viz in enumerate(existing) if i not in delete_indices]
        
        # Merge remaining + new
        if delete_indices or new_viz_urls:
            updates["viz_urls"] = existing + new_viz_urls if (existing or new_viz_urls) else None
        
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
