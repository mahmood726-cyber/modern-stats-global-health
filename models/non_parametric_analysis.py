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
    # 1. DATA LOADING
    wb = pd.read_parquet(os.path.join(DATA_DIR, "wb_indicators.parquet"))
    who = pd.read_parquet(os.path.join(DATA_DIR, "who_life_expectancy.parquet"))
    
    # Merge Panel
    df = wb.merge(who, on=["iso3c", "year"], how="inner")
    df_2019 = df[df["year"] == 2019].dropna(subset=["gdp_pc_usd", "health_exp_pct_gdp", "life_expectancy"])
    
    if df_2019.empty:
        print("No data found for 2019 VCM analysis.")
        return

    # Sort by GDP for smooth function estimation
    df_2019 = df_2019.sort_values("gdp_pc_usd")
    
    Y = df_2019["life_expectancy"].values
    D = df_2019["health_exp_pct_gdp"].values
    X_log = np.log10(df_2019["gdp_pc_usd"].values)
    
    # 2. VARYING COEFFICIENT MODEL (VCM)
    # Basis Expansion: Y = Spline(X) + [Spline(X) * D]
    bs = BSplines(X_log, df=[6], degree=[3])
    basis_matrix = bs.transform(X_log)
    n_basis = basis_matrix.shape[1]
    
    # Full Model Matrix
    # [Intercept, Spline_1...Spline_5, Spline_1*D...Spline_5*D]
    X_const = sm.add_constant(basis_matrix)
    interaction_matrix = basis_matrix * D[:, np.newaxis]
    X_vcm = np.hstack([X_const, interaction_matrix])
    
    vcm_model = sm.OLS(Y, X_vcm).fit()
    
    # Extract coefficients (Const:1, Spline:5, Interaction:5)
    # Interaction coefficients start at index 1 + n_basis
    interaction_coeffs = vcm_model.params[1 + n_basis:]
    beta_gdp = basis_matrix @ interaction_coeffs
    
    # 3. DOUBLE MACHINE LEARNING (DML) Baseline
    model_y = GLMGam(Y, smoother=bs).fit()
    Y_res = Y - model_y.predict()
    model_d = GLMGam(D, smoother=bs).fit()
    D_res = D - model_d.predict()
    dml_model = sm.OLS(Y_res, sm.add_constant(D_res)).fit()
    causal_effect_avg = dml_model.params[1]
    
    # 4. QUANTILE SPLINES
    quantiles = [0.1, 0.5, 0.9]
    q_fits = {}
    for q in quantiles:
        q_model = sm.QuantReg(Y, X_const).fit(q=q)
        q_fits[f"q{int(q*100)}"] = q_model.predict(X_const)
    
    # Save Results
    results = {
        "analysis_year": 2019,
        "n_countries": len(df_2019),
        "causal_effect_avg": float(causal_effect_avg),
        "vcm_beta_mean": float(np.mean(beta_gdp)),
        "data_points": [
            {
                "iso3c": iso3,
                "gdp": float(g),
                "health_exp": float(he),
                "life_expectancy": float(le),
                "q10": float(q10),
                "q50": float(q50),
                "q90": float(q90),
                "beta_gdp": float(b)
            }
            for iso3, g, he, le, q10, q50, q90, b in zip(
                df_2019["iso3c"], df_2019["gdp_pc_usd"], D, Y, 
                q_fits["q10"], q_fits["q50"], q_fits["q90"], beta_gdp
            )
        ]
    }
    
    if not os.path.exists(DASHBOARD_DIR):
        os.makedirs(DASHBOARD_DIR)
        
    with open(os.path.join(DASHBOARD_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=4)
    print("VCM analysis complete.")

if __name__ == "__main__":
    run_analysis()
