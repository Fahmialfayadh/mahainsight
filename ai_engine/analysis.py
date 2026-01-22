import pandas as pd
import numpy as np
import requests
import re
import json
from io import StringIO

def load_data(url):
    """Load CSV data from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except Exception as e:
        return None

def scan_metadata(df):
    """Scan dataset for metadata and potential units."""
    meta = {
        "columns": list(df.columns),
        "row_count": len(df),
        "units": {}
    }
    
    # Simple Unit Heuristics
    for col in df.columns:
        col_lower = col.lower()
        if "%" in col or "percent" in col_lower or "rate" in col_lower:
            meta["units"][col] = "%"
        elif "usd" in col_lower or "$" in col:
            meta["units"][col] = "USD"
        elif "idr" in col_lower or "rp" in col_lower:
            meta["units"][col] = "IDR"
        elif "pop" in col_lower or "people" in col_lower:
            meta["units"][col] = "people"
        elif "year" in col_lower:
            meta["units"][col] = "year"
            
    return meta

def calculate_confidence(df_filtered, original_count):
    """Calculate confidence score based on sample size and data quality."""
    if df_filtered.empty:
        return {"score": "none", "reason": "No data found matching criteria"}
        
    count = len(df_filtered)
    ratio = count / original_count if original_count > 0 else 0
    
    # Missing value density check (on numeric columns)
    numeric_df = df_filtered.select_dtypes(include=[np.number])
    null_density = 0
    if not numeric_df.empty:
        null_density = numeric_df.isna().mean().mean()
    
    reason = []
    score = "high"
    
    if count < 5:
        score = "low"
        reason.append("Very small sample size (< 5 rows)")
    elif count < 30 and ratio < 0.1:
        score = "medium" 
        reason.append("Small subset")
        
    if null_density > 0.3:
        score = "low"
        reason.append("High missing value density (> 30%)")
        
    if not reason:
        reason.append("Sufficient data density")
        
    return {
        "score": score,
        "reason": "; ".join(reason),
        "sample_size": count,
        "null_density": f"{null_density:.1%}"
    }

def detect_columns(df):
    """Detect potential semantic columns (Year, Country, Value)."""
    cols = {
        "year": [],
        "country": [],
        "iso": [],
        "value": []
    }
    
    for col in df.columns:
        lname = col.lower()
        if any(x in lname for x in ['year', 'tahun', 'time']):
            cols['year'].append(col)
        elif any(x in lname for x in ['country', 'negara', 'region']):
            cols['country'].append(col)
        elif any(x in lname for x in ['iso', 'code', 'kode']):
            cols['iso'].append(col)
        elif np.issubdtype(df[col].dtype, np.number):
            if not any(x in lname for x in ['year', 'id', 'code']):
                cols['value'].append(col)
                
    return cols

def extract_filters(df, query):
    """Extract filter conditions from query."""
    query_lower = query.lower()
    filters = {}
    
    # 1. Year Detection
    years = re.findall(r'\b(19|20)\d{2}\b', query)
    if years:
        full_years = re.findall(r'\b(?:19|20)\d{2}\b', query)
        filters['year'] = [int(y) for y in full_years]

    # 2. Categorical/Entity Detection
    string_cols = df.select_dtypes(include=['object', 'string']).columns
    
    for col in string_cols:
        unique_vals = df[col].dropna().unique()
        for val in unique_vals:
            val_str = str(val)
            if len(val_str) < 2: continue 
            
            if len(val_str) <= 3:
                if re.search(r'\b' + re.escape(val_str.lower()) + r'\b', query_lower):
                    if col not in filters: filters[col] = []
                    filters[col].append(val)
            else:
                 if val_str.lower() in query_lower:
                    if col not in filters: filters[col] = []
                    filters[col].append(val)
                    
    return filters

def analyze_dataset(data_url, query):
    """
    Main entry point. Output is a DICTIONARY (structured JSON).
    """
    df = load_data(data_url)
    if df is None:
        return {"status": "error", "message": "Could not load dataset"}

    metadata = scan_metadata(df)
    semantic_cols = detect_columns(df)
    filters = extract_filters(df, query)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    # Apply filters
    filtered_df = df.copy()
    filter_logs = []
    
    if 'year' in filters and semantic_cols['year']:
        y_col = semantic_cols['year'][0]
        filtered_df = filtered_df[filtered_df[y_col].isin(filters['year'])]
        filter_logs.append(f"Date Filter: {filters['year']}")

    for col, vals in filters.items():
        if col == 'year': continue
        filtered_df = filtered_df[filtered_df[col].isin(vals)]
        filter_logs.append(f"Entity Filter ({col}): {vals}")

    # Confidence check
    confidence = calculate_confidence(filtered_df, len(df))
    
    # Recompute numeric columns based on FILTERED data (critical fix)
    numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns

    # --- V2: INTENT & METRIC DETECTION ---
    
    # 1. Detect Primary Metric (Numeric Column)
    primary_metric = None
    if not numeric_cols.empty:
        # Heuristic: First numeric col that isn't 'year' or 'id'
        # Improved: Look for 'value', 'rate', 'gdp', 'population' in name
        priority_keywords = ['value', 'score', 'rate', 'gdp', 'population', 'count', 'total']
        
        for kw in priority_keywords:
            for col in numeric_cols:
                if kw in col.lower():
                    primary_metric = col
                    break
            if primary_metric: break
        
        if not primary_metric:
            primary_metric = numeric_cols[0]

    # 2. Detect Intent
    intent = "descriptive" # default
    q_lower = query.lower()
    if any(x in q_lower for x in ['trend', 'growth', 'tumbuh', 'naik', 'turun', 'change', 'perubahan']):
        intent = "trend"
    elif any(x in q_lower for x in ['rank', 'top', 'bottom', 'paling', 'tertinggi', 'terendah']):
        intent = "ranking"
    elif any(x in q_lower for x in ['compare', 'banding', 'vs', 'beda']):
        intent = "comparison"
    elif any(x in q_lower for x in ['rata', 'mean', 'avg', 'sum', 'total']):
        intent = "aggregation"

    # --- V2: ANALYTICAL CALCULATIONS ---
    
    insights = {}
    
    # A. Trend Analysis (if Year exists)
    if 'year' in semantic_cols and semantic_cols['year'] and primary_metric:
        y_col = semantic_cols['year'][0]
        # Sort by year
        df_sorted = filtered_df.sort_values(y_col)
        
        if len(df_sorted) > 1:
            start_val = df_sorted.iloc[0][primary_metric]
            end_val = df_sorted.iloc[-1][primary_metric]
            start_year = df_sorted.iloc[0][y_col]
            end_year = df_sorted.iloc[-1][y_col]
            
            # Guard against NaN values (critical fix #2)
            if pd.isna(start_val) or pd.isna(end_val):
                pass  # Skip trend calculation silently if data is incomplete
            else:
                delta = end_val - start_val
                growth_rate = (delta / start_val) * 100 if start_val != 0 else 0
                direction = "UP" if delta > 0 else "DOWN" if delta < 0 else "FLAT"
                
                trend_insight = {
                    "metric": primary_metric,
                    "direction": direction,
                    "start_year": int(start_year),
                    "end_year": int(end_year),
                    "absolute_change": float(round(delta, 2)),
                    "growth_rate_percent": float(round(growth_rate, 2))
                }
                
                # Attach unit (critical fix #5)
                unit = metadata.get("units", {}).get(primary_metric)
                if unit:
                    trend_insight["unit"] = unit
                
                insights['trend'] = trend_insight

    # B. Ranking Analysis (Top/Bottom)
    if primary_metric and len(filtered_df) > 1:
        # Guard against all-NaN metric column (critical fix #3)
        if filtered_df[primary_metric].notna().sum() > 0:
            top_3 = filtered_df.nlargest(3, primary_metric).to_dict(orient='records')
            bottom_3 = filtered_df.nsmallest(3, primary_metric).to_dict(orient='records')
            
            ranking_insight = {
                "metric": primary_metric,
                "top_3": top_3,
                "bottom_3": bottom_3
            }
            
            # Attach unit (critical fix #5)
            unit = metadata.get("units", {}).get(primary_metric)
            if unit:
                ranking_insight["unit"] = unit
            
            insights['ranking'] = ranking_insight

    # C. Comparison Context (vs Global Mean)
    if primary_metric:
        # Calculate Global Mean (from unfiltered DF)
        global_mean = df[primary_metric].mean() if primary_metric in df.columns else 0
        filtered_mean = filtered_df[primary_metric].mean()
        
        diff_percent = ((filtered_mean - global_mean) / global_mean) * 100 if global_mean != 0 else 0
        
        comparison_insight = {
            "metric": primary_metric,
            "global_mean": float(round(global_mean, 2)),
            "subset_mean": float(round(filtered_mean, 2)),
            "vs_global_status": "ABOVE" if filtered_mean > global_mean else "BELOW",
            "diff_percent": float(round(diff_percent, 2)),
            "_warning": "Comparison uses full dataset baseline (may span different periods)"  # Critical fix #4
        }
        
        # Attach unit (critical fix #5)
        unit = metadata.get("units", {}).get(primary_metric)
        if unit:
            comparison_insight["unit"] = unit
        
        insights['comparison'] = comparison_insight

    # Aggregations
    aggregations = {}
    
    if not filtered_df.empty and not numeric_cols.empty:
        # Defaults
        aggregations["summary_stats"] = filtered_df[numeric_cols].describe().to_dict()
        
        # Simple Intent-based aggregation
        if intent == "aggregation":
            if any(x in q_lower for x in ['mean', 'average', 'rata']):
                aggregations["custom_metric"] = "mean"
                aggregations["custom_values"] = filtered_df[numeric_cols].mean().to_dict()
            elif any(x in q_lower for x in ['sum', 'total', 'jumlah']):
                aggregations["custom_metric"] = "sum"
                aggregations["custom_values"] = filtered_df[numeric_cols].sum().to_dict()

    # Sample Data (limit 5)
    samples = []
    if not filtered_df.empty:
        # Convert to records logic
        samples = filtered_df.head(5).to_dict(orient='records')

    # Construct Final Schema
    result = {
        "status": "success",
        "intent": intent,
        "primary_metric": primary_metric,
        "confidence": confidence,
        "metadata": metadata,
        "applied_filters": filter_logs,
        "insights": insights,
        "aggregations": aggregations,
        "sample_rows": samples,
        "warnings": []
    }
    
    if filtered_df.empty:
        result["warnings"].append("No data matched the specific filters.")
    
    return result
