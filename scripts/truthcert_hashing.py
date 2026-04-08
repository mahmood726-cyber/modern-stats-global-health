import hashlib
import json
import os
from datetime import datetime

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_manifest(data_dir, output_file):
    manifest = {
        "project": "modern-stats-global-health",
        "timestamp": datetime.now().isoformat(),
        "files": []
    }
    
    # Files often have creation/modification times that act as fetch_timestamps
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        if os.path.isfile(file_path) and filename != "manifest.json":
            file_hash = compute_sha256(file_path)
            # Use file modification time as fetch_timestamp
            fetch_time = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            
            manifest["files"].append({
                "filename": filename,
                "sha256": file_hash,
                "size_bytes": os.path.getsize(file_path),
                "fetch_timestamp": fetch_time
            })
            
    with open(output_file, "w") as f:
        json.dump(manifest, f, indent=4)
    print(f"Manifest with fetch timestamps written to {output_file}")

if __name__ == "__main__":
    generate_manifest("data", "data/manifest.json")
