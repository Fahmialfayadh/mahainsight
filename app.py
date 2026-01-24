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
# import plotly.express as px
# import plotly.io as pio
import requests
from io import StringIO
import json
from groq import Groq
import numpy as np
from db import (
    get_all_posts, get_post_by_slug, create_post, 
    update_post, delete_post, upload_file,
    create_user, get_user_by_email, get_user_by_id,
    get_all_users, set_admin_status,
    get_user_ai_usage, increment_user_ai_usage
)
from werkzeug.security import generate_password_hash, check_password_hash

# Import JWT auth system
from auth.routes import auth_bp
from auth.auth_middleware import jwt_required, admin_required, get_current_user
from flask import g

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default-secret-key")

# Session cookie configuration
# For localhost: use Lax (None requires HTTPS)
# For production with HTTPS: use None for cross-site compatibility
IS_PRODUCTION = os.getenv("FLASK_ENV") == "production"
app.config['SESSION_COOKIE_SAMESITE'] = 'None' if IS_PRODUCTION else 'Lax'
app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Session lifetime: 30 days (matches refresh token expiry)
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Register authentication blueprint
app.register_blueprint(auth_bp)

# ============== CONTEXT PROCESSOR ==============

@app.context_processor
def inject_user():
    """Inject current user from JWT into all templates."""
    user = get_current_user()
    if user:
        # Also populate session for backward compatibility with templates
        session['user_id'] = user['user_id']
        session['user_name'] = user.get('email', '').split('@')[0]  # Use email prefix as name
        session['is_admin'] = user.get('is_admin', False)
        
        # Try to get full name from database
        try:
            from db import get_user_by_id
            user_data = get_user_by_id(user['user_id'])
            if user_data and user_data.get('full_name'):
                session['user_name'] = user_data['full_name']
        except:
            pass
    else:
        # Clear session if no JWT token
        session.pop('user_id', None)
        session.pop('user_name', None)
        session.pop('is_admin', None)
    
    return dict(current_user=user)

# ============== HELPERS ==============

# Legacy decorators kept for backward compatibility
# These now use JWT tokens instead of sessions
def login_required(f):
    """Decorator to require admin login (is_admin=True) - JWT version."""
    return admin_required(f)


def user_required(f):
    """Decorator to require user login - JWT version."""
    return jwt_required(f)

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
        "break-on-newline"  
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


def get_csv_context(data_url: str, query: str = None) -> str:
    """Fetch CSV and generate a summary context with smart search."""
    if not data_url:
        return ""
    try:
        response = requests.get(data_url, timeout=10)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        
        # Create a summary of the data
        buffer = StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()
        
        # explicit column list
        columns = "\n".join([f"- {col} ({dtype})" for col, dtype in df.dtypes.items()])

        # Helper for markdown table
        def manual_to_markdown(d):
            if d.empty: return ""
            cols = d.columns.tolist()
            # Header
            res = ["| " + " | ".join(str(c) for c in cols) + " |"]
            # Separator
            res.append("| " + " | ".join(["---"] * len(cols)) + " |")
            # Rows
            for _, row in d.iterrows():
                res.append("| " + " | ".join(str(val).replace("\n", " ") for val in row) + " |")
            return "\n".join(res)

        # 1. General Stats
        try:
            description = manual_to_markdown(df.describe().reset_index()) 
        except: 
            description = "No numerical stats available."

        # 2. Sample Data (Head)
        head = manual_to_markdown(df.head(5))

        # 3. Smart Search (Relevant Rows)
        relevant_rows = ""
        if query:
            # Simple keyword matching: split query into words, filter rows containing them
            # Filter non-stopwords (very basic) to avoid matching "the", "a", etc. but maintain important ones
            # For robustness, let's look for exact string matches in object columns
            
            # Normalize query: lowercase
            q_lower = query.lower()
            
            # Find rows where any string column contains the query terms
            # We'll try to match the whole phrase or significant words
            
            # Method: Concatenate all row values to string and search
            # This is expensive for huge data but fine for typical 100-5000 row CSVs in this context
            
            # Efficient-ish search:
            mask = np.column_stack([df[col].astype(str).str.contains(q_word, case=False, na=False) 
                                    for col in df.columns 
                                    for q_word in q_lower.split() if len(q_word) > 3])
            
            # If any column matched any significant word
            if mask.any():
                # Get matched rows (limit to top 5 matches to save context)
                matched_row_indices = mask.any(axis=1)
                matches = df[matched_row_indices].head(5)
                
                if not matches.empty:
                    relevant_rows = f"""
                    \nRELEVANT ROWS FOUND (Matches your query '{query}'):
                    {manual_to_markdown(matches)}
                    """
        
        context = f"""
                    Dataset Overview:
                    {info_str}

                    Columns & Data Types:
                    {columns}

                    Statistical Summary:
                    {description}

                    Sample Data (First 5 Rows):
                    {head}
                    {relevant_rows}
                     """
        return context
    except Exception as e:
        print(f"Error fetching CSV context: {e}")
        return f"Error loading dataset: {str(e)}"


# ============== PUBLIC ROUTES ==============

@app.route("/")
def index():
    """Homepage - List all articles."""
    posts = get_all_posts()
    # Add plain text preview for each post
    for post in posts:
        post["preview"] = strip_markdown(post.get("content_md", ""))[:150]
    return render_template("index.html", posts=posts)


@app.route("/datasets")
def datasets():
    """List available datasets from articles."""
    all_posts = get_all_posts()
    # Filter posts that have a data_url
    dataset_posts = [p for p in all_posts if p.get("data_url")]
    
    return render_template("datasets.html", posts=dataset_posts)


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


@app.route("/api/ai/summary", methods=["POST"])
@jwt_required
def ai_summary():
    """Generate article summary using Groq AI."""
    
    post_id = request.json.get("post_id")
    if not post_id:
        return jsonify({"error": "Post ID required"}), 400
        
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return jsonify({"error": "AI service not configured (Missing API Key)"}), 503
        
    posts = get_all_posts()
    post = next((p for p in posts if p["id"] == int(post_id)), None)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    try:
        client = Groq(api_key=api_key)
        
        # Get data context if available
        data_context = get_csv_context(post.get("data_url"))
        
        content = strip_markdown(post.get("content_md", ""))
        
        prompt = f"""
        Your name is Vercax. You are a helpful data analyst assistant. 
        Please provide a concise summary of the following article.
        
        Article Content:
        {content[:4000]}  # Limit content length
        
        {f'Dataset Context based on attached CSV:{data_context}' if data_context else ''}
        
        Focus on the key insights and findings. Use Markdown formatting.
        """
        
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        
        return jsonify({
            "summary": completion.choices[0].message.content
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/chat", methods=["POST"])
@jwt_required
def ai_chat():
    """Answer questions about the article/data using Groq AI."""
    data = request.json
    post_id = data.get("post_id")
    question = data.get("question")
    
    if not post_id or not question:
        return jsonify({"error": "Missing parameters"}), 400
        
    user = get_current_user()
    user_id = user["user_id"] if user else None
    is_admin = user["is_admin"] if user else False
    
    # === RATE LIMIT CHECK ===
    remaining_quota = 3 # default
    
    if not is_admin:
        # Regular users: Check DB usage
        current_usage = get_user_ai_usage(user_id, post_id)
        if current_usage >= 3:
            return jsonify({
                "error": "Limit exhausted", 
                "message": "Anda telah mencapai batas 3 pertanyaan untuk artikel ini dalam 24 jam."
            }), 429
        remaining_quota = 3 - current_usage
    else:
        # Admins: Uncapped
        remaining_quota = 999 

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return jsonify({"error": "AI service not configured"}), 503

    posts = get_all_posts()
    post = next((p for p in posts if p["id"] == int(post_id)), None)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    try:
        client = Groq(api_key=api_key)
        
        # Use simple pandas Markdown for fallback if needed inside the engine, 
        # but the engine handles formatting now.
        
        # === CALL PYTHON ANALYSIS ENGINE ===
        from ai_engine.analysis import analyze_dataset
        import json
        
        # The engine performs filtering and calculations based on the query
        # Returns a Dict (Schema V2)
        analysis_dict = analyze_dataset(post.get("data_url"), question)
        
        # Convert to strict JSON string for the LLM
        analysis_json = json.dumps(analysis_dict, indent=2, default=str)
        
        content = strip_markdown(post.get("content_md", ""))
        
        system_prompt = f"""
        You are Vercax, an expert data analyst AI for MahaInsight.
        
        Usage Instructions:
        1. A Python Analysis Engine has ALREADY processed the user's question against the dataset.
        2. It has provided the "PYTHON ANALYSIS RESULT" below in strictly structured JSON format.
        3. **TRUST RULE**: The values in `aggregations` and `confidence` are calculated facts. Use them directly. Do not re-calculate.
        4. **CONFIDENCE CHECK**: Look at `confidence.score`. If 'low', warn the user that the data is limited.
        5. **CONTEXTUALIZE**: Use `metadata.units` to ensure every number you cite has the correct unit (%, USD, etc).

        CONTEXT 1: The Article
        {content[:3000]}

        CONTEXT 2: PYTHON ANALYSIS RESULT (JSON)
        ```json
        {analysis_json}
        ```

        Answer the user's question using the specific facts, units, and stats found in Context 2.
        """
        
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            model="llama-3.1-8b-instant",
        )
        
        
        # Increment counter (if not admin, or we track admin usage too but don't limit?)
        # Let's track everyone for analytics, but only limit non-admins
        increment_user_ai_usage(user_id, post_id)
        
        # Calculate new remaining
        if not is_admin:
            new_remaining = remaining_quota - 1
        else:
            new_remaining = 999
        
        return jsonify({
            "answer": completion.choices[0].message.content,
            "remaining": new_remaining
        })
    except Exception as e:
        print(f"AI Chat Error: {e}")
        return jsonify({"error": str(e)}), 500



@app.route("/api/ai/usage/<int:post_id>")
def get_ai_usage_api(post_id):
    """Get remaining usage for a user on a post."""
    user = get_current_user()
    if not user:
        return jsonify({"remaining": 0, "is_admin": False})
        
    user_id = user["user_id"]
    is_admin = user["is_admin"]
    
    if is_admin:
        return jsonify({"remaining": 999, "is_admin": True})
        
    usage = get_user_ai_usage(user_id, post_id)
    return jsonify({"remaining": max(0, 3 - usage), "is_admin": False})


# @app.route("/api/plotly-chart")
# def plotly_chart():
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
# Auth routes moved to auth/routes.py and registered as blueprint
# Backward compatibility routes

@app.route("/user-login")
def user_login_redirect():
    return redirect(url_for("auth.login"))

@app.route("/user-logout")
def user_logout_redirect():
    return redirect(url_for("auth.logout"))

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
        petasight_link = request.form.get("petasight_link")
        
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
                viz_urls=viz_urls if viz_urls else None,
                petasight_link=petasight_link
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
            "petasight_link": request.form.get("petasight_link"),
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


@app.route("/admin/users")
@login_required
def admin_users():
    """Admin dashboard - List all users."""
    users = get_all_users()
    current_user_id = session.get("user_id")
    return render_template("admin_users.html", users=users, current_user_id=current_user_id)


@app.route("/admin/users/toggle/<int:user_id>", methods=["POST"])
@login_required
def toggle_admin(user_id):
    """Toggle admin status for a user."""
    # Prevent self-demotion
    if user_id == session.get("user_id"):
        flash("Anda tidak dapat mengubah status admin diri sendiri.", "error")
        return redirect(url_for("admin_users"))
        
    try:
        target_user = get_user_by_id(user_id)
        if not target_user:
            flash("User tidak ditemukan", "error")
            return redirect(url_for("admin_users"))
            
        new_status = not target_user.get("is_admin", False)
        set_admin_status(user_id, new_status)
        
        status_msg = "dijadikan Admin" if new_status else "dihapus dari Admin"
        flash(f"User {target_user.get('email')} berhasil {status_msg}.", "success")
        
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        
    return redirect(url_for("admin_users"))


# ============== RUN ==============

if __name__ == "__main__":
    app.run(debug=True)
