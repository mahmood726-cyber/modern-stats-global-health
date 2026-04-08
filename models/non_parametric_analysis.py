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
    # 1. DATA LOADING (Full Panel: 2010-2024)
    wb = pd.read_parquet(os.path.join(DATA_DIR, "wb_indicators.parquet"))
    who = pd.read_parquet(os.path.join(DATA_DIR, "who_life_expectancy.parquet"))
    
    # Merge Panel (Country-Year)
    df = wb.merge(who, on=["iso3c", "year"], how="inner")
    df = df.dropna(subset=["gdp_pc_usd", "health_exp_pct_gdp", "life_expectancy"])
    
    if df.empty:
        print("No panel data found for ST-VCM analysis.")
        return

    # Sort for surface estimation
    df = df.sort_values(["year", "gdp_pc_usd"])
    
    Y = df["life_expectancy"].values
    D = df["health_exp_pct_gdp"].values
    X_log = np.log10(df["gdp_pc_usd"].values)
    T = df["year"].values
    T_norm = (T - T.min()) / (T.max() - T.min()) # Normalize Time for splines
    
    # 2. SPATIO-TEMPORAL VARYING COEFFICIENT MODEL (ST-VCM)
    # We use a 2D Tensor Product of Splines: f(GDP, Year)
    # Basis 1: GDP (df=5), Basis 2: Year (df=4)
    # Total Basis: 5 * 4 = 20 components
    
    # Create 2D Basis manually (Tensor Product)
    bs_gdp = BSplines(X_log, df=[5], degree=[3])
    basis_gdp = bs_gdp.transform(X_log)
    
    bs_year = BSplines(T_norm, df=[4], degree=[3])
    basis_year = bs_year.transform(T_norm)
    
    # Tensor Product Expansion
    n_obs = len(df)
    n_gdp = basis_gdp.shape[1]
    n_year = basis_year.shape[1]
    tp_basis = np.zeros((n_obs, n_gdp * n_year))
    for i in range(n_gdp):
        for j in range(n_year):
            tp_basis[:, i * n_year + j] = basis_gdp[:, i] * basis_year[:, j]
            
    # Interaction Basis: TP_Basis * Health Expenditure
    tp_interaction = tp_basis * D[:, np.newaxis]
    
    # Full Model: Intercept + TP_Basis (Baseline) + TP_Interaction (VCM Effect)
    X_st_vcm = np.hstack([sm.add_constant(tp_basis), tp_interaction])
    model = sm.OLS(Y, X_st_vcm).fit()
    
    # 3. EXTRACT THE SURFACE: beta(GDP, Year)
    # Coefficients for interaction start after constant (1) and baseline basis (n_gdp*n_year)
    interaction_coeffs = model.params[1 + (n_gdp * n_year):]
    beta_surface = tp_basis @ interaction_coeffs
    
    # 4. TEMPORAL TRENDS
    # Compute average efficiency per year
    df["beta_st"] = beta_surface
    temporal_efficiency = df.groupby("year")["beta_st"].mean().to_dict()
    
    # 5. DOUBLE MACHINE LEARNING (Panel Baseline)
    # (Simple panel-averaged causal effect)
    model_y = sm.OLS(Y, sm.add_constant(tp_basis)).fit()
    Y_res = Y - model_y.predict()
    model_d = sm.OLS(D, sm.add_constant(tp_basis)).fit()
    D_res = D - model_d.predict()
    dml_model = sm.OLS(Y_res, sm.add_constant(D_res)).fit()
    causal_effect_avg = dml_model.params[1]
    
    # Save Results
    results = {
        "analysis_type": "ST-VCM",
        "n_observations": n_obs,
        "causal_effect_avg": float(causal_effect_avg),
        "temporal_efficiency": temporal_efficiency,
        "data_points": [
            {
                "iso3c": iso3,
                "year": int(y),
                "gdp": float(g),
                "health_exp": float(he),
                "life_expectancy": float(le),
                "beta_st": float(b) # Spatio-Temporal Efficiency
            }
            for iso3, y, g, he, le, b in zip(
                df["iso3c"], df["year"], df["gdp_pc_usd"], D, Y, beta_surface
            )
        ]
    }
    
    if not os.path.exists(DASHBOARD_DIR):
        os.makedirs(DASHBOARD_DIR)
        
    with open(os.path.join(DASHBOARD_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=4)
    print("Spatio-Temporal VCM (ST-VCM) analysis complete.")

if __name__ == "__main__":
    run_analysis()
