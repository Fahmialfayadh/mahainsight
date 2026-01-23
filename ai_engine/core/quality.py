"""
Data Quality Module
Responsible for detecting anomalies, duplicates, and assessing data confidence.
"""
import pandas as pd
import numpy as np

def check_duplicates(df, subset_cols=None):
    """
    Check for duplicate rows.
    """
    if subset_cols:
        # Check duplicates based on keys (e.g., Year + Country)
        valid_cols = [c for c in subset_cols if c in df.columns]
        if valid_cols:
            count = df.duplicated(subset=valid_cols).sum()
            return {"count": int(count), "keys": valid_cols}
            
    # Default: full row duplicates
    count = df.duplicated().sum()
    return {"count": int(count), "keys": "all_columns"}

def check_anomalies(df, semantic_cols):
    """
    Detect statistical anomalies and logic errors.
    """
    anomalies = []
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        # 1. Negative Values Check (for non-temperature/delta metrics)
        # Assuming most metrics (Population, GDP, Rates) shouldn't be negative
        # Provide exception list if needed
        safe_negative_cols = ['change', 'delta', 'temp', 'balance', 'net']
        if not any(x in col.lower() for x in safe_negative_cols):
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                anomalies.append(f"Found {neg_count} negative values in '{col}' (potential error for this metric type)")

        # 2. Extreme Outliers (Z-score > 5 for simple check)
        if len(df) > 10:
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                z_scores = np.abs((df[col] - mean) / std)
                outliers = (z_scores > 5).sum()
                if outliers > 0:
                    anomalies.append(f"Found {outliers} extreme outliers (Z-score > 5) in '{col}'")
                    
    return anomalies

def generate_quality_report(df, original_dataset_len=0):
    """
    Generate comprehensive data quality report and confidence score.
    """
    if df.empty:
        return {"score": "none", "reason": "No data found matching criteria"}
        
    count = len(df)
    
    # Missing value density
    numeric_df = df.select_dtypes(include=[np.number])
    null_density = 0
    if not numeric_df.empty:
        null_density = numeric_df.isna().mean().mean()
    
    # Scoring Logic
    reason = []
    score = "high"
    
    # 1. Sample Size
    if count < 5:
        score = "low"
        reason.append("Peringatan: Ukuran sampel sangat kecil (< 5 observasi), hasil mungkin tidak representatif.")
    elif count < 30:
        score = "medium" 
        reason.append("Catatan: Sampel terbatas (< 30 observasi).")
        
    # 2. Missing Values
    if null_density > 0.3:
        score = "low"
        reason.append(f"Kritis: Densitas nilai hilang tinggi ({null_density:.1%}), analisis mungkin bias.")
    elif null_density > 0.1:
        if score == "high": score = "medium"
        reason.append(f"Peringatan: Defisiensi data terdeteksi ({null_density:.1%}).")
        
    # Create Professional Summary
    summary_parts = []
    
    # Null Check Status
    if numeric_df.empty:
        summary_parts.append("Pemeriksaan nilai kosong tidak dapat dilakukan karena tidak ditemukan kolom numerik.")
    else:
        summary_parts.append(f"Pemeriksaan kualitas data menunjukkan densitas nilai kosong sebesar {null_density:.1%} pada variabel numerik yang dianalisis.")
        
    # Anomaly Status
    # Note: Anomalies are passed in separately usually, but we can infer from reason if critical
    
    # Limitation/Context Stating
    summary_parts.append("Pemeriksaan duplikasi dan konsistensi relasional tidak dilakukan secara menyeluruh pada tahap analisis cepat ini.")
    
    # Final Conclusion
    if score == "high":
        summary_parts.append("Secara keseluruhan, dataset memiliki tingkat kelengkapan data yang sangat baik, dengan validitas statistik yang memadai untuk analisis lebih lanjut.")
    elif score == "medium":
        summary_parts.append("Secara umum kualitas data memadai, namun interpretasi harus mempertimbangkan keterbatasan ukuran sampel atau kelengkapan variabel.")
    else:
        summary_parts.append("Dataset memiliki isu kualitas signifikan yang mungkin membatasi validitas kesimpulan statistik.")

    return {
        "score": score,
        "reason": "; ".join(reason),
        "sample_size": count,
        "null_density": f"{null_density:.1%}",
        "summary": " ".join(summary_parts)
    }
