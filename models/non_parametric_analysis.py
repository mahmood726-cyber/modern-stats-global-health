import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.gam.generalized_additive_model import GLMGam
from statsmodels.gam.api import BSplines
import json
import os

DATA_DIR = "data"
DASHBOARD_DIR = "dashboard"

def run_analysis():
    # Load data
    # Ingestion now standardizes on iso3c
    wb = pd.read_parquet(os.path.join(DATA_DIR, "wb_indicators.parquet"))
    who = pd.read_parquet(os.path.join(DATA_DIR, "who_life_expectancy.parquet"))
    
    # Merge datasets
    df = wb.merge(who, on=["iso3c", "year"], how="inner")
    
    # Focus on 2019 cross-sectional analysis
    df_2019 = df[df["year"] == 2019].dropna(subset=["gdp_pc_usd", "life_expectancy"])
    
    if df_2019.empty:
        print("No data found for 2019 analysis.")
        return

    # Sort by GDP for plotting
    df_2019 = df_2019.sort_values("gdp_pc_usd")
    
    X = df_2019["gdp_pc_usd"].values
    y = df_2019["life_expectancy"].values
    
    # 1. Linear Regression Baseline (Log-GDP for fairness in baseline too)
    X_log = np.log10(X)
    X_lin = sm.add_constant(X_log)
    lin_model = sm.OLS(y, X_lin).fit()
    y_lin = lin_model.predict(X_lin)
    
    # 2. Modern Non-parametric: Generalized Additive Model (GAM)
    # Using B-splines for the Log10-GDP
    # df=5 for moderate smoothing
    bs = BSplines(X_log, df=[5], degree=[3])
    gam_model = GLMGam(y, smoother=bs).fit()
    y_gam = gam_model.predict()
    
    # Compute Non-Linearity Score (% Mean Absolute Deviation from Linear)
    mean_le = np.mean(y)
    mean_abs_diff = np.mean(np.abs(y_gam - y_lin))
    pct_divergence = (mean_abs_diff / mean_le) * 100
    
    print(f"Mean Delta from Linear Baseline: {mean_abs_diff:.2f} years")
    print(f"Non-Linearity Score (Divergence %): {pct_divergence:.2f}%")
    
    # Save results for dashboard
    results = {
        "analysis_year": 2019,
        "n_countries": len(df_2019),
        "mean_delta_years": float(mean_abs_diff),
        "non_linearity_score_pct": float(pct_divergence),
        "data_points": [
            {
                "iso3c": iso3,
                "gdp": float(g),
                "life_expectancy": float(le),
                "linear_fit": float(lf),
                "np_fit": float(nf)
            }
            for iso3, g, le, lf, nf in zip(df_2019["iso3c"], X, y, y_lin, y_gam)
        ]
    }
    
    if not os.path.exists(DASHBOARD_DIR):
        os.makedirs(DASHBOARD_DIR)
        
    with open(os.path.join(DASHBOARD_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=4)
    print("GAM analysis results saved to dashboard/results.json")

if __name__ == "__main__":
    run_analysis()
