import os
import subprocess
import json

def test_ingestion():
    print("Testing Ingestion...")
    # Clean data dir for fresh test (optional, but let's just check if it runs)
    result = subprocess.run(["python", "scripts/ingest_wb_who.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"Ingestion failed: {result.stderr}"
    assert os.path.exists("data/wb_indicators.parquet"), "WB data missing"
    assert os.path.exists("data/who_life_expectancy.parquet"), "WHO data missing"
    print("Ingestion Pass.")

def test_analysis():
    print("Testing Analysis...")
    result = subprocess.run(["python", "models/non_parametric_analysis.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"Analysis failed: {result.stderr}"
    assert os.path.exists("dashboard/results.json"), "Analysis results missing"
    
    with open("dashboard/results.json", "r") as f:
        res = json.load(f)
        assert res["n_countries"] > 0, "No countries analyzed"
        assert res["mean_delta"] > 0, "Zero delta unexpected"
    print("Analysis Pass.")

def test_hashing():
    print("Testing TruthCert Hashing...")
    result = subprocess.run(["python", "scripts/truthcert_hashing.py"], capture_output=True, text=True)
    assert result.returncode == 0
    assert os.path.exists("data/manifest.json")
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
