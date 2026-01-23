import pandas as pd
import numpy as np
import requests
import re
import json
from io import StringIO

# Import Core Modules
from ai_engine.core import schema, quality, temporal

def load_data(url):
    """Load CSV data from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except Exception as e:
        return None

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
    Main Orchestrator. 
    Integrates Schema, Quality, and Temporal analysis modules.
    """
    # 1. Load Data
    df = load_data(data_url)
    if df is None:
        return {"status": "error", "message": "Could not load dataset"}

    # 2. Schema & Metadata Analysis (Module: Schema)
    metadata = schema.scan_metadata(df)
    semantic_cols = schema.detect_semantic_columns(df)
    
    # 3. Filter Extraction & Application
    filters = extract_filters(df, query)
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

    # 4. Data Quality Check (Module: Quality)
    confidence_report = quality.generate_quality_report(filtered_df, len(df))
    anomalies = quality.check_anomalies(filtered_df, semantic_cols)
    
    # 5. Temporal Intelligence (Module: Temporal)
    temporal_analysis = {}
    if semantic_cols['year']:
        y_col = semantic_cols['year'][0]
        temporal_analysis["range"] = temporal.analyze_time_range(filtered_df, y_col)
        temporal_analysis["gaps"] = temporal.detect_gaps(filtered_df, y_col)
        temporal_analysis["frequency"] = temporal.infer_frequency(filtered_df, y_col)

    # 6. Intent & Metric Detection (Preserved Logic)
    numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns
    primary_metric = None
    if not numeric_cols.empty:
        priority_keywords = ['value', 'score', 'rate', 'gdp', 'population', 'count', 'total']
        for kw in priority_keywords:
            for col in numeric_cols:
                if kw in col.lower():
                    primary_metric = col
                    break
            if primary_metric: break
        if not primary_metric:
            primary_metric = numeric_cols[0]

    intent = "descriptive"
    q_lower = query.lower()
    if any(x in q_lower for x in ['trend', 'growth', 'tumbuh', 'naik', 'turun', 'change', 'perubahan']):
        intent = "trend"
    elif any(x in q_lower for x in ['rank', 'top', 'bottom', 'paling', 'tertinggi', 'terendah']):
        intent = "ranking"
    elif any(x in q_lower for x in ['compare', 'banding', 'vs', 'beda']):
        intent = "comparison"
    elif any(x in q_lower for x in ['rata', 'mean', 'avg', 'sum', 'total']):
        intent = "aggregation"

    # 7. Analytical Insights Generation
    insights = {}
    
    # A. Trend
    if semantic_cols['year'] and primary_metric:
        y_col = semantic_cols['year'][0]
        df_sorted = filtered_df.sort_values(y_col)
        if len(df_sorted) > 1:
            start_val = df_sorted.iloc[0][primary_metric]
            end_val = df_sorted.iloc[-1][primary_metric]
            start_year = df_sorted.iloc[0][y_col]
            end_year = df_sorted.iloc[-1][y_col]
            
            if not (pd.isna(start_val) or pd.isna(end_val)):
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
                unit = metadata.get("units", {}).get(primary_metric)
                if unit: trend_insight["unit"] = unit
                insights['trend'] = trend_insight

    # B. Ranking
    if primary_metric and len(filtered_df) > 1 and filtered_df[primary_metric].notna().sum() > 0:
        top_3 = filtered_df.nlargest(3, primary_metric).to_dict(orient='records')
        bottom_3 = filtered_df.nsmallest(3, primary_metric).to_dict(orient='records')
        
        ranking_insight = {
            "metric": primary_metric,
            "top_3": top_3,
            "bottom_3": bottom_3
        }
        unit = metadata.get("units", {}).get(primary_metric)
        if unit: ranking_insight["unit"] = unit
        insights['ranking'] = ranking_insight

    # C. Comparison
    if primary_metric:
        global_mean = df[primary_metric].mean() if primary_metric in df.columns else 0
        filtered_mean = filtered_df[primary_metric].mean()
        diff_percent = ((filtered_mean - global_mean) / global_mean) * 100 if global_mean != 0 else 0
        
        comparison_insight = {
            "metric": primary_metric,
            "global_mean": float(round(global_mean, 2)),
            "subset_mean": float(round(filtered_mean, 2)),
            "vs_global_status": "ABOVE" if filtered_mean > global_mean else "BELOW",
            "diff_percent": float(round(diff_percent, 2)),
            "_warning": "Comparison uses full dataset baseline"
        }
        unit = metadata.get("units", {}).get(primary_metric)
        if unit: comparison_insight["unit"] = unit
        insights['comparison'] = comparison_insight

    # 8. Aggregations
    aggregations = {}
    if not filtered_df.empty and not numeric_cols.empty:
        aggregations["summary_stats"] = filtered_df[numeric_cols].describe().to_dict()
        
        if intent == "aggregation":
            if any(x in q_lower for x in ['mean', 'average', 'rata']):
                aggregations["custom_metric"] = "mean"
                aggregations["custom_values"] = filtered_df[numeric_cols].mean().to_dict()
            elif any(x in q_lower for x in ['sum', 'total', 'jumlah']):
                aggregations["custom_metric"] = "sum"
                aggregations["custom_values"] = filtered_df[numeric_cols].sum().to_dict()

    # 9. Sample Rows
    samples = []
    if not filtered_df.empty:
        samples = filtered_df.head(5).to_dict(orient='records')

    # Construct Final Result
    result = {
        "status": "success",
        "intent": intent,
        "primary_metric": primary_metric,
        "confidence": confidence_report,    # Enhanced Quality Report
        "data_quality_anomalies": anomalies,# New Anomaly List
        "temporal_analysis": temporal_analysis, # New Temporal Intel
        "metadata": metadata,               # Enhanced Metadata
        "applied_filters": filter_logs,
        "insights": insights,
        "aggregations": aggregations,
        "sample_rows": samples,
        "warnings": []
    }
    
    if filtered_df.empty:
        result["warnings"].append("No data matched the specific filters.")
    
    return result
