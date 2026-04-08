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

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_wb(indicator, name):
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=1000&date=2010:2024"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        if len(data) > 1:
            records = data[1]
            rows = []
            for rec in records:
                iso3c = rec.get("country", {}).get("id")
                year = rec.get("date")
                val = rec.get("value")
                if iso3c and year and val is not None:
                    rows.append({"iso3c": iso3c, "year": int(year), name: float(val)})
            df = pd.DataFrame(rows)
            # WB returns 2-char ID by default in some cases, but v2/country/all/ should have 2-char.
            # Let's check. Actually 'id' in 'country' for v2 is usually 2-char.
            # We'll need a mapping if we want iso3c.
            return df
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
        
    countries = fetch_wb_countries()
    if countries is not None:
        countries.to_parquet(os.path.join(DATA_DIR, "country_mapping.parquet"))
        print("Country mapping saved.")

    all_wb = []
    for ind, name in WB_INDICATORS.items():
        print(f"Fetching WB {ind}...")
        df = fetch_wb(ind, name)
        if df is not None:
            all_wb.append(df)
            
    if all_wb:
        wb_merged = all_wb[0]
        for df in all_wb[1:]:
            wb_merged = wb_merged.merge(df, on=["iso3c", "year"], how="outer")
        wb_merged.to_parquet(os.path.join(DATA_DIR, "wb_indicators.parquet"))
        print("World Bank indicators saved.")
        
    for ind, name in WHO_INDICATORS.items():
        print(f"Fetching WHO {ind}...")
        df = fetch_who(ind, name)
        if df is not None:
            df.to_parquet(os.path.join(DATA_DIR, f"who_{name}.parquet"))
            print(f"WHO {name} saved.")

if __name__ == "__main__":
    ingest()
