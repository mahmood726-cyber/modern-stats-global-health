import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.nonparametric.kernel_regression import KernelReg
import json
import os

DATA_DIR = "data"
DASHBOARD_DIR = "dashboard"

def run_analysis():
    # Load data
    wb = pd.read_parquet(os.path.join(DATA_DIR, "wb_indicators.parquet"))
    who = pd.read_parquet(os.path.join(DATA_DIR, "who_life_expectancy.parquet"))
    mapping = pd.read_parquet(os.path.join(DATA_DIR, "country_mapping.parquet"))
    
    # Map WB iso2 to iso3
    wb = wb.merge(mapping, left_on="iso3c", right_on="iso2", suffixes=("_wb", "_map"))
    wb = wb.drop(columns=["iso3c_wb", "iso2"]).rename(columns={"iso3c_map": "iso3c"})
    
    # Merge datasets
    df = wb.merge(who, on=["iso3c", "year"], how="inner")
    
    # Focus on a specific year for the cross-sectional analysis (e.g., 2021)
    df_2021 = df[df["year"] == 2019].dropna(subset=["gdp_pc_usd", "life_expectancy"])
    
    if df_2021.empty:
        print("No data found for 2019 analysis.")
        return

    # Sort by GDP for plotting
    df_2021 = df_2021.sort_values("gdp_pc_usd")
    
    X = df_2021["gdp_pc_usd"].values
    y = df_2021["life_expectancy"].values
    
    # 1. Linear Regression Baseline
    X_lin = sm.add_constant(X)
    lin_model = sm.OLS(y, X_lin).fit()
    y_lin = lin_model.predict(X_lin)
    
    # 2. Non-parametric Kernel Regression
    # We'll use a log scale for GDP as it's typically log-normally distributed
    X_log = np.log(X)
    kr = KernelReg(y, X_log, 'c')
    y_np, _ = kr.fit(X_log)
    
    # Compute Delta
    delta = np.mean(np.abs(y_np - y_lin))
    print(f"Mean Delta from Linear Baseline: {delta:.2f} years")
    
    # Save results for dashboard
    results = {
        "analysis_year": 2019,
        "n_countries": len(df_2021),
        "mean_delta": float(delta),
        "data_points": [
            {
                "iso3c": iso3,
                "gdp": float(g),
                "life_expectancy": float(le),
                "linear_fit": float(lf),
                "np_fit": float(nf)
            }
            for iso3, g, le, lf, nf in zip(df_2021["iso3c"], X, y, y_lin, y_np)
        ]
    }
    
    if not os.path.exists(DASHBOARD_DIR):
        os.makedirs(DASHBOARD_DIR)
        
    with open(os.path.join(DASHBOARD_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=4)
    print("Analysis results saved to dashboard/results.json")

if __name__ == "__main__":
    run_analysis()
