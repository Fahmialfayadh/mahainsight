"""
Temporal Intelligence Module
Responsible for analyzing time series properties, gaps, and ranges.
"""
import pandas as pd
import numpy as np

def analyze_time_range(df, year_col):
    """
    Analyze the temporal span and consistency of the data.
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
    
    return {
        "start_year": int(start_year),
        "end_year": int(end_year),
        "span_years": int(span),
        "total_periods": len(years)
    }

def detect_gaps(df, year_col):
    """
    Detect missing years in the time series sequence.
    """
    if year_col not in df.columns:
        return []
        
    years = df[year_col].dropna().unique()
    if len(years) < 2:
        return []
        
    years = sorted(years.astype(int))
    full_range = set(range(years[0], years[-1] + 1))
    existing = set(years)
    
    missing = sorted(list(full_range - existing))
    
    # Group consecutive missing years for cleaner output
    # e.g., "2010, 2011, 2012" -> "2010-2012"
    gaps = []
    if missing:
        # Simple list for now, upgrade logic later if needed
        if len(missing) > 5:
            gaps.append(f"{len(missing)} missing years detected (e.g. {missing[:3]}...)")
        else:
            gaps.append(f"Missing years: {missing}")
            
    return gaps

def infer_frequency(df, year_col):
    """
    Infer if data is Annual, Monthly, etc. (Currently supports Annual).
    """
    # Placeholder for more complex freq detection
    # For now, assumes Annual if column contains 'year'
    return "Annual"
