import os
import shutil
import hashlib
import json
from datetime import datetime

# Source paths (from existing lakehouses)
IHME_SOURCE = r"C:\Projects\ihme-data-lakehouse\data\silver\gbd_results\native"
WB_SOURCE = r"C:\Projects\wb-data-lakehouse\data\harmonized" # Check if this exists
CTGOV_SOURCE = r"C:\Projects\ctgov-analyses\ctgov_transparency_intelligence\data"

# Target paths
DATA_DIR = "data"

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def prepare_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    manifest = {
        "project": "modern-stats-global-health",
        "timestamp": datetime.now().isoformat(),
        "files": []
    }
    
    # 1. IHME Data
    if os.path.exists(IHME_SOURCE):
        for filename in os.listdir(IHME_SOURCE):
            if filename.endswith(".parquet"):
                src = os.path.join(IHME_SOURCE, filename)
                dst = os.path.join(DATA_DIR, f"ihme_{filename}")
                shutil.copy2(src, dst)
                print(f"Copied IHME {filename}")
                manifest["files"].append({
                    "source": "IHME GBD 2021",
                    "filename": f"ihme_{filename}",
                    "sha256": compute_sha256(dst)
                })

    # 2. CT.gov Data (RDS to start, but I might need to convert it)
    if os.path.exists(CTGOV_SOURCE):
        for filename in os.listdir(CTGOV_SOURCE):
            if filename.endswith(".rds"):
                src = os.path.join(CTGOV_SOURCE, filename)
                dst = os.path.join(DATA_DIR, filename)
                shutil.copy2(src, dst)
                print(f"Copied CT.gov {filename}")
                manifest["files"].append({
                    "source": "ClinicalTrials.gov",
                    "filename": filename,
                    "sha256": compute_sha256(dst)
                })
                
    # 3. World Bank Placeholder (if harmonized data isn't easily found, we'll fetch it)
    # For now, let's just write the manifest
    with open(os.path.join(DATA_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)
    print("Initial manifest written.")

if __name__ == "__main__":
    prepare_data()
