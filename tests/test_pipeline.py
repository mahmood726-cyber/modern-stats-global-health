import os
import subprocess
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "results.json"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.json"
WB_PATH = PROJECT_ROOT / "data" / "wb_indicators.parquet"
WHO_PATH = PROJECT_ROOT / "data" / "who_life_expectancy.parquet"

def test_ingestion():
    print("Testing Ingestion...")
    # Clean data dir for fresh test (optional, but let's just check if it runs)
    result = subprocess.run(["python", "scripts/ingest_wb_who.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"Ingestion failed: {result.stderr}"
    assert WB_PATH.exists(), "WB data missing"
    assert WHO_PATH.exists(), "WHO data missing"
    print("Ingestion Pass.")

def test_analysis():
    print("Testing Analysis...")
    result = subprocess.run(["python", "models/non_parametric_analysis.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"Analysis failed: {result.stderr}"
    assert RESULTS_PATH.exists(), "Analysis results missing"
    
    with RESULTS_PATH.open("r", encoding="utf-8") as f:
        res = json.load(f)
        assert len(res["data_points"]) > 0, "No countries analyzed"
        assert res["policy_gains"]["avg_gain_2pct"] > 0, "Zero delta unexpected"
    print("Analysis Pass.")

def test_hashing():
    print("Testing TruthCert Hashing...")
    result = subprocess.run(["python", "scripts/truthcert_hashing.py"], capture_output=True, text=True)
    assert result.returncode == 0
    assert MANIFEST_PATH.exists()
    print("Hashing Pass.")

if __name__ == "__main__":
    try:
        test_ingestion()
        test_analysis()
        test_hashing()
        print("\nALL TESTS PASSED.")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
