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
    # 1. DATA LOADING & HARMONIZATION
    wb = pd.read_parquet(os.path.join(DATA_DIR, "wb_indicators.parquet"))
    who = pd.read_parquet(os.path.join(DATA_DIR, "who_life_expectancy.parquet"))
    ihme = pd.read_parquet(os.path.join(DATA_DIR, "ihme_dalys.parquet"))
    
    # Harmonize IHME (using location_name as bridge if iso3c missing)
    # Actually, let's try to map IHME's United Kingdom, USA, etc. to ISO
    # For a quick journal-style prototype, we'll use WHO and WB mainly, 
    # and if IHME has 'location_name', we'll try a simple merge.
    
    # Merge WB and WHO first
    df = wb.merge(who, on=["iso3c", "year"], how="inner")
    
    # Focus on 2019 cross-section
    df_2019 = df[df["year"] == 2019].dropna(subset=["gdp_pc_usd", "health_exp_pct_gdp", "life_expectancy"])
    
    if df_2019.empty:
        print("No data found for 2019 causal analysis.")
        return

    # Sort for plotting
    df_2019 = df_2019.sort_values("gdp_pc_usd")
    
    Y = df_2019["life_expectancy"].values
    D = df_2019["health_exp_pct_gdp"].values
    X_log = np.log10(df_2019["gdp_pc_usd"].values)
    
    # 2. DOUBLE MACHINE LEARNING (DML) - Orthogonalization
    # We estimate the causal effect of Health Exp (D) on Life Exp (Y) 
    # while non-parametrically controlling for GDP (X).
    
    bs_nuisance = BSplines(X_log, df=[5], degree=[3])
    
    # Residualize Y (Outcome)
    model_y = GLMGam(Y, smoother=bs_nuisance).fit()
    Y_res = Y - model_y.predict()
    
    # Residualize D (Treatment)
    model_d = GLMGam(D, smoother=bs_nuisance).fit()
    D_res = D - model_d.predict()
    
    # The Causal Partial Effect: OLS of residuals
    dml_model = sm.OLS(Y_res, sm.add_constant(D_res)).fit()
    causal_effect = dml_model.params[1]
    causal_ci = dml_model.conf_int()[1]
    
    print(f"DML Causal Effect (Health Exp -> Life Exp): {causal_effect:.3f} years per % GDP")
    print(f"95% CI: [{causal_ci[0]:.3f}, {causal_ci[1]:.3f}]")
    
    # 3. DISTRIBUTIONAL QUANTILE SPLINES
    quantiles = [0.1, 0.5, 0.9]
    q_fits = {}
    basis_matrix = bs_nuisance.transform(X_log)
    basis_matrix_const = sm.add_constant(basis_matrix)
    
    for q in quantiles:
        q_model = sm.QuantReg(Y, basis_matrix_const).fit(q=q)
        q_fits[f"q{int(q*100)}"] = q_model.predict(basis_matrix_const)
    
    # Baseline for Non-linearity
    X_lin = sm.add_constant(X_log)
    lin_model = sm.OLS(Y, X_lin).fit()
    y_lin = lin_model.predict(X_lin)
    gam_model = GLMGam(Y, smoother=bs_nuisance).fit()
    y_gam = gam_model.predict()
    
    mean_le = np.mean(Y)
    mean_abs_diff = np.mean(np.abs(y_gam - y_lin))
    pct_divergence = (mean_abs_diff / mean_le) * 100
    
    # Save Results
    results = {
        "analysis_year": 2019,
        "n_countries": len(df_2019),
        "causal_effect": float(causal_effect),
        "causal_ci_lower": float(causal_ci[0]),
        "causal_ci_upper": float(causal_ci[1]),
        "non_linearity_score_pct": float(pct_divergence),
        "data_points": [
            {
                "iso3c": iso3,
                "gdp": float(g),
                "health_exp": float(he),
                "life_expectancy": float(le),
                "linear_fit": float(lf),
                "gam_fit": float(gf),
                "q10": float(q10),
                "q50": float(q50),
                "q90": float(q90),
                "d_res": float(dr),
                "y_res": float(yr)
            }
            for iso3, g, he, le, lf, gf, q10, q50, q90, dr, yr in zip(
                df_2019["iso3c"], df_2019["gdp_pc_usd"], D, Y, y_lin, y_gam, 
                q_fits["q10"], q_fits["q50"], q_fits["q90"], D_res, Y_res
            )
        ]
    }
    
    if not os.path.exists(DASHBOARD_DIR):
        os.makedirs(DASHBOARD_DIR)
        
    with open(os.path.join(DASHBOARD_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=4)
    print("Double Machine Learning analysis complete.")

if __name__ == "__main__":
    run_analysis()
