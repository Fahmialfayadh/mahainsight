# MahaInsight

MahaInsight is a data analyst portfolio platform designed to publish data-driven stories with full transparency. It combines interactive visualizations, detailed narratives, and AI-powered insights to essentially bridge the gap between raw data and understandable stories.

## Features

### 1. Interactive Data Stories
- **Markdown Support**: Articles are written in Markdown, allowing for rich text formatting.
- **Embedded Visualizations**: Seamlessly integrates Supabase-hosted Plotly visualizations.
- **Source Transparency**: Each article links back to its original data source and Petasight mapping (if applicable).

### 2. Smart Search & Discovery
- **Multi-Tag Filtering**: Users can select multiple topics (e.g., "Economy", "Climate") to filter articles effectively. The system uses intelligent OR-logic to broaden discovery.
- **Real-Time Interaction**: Experience a seamless search flow where results update instantly without page reloads.
- **Contextual Sticky Bars**: Search bars and navigation remain accessible as you explore, ensuring you never lose your place.

### 3. AI-Powered Analysis (Hybrid Intelligence Architecture)
MahaInsight uses a **Hybrid Intelligence** approach, combining deterministic Python processing with probabilistic LLM (Groq Llama 3.1 8b) reasoning. This minimizes hallucinations and ensures calculation accuracy.

#### The "Hybrid Engine" Workflow (`ai_engine/`)
When a user asks a question, the system does **NOT** just send the raw CSV to the LLM. Instead, it follows a strict 7-step pipeline:

1.  **Schema Inference** (`schema.py`):
    - Automatically detects semantic column types (Temporal, Geospatial, Numeric, Rate, Index).
    - Infers units (e.g., detects "%" and forbids summation, detects "USD" and allows summation).
2.  **Deterministic Filtering** (`analysis.py`):
    - Extracts years (e.g., "2024") and entity names from the user's natural language query using Regex.
    - Filters the Pandas DataFrame *before* any analysis to ensure relevance.
3.  **Data Quality Check** (`quality.py`):
    - Calculates a **Confidence Score** based on missing values (null rate) and sample size.
    - identifying Z-Score anomalies (> 5 standard deviations) to warn the user about outliers.
4.  **Intent Recognition**:
    - Classifies the question into: `Trend`, `Ranking`, `Comparison`, or `Aggregation` based on keywords.
5.  **Statistical Calculation** (The "Hard" Logic):
    - **Trend**: Calculates CAGR and "Recent Momentum" moves.
    - **Ranking**: Identifies Top/Bottom N records.
    - **Aggregation**: Safely aggregates data. *Crucially, it prevents invalid math, such as Summing percentages.*
6.  **Context Construction**:
    - The engine packages a strict JSON object containing *only* the calculated facts, metadata, and quality warnings.
7.  **LLM Narrative Generation**:
    - Llama 3.1 receives the JSON and is prompted to act as a narrator ("Vercax"), translating the hard stats into a fluent, contextual answer.

#### Usage Limits
- **Regular Users**: Capped at **3 questions per article per 24 hours**. This quota is tracked via database to ensure fair usage.
- **Admins**: Unlimited usage for testing and management.

### 4. Adaptive User Experience
- **Immersive Design**: Features a modern, glassmorphism-inspired UI with carefully curated color palettes and smooth gradients.
- **Mobile-First Architecture**: Fully responsive layouts with collapsible sidebars and touch-optimized interactive elements.
- **Global Theme Sync**: Dark mode and styling preferences are persisted across sessions and pages for a consistent reading environment.

### 5. Dynamic Visualizations & Security
- **Visualization Proxy**: To bypass third-party cookie issues and ensure security, all Plotly HTMLs are served via a core `viz-proxy` endpoint `(/viz-proxy?url=...)`.
- **Performance**: The proxy layer implements **ETag caching** and aggressive browser caching (24 hours) to minimize latency and bandwidth costs.

### 6. Open Data Access
- **Dataset Repository**: A dedicated `/datasets` page lists all open data used in articles.
- **Instant CSV Preview**: Powered by **PapaParse.js**, users can instantly preview the first 20 rows of any dataset directly in the browser—no download required.
- **Direct Download**: One-click download for full CSV files to encourage independent analysis.

### 7. Admin Dashboard
- **Content Management**: Create, edit, and delete posts.
- **User Management**: View user lists and toggle admin privileges.
- **File Management**: Direct upload for CSV datasets, thumbnails, and HTML plots to Supabase Storage.

## Tech Stack

- **Backend**: Python (Flask)
- **Database & Auth**: Supabase (PostgreSQL + GoTrue)
- **AI Engine**: Groq API (Llama 3.1)
- **Frontend**: Jinja2 Templates, Tailwind CSS, Plotly.js, PapaParse.js
- **Deployment**: Ready for Heroku/Production environments

## Project Structure

- `app.py`: Main application entry point and route definitions.
- `ai_engine/`:
    - `core/`: Data schema inference and quality checks.
    - `analysis.py`: Python engine for executing data queries.
- `auth/`: Authentication blueprints (Login, Register, OAuth).
- `static/`:
    - `js/`: Client-side logic including `detail.js` (Chat UI) and `base.js`.
    - `style/`: Tailwind input CSS.
- `templates/`: Jinja2 HTML templates.

## License

[MIT](LICENSE)
