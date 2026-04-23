import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.gam.api import BSplines
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_PATH = PROJECT_ROOT / "results.json"

def run_analysis():
    # 1. DATA LOADING
    wb = pd.read_parquet(DATA_DIR / "wb_indicators.parquet")
    who = pd.read_parquet(DATA_DIR / "who_life_expectancy.parquet")
    df = wb.merge(who, on=["iso3c", "year"], how="inner")
    df = df.dropna(subset=["gdp_pc_usd", "health_exp_pct_gdp", "life_expectancy"])
    
    if df.empty:
        print("No panel data found.")
        return

    # Sort for surface estimation
    df = df.sort_values(["year", "gdp_pc_usd"])
    Y = df["life_expectancy"].values
    D = df["health_exp_pct_gdp"].values
    X_log = np.log10(df["gdp_pc_usd"].values)
    T = df["year"].values
    T_norm = (T - T.min()) / (T.max() - T.min())
    
    # 2. ST-VCM CORE MODEL
    bs_gdp = BSplines(X_log, df=[5], degree=[3])
    basis_gdp = bs_gdp.transform(X_log)
    bs_year = BSplines(T_norm, df=[4], degree=[3])
    basis_year = bs_year.transform(T_norm)
    
    n_obs = len(df)
    n_gdp = basis_gdp.shape[1]
    n_year = basis_year.shape[1]
    tp_basis = np.zeros((n_obs, n_gdp * n_year))
    for i in range(n_gdp):
        for j in range(n_year):
            tp_basis[:, i * n_year + j] = basis_gdp[:, i] * basis_year[:, j]
            
    tp_interaction = tp_basis * D[:, np.newaxis]
    X_st_vcm = np.hstack([sm.add_constant(tp_basis), tp_interaction])
    model = sm.OLS(Y, X_st_vcm).fit()
    
    interaction_coeffs = model.params[1 + (n_gdp * n_year):]
    beta_surface = tp_basis @ interaction_coeffs
    df["beta_st"] = beta_surface

    # 3. BOOTSTRAP STRESS TEST (10 iterations for speed, 100 for journal)
    print("Running Bootstrap Stress Test...")
    boot_betas = []
    for b in range(10):
        idx = np.random.choice(n_obs, n_obs, replace=True)
        try:
            m_boot = sm.OLS(Y[idx], X_st_vcm[idx, :]).fit()
            i_coeffs_boot = m_boot.params[1 + (n_gdp * n_year):]
            boot_betas.append(tp_basis @ i_coeffs_boot)
        except:
            continue
    
    boot_betas_arr = np.array(boot_betas)
    beta_std = np.std(boot_betas_arr, axis=0)
    
    # Resilience Score: 1 - CV (Coefficient of Variation)
    mask = np.abs(beta_surface) > 1e-5
    resilience_score = 1.0 - np.mean(beta_std[mask] / np.abs(beta_surface[mask]))
    print(f"Model Resilience Score: {resilience_score:.3f}")

    # 4. POLICY COUNTERFACTUALS (Scenario: +2% Health Spending)
    # Gain = beta(GDP, Year) * 2
    df["gain_2pct"] = df["beta_st"] * 2.0
    
    # Efficiency Frontier: 75th percentile of beta for this year
    frontier = df.groupby("year")["beta_st"].transform(lambda x: x.quantile(0.75))
    df["gain_frontier"] = np.maximum(0, (frontier - df["beta_st"]) * df["health_exp_pct_gdp"])
    
    # Final Metrics
    total_gain_2pct = df[df["year"] == 2019]["gain_2pct"].mean()
    total_gain_frontier = df[df["year"] == 2019]["gain_frontier"].mean()

    # Save Results
    results = {
        "analysis_type": "ST-VCM-Policy",
        "resilience_score": float(resilience_score),
        "policy_gains": {
            "avg_gain_2pct": float(total_gain_2pct),
            "avg_gain_frontier": float(total_gain_frontier)
        },
        "data_points": [
            {
                "iso3c": iso3,
                "year": int(y),
                "gdp": float(g),
                "health_exp": float(he),
                "life_expectancy": float(le),
                "beta_st": float(b),
                "beta_std": float(s),
                "gain_2pct": float(g2),
                "gain_frontier": float(gf)
            }
            for iso3, y, g, he, le, b, s, g2, gf in zip(
                df["iso3c"], df["year"], df["gdp_pc_usd"], D, Y, 
                df["beta_st"], beta_std, df["gain_2pct"], df["gain_frontier"]
            )
        ]
    }
    
    with RESULTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print(f"Stress Test and Policy Simulation complete. Results saved to {RESULTS_PATH}.")

if __name__ == "__main__":
    run_analysis()
