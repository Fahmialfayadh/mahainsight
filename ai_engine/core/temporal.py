"""
Temporal Intelligence Module
Responsible for analyzing time series properties, gaps, and ranges.
"""
import pandas as pd
import numpy as np

def analyze_time_range(df, year_col):
    """
    Analyze the temporal span and consistency of the data.
    Returns metadata about Full Range and Recent Period (Momentum).
    """
    if year_col not in df.columns:
        return None
        
    years = df[year_col].dropna().unique()
    if len(years) == 0:
        return None
        
    years = sorted(years.astype(int))
    start_year = years[0]
    end_year = years[-1]
    span = end_year - start_year + 1
    
    # 1. Full Range Context
    context = {
        "start_year": int(start_year),
        "end_year": int(end_year),
        "span_years": int(span),
        "total_periods": len(years),
        "coverage_type": "Single Year" if span == 1 else "Multi-Year"
    }
    
    # 2. Recent Momentum Context (Last 3-5 years)
    # Define "Recent" as the last 5 years relative to the END of the dataset
    recent_threshold = end_year - 4 # e.g. if 2023, then 2019-2023
    recent_years = [y for y in years if y >= recent_threshold]
    
    if len(recent_years) >= 3:
        context["recent_period"] = {
            "start_year": min(recent_years),
            "end_year": max(recent_years),
            "available_years": len(recent_years),
            "is_continuous": (max(recent_years) - min(recent_years) + 1) == len(recent_years)
        }
    else:
        context["recent_period"] = None # Not enough data for momentum analysis

    return context

def detect_gaps(df, year_col):
    """
    Detect missing years and assess stability.
    """
    if year_col not in df.columns:
        return {"gaps": [], "stability_score": "unknown"}
        
    years = df[year_col].dropna().unique()
    if len(years) < 2:
        return {"gaps": [], "stability_score": "high"} # Single point is stable by definition
        
    years = sorted(years.astype(int))
    full_range = set(range(years[0], years[-1] + 1))
    existing = set(years)
    
    missing = sorted(list(full_range - existing))
    
    # Group consecutive missing years
    gaps = []
    if missing:
        if len(missing) > 5:
            gaps.append(f"{len(missing)} missing years detected (e.g. {missing[:3]}...)")
        else:
            gaps.append(f"Missing years: {missing}")
            
    # Assess Stability
    missing_ratio = len(missing) / len(full_range)
    if missing_ratio == 0:
        stability = "high" # Perfect continuity
    elif missing_ratio < 0.2:
        stability = "medium" # Some gaps
    else:
        stability = "low" # Many gaps (swiss cheese data)
        
    return {"gaps": gaps, "stability_score": stability, "missing_count": len(missing)}

def infer_frequency(df, year_col):
    """
    Infer if data is Annual, Monthly, etc. (Currently supports Annual).
    """
    # Placeholder for more complex freq detection
    return "Annual"
