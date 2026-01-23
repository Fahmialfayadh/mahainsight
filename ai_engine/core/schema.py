"""
Schema Inference Module
Responsible for detecting semantic types and metadata from the dataset.
"""
import pandas as pd
import numpy as np
import re

def scan_metadata(df):
    """
    Scan dataset for metadata, potential units, and column types.
    """
    meta = {
        "columns": list(df.columns),
        "row_count": len(df),
        "units": {},
        "semantic_types": {}
    }
    
    # 1. Unit & Type Heuristics
    for col in df.columns:
        col_lower = col.lower()
        
        # Unit detection
        if "%" in col or "percent" in col_lower or "rate" in col_lower:
            meta["units"][col] = "%"
            meta["semantic_types"][col] = "percentage"
        elif "usd" in col_lower or "$" in col:
            meta["units"][col] = "USD"
            meta["semantic_types"][col] = "currency"
        elif "idr" in col_lower or "rp" in col_lower:
            meta["units"][col] = "IDR"
            meta["semantic_types"][col] = "currency"
        elif "pop" in col_lower or "people" in col_lower:
            meta["units"][col] = "people"
            meta["semantic_types"][col] = "count"
        elif "year" in col_lower or "tahun" in col_lower:
            meta["units"][col] = "year"
            meta["semantic_types"][col] = "temporal"
        elif "idx" in col_lower or "index" in col_lower:
            meta["semantic_types"][col] = "index"
            
    return meta

def detect_semantic_columns(df):
    """
    Detect semantic roles of columns (Time, Entity, Metric).
    """
    cols = {
        "year": [],
        "country": [],
        "iso": [],
        "value": [],
        "category": []
    }
    
    for col in df.columns:
        lname = col.lower()
        dtype = df[col].dtype
        
        # Temporal
        if any(x in lname for x in ['year', 'tahun', 'time', 'date', 'periode']):
            cols['year'].append(col)
            
        # Entity / Geospatial
        elif any(x in lname for x in ['country', 'negara', 'region', 'provinsi', 'city', 'wilayah']):
            cols['country'].append(col)
        elif any(x in lname for x in ['iso', 'code', 'kode']):
            cols['iso'].append(col)
            
        # Metrics (Numeric)
        elif np.issubdtype(dtype, np.number):
            # Exclude ID-like columns if they look like integers but act as keys
            if 'id' in lname and not any(x in lname for x in ['rate', 'score', 'value']):
                cols['category'].append(col)
            else:
                cols['value'].append(col)
                
        # Categorical
        elif dtype == 'object' or dtype == 'string':
            cols['category'].append(col)
                
    return cols

def validate_aggregation_rules(semantic_type):
    """
    Return allowed aggregation methods for a given semantic type.
    """
    rules = {
        "percentage": ["mean", "min", "max"], # Summing percentages is usually wrong
        "rate": ["mean", "min", "max", "weighted_mean"],
        "index": ["mean", "min", "max"],
        "count": ["sum", "mean", "min", "max"],
        "currency": ["sum", "mean", "min", "max"],
        "temporal": ["min", "max"] # Start/End dates
    }
    return rules.get(semantic_type, ["count", "min", "max"]) # Default restricted
