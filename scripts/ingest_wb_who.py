import pandas as pd
import requests
import json
import os
import hashlib
from datetime import datetime

# WB Indicators
WB_INDICATORS = {
    "NY.GDP.PCAP.CD": "gdp_pc_usd",
    "SH.XPD.CHEX.GD.ZS": "health_exp_pct_gdp"
}

# WHO Indicators
WHO_INDICATORS = {
    "WHOSIS_000001": "life_expectancy"
}

DATA_DIR = "data"

def fetch_wb(indicator, name):
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=1000&date=2010:2024"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        if len(data) > 1:
            records = data[1]
            rows = []
            for rec in records:
                iso2 = rec.get("country", {}).get("id")
                year = rec.get("date")
                val = rec.get("value")
                if iso2 and year and val is not None:
                    rows.append({"iso2": iso2, "year": int(year), name: float(val)})
            return pd.DataFrame(rows)
    return None

def fetch_who(indicator, name):
    url = f"https://ghoapi.azureedge.net/api/{indicator}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        value_list = data.get("value", [])
        rows = []
        for rec in value_list:
            iso3c = rec.get("SpatialDim")
            year = rec.get("TimeDim")
            val = rec.get("NumericValue")
            sex = rec.get("Dim1")
            if iso3c and year and val is not None and sex == "SEX_BTSX":
                rows.append({"iso3c": iso3c, "year": int(year), name: float(val)})
        df = pd.DataFrame(rows)
        return df
    return None

def fetch_wb_countries():
    url = "https://api.worldbank.org/v2/country?format=json&per_page=1000"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        if len(data) > 1:
            records = data[1]
            rows = []
            for rec in records:
                iso3 = rec.get("id")
                iso2 = rec.get("iso2Code")
                if iso2 and iso3:
                    rows.append({"iso2": iso2, "iso3c": iso3})
            return pd.DataFrame(rows)
    return None

def ingest():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    print("Fetching country mapping...")
    countries = fetch_wb_countries()
    
    all_wb = []
    for ind, name in WB_INDICATORS.items():
        print(f"Fetching WB {ind}...")
        df = fetch_wb(ind, name)
        if df is not None:
            all_wb.append(df)
            
    if all_wb and countries is not None:
        wb_merged = all_wb[0]
        for df in all_wb[1:]:
            wb_merged = wb_merged.merge(df, on=["iso2", "year"], how="outer")
        
        # Standardize WB to iso3c during ingestion
        wb_final = wb_merged.merge(countries, on="iso2", how="inner").drop(columns=["iso2"])
        wb_final.to_parquet(os.path.join(DATA_DIR, "wb_indicators.parquet"))
        print("World Bank indicators saved with ISO3C mapping.")
        
    for ind, name in WHO_INDICATORS.items():
        print(f"Fetching WHO {ind}...")
        df = fetch_who(ind, name)
        if df is not None:
            df.to_parquet(os.path.join(DATA_DIR, f"who_{name}.parquet"))
            print(f"WHO {name} saved.")

if __name__ == "__main__":
    ingest()
